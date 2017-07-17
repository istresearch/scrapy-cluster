import requests
import argparse
import uuid
import logging
import time
import json
import plotly
import datetime

from flask import Flask, render_template, request, flash, redirect
from flask_table import Table, Col, DatetimeCol
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
        self.pollids_km = deque([])
        self.pollids_rm = deque([])
        self.pollids_c = deque([])
        self.stats = {}

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

        self._initiate_stats_req_thread = Thread(target=self._initiate_stats_req_loop)
        self._initiate_stats_req_thread.setDaemon(True)
        self._initiate_stats_req_thread.start()

        self.start_time = self.get_time()

        self.stats['kafka-monitor'] = {}
        self.stats['kafka-monitor']['total'] = []
        self.stats['kafka-monitor']['fail'] = []

        self.stats['redis-monitor'] = {}
        self.stats['redis-monitor']['total'] = []
        self.stats['redis-monitor']['fail'] = []

        self.stats['queue'] = {}
        self.stats['queue']['total_backlog'] = []

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
        self.logger.info("Running main flask method on port " + str(self.settings['FLASK_PORT']))
        self.app.run(host='0.0.0.0', port=self.settings['FLASK_PORT'], debug=self.settings['DEBUG'])

    # Declare table
    class ItemTable(Table):
        classes = ['table', 'table-striped']
        timestamp = DatetimeCol('timestamp')
        total_requests = Col('total_requests')

    def _initiate_stats_req_loop(self):
        self.logger.debug("running stats req loop thread")
        while not self.closed:
            self._kafka_stats()
            self._kafka_stats_poll()
            self._redis_stats()
            self._redis_stats_poll()
            self._crawler_stats()
            self._crawler_stats_poll()
            time.sleep(self.settings['STAT_REQ_FREQ'])

    def _kafka_stats(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "kafka-monitor"}

        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = json.loads(r.content)

        if 'poll_id' in res:
            pollid = res['poll_id']
            self.pollids_km.append(pollid)
        elif res['status'] == 'SUCCESS':
            dt = datetime.datetime.now()
            if 'total' in res['data']:
                res['data']['total']['ts'] = dt
                self.stats['kafka-monitor']['total'].append(res['data']['total'])
                self.stats['kafka-monitor']['total'] = self.stats['kafka-monitor']['total'][:10]
            if 'fail' in res['data']:
                res['data']['total']['ts'] = dt
                self.stats['kafka-monitor']['fail'].append(res['data']['fail'])
                self.stats['kafka-monitor']['fail'] = self.stats['kafka-monitor']['fail'][:10]

    def _kafka_stats_poll(self):
        while self.pollids_km:
            pollid = self.pollids_km.popleft()
            data = {"poll_id": pollid}

            r = requests.post(self.settings['REST_HOST'] + "/poll", json=data)
            res = json.loads(r.content)

            if res.status == "FAILURE":
                self.pollids_km.appendleft(pollid)
            else:
                dt = datetime.datetime.now()
                if 'total' in res['data']:
                    res['data']['total']['ts'] = dt
                    self.stats['kafka-monitor']['total'].append(res['data']['total'])
                    self.stats['kafka-monitor']['total'] = self.stats['kafka-monitor']['total'][:10]
                if 'fail' in res['data']:
                    res['data']['total']['ts'] = dt
                    self.stats['kafka-monitor']['fail'].append(res['data']['fail'])
                    self.stats['kafka-monitor']['fail'] = self.stats['kafka-monitor']['fail'][:10]

    def _redis_stats(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "redis-monitor"}

        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = json.loads(r.content)

        if 'poll_id' in res:
            pollid = res['poll_id']
            self.pollids_rm.append(pollid)
        elif res['status'] == 'SUCCESS':
            dt = datetime.datetime.now()
            if 'total' in res['data']:
                res['data']['total']['ts'] = dt
                self.stats['redis-monitor']['total'].append(res['data']['total'])
                self.stats['redis-monitor']['total'] = self.stats['redis-monitor']['total'][:10]
            if 'fail' in res['data']:
                res['data']['total']['ts'] = dt
                self.stats['redis-monitor']['fail'].append(res['data']['fail'])
                self.stats['redis-monitor']['fail'] = self.stats['redis-monitor']['fail'][:10]

    def _redis_stats_poll(self):
        while self.pollids_rm:
            pollid = self.pollids_rm.popleft()
            data = {"poll_id": pollid}

            r = requests.post(self.settings['REST_HOST'] + "/poll", json=data)
            res = json.loads(r.content)

            if res.status == "FAILURE":
                self.pollids_rm.appendleft(pollid)
            else:
                dt = datetime.datetime.now()
                if 'total' in res['data']:
                    res['data']['total']['ts'] = dt
                    self.stats['redis-monitor']['total'].append(res['data']['total'])
                    self.stats['redis-monitor']['total'] = self.stats['redis-monitor']['total'][:10]
                if 'fail' in res['data']:
                    res['data']['total']['ts'] = dt
                    self.stats['redis-monitor']['fail'].append(res['data']['fail'])
                    self.stats['redis-monitor']['fail'] = self.stats['redis-monitor']['fail'][:10]

    def _crawler_stats(self):
        data = {"appid": self.appid, "uuid": self.my_uuid, "stats": "queue"}

        r = requests.post(self.settings['REST_HOST'] + "/feed", json=data)
        res = json.loads(r.content)

        if 'poll_id' in res:
            pollid = res['poll_id']
            self.pollids_c.append(pollid)
        elif res['status'] == 'SUCCESS':
            dt = datetime.datetime.now()
            if 'queues' in res['data']:
                res['data']['queues']['ts'] = dt
                self.stats['queue']['total_backlog'].append(res['data']['queues'])
                self.stats['queue']['total_backlog'] = self.stats['queue']['total_backlog'][:10]

    def _crawler_stats_poll(self):
        while self.pollids_rm:
            pollid = self.pollids_c.popleft()
            data = {"poll_id": pollid}

            r = requests.post(self.settings['REST_HOST'] + "/poll", json=data)
            res = json.loads(r.content)

            if res.status == "FAILURE":
                self.pollids_c.appendleft(pollid)
            else:
                dt = datetime.datetime.now()
                if 'queues' in res['data']:
                    res['data']['queues']['ts'] = dt
                    self.stats['queue']['total_backlog'].append(res['data']['queues'])
                    self.stats['queue']['total_backlog'] = self.stats['queue']['total_backlog'][:10]

    def rest_api(self, endpoint, data=None):
        api_endpoint = self.settings['REST_HOST'] + endpoint
        response = requests.get(api_endpoint, json=data)
        return response

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
        r = self.rest_api('/')
        if r.status_code == 200:
            status = r.json()
        else:
            status = {
                "kafka_connected": False,
                "node_health": "RED",
                "redis_connected": False,
                "uptime_sec": 0}
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
        ts_1 = []
        total_1 = []
        dt_items = []

        for item in self.stats['kafka-monitor']['total']:
            ts_1.append(item['ts'])
            total_1.append(item['900'])
            dt_items.append(dict(timestamp=item['ts'], total_requests=item['900']))

        graphs = [
            dict(
                data=[
                    dict(
                        x=ts_1,
                        y=total_1,
                        type='bar'
                    ),
                ],
                layout=dict(
                    title='Total Requests'
                )
            ),
        ]

        ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

        # Convert the figures to JSON
        graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

        table = self.ItemTable(dt_items)

        return render_template("kafka.html",
                               ids=ids,
                               graphJSON=graphJSON, table=table)

    def redis(self):
        ts_1 = []
        total_1 = []
        dt_items = []

        for item in self.stats['redis-monitor']['total']:
            ts_1.append(item['ts'])
            total_1.append(item['900'])
            dt_items.append(dict(timestamp=item['ts'], total_requests=item['900']))

        graphs = [
            dict(
                data=[
                    dict(
                        x=ts_1,
                        y=total_1,
                        type='bar'
                    ),
                ],
                layout=dict(
                    title='Total Requests'
                )
            ),
        ]

        ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

        # Convert the figures to JSON
        graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

        table = self.ItemTable(dt_items)
        return render_template("redis.html",
                               ids=ids,
                               graphJSON=graphJSON, table=table)

    def crawler(self):
        ts_1 = []
        total_1 = []
        dt_items = []

        for item in self.stats['queue']['total_backlog']:
            ts_1.append(item['ts'])
            total_1.append(item['total_backlog'])
            dt_items.append(dict(timestamp=item['ts'], total_requests=item['total_backlog']))

        graphs = [
            dict(
                data=[
                    dict(
                        x=ts_1,
                        y=total_1,
                        type='bar'
                    ),
                ],
                layout=dict(
                    title='Backlog'
                )
            ),
        ]

        ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]

        # Convert the figures to JSON
        graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

        table = self.ItemTable(dt_items)
        return render_template("crawler.html",
                               ids=ids,
                               graphJSON=graphJSON, table=table)


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

    ui_service = AdminUIService(args['settings'])
    ui_service.setup(level=args['log_level'], log_file=args['log_file'], json=args['log_json'])

    try:
        ui_service.run()
    finally:
        ui_service.close()
