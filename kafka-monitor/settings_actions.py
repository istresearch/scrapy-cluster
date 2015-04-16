# Redis host information
REDIS_HOST = 'server-106'
REDIS_PORT = 6379

# Kafka server information
KAFKA_HOSTS = 'server-107:9092'
KAFKA_INCOMING_TOPIC = 'demo.inbound_actions'
KAFKA_GROUP = 'demo-group'

SCHEMA = "action_schema.json"
SCHEMA_METHOD = "handle_action_request"
