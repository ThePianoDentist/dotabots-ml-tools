import fileinput
import re
import numpy
import os
#from scipy.special import expit need blas on pc

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

FUNCTION_LOCATION = os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/scripts/vscripts/bots/neural_net.lua")


class Result:
    """
    Result expects dictionary as input
    """
    def __init__(self, result_dict):
        # TODO add incoming damage stuff?
        # These are proportionality factors not actual values
        self.hero_movespeed = result_dict["hero_movespeed"]
        self.hero_attackspeed = result_dict["hero_attackspeed"]
        self.hero_attackrange = result_dict["hero_attackrange"]
        self.hero_attackdamage = result_dict["hero_attackdamage"]

        self.fraction_neutral_left = result_dict["fraction_neutral_left"]
        self.neutral_total_eff_hp = result_dict["neutral_total_eff_hp"]  # use effective hp?
        self.targeted_neutral_eff_hp = result_dict["targeted_neutral_eff_hp"]

        self.fraction_lane_left = result_dict["fraction_lane_left"]
        self.lane_total_eff_hp = result_dict["lane_total_eff_hp"]
        self.targeted_lane_eff_hp = result_dict["targeted_lane_eff_hp"]

        self.damage_spread_neutral = result_dict["damage_spread_neutral"]
        self.damage_spread_lane = result_dict["damage_spread_lane"]

        # Outputs
        self.success = result_dict["success"]

    @property
    def input(self):
        return numpy.array([
            self.hero_movespeed, self.hero_attackspeed, self.hero_attackrange, self.hero_attackdamage,
            self.fraction_neutral_left, self.neutral_total_eff_hp, self.targeted_neutral_eff_hp, self.fraction_lane_left,
            self.lane_total_eff_hp, self.targeted_lane_eff_hp, self.damage_spread_neutral,
            self.damage_spread_lane
        ])

    @property
    def output(self):
        return numpy.array([self.success])


