#!/usr/bin/python

from kafka.client import KafkaClient
from kafka.consumer import SimpleConsumer
from kafka.producer import SimpleProducer
from kafka.common import OffsetOutOfRangeError
from collections import OrderedDict

import time
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

    plugin_dir = "plugins/"
    default_plugins = {
        'plugins.scraper_handler.ScraperHandler': 100,
        'plugins.action_handler.ActionHandler': 200,
    }

    def __init__(self, settings):
        # dynamic import of settings file
        # remove the .py from the filename
        self.settings = importlib.import_module(settings[:-3])

    def import_class(self, cl):
        '''
        Imports a class from a string

        @param name: the module and class name in dot notation
        '''
        d = cl.rfind(".")
        classname = cl[d+1:len(cl)]
        m = __import__(cl[0:d], globals(), locals(), [classname])
        return getattr(m, classname)

    def _load_plugins(self):
        '''
        Sets up all plugins, defaults and settings.py
        '''
        try:
            loaded_plugins = self.settings.PLUGINS
            self.default_plugins.update(self.settings.PLUGINS)
        except Exception as e:
            pass

        self.plugins_dict = {}
        for key in self.default_plugins:
            # skip loading the plugin if its value is None
            if self.default_plugins[key] is None:
                continue
            # valid plugin, import and setup
            the_class = self.import_class(key)
            instance = the_class()
            instance.setup(self.settings)

            the_schema = None
            with open(self.plugin_dir + instance.schema) as the_file:
                the_schema = json.load(the_file)

            mini = {}
            mini['instance'] = instance
            mini['schema'] = the_schema

            self.plugins_dict[self.default_plugins[key]] = mini

        self.plugins_dict = OrderedDict(sorted(self.plugins_dict.items(),
                                                key=lambda t: t[0]))

    def setup(self):
        self.kafka_conn = KafkaClient(self.settings.KAFKA_HOSTS)
        self.kafka_conn.ensure_topic_exists(self.settings.KAFKA_INCOMING_TOPIC)
        self.consumer = SimpleConsumer(self.kafka_conn,
                                  self.settings.KAFKA_GROUP,
                                  self.settings.KAFKA_INCOMING_TOPIC,
                                  auto_commit=True,
                                  iter_timeout=1.0)

        self.validator = self.extend_with_default(Draft4Validator)
        self._load_plugins()

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

    def _main_loop(self):
        '''
        Continuous loop that reads from a kafka topic and tries to validate
        incoming messages
        '''
        while True:
            self._process_messages()
            time.sleep(.01)

    def _process_messages(self):
        try:
            for message in self.consumer.get_messages():
                if message is None:
                    break
                try:
                    the_dict = json.loads(message.message.value)

                    found_plugin = False
                    for key in self.plugins_dict:
                        obj = self.plugins_dict[key]
                        instance = obj['instance']
                        schema = obj['schema']

                        try:
                            self.validator(schema).validate(the_dict)
                            found_plugin = True
                            ret = instance.handle(the_dict)
                            # break if nothing is returned
                            if ret is None:
                                break
                        except ValidationError as ex:
                            pass
                    if not found_plugin:
                        print "Did not find schema to validate request"

                except ValueError:
                        print "bad json recieved"
        except OffsetOutOfRangeError:
            # consumer has no idea where they are
            self.consumer.seek(0,2)

    def run(self):
        '''
        Set up and run
        '''
        self.setup()
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
    """kafka-monitor: Monitor the Kafka topic for incoming URLs, validate the
    input requests.

    Usage:
        kafka-monitor run [--settings=<settings>]
        kafka-monitor feed [--settings=<settings>] <json_req>

    Examples:

       Run the monitor:

            python kafka-monitor.py run

        It'll sit there. In a separate terminal, feed it some data:

            python kafka-monitor.py feed '{"url": "http://istresearch.com", "appid":"testapp", "crawlid":"ABC123"}'

        For longer crawls, retrieve some information:

            python kafka-monitor.py feed '{"action":"info", "appid":"testapp", "crawlid":"ABC123", "uuid":"someuuid", "spiderid":"link"}'

        That message will be inserted into the Kafka topic. You should then see the
        monitor terminal pick it up and insert the data into Redis. Or, if you
        made a typo, you'll see a json or jsonschema validation error.

    Options:
        -s --settings <settings>      The settings file to read from [default: settings.py].
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
