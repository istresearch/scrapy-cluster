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
    }

    def __init__(self, settings):
        self.setup(settings)

    def setup(self, settings):
        '''
        Connection stuff here so we can mock it
        '''
        # dynamic import of settings file
        # remove the .py from the filename
        self.settings = importlib.import_module(settings[:-3])

        self.redis_conn = redis.Redis(host=self.settings.REDIS_HOST,
                                      port=self.settings.REDIS_PORT)
        self._load_plugins()

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
        Sets up all plugins, defaults and settings.py
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
            instance.setup(self.settings)
            # share the redis connection
            instance.redis_conn = self.redis_conn

            the_regex = instance.regex

            mini = {}
            mini['instance'] = instance
            if the_regex is None:
                print "No regex found! throw error"
                continue
            mini['regex'] = the_regex

            self.plugins_dict[self.default_plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(self.plugins_dict.items(),
                                                key=lambda t: t[0]))

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
                instance = obj['instance']
                regex = obj['regex']
                for key in self.redis_conn.scan_iter(match=regex):
                    val = self.redis_conn.get(key)
                    try:
                        instance.handle(key, val)
                    except Exception as e:
                        print traceback.format_exc()
                        pass
                    self.redis_conn.delete(key)

            #self._do_info()
            #self._do_expire()
            #self._do_stop()

            time.sleep(0.1)

#     def _do_info(self):
#         '''
#         Processes info action requests
#         '''
#         for key in self.redis_conn.scan_iter(match="info:*:*"):
#             # the master dict to return
#             master = {}
#             master['uuid'] = self.redis_conn.get(key)
#             master['total_pending'] = 0
#             master['server_time'] = int(time.time())
#
#             # break down key
#             elements = key.split(":")
#             dict = {}
#             dict['spiderid'] = elements[1]
#             dict['appid'] = elements[2]
#
#             if len(elements) == 4:
#                 dict['crawlid'] = elements[3]
#
#             # generate the information requested
#             if 'crawlid' in dict:
#                 master = self._build_crawlid_info(master, dict)
#             else:
#                 master = self._build_appid_info(master, dict)
#
#             self.redis_conn.delete(key)
#
#             if self._send_to_kafka(master):
#                 pass
#                 #print 'Sent info to kafka'
#             else:
#                 print 'Failed to send info to kafka'

    def _do_expire(self):
        '''
        Processes expire requests
        Very similar to _do_stop()
        '''
        for key in self.redis_conn.scan_iter(match="timeout:*:*:*"):
            timeout = float(self.redis_conn.get(key))
            curr_time = time.time()
            if curr_time > timeout:
                # break down key
                elements = key.split(":")
                spiderid = elements[1]
                appid = elements[2]
                crawlid = elements[3]

                # add crawl to blacklist so it doesnt propagate
                redis_key = spiderid + ":blacklist"
                value = '{appid}||{crawlid}'.format(appid=appid,
                                                crawlid=crawlid)
                # add this to the blacklist set
                self.redis_conn.sadd(redis_key, value)

                # everything stored in the queue is now expired
                result = self._purge_crawl(spiderid, appid, crawlid)

                # item to send to kafka
                extras = {}
                extras['action'] = "expire"
                extras['spiderid'] = spiderid
                extras['appid'] = appid
                extras['crawlid'] = crawlid
                extras['total_expired'] = result

                self.redis_conn.delete(key)

                if self._send_to_kafka(extras):
                    #print 'Sent expired ack to kafka'
                    pass
                else:
                    print 'Failed to send expired ack to kafka'

    def _do_stop(self):
        '''
        Processes stop action requests
        '''
        for key in self.redis_conn.scan_iter(match="stop:*:*:*"):
            # break down key
            elements = key.split(":")
            spiderid = elements[1]
            appid = elements[2]
            crawlid = elements[3]
            uuid = self.redis_conn.get(key)

            redis_key = spiderid + ":blacklist"
            value = '{appid}||{crawlid}'.format(appid=appid,
                                                crawlid=crawlid)

            # add this to the blacklist set
            self.redis_conn.sadd(redis_key, value)

            # purge crawlid from current set
            result = self._purge_crawl(spiderid, appid, crawlid)

            # item to send to kafka
            extras = {}
            extras['action'] = "stop"
            extras['spiderid'] = spiderid
            extras['appid'] = appid
            extras['crawlid'] = crawlid
            extras['total_purged'] = result

            self.redis_conn.delete(key)

            if self._send_to_kafka(extras):
                # delete timeout for crawl (if needed) since stopped
                timeout_key = 'timeout:{sid}:{aid}:{cid}'.format(
                                        sid=spiderid,
                                        aid=appid,
                                        cid=crawlid)
                self.redis_conn.delete(timeout_key)
                #print 'Sent stop ack to kafka'
            else:
                print 'Failed to send stop ack to kafka'

    def _purge_crawl(self, spiderid, appid, crawlid):
        '''
        Wrapper for purging the crawlid from the queues

        @param spiderid: the spider id
        @param appid: the app id
        @param crawlid: the crawl id
        @return: The number of requests purged
        '''
        # purge three times to try to make sure everything is cleaned
        total = self._mini_purge(spiderid, appid, crawlid)
        total = total + self._mini_purge(spiderid, appid, crawlid)
        total = total + self._mini_purge(spiderid, appid, crawlid)

        return total

    def _mini_purge(self, spiderid, appid, crawlid):
        '''
        Actually purges the crawlid from the queue

        @param spiderid: the spider id
        @param appid: the app id
        @param crawlid: the crawl id
        @return: The number of requests purged
        '''
        total_purged = 0

        match_string = '{sid}:*:queue'.format(sid=spiderid)
        # using scan for speed vs keys
        for key in self.redis_conn.scan_iter(match=match_string):
            for item in self.redis_conn.zscan_iter(key):
                item_key = item[0]
                item = pickle.loads(item_key)
                if 'meta' in item:
                    item = item['meta']

                if item['appid'] == appid and item['crawlid'] == crawlid:
                    self.redis_conn.zrem(key, item_key)
                    total_purged = total_purged + 1

        return total_purged

def main():
    """redis-monitor: Monitor the Scrapy Cluster Redis instance.

    Usage:
        redis-monitor [--settings=<settings>]

    Options:
        -s --settings <settings>      The settings file to read from [default: settings.py].
    """
    args = docopt(main.__doc__)
    redis_monitor = RedisMonitor(args['--settings'])
    redis_monitor.run()

if __name__ == "__main__":
    sys.exit(main())
