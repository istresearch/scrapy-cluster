# Flask configuration
FLASK_LOGGING_ENABLED = True
FLASK_PORT = 5000

# logging setup
LOGGER_NAME = 'ui_service'
LOG_DIR = 'logs'
LOG_FILE = 'ui_service.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = True
LOG_JSON = False
LOG_LEVEL = 'INFO'

# internal configuration
REST_ENDPOINT = "http://localhost:5343"
REQUEST_SO_TIMEOUT_SECS = 6.05 # set timeout slightly larger than a multiple of 3
REQUEST_READ_TIMEOUT_SECS = 10

# Angular settings are dir /static
