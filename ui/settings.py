# This file houses all default settings for the Admin UI
# to override please use a custom localsettings.py file

# Flask configuration
FLASK_LOGGING_ENABLED = True
FLASK_PORT = 5000
DEBUG = False

STAT_REQ_FREQ = 60
STAT_START_DELAY = 10

# REST host information
REST_HOST = 'http://localhost:5343'

DAEMON_THREAD_JOIN_TIMEOUT = 10

# logging setup
LOGGER_NAME = 'ui-service'
LOG_DIR = 'logs'
LOG_FILE = 'ui_service.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = True
LOG_JSON = False
LOG_LEVEL = 'INFO'
