import redis
import logging
import sys
import time
import re
import pickle
import traceback
import json
import importlib

from docopt import docopt
from collections import OrderedDict

class RedisMonitor:

    plugin_dir = "plugins/"
    default_plugins = {
        'plugins.info_monitor.InfoMonitor': 100,
        'plugins.stop_monitor.StopMonitor': 200,
        'plugins.expire_monitor.ExpireMonitor': 300,
    }

    def __init__(self, settings):
        # dynamic import of settings file
        # remove the .py from the filename
        self.settings = importlib.import_module(settings[:-3])
        self.redis_conn = None

    def setup(self):
        '''
        Connection stuff here so we can mock it
        '''
        self.redis_conn = redis.Redis(host=self.settings.REDIS_HOST,
                                      port=self.settings.REDIS_PORT)
        self._load_plugins()
        self._run_setups()

    def import_class(self, cl):
        '''
        Imports a class from a string

        @param name: the module and class name in dot notation
        '''
        d = cl.rfind(".")
        classname = cl[d+1:len(cl)]
        m = __import__(cl[0:d], globals(), locals(), [classname])
        return getattr(m, classname)

    def _load_plugins(self):
        '''
        Sets up all plugins and defaults
        '''
        try:
            loaded_plugins = self.settings.PLUGINS
            self.default_plugins.update(self.settings.PLUGINS)
        except Exception as e:
            pass

        self.plugins_dict = {}
        for key in self.default_plugins:
            # skip loading the plugin if its value is None
            if self.default_plugins[key] is None:
                continue
            # valid plugin, import and setup
            the_class = self.import_class(key)
            instance = the_class()
            # not loading settings b/c of potential connections
            # share the redis connection
            instance.redis_conn = self.redis_conn

            the_regex = instance.regex

            mini = {}
            mini['instance'] = instance
            if the_regex is None:
                raise ImportError()
                #continue
            mini['regex'] = the_regex

            self.plugins_dict[self.default_plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(self.plugins_dict.items(),
                                                key=lambda t: t[0]))

    def _run_setups(self):
        '''
        Runs the setups for all loaded classes, useful for skipping
        connection loading
        '''
        for key in self.plugins_dict:
            obj = self.plugins_dict[key]
            obj['instance'].setup(self.settings)

    def run(self):
        '''
        The external main run loop
        '''
        self._main_loop()

    def _main_loop(self):
        '''
        The internal while true main loop for the redis monitor
        '''
        while True:
            for plugin_key in self.plugins_dict:
                obj = self.plugins_dict[plugin_key]
                self._process_plugin(obj)

            time.sleep(0.1)

    def _process_plugin(self, plugin):
        '''
        Logic to handle each plugin that is active

        @param plugin: a plugin dict object
        '''
        instance = plugin['instance']
        regex = plugin['regex']
        for key in self.redis_conn.scan_iter(match=regex):
            val = self.redis_conn.get(key)
            try:
                instance.handle(key, val)
            except Exception as e:
                print traceback.format_exc()
                pass

def main():
    """redis-monitor: Monitor the Scrapy Cluster Redis instance.

    Usage:
        redis-monitor [--settings=<settings>]

    Options:
        -s --settings <settings>      The settings file to read from [default: settings.py].
    """
    args = docopt(main.__doc__)
    redis_monitor = RedisMonitor(args['--settings'])
    redis_monitor.setup()
    redis_monitor.run()

if __name__ == "__main__":
    sys.exit(main())
