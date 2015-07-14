# Redis host information
REDIS_HOST = 'node2'
REDIS_PORT = 6379

# Kafka server information
KAFKA_HOSTS = 'node3'
KAFKA_INCOMING_TOPIC = 'demo.incoming_urls'
KAFKA_GROUP = 'demo-group'

HANDLER = "handlers.scraper_handler.ScraperHandler"

#SCHEMA = "scraper_schema.json"
#SCHEMA_METHOD = "handle_crawl_request"
