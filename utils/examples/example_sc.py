import argparse
from getch import getch
from time import time
from scutils.stats_collector import StatsCollector

# set up arg parser
parser = argparse.ArgumentParser(
    description='Example key press stats collector.\n')
parser.add_argument('-rw', '--rolling-window', action='store_true',
                    required=False, help="Use a RollingTimeWindow counter",
                    default=False)
parser.add_argument('-r', '--redis-host', action='store', required=True,
                    help="The Redis host ip")
parser.add_argument('-p', '--redis-port', action='store', default='6379',
                    help="The Redis port")
parser.add_argument('-P', '--redis-password', action='store', default=None,
                    help="The Redis password")

args = vars(parser.parse_args())

the_window = StatsCollector.SECONDS_1_MINUTE

if args['rolling_window']:
    counter = StatsCollector.get_rolling_time_window(host=args['redis_host'],
                                                     port=args['redis_port'],
                                                     password=args['redis_password'],
                                                     window=the_window,
                                                     cycle_time=1)
else:
    counter = StatsCollector.get_time_window(host=args['redis_host'],
                                                     port=args['redis_port'],
                                                     password=args['redis_password'],
                                                     window=the_window,
                                                     keep_max=3)

print("Kill this program by pressing `ENTER` when done")

the_time = int(time())
floor_time = the_time % the_window
final_time = the_time - floor_time

pressed_enter = False
while not pressed_enter:
    print("The current counter value is " + str(counter.value()))
    key = getch()

    if key == '\r' or key == '\n':
        pressed_enter = True
    elif key == ' ':
        counter.increment()

    if not args['rolling_window']:
        new_time = int(time())
        floor_time = new_time % the_window
        new_final_time = new_time - floor_time

        if new_final_time != final_time:
            print("The counter window will roll soon")
            final_time = new_final_time

print("The final counter value is " + str(counter.value()))
counter.delete_key()
