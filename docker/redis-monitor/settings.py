# THIS FILE SHOULD STAY IN SYNC WITH /redis-monitor/settings.py

# This file houses all default settings for the Redis Monitor
# to override please use a custom localsettings.py file
import os
def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Redis host configuration
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', 10))

KAFKA_HOSTS = [x.strip() for x in os.getenv('KAFKA_HOSTS', 'kafka:9092').split(',')]
KAFKA_TOPIC_PREFIX = os.getenv('KAFKA_TOPIC_PREFIX', 'demo')
KAFKA_CONN_TIMEOUT = 5
KAFKA_APPID_TOPICS = str2bool(os.getenv('KAFKA_APPID_TOPICS', False))
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking

# Zookeeper Settings
ZOOKEEPER_ASSIGN_PATH = '/scrapy-cluster/crawler/'
ZOOKEEPER_ID = 'all'
ZOOKEEPER_HOSTS = os.getenv('ZOOKEEPER_HOSTS', 'zookeeper:2181')

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
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_FILE = 'redis_monitor.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = str2bool(os.getenv('LOG_STDOUT', True))
LOG_JSON = str2bool(os.getenv('LOG_JSON', False))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# stats setup
STATS_TOTAL = str2bool(os.getenv('STATS_TOTAL', True))
STATS_PLUGINS = str2bool(os.getenv('STATS_PLUGINS', True))
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

