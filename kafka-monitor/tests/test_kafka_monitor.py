'''
Offline tests
'''
from builtins import object

from unittest import TestCase
from mock import MagicMock

from kafka_monitor import KafkaMonitor
from plugins.base_handler import BaseHandler

from kafka.common import OffsetOutOfRangeError
from jsonschema import Draft4Validator


class ExampleHandler(BaseHandler):
    schema = "crazy_schema.json"

    def setup(self, settings):
        pass


class TestKafkaMonitor(TestCase):

    def setUp(self):
        self.kafka_monitor = KafkaMonitor("settings.py", True)
        self.kafka_monitor.settings = self.kafka_monitor.wrapper.load("settings.py")
        self.kafka_monitor.logger = MagicMock()

    def test_load_plugins(self):
        # test loading default plugins
        assert_keys = [100, 200, 300, 400]
        self.kafka_monitor._load_plugins()
        self.assertEqual(list(self.kafka_monitor.plugins_dict.keys()), assert_keys)

        # test removing a plugin from settings
        assert_keys = [200, 300, 400]
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.scraper_handler.ScraperHandler'] = None
        self.kafka_monitor._load_plugins()
        self.assertEqual(list(self.kafka_monitor.plugins_dict.keys()), assert_keys)
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.scraper_handler.ScraperHandler'] = 100

        # fail if the class is not found
        self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler'] = 300
        self.assertRaises(ImportError, self.kafka_monitor._load_plugins)
        del self.kafka_monitor.settings['PLUGINS'] \
            ['plugins.crazy_class.CrazyHandler']

        # Throw error if schema could not be found
        self.kafka_monitor.settings['PLUGINS'] \
            ['tests.test_kafka_monitor.ExampleHandler'] = 300,
        self.assertRaises(IOError, self.kafka_monitor._load_plugins)
        del self.kafka_monitor.settings['PLUGINS'] \
            ['tests.test_kafka_monitor.ExampleHandler']

    def test_load_stats_total(self):
        # test no rolling stats, only total
        self.kafka_monitor.stats_dict = {}
        self.kafka_monitor.settings['STATS_TIMES'] = []
        self.kafka_monitor._setup_stats_total(MagicMock())

        self.assertEqual(list(self.kafka_monitor.stats_dict['total'].keys()), ['lifetime'])
        self.assertEqual(list(self.kafka_monitor.stats_dict['fail'].keys()), ['lifetime'])

        # test good/bad rolling stats
        self.kafka_monitor.stats_dict = {}
        self.kafka_monitor.settings['STATS_TIMES'] = [
            'SECONDS_15_MINUTE',
            'SECONDS_1_HOUR',
            'SECONDS_DUMB',
        ]
        good = [
            'lifetime',  # for totals, not DUMB
            '900',
            '3600',
        ]

        self.kafka_monitor._setup_stats_total(MagicMock())
        self.assertEqual(
            sorted([str(x) for x in self.kafka_monitor.stats_dict['total'].keys()]),
            sorted(good))
        self.assertEqual(
            sorted([str(x) for x in self.kafka_monitor.stats_dict['fail'].keys()]),
            sorted(good))

        k1 = 'stats:kafka-monitor:total'
        k2 = 'stats:kafka-monitor:fail'

        for time_key in self.kafka_monitor.stats_dict['total']:
            if time_key == 0:
                self.assertEqual(
                    self.kafka_monitor.stats_dict['total'][0].key,
                    '{k}:lifetime'.format(k=k1)
                    )
            else:
                self.assertEqual(
                    self.kafka_monitor.stats_dict['total'][time_key].key,
                    '{k}:{t}'.format(k=k1, t=time_key)
                    )

        for time_key in self.kafka_monitor.stats_dict['fail']:
            if time_key == 0:
                self.assertEqual(
                    self.kafka_monitor.stats_dict['fail'][0].key,
                    '{k}:lifetime'.format(k=k2)
                    )
            else:
                self.assertEqual(
                    self.kafka_monitor.stats_dict['fail'][time_key].key,
                    '{k}:{t}'.format(k=k2, t=time_key)
                    )


    def test_load_stats_plugins(self):
        # lets assume we are loading the default plugins
        self.kafka_monitor._load_plugins()

        # test no rolling stats
        self.kafka_monitor.stats_dict = {}
        self.kafka_monitor.settings['STATS_TIMES'] = []
        self.kafka_monitor._setup_stats_plugins(MagicMock())
        defaults = [
            'ScraperHandler',
            'ActionHandler',
            'StatsHandler',
            'ZookeeperHandler'
        ]

        self.assertEqual(
            sorted(list(self.kafka_monitor.stats_dict['plugins'].keys())),
            sorted(defaults))

        for key in self.kafka_monitor.plugins_dict:
            plugin_name = self.kafka_monitor.plugins_dict[key]['instance'].__class__.__name__
            self.assertEqual(
                list(self.kafka_monitor.stats_dict['plugins'][plugin_name].keys()),
                ['lifetime'])

        # test good/bad rolling stats
        self.kafka_monitor.stats_dict = {}
        self.kafka_monitor.settings['STATS_TIMES'] = [
            'SECONDS_15_MINUTE',
            'SECONDS_1_HOUR',
            'SECONDS_DUMB',
        ]
        good = [
            'lifetime',  # for totals, not DUMB
            '900',
            '3600',
        ]

        self.kafka_monitor._setup_stats_plugins(MagicMock())

        self.assertEqual(
            sorted(self.kafka_monitor.stats_dict['plugins'].keys()),
            sorted(defaults))

        for key in self.kafka_monitor.plugins_dict:
            plugin_name = self.kafka_monitor.plugins_dict[key]['instance'].__class__.__name__
            self.assertEqual(
                sorted([str(x) for x in self.kafka_monitor.stats_dict['plugins'][plugin_name].keys()]),
                sorted(good))

        for plugin_key in self.kafka_monitor.stats_dict['plugins']:
            k1 = 'stats:kafka-monitor:{p}'.format(p=plugin_key)
            for time_key in self.kafka_monitor.stats_dict['plugins'][plugin_key]:
                if time_key == 0:
                    self.assertEqual(
                        self.kafka_monitor.stats_dict['plugins'][plugin_key][0].key,
                        '{k}:lifetime'.format(k=k1)
                        )
                else:
                    self.assertEqual(
                        self.kafka_monitor.stats_dict['plugins'][plugin_key][time_key].key,
                        '{k}:{t}'.format(k=k1, t=time_key)
                        )

    def test_process_messages(self):
        self.kafka_monitor.consumer = MagicMock()
        self.kafka_monitor.stats_dict = {}

        # handle kafka offset errors
        self.kafka_monitor.consumer = MagicMock(
                        side_effect=OffsetOutOfRangeError("1"))
        try:
            self.kafka_monitor._process_messages()
        except OffsetOutOfRangeError:
            self.fail("_process_messages did not handle Kafka Offset Error")

        # handle bad json errors
        message_string = "{\"sdasdf   sd}"

        # fake class so we can use dot notation
        class a(object):
            pass

        m = a()
        m.value = message_string
        messages = [m]

        self.kafka_monitor.consumer = MagicMock()
        self.kafka_monitor.consumer.__iter__.return_value = messages
        try:
            self.kafka_monitor._process_messages()
        except OffsetOutOfRangeError:
            self.fail("_process_messages did not handle bad json")

        # set up to process messages
        self.kafka_monitor._load_plugins()
        self.kafka_monitor.validator = self.kafka_monitor.extend_with_default(Draft4Validator)
        list(self.kafka_monitor.plugins_dict.items())[0][1]['instance'].handle = MagicMock(side_effect=AssertionError("scrape"))
        list(self.kafka_monitor.plugins_dict.items())[1][1]['instance'].handle = MagicMock(side_effect=AssertionError("action"))

        #  test that handler function is called for the scraper
        message_string = "{\"url\":\"www.stuff.com\",\"crawlid\":\"1234\"," \
            "\"appid\":\"testapp\"}"
        m.value = message_string
        messages = [m]
        self.kafka_monitor.consumer.__iter__.return_value = messages
        try:
            self.kafka_monitor._process_messages()
            self.fail("Scrape not called")
        except AssertionError as e:
            self.assertEqual("scrape", str(e))

        # test that handler function is called for the actions
        message_string = "{\"uuid\":\"blah\",\"crawlid\":\"1234\"," \
            "\"appid\":\"testapp\",\"action\":\"info\",\"spiderid\":\"link\"}"

        m.value = message_string
        messages = [m]
        self.kafka_monitor.consumer.__iter__.return_value = messages
        try:
            self.kafka_monitor._process_messages()
            self.fail("Action not called")
        except AssertionError as e:
            self.assertEqual("action", str(e))

