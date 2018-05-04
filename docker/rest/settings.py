# THIS FILE SHOULD STAY IN SYNC WITH /rest/settings.py

# This file houses all default settings for the Redis Monitor
# to override please use a custom localsettings.py file
import os
def str2bool(v):
    return str(v).lower() in ('true', '1') if type(v) == str else bool(v)

# Flask configuration
FLASK_LOGGING_ENABLED = os.getenv('FLASK_LOGGING_ENABLED', True)
FLASK_PORT = int(os.getenv('FLASK_PORT', 5343))

# Redis host information
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

# Kafka server information ------------
KAFKA_HOSTS = [x.strip() for x in os.getenv('KAFKA_HOSTS', 'kafka:9092').split(',')]
KAFKA_TOPIC_PREFIX = os.getenv('KAFKA_TOPIC_PREFIX', 'demo')
KAFKA_FEED_TIMEOUT = 10

KAFKA_CONSUMER_AUTO_OFFSET_RESET = 'latest'
KAFKA_CONSUMER_TIMEOUT = 50
KAFKA_CONSUMER_COMMIT_INTERVAL_MS = 5000
KAFKA_CONSUMER_AUTO_COMMIT_ENABLE = True
KAFKA_CONSUMER_FETCH_MESSAGE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
KAFKA_CONSUMER_SLEEP_TIME = 1

KAFKA_PRODUCER_TOPIC = os.getenv('KAFKA_PRODUCER_TOPIC', 'demo.incoming')
KAFKA_PRODUCER_BATCH_LINGER_MS = 25  # 25 ms before flush
KAFKA_PRODUCER_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB before blocking

# logging setup
LOGGER_NAME = 'rest-service'
LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_FILE = 'rest_service.log'
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUPS = 5
LOG_STDOUT = str2bool(os.getenv('LOG_STDOUT', True))
LOG_JSON = str2bool(os.getenv('LOG_JSON', False))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# internal configuration
SLEEP_TIME = 5
HEARTBEAT_TIMEOUT = 120
DAEMON_THREAD_JOIN_TIMEOUT = 10
WAIT_FOR_RESPONSE_TIME = 5
SCHEMA_DIR = 'schemas/'
