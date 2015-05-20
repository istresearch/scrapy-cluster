#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer
from kafka.common import OffsetOutOfRangeError

import time
import redis
import json
import sys
import importlib

from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators

from docopt import docopt

try:
    import cPickle as pickle
except ImportError:
    import pickle

class KafkaMonitor:

    def __init__(self, settings):
        # dynamic import of settings file
        # remove the .py from the filename
        self.settings = importlib.import_module(settings[:-3])

        # only need kafka for both uses
        self.kafka_conn = KafkaClient(self.settings.KAFKA_HOSTS)

    def get_method(self, key):
        if key == 'handle_crawl_request':
            return self.handle_crawl_request
        elif key == 'handle_action_request':
            return self.handle_action_request
        raise AttributeError(key)

    def setup(self):
        self.redis_conn = redis.Redis(host=self.settings.REDIS_HOST,
                                      port=self.settings.REDIS_PORT)

        self.kafka_conn.ensure_topic_exists(self.settings.KAFKA_INCOMING_TOPIC)
        self.consumer = SimpleConsumer(self.kafka_conn,
                                  self.settings.KAFKA_GROUP,
                                  self.settings.KAFKA_INCOMING_TOPIC,
                                  auto_commit=True,
                                  iter_timeout=1.0)

        self.result_method = self.get_method(self.settings.SCHEMA_METHOD)

        self.validator = self.extend_with_default(Draft4Validator)

    def extend_with_default(self, validator_class):
        '''
        Method to add default fields to our schema validation
        ( From the docs )
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
        key = "{sid}:queue".format(sid=dict['spiderid'])
        val = pickle.dumps(dict, protocol=-1)

        # shortcut to shove stuff into the priority queue
        self.redis_conn.zadd(key, val, -dict['priority'])

        # if timeout crawl, add value to redis
        if 'expires' in dict:
            key = "timeout:{sid}:{appid}:{crawlid}".format(
                            sid=dict['spiderid'],
                            appid=dict['appid'],
                            crawlid=dict['crawlid'])
            self.redis_conn.set(key, dict['expires'])

    def handle_action_request(self, dict):
        '''
        Processes a vaild action request

        @param dict: The valid dictionary object
        '''
        # format key
        key = "{action}:{spiderid}:{appid}".format(
                action = dict['action'],
                spiderid = dict['spiderid'],
                appid = dict['appid'])

        if "crawlid" in dict:
            key = key + ":" + dict['crawlid']

        self.redis_conn.set(key, dict['uuid'])

    def _main_loop(self):
        '''
        Continuous loop that reads from a kafka topic and tries to validate
        incoming messages
        '''
        while True:
            start = time.time()

            try:
                for message in self.consumer.get_messages():
                    if message is None:
                        break
                    try:
                        the_dict = json.loads(message.message.value)

                        try:
                            self.validator(self.schema).validate(the_dict)
                            self.result_method(the_dict)
                        except ValidationError as ex:
                            print "invalid json received"

                    except ValueError:
                            print "bad json recieved"
            except OffsetOutOfRangeError:
                # consumer has no idea where they are
                self.consumer.seek(0,2)

            end = time.time()
            time.sleep(.01)

    def run(self):
        '''
        Sets up the schema to be validated against
        '''
        self.setup()
        with open(self.settings.SCHEMA) as the_file:
            # No try/catch so we can see if there is a json parse error
            # on the schemas
            self.schema = json.load(the_file)
            self._main_loop()

    def feed(self, json_item):
        '''
        Feeds a json item into the Kafka topic

        @param json_item: The loaded json object
        '''
        topic = self.settings.KAFKA_INCOMING_TOPIC
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
        monitor run --settings=<settings>
        monitor feed --settings=<settings> <json_req>

    Examples:

       Run the monitors:

            python kafka-monitor.py run --settings=settings_crawling.py
            python kafka-monitor.py run --settings=settings_actions.py

        It'll sit there. In a separate terminal, feed it some data:

            python kafka-monitor.py feed -s settings_crawling.py '{"url": "http://istresearch.com", "appid":"testapp", "crawlid":"ABC123"}'

        For longer crawls, retrieve some information:

            python kafka-monitor.py feed -s settings_actions.py '{"action":"info", "appid":"testapp", "crawlid":"ABC123", "uuid":"someuuid", "spiderid":"link"}'

        That message will be inserted into the Kafka topic. You should then see the
        monitor terminal pick it up and insert the data into Redis. Or, if you
        made a typo, you'll see a json or jsonschema validation error.

    Options:
        -s --settings <settings>      The settings file to read from
    """
    args = docopt(main.__doc__)

    kafka_monitor = KafkaMonitor(args['--settings'])

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
