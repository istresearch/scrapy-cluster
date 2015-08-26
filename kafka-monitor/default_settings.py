# This file houses all default settings for the Kafka Monitor
# to override please use a custom settings.py file

# Redis host information
REDIS_HOST = 'localhost'
REDIS_PORT = 6379

# Kafka server information
KAFKA_HOSTS = 'localhost:9092'
KAFKA_INCOMING_TOPIC = 'demo.incoming'
KAFKA_GROUP = 'demo-group'

# plugin setup
PLUGIN_DIR = 'plugins/'
PLUGINS = {
    'plugins.scraper_handler.ScraperHandler': 100,
    'plugins.action_handler.ActionHandler': 200,
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

