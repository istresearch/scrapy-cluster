# This file houses all default settings for the Redis Monitor
# to override please use a custom localsettings.py file

# Redis host configuration
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None
REDIS_SOCKET_TIMEOUT = 10

KAFKA_HOSTS = 'localhost:9092'
KAFKA_TOPIC_PREFIX = 'demo'
KAFKA_CONN_TIMEOUT = 5
KAFKA_APPID_TOPICS = False
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking

# Zookeeper Settings
ZOOKEEPER_ASSIGN_PATH = '/scrapy-cluster/crawler/'
ZOOKEEPER_ID = 'all'
ZOOKEEPER_HOSTS = 'localhost:2181'

PLUGIN_DIR = "plugins/"
PLUGINS = {
    'plugins.info_monitor.InfoMonitor': 100,
    'plugins.stop_monitor.StopMonitor': 200,
    'plugins.expire_monitor.ExpireMonitor': 300,
    'plugins.stats_monitor.StatsMonitor': 400,
    'plugins.zookeeper_monitor.ZookeeperMonitor': 500,
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

# retry failures on actions
RETRY_FAILURES = True
RETRY_FAILURES_MAX = 3
REDIS_LOCK_EXPIRATION = 6
# main thread sleep time
SLEEP_TIME = 0.1
HEARTBEAT_TIMEOUT = 120