class NeuralNet:
    """
    A lot of ideas learnt/taken from http://iamtrask.github.io/2015/07/12/basic-python-network/
    """
    # TODO do I really need so many nodes. can the net be more lightweight?
    def __init__(self, parameter_names, weights=None):
        self.parameter_names = parameter_names
        # These are normal python lists. not numpy arrays. because you cannot nicely make an empty 2d numpy array,
        # then add to it. We will just convert to numpy arrays when necessary
        self.input = []
        self.output = [] # TODO does a simple 0, 1 for success/failure make sense when you can fail from being too late, or too early?
        self.hidden = []  # Dont use as property. would lead to recalculating hidden for error() and update_weights()
        numpy.random.seed(1)  # Makes random number distribution the same over different runs. helps with testing (program_change = your_change)
        numpy.random.seed(1)  # Makes random number distribution the same over different runs. helps with testing (program_change = your_change)
        self.weights = 2 * numpy.random.random((self.num_inputs, 1)) - 1 if not weights else weights
        self.hidden_layers = 2  # currently just doing simple. if this going to be a tool for other people to use. probably want to allow them to specify style of net
        self.nodes_per_layer = len(parameter_names)  # For multilayer nets...do you have same node num in each layer?
        self.learning_rate = 1
        if self.hidden_layers == 2:  # should prob just delete one layer code. trying to make handle layers/node setup dynamic is probably what theanos and kerbaras and stuff for
            # TODO should probably be tuples rather than these hacky dicts
            self.hidden = {0: [], 1: []}
            self.weights = {0: 2 * numpy.random.random((self.num_inputs, self.num_inputs + 1)) - 1,
                            1: 2 * numpy.random.random((self.num_inputs + 1, 1)) - 1}

        self.update_params()

        """
        http://stats.stackexchange.com/questions/181/how-to-choose-the-number-of-hidden-layers-and-nodes-in-a-feedforward-neural-netw
        In sum, for most problems, one could probably get decent performance (even without a second optimization step)
         by setting the hidden layer configuration using just two rules: (i) number of hidden layers equals one; and
        (ii) the number of neurons in that layer is the mean of the neurons in the input and output layers.
        """

        # I think the above saying most problems can use one layer has to be ignored
        # I dont think its possible to 'learn' against combinations of inputs affecting output with a second layer

    def add_result(self, new_result):
        self.input.append(new_result.input)   # TODO is append the best thing here?
        self.output.append(new_result.output)
        # Don't need to update hidden as update_hidden will be called setting it to new length. Should I explicitly block this though?

    def update_hidden_2(self):
        self.hidden[0] = self.sigmoid(numpy.dot(numpy.array(self.input), self.weights[0]))  # TODO repalce with scipy func
        self.hidden[1] = self.sigmoid(numpy.dot(numpy.array(self.hidden[0]), self.weights[1]))  # TODO repalce with scipy func

    def update_hidden(self):
        self.hidden = self.sigmoid(numpy.dot(numpy.array(self.input), self.weights))  # TODO repalce with scipy func

    @property # TODO probably should be a property if we set it once then never change. overcomplicating stuff to use fancy features for no reason I thinbk.
    def num_inputs(self):
        # Needs updating if we ever have more complex reward systems which ahve multiple output variables
        return len(self.parameter_names) - 1

    @property
    def error(self):
        return numpy.array(self.output) - self.hidden

    @property
    def error_2(self):
        return numpy.array(self.output) - self.hidden[1]

    # @property
    # def error_1(self):
    #     return self.error_2 * l2_delta.dot(numpy.array(self.weights[1]).T)
    #     return numpy.array(self.output) - self.hidden[0]

    def update_weights_2(self):

        weights_two_shift = self.learning_rate * (numpy.array(self.output) - self.hidden[1]) * self.deriv_sigmoid(self.hidden[1])
        self.weights[1] += numpy.dot(numpy.array(self.hidden[0]).T, weights_two_shift)
        self.weights[0] += numpy.dot(numpy.array(self.input).T,
                                     weights_two_shift * self.deriv_sigmoid(self.hidden[0]))
        # logger.info("Weights updated (0): %s" % self.weights[0])
        # logger.info("Weights updated (1): %s" % self.weights[1])

    # TODO add a function that terminates on;condump a clause indicating we can't do better and are wasting time looping furhter
    def iterate_weights(self, iterations):
        for i in range(iterations):
            self.update_hidden()
            self.update_weights()
        logger.debug("Final error: %s" % str(numpy.mean(numpy.abs(self.error))))

    # TODO add a function that terminates on a clause indicating we can't do better and are wasting time looping furhter
    def iterate_weights_2(self, iterations):
        for i in range(iterations):
            self.update_hidden_2()
            self.update_weights_2()
        logger.debug("Final error: %s" % str(numpy.mean(numpy.abs(self.error_2))))

    @staticmethod
    def sigmoid(x):
        """
        :param x:
        :return: Returns x scaled to between [0, 1] # TODO is this interval correct or is it (0, 1)
        """
        return 1 / (1 + numpy.exp(-x))

    @staticmethod
    def deriv_sigmoid(x):
        """
        :param x:
        :return:
        """
        return x * (1 - x)

    @staticmethod
    def change_script_parameters(contents, parameter_name, new_value):
        # TODO add error handling for if regex does not match
        if re.search('(params\[[\'"]p_%s[\'"]\]\s?=)(.*?)( --dynamic)' % parameter_name, contents):
            # TODO why does this except?
            # return re.sub('(params\[[\'"]p_%s[\'"]\]\s?=).*?( --dynamic)' % parameter_name, r'\1%s\2' % new_value,
            #               contents)
            return re.sub('(params\[[\'"]p_%s[\'"]\]\s?=).*?( --dynamic)' % parameter_name,
                          r'params["p_%s"] = %s --dynamic' % (parameter_name, new_value),
                          contents)
        else:
            logger.warning("Regex replace for %s failed" % parameter_name)
            return contents

    @staticmethod
    def change_script_parameters_weights1_index(contents, index, new_value):
        lua_index = index + 1  # Lua lists start at 1
        # TODO add error handling for if regex does not match
        if re.search('(weights_1\[%s\]\s?=\s?\{)(.*?)(\} --dynamic)' % lua_index, contents):
            # TODO why does this except?
            # return re.sub('(params\[[\'"]p_%s[\'"]\]\s?=).*?( --dynamic)' % parameter_name, r'\1%s\2' % new_value,
            #               contents)
            return re.sub('(weights_1\[%s\]\s?=\s?\{).*?(\} --dynamic)' % lua_index,
                          r'weights_1[%s] = {%s} --dynamic' % (lua_index, new_value[index][0]),
                          contents)
        else:
            logger.error("Regex replace for %s failed" % index)
            return contents

    @staticmethod
    def change_script_parameters_weights0_index(contents, index, new_values):
        lua_index = index + 1  # Lua lists start at 1
        # TODO add error handling for if regex does not match
        if re.search('(weights_0\[%s\]\s?=\s?\{)(.*?)(\} --dynamic)' % lua_index, contents):
            # TODO why does this except?
            # return re.sub('(params\[[\'"]p_%s[\'"]\]\s?=).*?( --dynamic)' % parameter_name, r'\1%s\2' % new_value,
            #               contents)
            replacement_str = r'weights_0[%s] = {' % lua_index
            for weight in new_values[index]:
                replacement_str += '{%s},' % weight
            replacement_str += '} --dynamic'
            return re.sub('(weights_0\[%s\]\s?=\s?\{).*?(\} --dynamic)' % lua_index,
                          replacement_str,
                          contents)
        else:
            logger.error("Regex replace for %s failed" % lua_index)
            return contents

    def update_lua_run_num(self, contents):
        # TODO Add error handling?
        return re.sub('run = \d+ --dynamic',
                      'run = %s --dynamic' % (len(self.input) + 1),  # +1 because we want for next run. not for run just gone
                      contents)

    def update_params(self):
        """
        Open lua script file with parameters in and update them for next run
        (This could also be implemented with fileinput) http://stackoverflow.com/questions/3043849/use-regular-expression-with-fileinput
        :return:
        """
        with open(FUNCTION_LOCATION, "r+") as f:
            contents = f.read()
            for i in range(13):
                contents = self.change_script_parameters_weights1_index(contents, i, self.weights[1])
                if i == 12:
                    break
                contents = self.change_script_parameters_weights0_index(contents, i, self.weights[0])
            contents = self.update_lua_run_num(contents)
            # f.truncate()
            # f.seek(0)
            # f.write(contents)
            # print(contents)

        # Was seeing some weird behaviour with truncate and seek (Added weird line that broke script). so just writing a whole 'new' file
        with open(FUNCTION_LOCATION, "w+") as f:
            f.write(contents)

    # def __str__(self):
    #     # TODO can probably make this a fancy one-liner
    #     out = ""
    #     for i, name in enumerate(self.parameter_names):
    #         if name == "success":
    #             break
    #         out += "Name: %s, Weight: %s\n" % (name, self.weights[i])
    #     return out

    # def __str__(self):
    #     out = ""
    #     for key, value in self.weights.items():
    #         out += "k: %s\n%s\n\n" % (key, value)
    #     return out