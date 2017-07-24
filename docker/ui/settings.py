# THIS FILE SHOULD STAY IN SYNC WITH /ui/settings.py

# This file houses all default settings for the UI
# to override please use a custom localsettings.py file
import os


def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Flask configuration
FLASK_LOGGING_ENABLED = os.getenv('FLASK_LOGGING_ENABLED', True)
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
DEBUG = str2bool(os.getenv('DEBUG', False))

STAT_REQ_FREQ = int(os.getenv('STAT_REQ_FREQ', 60))
STAT_START_DELAY = int(os.getenv('STAT_START_DELAY', 10))

# logging setup
LOGGER_NAME = 'ui_service'
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_FILE = 'ui_service.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = str2bool(os.getenv('LOG_STDOUT', True))
LOG_JSON = str2bool(os.getenv('LOG_JSON', False))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# internal configuration
REST_HOST = os.getenv('REST_HOST', "http://rest:5343")
DAEMON_THREAD_JOIN_TIMEOUT = 10
