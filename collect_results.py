import time
from run import Run

def main():
    while True:
        run = Run(1)
        print("Hi")
        run.launch_game()
        run.set_logs()  # Shouldnt matter that this occurs after game launch. I only care about logs around pull
        time.sleep(5)
        #run.get_results()
        run.dump_console()
        time.sleep(5)
        run.leave_game()
        run.read_log()  # TODO this bit can be async whilst we are starting the next game

if __name__ == "__main__":
    main()