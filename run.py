import datetime
import os
import re
import time
import logging
import json

import pyautogui as pa

#from game_inputs import PressKey, ReleaseKey
import game_inputs
from units import Hero, LaneCreep

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LOG_LOCATION = "C:\Program Files (x86)\Steam\steamapps\common\dota 2 beta\game\dota"
LOG_SIGNIFIER = "JSN:"

def delay(func):
    from functools import wraps
    @wraps(func)
    def inner(*args, sleep=1, **kwargs):
        from time import sleep as slp
        slp(sleep)
        return func(*args, **kwargs)

    return inner


PressKey = delay(game_inputs.PressKey)
ReleaseKey = delay(game_inputs.ReleaseKey)
typewrite = delay(pa.typewrite)
click = delay(pa.click)


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
        PressKey(0x27)
        ReleaseKey(0x27)
        typewrite("con_logfile_suffix %s" % self.log_suffix)
        PressKey(0x27, sleep=2)
        ReleaseKey(0x27)

    @classmethod
    def launch_game(cls):
        logger.info("Launching Game")
        click_pic = delay(cls.click_pic)
        click_pic('playdota.png')
        click_pic('createlobby.png')
        click_pic('startgame.png')
        click(282, 748, delay_secs=10)
        PressKey(0x1C, delay_secs=8)
        ReleaseKey(0x1C)
        typewrite("-startgame")
        PressKey(0x1C)
        ReleaseKey(0x1C)

    @classmethod
    def leave_game(cls):
        logger.info("Leaving Game")
        click_pic = delay(cls.click_pic)
        PressKey(0x27)
        ReleaseKey(0x27)
        typewrite("disconnect")
        PressKey(0x1C)
        ReleaseKey(0x1C)
        PressKey(0x27)
        ReleaseKey(0x27)
        click_pic('leave.png', delay_secs=2)
        click_pic('leave_confirm.png')

    @classmethod
    def dump_console(cls):
        logger.info("Dumping console")
        PressKey(0x27)
        ReleaseKey(0x27)
        typewrite("condump")
        PressKey(0x1C)
        ReleaseKey(0x1C)
        PressKey(0x27)
        ReleaseKey(0x27)


    # def get_results():
    #     return

    @staticmethod
    def get_coords_pic(picname):
        return pa.locateOnScreen(os.getcwd() + '\\' + picname)

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
        for i in range(secs):
            print("Sleep %s" % (i + 1))
            time.sleep(1)
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
