import fileinput
import re
import numpy
import os
#from scipy.special import expit need blas on pc

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FUNCTION_LOCATION = os.path.normpath("C:/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/scripts/vscripts/bots/hero_funcs/pulling.lua")


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

        self.fraction_neutrals_left = result_dict["fraction_neutrals_left"]
        self.neutral_total_hp = result_dict["neutral_total_hp"]  # use effective hp?
        self.neutral_most_targeted_hp = result_dict["neutral_most_targeted_hp"]

        self.num_lane_creeps = result_dict["num_lane_creeps"]
        self.lane_creeps_total_hp = result_dict["lane_creeps_total_hp"]
        self.lane_creeps_most_targeted_hp = result_dict["lane_creeps_most_targeted_hp"]

        self.damage_spread_neutral = result_dict["damage_spread_neutral"]
        self.damage_spread_lane = result_dict["damage_spread_lane"]

        # Outputs
        self.success = result_dict["success"]
    # def __init__(self, hero_movespeed, hero_attackspeed, hero_attackrange, hero_attackdamage, fraction_neutrals_left,
    #              neutral_total_hp, neutral_most_targeted_hp, num_lane_creeps, lane_creeps_total_hp,
    #              lane_creeps_most_targeted_hp, damage_spread_neutral, damage_spread_lane, success
    #              ):
    #
    #     # These are proportionality factors not actual values
    #     self.hero_movespeed = hero_movespeed
    #     self.hero_attackspeed = hero_attackspeed
    #     self.hero_attackrange = hero_attackrange
    #     self.hero_attackdamage = hero_attackdamage
    #
    #     self.fraction_neutrals_left = fraction_neutrals_left
    #     self.neutral_total_hp = neutral_total_hp  # use effective hp?
    #     self.neutral_most_targeted_hp = neutral_most_targeted_hp
    #
    #     self.num_lane_creeps = num_lane_creeps
    #     self.lane_creeps_total_hp = lane_creeps_total_hp
    #     self.lane_creeps_most_targeted_hp = lane_creeps_most_targeted_hp
    #
    #     self.damage_spread_neutral = damage_spread_neutral
    #     self.damage_spread_lane = damage_spread_lane
    #
    #     # Outputs
    #     self.success = success

    @property
    def input(self):
        return numpy.array([
            self.hero_movespeed, self.hero_attackspeed, self.hero_attackrange, self.hero_attackdamage,
            self.fraction_neutrals_left, self.neutral_total_hp, self.neutral_most_targeted_hp, self.num_lane_creeps,
            self.lane_creeps_total_hp, self.lane_creeps_most_targeted_hp, self.damage_spread_neutral,
            self.damage_spread_lane
        ])

    @property
    def output(self):
        return numpy.array([self.success])


class NeuralNet:
    """
    A lot of ideas learnt/taken from http://iamtrask.github.io/2015/07/12/basic-python-network/
    """
    def __init__(self, parameter_names):
        self.parameter_names = parameter_names
        # These are normal python lists. not numpy arrays. because you cannot nicely make an empty 2d numpy array,
        # then add to it. We will just convert to numpy arrays when necessary
        self.input = []
        self.output = [] # TODO does a simple 0, 1 for success/failure make sense when you can fail from being too late, or too early?
        self.hidden = []  # Dont use as property. would lead to recalculating hidden for error() and update_weights()
        numpy.random.seed(1)  # Makes random number distribution the same over different runs. helps with testing (program_change = your_change)
        numpy.random.seed(1)  # Makes random number distribution the same over different runs. helps with testing (program_change = your_change)
        self.weights = 2 * numpy.random.random((self.num_inputs, 1)) - 1
        self.hidden_layers = 1  # currently just doing simple. if this going to be a tool for other people to use. probably want to allow them to specify style of net
        self.nodes_per_layer = len(parameter_names)  # For multilayer nets...do you have same node num in each layer?

        """
        http://stats.stackexchange.com/questions/181/how-to-choose-the-number-of-hidden-layers-and-nodes-in-a-feedforward-neural-netw
        In sum, for most problems, one could probably get decent performance (even without a second optimization step)
         by setting the hidden layer configuration using just two rules: (i) number of hidden layers equals one; and
        (ii) the number of neurons in that layer is the mean of the neurons in the input and output layers.
        """

    def add_result(self, new_result):
        self.input.append(new_result.input)   # TODO is append the best thing here?
        self.output.append(new_result.output)
        # Don't need to update hidden as update_hidden will be called setting it to new length. Should I explicitly block this though?

    def update_hidden(self):
        self.hidden = self.sigmoid(numpy.dot(numpy.array(self.input), self.weights))  # TODO repalce with scipy func

    @property
    def num_inputs(self):
        # Needs updating if we ever have more complex reward systems which ahve multiple output variables
        return len(self.parameter_names) - 1

    @property
    def error(self):
        return numpy.array(self.output) - self.hidden

    def update_weights(self):
        self.weights += numpy.dot(numpy.array(self.input).T, self.error * self.deriv_sigmoid(self.hidden))

    # TODO add a function that terminates on a clause indicating we can't do better and are wasting time looping furhter
    def find_weights(self, iterations):
        for i in range(iterations):
            self.update_hidden()
            self.update_weights()
        return self.weights

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
        #import pdb; pdb.set_trace()
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

    def update_params(self):
        """
        Open lua script file with parameters in and update them for next run
        (This could also be implemented with fileinput) http://stackoverflow.com/questions/3043849/use-regular-expression-with-fileinput
        :return:
        """
        with open(FUNCTION_LOCATION, "r+") as f:
            contents = f.read()
            for i, param in enumerate(self.parameter_names):
                if param == "success":  # Finished inputs
                    break
                contents = self.change_script_parameters(contents, param, self.weights[i][0])
            f.truncate()
            f.seek(0)
            f.write(contents)