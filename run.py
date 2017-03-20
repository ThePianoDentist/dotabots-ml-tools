import datetime
import json
import logging
import os
import re
import time

import pyautogui as pa


from neural_net import NeuralNet, Result
from game_inputs import PressKey, ReleaseKey
from units import Hero, LaneCreep

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

LOG_LOCATION = "C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"
LOG_SIGNIFIER = "JSN:"


class Loop:
    """
    Task: Description of behaviour trying to learn. i.e. doublepull
    """
    def __init__(self, parameter_names, db, max_runs, starting_weights=None):
        self.neural_net = NeuralNet(parameter_names, starting_weights)
        self.run_id = None
        self.db = db
        self.max_runs = max_runs

    def go(self):
        run_counter = 0
        #lets you get mouse over dota
        while run_counter < self.max_runs:
            run_counter += 1
            self.run = Run(self.db.get_num_results() + 1)
            print("Hi")
            time.sleep(2.5)
            self.run.start_game()
            self.run.set_logs()  # Shouldnt matter that this occurs after game launch. I only care about logs around pull
            self.run.follow_bot()
            self.run.wait_for_pull() # ASYNCIO time?
            self.run.dump_console()
            self.run.restart()
            self.run.delay(pa.click, 282, 748, delay_secs=3)  # click the skip button
            # At this point the bot script sends the new result to database
            new_result = self.run.read_log()
            self.db.add_run(self.run.id, new_result)
            time.sleep(0.01)  # this is only because I expected game to send result to elastic search. not python
            result = Result(self.db.get_run(self.run.id))
            self.neural_net.add_result(result)
            self.neural_net.iterate_weights_2(100)
            # print(self.neural_net.weights)
            logger.info(self.neural_net)
            self.neural_net.update_params()
            #self.run.read_log()  # TODO this bit can be async whilst we are starting the next game

class Run(object):
    """
    score: rating of how well the double pull went. judged by fraction of creeps that were double pulled
    """

    def __init__(self, id):
        self.id = id
        self.log_suffix = datetime.datetime.today().strftime("%Y-%m-%d") + "_run" + str(self.id)
        self.lane_creeps = []
        self.neutral_creeps = []
        self.hero = None
        self.damage_spread_neutral = 0
        self.damage_spread_lane = 0

    def set_logs(self):
        self.single_log_line("con_logfile_suffix %s" % self.log_suffix)

    @classmethod
    def launch_game(cls):
        logger.info("Launching Game")
        cls.delay(cls.click_pic, 'playdota.png')
        cls.delay(cls.click_pic, 'createlobby.png')
        cls.delay(cls.click_pic, 'startgame.png')
        cls.delay(pa.click, 282, 748, delay_secs=10)
        cls.delay(PressKey, 0x1C, delay_secs=8)
        cls.delay(ReleaseKey, 0x1C)
        cls.delay(pa.typewrite, "-startgame")
        cls.delay(PressKey, 0x1C)
        cls.delay(ReleaseKey, 0x1C)

    @classmethod
    def single_log_line(cls, log_string):
        cls.delay(PressKey, 0x27)
        ReleaseKey(0x27)
        cls.delay(pa.typewrite, log_string)
        cls.delay(cls.click_pic, 'submit.png')  # Pressing enter doesnt seem to work here?
        cls.delay(PressKey, 0x27)
        ReleaseKey(0x27)
        pa.moveRel(25, 25)  # Cannot recognise submit button if cursor still over it

    @classmethod
    def wait_for_pull(cls):
        # we can give hero a tp scroll and use image to know when reload
        logger.info("Waiting for double pull to occur")
        time.sleep(13)  # TODO this is terrible
        # while not pa.locateOnScreen(os.getcwd() + '\\button_images\\115.png'):
        #     time.sleep(0.001)
        # else:
        #     logger.info("Found sgnifier. Pull over. Results sent")
        #     return

    @classmethod
    def start_game(cls):
        logger.info("Starting game")
        cls.single_log_line("dota_start_game")

    @classmethod
    def restart(cls):
        logger.info("Restarting game")
        cls.single_log_line("restart")

    @classmethod
    def follow_bot(cls):
        logger.info("Clicking bot portrait to follow bot")
        # TODO have these coords depend on what slot bot is in
        pa.click(744, 103)
        pa.click(730, 927, clicks=2)

    @classmethod
    def leave_game(cls):
        logger.info("Leaving Game")
        cls.delay(PressKey, 0x27)
        cls.delay(ReleaseKey, 0x27)
        cls.delay(pa.typewrite, "disconnect")
        cls.delay(PressKey, 0x1C)
        cls.delay(ReleaseKey, 0x1C)
        cls.delay(PressKey, 0x27)
        cls.delay(ReleaseKey, 0x27)
        cls.delay(cls.click_pic, 'leave.png', delay_secs=2)
        cls.delay(cls.click_pic, 'leave_confirm.png')

    @classmethod
    def dump_console(cls):
        logger.info("Dumping console")
        cls.single_log_line("condump")

    @staticmethod
    def get_coords_pic(picname):
        return pa.locateCenterOnScreen(os.getcwd() + '\\button_images\\' + picname)

    @classmethod
    def click_pic(cls, picname):
        coords = cls.get_coords_pic(picname)
        if not coords:
            raise Exception("Could not find button")
        pa.moveTo(coords)
        time.sleep(2)
        pa.click(coords)

    @staticmethod
    def delay(func, *args, **kwargs):
        secs = kwargs.pop("delay_secs", 0.1)
        logger.info("Sleeping for %s seconds" % secs)
        time.sleep(secs)
        return func(*args, **kwargs)

    def read_log(self):
        logger.info("Parsing log file")
        # TODO log suffix isnt working properly now. Am i using it wrong?
        #logfile = "console" + self.log_suffix + ".log"
        logfile = "condump%s.txt" % str((self.id - 1)).zfill(3)
        with open(LOG_LOCATION + "\\" + logfile, "r+") as f:
            # print(f.read())
            lines = re.findall("\[VScript\] %s([^\n]+)\n" % LOG_SIGNIFIER, f.read())  # would readlines and a generator be better?
            for line in lines:
                print(line)
                return line  # TODO only allowing it to read one line. is this too restrictive?
                data = json.loads(line)
                self.db.index(index=self.task, doc_type="run", id=self.id)

    # TODO add something to pause/stop script if loses focus on dota window.
    # i.e. stop typing random stuff in the code by accident!
