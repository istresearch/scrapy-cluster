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
SLEEP_TIME = 5
WAIT_FOR_RESPONSE_TIME = 5
