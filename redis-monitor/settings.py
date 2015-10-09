# This file houses all default settings for the Redis Monitor
# to override please use a custom localsettings.py file

# Redis host configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

KAFKA_HOSTS = 'localhost:9092'
KAFKA_TOPIC_PREFIX = 'demo'
KAFKA_CONN_TIMEOUT = 5

PLUGIN_DIR = "plugins/"
PLUGINS = {
    'plugins.info_monitor.InfoMonitor': 100,
    'plugins.stop_monitor.StopMonitor': 200,
    'plugins.expire_monitor.ExpireMonitor': 300,
}

# logging setup
LOGGER_NAME = 'sc-logger'
LOG_DIR = 'logs'
LOG_FILE = 'main.log'
LOG_MAX_BYTES = '10MB'
LOG_BACKUPS = 5
LOG_STDOUT = True
LOG_JSON = False
LOG_LEVEL = 'INFO'