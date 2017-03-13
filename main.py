import time

from database import DBConnection
from run import Run, Loop

def main():
    parameter_names = [
        "hero_movespeed", "hero_attackspeed", "hero_attackrange", "hero_attackdamage", "fraction_neutral_left",
        "neutral_total_eff_hp", "targeted_neutral_eff_hp", "fraction_lane_left", "lane_total_eff_hp",
        "targeted_lane_eff_hp", "damage_spread_neutral", "damage_spread_lane", "success"
    ]

    #starting_weights = [0.0033, -0.85, -0.0015, 0.02, -4, -0.003, 0.003, 1.25, 0.0005, 0, 0, 0]
    db = DBConnection("doublepull")
    loop = Loop(parameter_names, db, 100, starting_weights)
    loop.go()

if __name__ == "__main__":
    main()