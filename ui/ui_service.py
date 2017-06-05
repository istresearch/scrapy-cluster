import requests
import argparse
import uuid
import logging
import time

from flask import Flask, render_template, request, flash, redirect
from collections import deque
from threading import Thread

from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper


class AdminUIService(object):

    # static strings
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    start_time = 0
    closed = False
    _initiate_stats_req_thread = None

    def __init__(self, settings_name):
        """
        @param settings_name: the local settings file name
        """
        self.settings_name = settings_name
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.app = Flask(__name__)
        self.my_uuid = str(uuid.uuid4()).split('-')[4]
        self.appid = Flask(__name__).name
        self.pollids = deque([])
        self.kafka_stats = {}

    def setup(self, level=None, log_file=None, json=None):
        """
        Load everything up. Note that any arg here will override both
        default and custom settings

        @param level: the log level
        @param log_file: boolean t/f whether to log to a file, else stdout
        @param json: boolean t/f whether to write the logs in json
        """
        self.settings = self.wrapper.load(self.settings_name)

        my_level = level if level else self.settings['LOG_LEVEL']
        # negate because logger wants True for std out
        my_output = not log_file if log_file else self.settings['LOG_STDOUT']
        my_json = json if json else self.settings['LOG_JSON']
        self.logger = LogFactory.get_instance(json=my_json, stdout=my_output,
                                              level=my_level,
                                              name=self.settings['LOGGER_NAME'],
                                              dir=self.settings['LOG_DIR'],
                                              file=self.settings['LOG_FILE'],
                                              bytes=self.settings['LOG_MAX_BYTES'],
                                              backups=self.settings['LOG_BACKUPS'])
        self._decorate_routes()

        # spawn heartbeat processing loop
        self._initiate_stats_req_thread = Thread(target=self._initiate_stats_req_loop)
        self._initiate_stats_req_thread.setDaemon(True)
        self._initiate_stats_req_thread.start()

        self.start_time = self.get_time()

        self.kafka_stats['stats'] = "Stats not populated yet!"

        # disable flask logger
        if self.settings['FLASK_LOGGING_ENABLED'] == False:
            log = logging.getLogger('werkzeug')
            log.disabled = True

    def get_time(self):
        """Returns the current time"""
        return time.time()

    def run(self):
        """
        Main flask run loop
        """
        self.logger.info("Running main flask method on port " +
                         str(self.settings['FLASK_PORT']))
        self.app.run(host='0.0.0.0', port=self.settings['FLASK_PORT'])

    def _initiate_stats_req_loop(self):
        """A main run loop thread to do work"""
        self.logger.debug("running stats req loop thread")
        while not self.closed:
            time.sleep(self.settings['STAT_REQ_FREQ'])
            self.kafka_stats()
            self.kafka_stats_poll()

    def kafka_stats(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "kafka-monitor"}

        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = r.content

        if res.data.poll_id:
            pollid = res.data.poll_id
            self.pollids.append(pollid)

    def kafka_stats_poll(self):
        pollid = self.pollids.popleft()

        data = {"poll_id": pollid}

        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = r.content

        if res.status == "FAILURE":
            self.pollids.appendleft(pollid)
        else:
            self.kafka_stats['stats'] = res.data

    def _close_thread(self, thread, thread_name):
        """Closes daemon threads

        @param thread: the thread to close
        @param thread_name: a human readable name of the thread
        """
        if thread is not None and thread.isAlive():
            self.logger.debug("Waiting for {} thread to close".format(thread_name))
            thread.join(timeout=self.settings['DAEMON_THREAD_JOIN_TIMEOUT'])
            if thread.isAlive():
                self.logger.warn("{} daemon thread unable to be shutdown"
                                 " within timeout".format(thread_name))

    def close(self):
        """
        Cleans up anything from the process
        """
        self._close_thread(self._initiate_stats_req_thread, "Stats Loop")

        self.logger.info("Closing Rest Service")
        self.closed = True

    # Routes --------------------

    def _decorate_routes(self):
        """
        Decorates the routes to use within the flask app
        """
        self.logger.debug("Decorating routes")

        self.app.add_url_rule('/', 'index', self.index,
                              methods=['GET'])
        self.app.add_url_rule('/submit', 'submit', self.submit,
                              methods=['POST', 'GET'])
        self.app.add_url_rule('/kafka', 'kafka', self.kafka,
                              methods=['GET'])
        self.app.add_url_rule('/redis', 'redis', self.redis,
                              methods=['GET'])
        self.app.add_url_rule('/crawler', 'crawler', self.crawler,
                              methods=['GET'])

    def index(self):
        r = requests.get(self.settings['REST_HOST'])
        if r.status_code == 200:
            status = r.json()
        else:
            status = "Unable to connect to Rest service"
        return render_template('index.html', status=status)

    def submit(self):
        if request.method == 'POST':
            if not request.form['url']:
                flash('Submit failed')
                return redirect("/")
            else:
                data = {"url": request.form['url'], "crawlid": request.form.get("crawlid", None),
                        "depth": request.form.get("depth", None), "priority": request.form.get("priority", None)}
                r = requests.post(self.settings['REST_HOST'] + "/feed", data=data)
                if r.content["status"] == "SUCCESS":
                    flash('You successfully submitted a crawl job')
                else:
                    flash('Submit failed')
                return redirect("/")

    def kafka(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "kafka-monitor"}
        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = r.content
        return render_template("kafka.html", result=res)

    def redis(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "redis-monitor"}
        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        return render_template("redis.html", result=r.content)

    def crawler(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "crawler"}
        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        return render_template("crawler.html", result=r.content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Admin UI Service\n')

    parser.add_argument('-s', '--settings', action='store',
                        required=False,
                        help="The settings file to read from",
                        default="localsettings.py")
    parser.add_argument('-ll', '--log-level', action='store',
                        required=False, help="The log level",
                        default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=True, default=None,
                        help='Log the output to the file specified in '
                        'settings.py. Otherwise logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=None,
                        help="Log the data in JSON format")

    args = vars(parser.parse_args())

    rest_service = AdminUIService(args['settings'])
    rest_service.setup(level=args['log_level'], log_file=args['log_file'], json=args['log_json'])

    try:
        rest_service.run()
    finally:
        rest_service.close()
