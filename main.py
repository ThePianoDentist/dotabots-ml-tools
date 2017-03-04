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
    # while True:
    #     run = Run(1)
    #     print("Hi")
    #     run.launch_game()
    #     run.set_logs()  # Shouldnt matter that this occurs after game launch. I only care about logs around pull
    #     time.sleep(5)
    #     #run.get_results()
    #     run.dump_console()
    #     time.sleep(5)
    #     run.leave_game()
    #     run.read_log()  # TODO this bit can be async whilst we are starting the next game

if __name__ == "__main__":
    main()