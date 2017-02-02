import argparse
from functools import wraps
from flask import Flask, request, send_file
import time
import logging

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

    # Routes --------------------

    def _decorate_routes(self):
        """
        Decorates the routes to use within the flask app
        """
        self.logger.debug("Decorating routes")
        self.app.add_url_rule('/', 'index', self.index, methods=['GET'])

    @log_call('\'index\' endpoint called')
    def index(self):
        return send_file("templates/index.html")


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
