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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_LOCATION = "C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"
LOG_SIGNIFIER = "JSN:"


class Loop():
    """
    Task: Description of behaviour trying to learn. i.e. doublepull
    """
    def __init__(self, task, parameter_names, db, max_runs):
        self.task = task
        self.neural_net = NeuralNet(parameter_names)
        self.run = None
        self.db = db
        self.max_runs = max_runs

    def go(self):
        run_counter = 0
        while run_counter < self.max_runs:
            run_counter += 1
            self.run = Run(run_counter)
            print("Hi")
            self.run.launch_game()
            #self.run.set_logs()  # Shouldnt matter that this occurs after game launch. I only care about logs around pull
            time.sleep(5)
            self.run.dump_console()
            time.sleep(5)
            #At this point the bot script sends the new result to database
            self.run.leave_game()  # ASYNCIO time?
            result = Result(self.db.get_run(self.task, self.run.id))
            self.neural_net.add_result(result)
            self.neural_net.update_hidden()
            self.neural_net.update_weights()
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
        self.delay(PressKey, 0x27)
        self.delay(ReleaseKey, 0x27)
        self.delay(pa.typewrite, "con_logfile_suffix %s" % self.log_suffix)
        self.delay(PressKey, 0x27, delay_secs=2)
        self.delay(ReleaseKey, 0x27)

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
        cls.delay(PressKey, 0x27)
        cls.delay(ReleaseKey, 0x27)
        cls.delay(pa.typewrite, "condump")
        cls.delay(PressKey, 0x1C)
        cls.delay(ReleaseKey, 0x1C)
        cls.delay(PressKey, 0x27)
        cls.delay(ReleaseKey, 0x27)

    @staticmethod
    def get_coords_pic(picname):
        return pa.locateOnScreen(os.getcwd() + '\\button_images\\' + picname)

    @classmethod
    def click_pic(cls, picname):
        coords = cls.get_coords_pic(picname)
        if not coords:
            raise Exception("Could not find button")
        pa.center(coords)
        pa.click(coords[:2])

    @staticmethod
    def delay(func, *args, **kwargs):
        secs = kwargs.pop("delay_secs", 1)
        logger.info("Sleeping for %s seconds" % secs)
        time.sleep(secs)
        return func(*args, **kwargs)

    def read_log(self):
        logger.info("Parsing log file")
        logfile = "console" + self.log_suffix + ".log"
        with open(LOG_LOCATION + "\\" + logfile, "r+") as f:
            # print(f.read())
            lines = re.findall("\[VScript\] %s([^\n]+)\n" % LOG_SIGNIFIER, f.read())  # would readlines and a generator be better?
            for line in lines:
                print(line)
                data = json.loads(line)
                if data.type == "parameter":
                    # type = "parameters", hero_data = hero_data, lane_creeps = lane_creeps, neutral_creeps = neutral_creeps,
                    # damage_spread_lane = damage_spread_lane, damage_spread_neutral = damage_spread_neutral
                    self.hero = Hero(data.hero_data)
                    self.damage_spread_neutral = data.damage_spread_neutral
                    self.damage_spread_lane = data.damage_spread_lane
                    for lc in data.lane_creeps:
                        self.lane_creeps.append(LaneCreep(lc))
                    for nc in data.neutral_creeps:
                        self.neutral_creeps.append(LaneCreep(nc))