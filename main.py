import time

from database import DBConnection
from run import Run, Loop


def main():
    parameter_names = [
        "hero_movespeed", "hero_attackspeed", "hero_attackrange", "hero_attackdamage", "fraction_neutrals_left",
        "neutral_total_hp", "neutral_most_targeted_hp", "num_lane_creeps", "lane_creeps_total_hp",
        "lane_creeps_most_targeted_hp", "damage_spread_neutral", "damage_spread_lane", "success"
    ]
    db = DBConnection()
    loop = Loop("doublepull", parameter_names, db, 6)
    loop.go()

if __name__ == "__main__":
    main()