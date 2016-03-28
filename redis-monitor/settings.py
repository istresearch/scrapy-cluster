# This file houses all default settings for the Redis Monitor
# to override please use a custom localsettings.py file

# Redis host configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

KAFKA_HOSTS = 'localhost:9092'
KAFKA_TOPIC_PREFIX = 'demo'
KAFKA_CONN_TIMEOUT = 5
KAFKA_APPID_TOPICS = False

PLUGIN_DIR = "plugins/"
PLUGINS = {
    'plugins.info_monitor.InfoMonitor': 100,
    'plugins.stop_monitor.StopMonitor': 200,
    'plugins.expire_monitor.ExpireMonitor': 300,
    'plugins.stats_monitor.StatsMonitor': 400,
}

# logging setup
LOGGER_NAME = 'redis-monitor'
LOG_DIR = 'logs'
LOG_FILE = 'redis_monitor.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = True
LOG_JSON = False
LOG_LEVEL = 'INFO'

# stats setup
STATS_TOTAL = True
STATS_PLUGINS = True
STATS_CYCLE = 5
STATS_DUMP = 60
STATS_DUMP_CRAWL = True
STATS_DUMP_QUEUE = True
# from time variables in scutils.stats_collector class
STATS_TIMES = [
    'SECONDS_15_MINUTE',
    'SECONDS_1_HOUR',
    'SECONDS_6_HOUR',
    'SECONDS_12_HOUR',
    'SECONDS_1_DAY',
    'SECONDS_1_WEEK',
]
