#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer

import time
import redis
import json
import sys

from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators

from docopt import docopt

from settings import (REDIS_HOST, REDIS_PORT, KAFKA_INCOMING_TOPIC, KAFKA_GROUP,
    KAFKA_HOSTS, SCHEMA)

try:
    import cPickle as pickle
except ImportError:
    import pickle

class KafkaMonitor:

    def __init__(self):
        # only need kafka for both uses
        self.kafka_conn = KafkaClient(KAFKA_HOSTS)

    def setup(self):
        # set up redis
        self.redis_conn = redis.Redis(host=REDIS_HOST,
                                      port=REDIS_PORT)

        # set up kafka
        self.kafka_conn.ensure_topic_exists(KAFKA_INCOMING_TOPIC)
        self.consumer = SimpleConsumer(self.kafka_conn,
                                  KAFKA_GROUP,
                                  KAFKA_INCOMING_TOPIC,
                                  auto_commit=True,
                                  iter_timeout=1.0)

        # set up validator with defaults
        self.validator = self.extend_with_default(Draft4Validator)

    def extend_with_default(self, validator_class):
        '''
        Method to add default fields to our schema validation
        '''
        validate_properties = validator_class.VALIDATORS["properties"]

        def set_defaults(validator, properties, instance, schema):
            for error in validate_properties(
                validator, properties, instance, schema,
            ):
                yield error

            for property, subschema in properties.iteritems():
                if "default" in subschema:
                    instance.setdefault(property, subschema["default"])

        return validators.extend(
            validator_class, {"properties" : set_defaults},
        )

    def handle_crawl_request(self, dict):
        '''
        Processes a vaild crawl request

        @param dict: a valid dictionary object
        '''
        # format key
        ex_res = self.extract(dict['url'])
        key = "{sid}:{dom}.{suf}:queue".format(
            sid=dict['spiderid'],
            dom=ex_res.domain,
            suf=ex_res.suffix)
        val = pickle.dumps(dict, protocol=-1)

        # shortcut to shove stuff into the priority queue
        self.redis_conn.zadd(key, val, -dict['priority'])

        # if timeout crawl, add value to redis
        # if timeout crawl, add value to redis
        if 'expires' in dict:
            key = "timeout:{crawlid}:value".format(
                            crawlid=dict['crawlid'])
            redis_conn.set(key, dict['expires'])

        print "successfully added crawl"

    def _main_loop(self):
        '''
        Continuous loop that reads from a kafka topic and tries to validate
        incoming messages
        '''
        while True:
            start = time.time()

            for message in self.consumer.get_messages():
                if message is None:
                    break
                try:
                    the_dict = json.loads(message.message.value)

                    try:
                        self.validator(self.schema).validate(the_dict)
                        self.handle_crawl_request(the_dict)
                    except ValidationError as ex:
                        print "invalid json received"
                except ValueError:
                        print "bad json recieved"

            end = time.time()
            time.sleep(.01)

    def run(self):
        '''
        Sets up the schema to be validated against
        '''
        self.setup()
        with open(SCHEMA) as the_file:
            # No try/catch so we can see if there is a json parse error
            # on the schemas
            self.schema = json.load(the_file)
            self._main_loop()

    def feed(self, json_item):
        '''
        Feeds a json item into the Kafka topic

        @param json_item: The loaded json object
        '''
        topic = KAFKA_INCOMING_TOPIC
        producer = SimpleProducer(self.kafka_conn)
        print "=> feeding JSON request into {0}...".format(topic)
        print json.dumps(json_item, indent=4)
        self.kafka_conn.ensure_topic_exists(topic)
        producer.send_messages(topic, json.dumps(json_item))
        print "=> done feeding request."

def main():
    """monitor: Monitor the Kafka topic for incoming URLs, validate the
    input requests.

    Usage:
        monitor run
        monitor feed <json_req>

    Examples:

       Run the monitor:

            python kafka-monitor.py run

        It'll sit there. In a separate terminal, feed it some data:

            python kafka-monitor.py feed '{"url": "http://istresearch.com", "appid":"testapp", "crawlid":"ABC123"}'

        That message will be inserted into the Kafka topic. You should then see the
        monitor terminal pick it up and insert the data into Redis. Or, if you
        made a typo, you'll see a json or jsonschema validation error.
    """
    args = docopt(main.__doc__)

    kafka_monitor = KafkaMonitor()

    if args["run"]:
        return kafka_monitor.run()
    if args["feed"]:
        json_req = args["<json_req>"]
        try:
            parsed = json.loads(json_req)
        except ValueError:
            print "json failed to parse"
            return 1
        else:
            return kafka_monitor.feed(parsed)


if __name__ == "__main__":
    sys.exit(main())
