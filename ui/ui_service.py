import argparse
from functools import wraps
from flask import Flask, request, send_file, redirect, jsonify
from flask_triangle import Triangle
import time
import logging
import requests
import traceback
from requests.exceptions import RequestException, \
                                ConnectionError, \
                                Timeout

from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper


# Route Decorators --------------------

def log_call(call_name):
    """Log the API call to the logger."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            instance = args[0]
            instance.logger.info(call_name, {"content": request.get_json()})
            return f(*args, **kw)
        return wrapper
    return decorator


class UIService(object):

    closed = False
    start_time = 0

    def __init__(self, settings_name):
        """
        @param settings_name: the local settings file name
        """
        self.settings_name = settings_name
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.app = Flask(__name__)
        Triangle(self.app)

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

        self.api_path = self.settings['REST_ENDPOINT']
        if self.api_path[-1:] != '/':
            self.api_path += '/'
        self.timeout = self.settings.get('REQUEST_SO_TIMEOUT_SECS', 6.05)
        self.read_timeout = self.settings.get('REQUEST_READ_TIMEOUT_SECS', 10)

        self._decorate_routes()

        self.start_time = time.time()

        # disable flask logger
        if self.settings['FLASK_LOGGING_ENABLED'] == False:
            log = logging.getLogger('werkzeug')
            log.disabled = True

    def run(self):
        """Main flask run loop"""
        self.logger.info("Running main flask method on port " + str(self.settings['FLASK_PORT']))
        self.app.run(host='0.0.0.0', port=self.settings['FLASK_PORT'])

    def close(self):
        """
        Cleans up anything from the process
        """
        self.logger.info("Closing UI Service")
        self.closed = True

    def _call_rest(self, path='', method='GET', data={}):
        """
        Calls the rest endpoint

        :param str path: the uri
        :param str method: the method
        :param obj data: the json data to send
        """
        final_path = self.api_path + path
        self.logger.debug("Rest Endpoint call",
                          {
                            "path": final_path,
                            "json": data,
                            "method": method
                          })
        try:
            response = requests.request(method=method,
                                       url=final_path,
                                       json=data,
                                       timeout=(self.timeout,
                                                self.read_timeout))
            return response.json(), response.status_code
        except ConnectionError as e:
            self.logger.warn("Connection Error",
                               {"ex": traceback.format_exc()})
        except Timeout as e:
            self.logger.warn("Request Timeout",
                               {"ex": traceback.format_exc()})
        except RequestException as e:
            self.logger.warn("Request Exception",
                             {"ex": traceback.format_exc()})

        r = {
            "status": "FAILURE",
            "data": {},
            "error": {
                "cause": "Failure during communication with the Rest endpoint"
            }}
        return r, 500

    # Routes --------------------

    def _decorate_routes(self):
        """
        Decorates the routes to use within the flask app
        """
        self.logger.debug("Decorating routes")
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])
        self.app.add_url_rule('/api', 'api_base', self.api_base,
                              methods=['GET', 'POST'])
        self.app.add_url_rule('/api/<path:url>', 'api', self.api,
                              methods=['POST'])

    @log_call('\'index\' endpoint called')
    def index(self):
        return send_file("templates/index.html")

    @log_call('\'api_base\' endpoint called')
    def api_base(self):
        resp, status = self._call_rest()
        return jsonify(resp), status

    @log_call('\'api\' endpoint called')
    def api(self, url):
        resp, status = self._call_rest(method=request.method,
                          path=url,
                          data=request.get_json())

        return jsonify(resp), status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Rest Service: Used for interacting and feeding Kafka'
        ' requests to the cluster and returning data back\n')

    parser.add_argument('-s', '--settings', action='store', required=False,
                        help="The settings file to read from", default="localsettings.py")
    parser.add_argument('-ll', '--log-level', action='store', required=False,
                        help="The log level", default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=True, default=None,
                        help='Log the output to the file specified in settings.py. Otherwise logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=None,
                        help="Log the data in JSON format")

    args = vars(parser.parse_args())

    ui_service = UIService(args['settings'])
    ui_service.setup(level=args['log_level'], log_file=args['log_file'], json=args['log_json'])

    try:
        ui_service.run()
    finally:
        ui_service.close()
