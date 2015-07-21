# Redis host information
REDIS_HOST = ''
REDIS_PORT = 6379

# Kafka server information
KAFKA_HOSTS = ''
KAFKA_INCOMING_TOPIC = 'demo.incoming_urls'
KAFKA_GROUP = 'demo-group'

PLUGINS = {
 'plugins.scraper_handler.ScraperHandler': 100,
 'plugins.action_handler.ActionHandler': 200,
}
