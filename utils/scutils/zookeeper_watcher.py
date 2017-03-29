from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import object
from kazoo.client import KazooClient, KazooState
from kazoo.exceptions import ZookeeperError, KazooException
from threading import Thread
import argparse
import sys
from time import sleep
import logging
log = logging.getLogger(__name__)


class ZookeeperWatcher(object):
    zoo_client = None  # The KazooClient to manage the config
    point_path = None  # Zookeeper path to pointed to file
    pointed_at_expired = None  # is True when the assignment has been set to
                               # None but we cannot remove the config listener
    valid_handler = None  # the function to call when the validity changes
    config_handler = None  # the function to call when the config changes
    error_handler = None  # the function to call when an error occurs in reading
    valid_file = False  # the current state of the ConfigWatcher with ZK
    do_not_restart = False  # used when closing via ^C
    old_data = ''  # The current file contents, to see if a change occurred
    old_pointed = ''  # the current pointed path, to see if change occurred

    INVALID_PATH = "Invalid pointer path"
    INVALID_GET = "Invalid get on file path"
    BAD_CONNECTION = "Connection interrupted with Zookeeper, re-establishing"

    def __init__(self, hosts, filepath, valid_handler=None,
                 config_handler=None, error_handler=None, pointer=False,
                 ensure=False, valid_init=True):
        '''
        Zookeeper file watcher, used to tell a program their zookeeper file has
        changed. Can be used to watch a single file, or both a file and path of
        its contents. Manages all connections, drops, reconnections for you.

        @param hosts: The zookeeper hosts to use
        @param filepath: The full path to the file to watch
        @param valid_handler: The method to call for a 'is valid' state change
        @param config_handler: The method to call when a content change occurs
        @param error_handler: The method to call when an error occurs
        @param pointer: Set to true if the file contents are actually a path to
                        another zookeeper file, where the real config resides
        @param ensure: Set to true for the ZooWatcher to create the watched file
        @param valid_init: Ensure the client can connect to Zookeeper first try

        Ex 1. /stuff/A: "stuff I care about"
        Ex 2. /stuff/A: "/other/stuff", /other/stuff: "contents I care about"
            - in Ex 2 you care about /other/stuff contents
              but are only aware of your assignment /stuff/A

        You can use this class as any combination of event driven or polling.
        Polling:
            In the main loop of your program, check if is_valid() is
            True, otherwise clear your contents as there is some ZK error.
        Event:
            You will be notified via the various handlers when content changes.
        '''
        self.hosts = hosts
        self.my_file = filepath
        self.pointer = pointer
        self.ensure = ensure
        self.valid_handler = valid_handler
        self.config_handler = config_handler
        self.error_handler = error_handler

        if valid_init:
            # this will throw an exception if it can't start right away
            self.zoo_client = KazooClient(hosts=self.hosts)
            self.zoo_client.start()

        self.threaded_start(no_init=True)

    def threaded_start(self, no_init=False):
        '''
        Spawns a worker thread to set up the zookeeper connection
        '''
        thread = Thread(target=self.init_connections, kwargs={
                        'no_init': no_init})
        thread.setDaemon(True)
        thread.start()
        thread.join()

    def init_connections(self, no_init=False):
        '''
        Sets up the initial Kazoo Client and watches
        '''
        success = False
        self.set_valid(False)

        if not no_init:
            if self.zoo_client:
                self.zoo_client.remove_listener(self.state_listener)
                self.old_data = ''
                self.old_pointed = ''

            while not success:
                try:
                    if self.zoo_client is None:
                        self.zoo_client = KazooClient(hosts=self.hosts)
                        self.zoo_client.start()
                    else:
                        # self.zoo_client.stop()
                        self.zoo_client._connection.connection_stopped.set()
                        self.zoo_client.close()
                        self.zoo_client = KazooClient(hosts=self.hosts)
                        self.zoo_client.start()
                except Exception as e:
                    log.error("ZKWatcher Exception: " + e.message)
                    sleep(1)
                    continue

                self.setup()
                success = self.update_file(self.my_file)
                sleep(5)
        else:
            self.setup()
            self.update_file(self.my_file)

    def setup(self):
        '''
        Ensures the path to the watched file exists and we have a state
        listener
        '''
        self.zoo_client.add_listener(self.state_listener)

        if self.ensure:
            self.zoo_client.ensure_path(self.my_file)

    def state_listener(self, state):
        '''
        Restarts the session if we get anything besides CONNECTED
        '''
        if state == KazooState.SUSPENDED:
            self.set_valid(False)
            self.call_error(self.BAD_CONNECTION)
        elif state == KazooState.LOST and not self.do_not_restart:
            self.threaded_start()
        elif state == KazooState.CONNECTED:
            # This is going to throw a SUSPENDED kazoo error
            # which will cause the sessions to be wiped and re established.
            # Used b/c of massive connection pool issues
            self.zoo_client.stop()

    def is_valid(self):
        '''
        @return: True if the currently watch file is valid
        '''
        return self.valid_file

    def ping(self):
        '''
        Simple command to test if the zookeeper session is able to connect
        at this very moment
        '''
        try:
            # dummy ping to ensure we are still connected
            self.zoo_client.server_version()
            return True
        except KazooException:
            return False

    def close(self, kill_restart=True):
        '''
        Use when you would like to close everything down
        @param kill_restart= Prevent kazoo restarting from occurring
        '''
        self.do_not_restart = kill_restart
        self.zoo_client.stop()
        self.zoo_client.close()

    def get_file_contents(self, pointer=False):
        '''
        Gets any file contents you care about. Defaults to the main file
        @param pointer: The the contents of the file pointer, not the pointed
        at file
        @return: A string of the contents
        '''
        if self.pointer:
            if pointer:
                return self.old_pointed
            else:
                return self.old_data
        else:
            return self.old_data

    def watch_file(self, event):
        '''
        Fired when changes made to the file
        '''
        if not self.update_file(self.my_file):
            self.threaded_start()

    def update_file(self, path):
        '''
        Updates the file watcher and calls the appropriate method for results
        @return: False if we need to keep trying the connection
        '''
        try:
            # grab the file
            result, stat = self.zoo_client.get(path, watch=self.watch_file)
        except ZookeeperError:
            self.set_valid(False)
            self.call_error(self.INVALID_GET)
            return False

        if self.pointer:
            if result is not None and len(result) > 0:
                self.pointed_at_expired = False
                # file is a pointer, go update and watch other file
                self.point_path = result
                if self.compare_pointer(result):
                    self.update_pointed()
            else:
                self.pointed_at_expired = True
                self.old_pointed = ''
                self.old_data = ''
                self.set_valid(False)
                self.call_error(self.INVALID_PATH)
        else:
            # file is not a pointer, return contents
            if self.compare_data(result):
                self.call_config(result)
            self.set_valid(True)

        return True

    def watch_pointed(self, event):
        '''
        Fired when changes made to pointed file
        '''
        self.update_pointed()

    def update_pointed(self):
        '''
        Grabs the latest file contents based on the pointer uri
        '''
        # only grab file if our pointer is still good (not None)
        if not self.pointed_at_expired:
            try:
                conf_string, stat2 = self.zoo_client.get(self.point_path,
                                                    watch=self.watch_pointed)
            except ZookeeperError:
                self.old_data = ''
                self.set_valid(False)
                self.pointed_at_expired = True
                self.call_error(self.INVALID_PATH)
                return

            if self.compare_data(conf_string):
                self.call_config(conf_string)
            self.set_valid(True)

    def set_valid(self, boolean):
        '''
        Sets the state and calls the change if needed
        @param bool: The state (true or false)
        '''
        old_state = self.is_valid()
        self.valid_file = boolean

        if old_state != self.valid_file:
            self.call_valid(self.valid_file)

    def call_valid(self, state):
        '''
        Calls the valid change function passed in
        @param valid_state: The new config
        '''
        if self.valid_handler is not None:
            self.valid_handler(self.is_valid())

    def call_config(self, new_config):
        '''
        Calls the config function passed in
        @param new_config: The new config
        '''
        if self.config_handler is not None:
            self.config_handler(new_config)

    def call_error(self, message):
        '''
        Calls the error function passed in
        @param message: The message to throw
        '''
        if self.error_handler is not None:
            self.error_handler(message)

    def compare_data(self, data):
        '''
        Compares the string data
        @return: True if the data is different
        '''
        if self.old_data != data:
            self.old_data = data
            return True
        return False

    def compare_pointer(self, data):
        '''
        Compares the string data
        @return: True if the data is different
        '''
        if self.old_pointed != data:
            self.old_pointed = data
            return True
        return False


def main():
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
        print("The valid state is now", state)

    def change_file(conf_string):
        print("Your file contents:", conf_string)

    def error_file(message):
        print("An error was thrown:", message)

    # You can use any or all of these, polling + handlers, some handlers, etc
    if pointer:
        if poll:
            zoo_watcher = ZookeeperWatcher(hosts, file, pointer=True)
        elif event:
            zoo_watcher = ZookeeperWatcher(hosts, file,
                                           valid_handler=valid_file,
                                           config_handler=change_file,
                                           error_handler=error_file,
                                           pointer=True, valid_init=valid)
    else:
        if poll:
            zoo_watcher = ZookeeperWatcher(hosts, file)
        elif event:
            zoo_watcher = ZookeeperWatcher(hosts, file,
                                           valid_handler=valid_file,
                                           config_handler=change_file,
                                           error_handler=error_file,
                                           valid_init=valid)

    try:
        while True:
            if poll:
                print("Valid File?", zoo_watcher.is_valid())
                print("Contents:", zoo_watcher.get_file_contents())
            sleep(sleep_time)
    except:
        pass
    zoo_watcher.close()

if __name__ == "__main__":
    sys.exit(main())
