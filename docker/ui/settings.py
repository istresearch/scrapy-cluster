# THIS FILE SHOULD STAY IN SYNC WITH /ui/settings.py

# This file houses all default settings for the UI
# to override please use a custom localsettings.py file
import os
def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Flask configuration
FLASK_LOGGING_ENABLED = os.getenv('FLASK_LOGGING_ENABLED', True)
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

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
REST_ENDPOINT = os.getenv('REST_ENDPOINT', "http://rest:5343")
REQUEST_SO_TIMEOUT_SECS = 6.05 # set timeout slightly larger than a multiple of 3
REQUEST_READ_TIMEOUT_SECS = 10

# Angular settings are dir /static

