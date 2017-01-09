from scutils.zookeeper_watcher import ZookeeperWatcher
from time import sleep
import argparse

parser = argparse.ArgumentParser(
            description="Zookeeper file watcher")
parser.add_argument('-z', '--zoo-keeper', action='store', required=True,
                    help="The Zookeeper connection <host>:<port>")
parser.add_argument('-f', '--file', action='store', required=True,
                    help="The full path to the file to watch in Zookeeper")
parser.add_argument('-p', '--pointer', action='store_const', const=True,
                    help="The file contents point to another file")
parser.add_argument('-s', '--sleep', nargs='?', const=1, default=1,
                    type=int, help="The time to sleep between poll checks")
parser.add_argument('-v', '--valid-init', action='store_false',
                    help="Do not ensure zookeeper is up upon initial setup",
                    default=True)
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('--poll', action='store_true', help="Polling example")
group.add_argument('--event', action='store_true',
                   help="Event driven example")

args = vars(parser.parse_args())

hosts = args['zoo_keeper']
file = args['file']
pointer = args['pointer']
sleep_time = args['sleep']
poll = args['poll']
event = args['event']
valid = args['valid_init']

def valid_file(state):
    print "The valid state is now", state

def change_file(conf_string):
    print "Your file contents:", conf_string

def error_file(message):
    print "An error was thrown:", message

# You can use any or all of these, polling + handlers, some handlers, etc
if pointer:
    if poll:
        zoo_watcher = ZookeeperWatcher(hosts, file, ensure=True,pointer=True)
    elif event:
        zoo_watcher = ZookeeperWatcher(hosts, file,
                                       valid_handler=valid_file,
                                       config_handler=change_file,
                                       error_handler=error_file,
                                       pointer=True, ensure=True, valid_init=valid)
else:
    if poll:
        zoo_watcher = ZookeeperWatcher(hosts, file, ensure=True)
    elif event:
        zoo_watcher = ZookeeperWatcher(hosts, file,
                                       valid_handler=valid_file,
                                       config_handler=change_file,
                                       error_handler=error_file,
                                       valid_init=valid, ensure=True)

print "Use a keyboard interrupt to shut down the process."
try:
    while True:
        if poll:
            print "Valid File?", zoo_watcher.is_valid()
            print "Contents:", zoo_watcher.get_file_contents()
        sleep(sleep_time)
except:
    pass
zoo_watcher.close()