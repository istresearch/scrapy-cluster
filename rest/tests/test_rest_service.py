'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from mock import call
from mock import mock_open
from rest_service import RestService
import mock
import socket
import time

from kafka.common import OffsetOutOfRangeError
from kafka.conn import ConnectionStates
from redis.exceptions import ConnectionError


class TestRestService(TestCase):

    def setUp(self):
        self.rest_service = RestService("settings.py")
        self.rest_service.settings = self.rest_service.wrapper.load("settings.py")
        self.rest_service.logger = MagicMock()

    @mock.patch('os.listdir', MagicMock(return_value=['hey.json']))
    @mock.patch('__builtin__.open', mock_open(read_data='bibble'), create=True)
    def test_load_schemas_bad(self):
        with self.assertRaises(ValueError):
            self.rest_service._load_schemas()

    @mock.patch('os.listdir', MagicMock(return_value=['hey2.json']))
    @mock.patch('__builtin__.open', mock_open(read_data='{\"stuff\":\"value\"}'), create=True)
    def test_load_schemas_bad(self):
        self.rest_service._load_schemas()
        self.assertEquals(self.rest_service.schemas,
                          {'hey2': {u'stuff': u'value'}})

    def test_process_messages(self):
        self.rest_service.consumer = MagicMock()
        self.rest_service._check_kafka_disconnect = MagicMock()

        # handle kafka offset errors
        self.rest_service.consumer = MagicMock(
                        side_effect=OffsetOutOfRangeError("1"))
        try:
            self.rest_service._process_messages()
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

        self.rest_service.consumer = MagicMock()
        self.rest_service.consumer.__iter__.return_value = messages
        try:
            self.rest_service._process_messages()
        except OffsetOutOfRangeError:
            self.fail("_process_messages did not handle bad json")

        # test got poll result
        self.rest_service.uuids = {'abc123': 'poll'}
        self.rest_service._send_result_to_redis = MagicMock()
        message_string = "{\"uuid\":\"abc123\"}"
        m.value = message_string
        messages = [m]
        self.rest_service._process_messages()
        self.assertTrue(self.rest_service._send_result_to_redis.called)

        # test got in process call result
        self.rest_service.uuids = {'abc123': None}
        self.rest_service._send_result_to_redis = MagicMock()
        message_string = "{\"uuid\":\"abc123\"}"
        m.value = message_string
        messages = [m]
        self.rest_service._process_messages()
        self.assertEquals(self.rest_service.uuids, {'abc123': {u'uuid': u'abc123'}})

    def test_send_result_to_redis(self):
        # test not connected
        self.rest_service.redis_connected = False
        self.rest_service.logger.warning = MagicMock()
        self.rest_service._send_result_to_redis('stuff')
        self.assertTrue(self.rest_service.logger.warning.called)

        # test connected
        self.rest_service.redis_connected = True
        self.rest_service.redis_conn = MagicMock()
        self.rest_service.redis_conn.set = MagicMock()
        self.rest_service._send_result_to_redis({'uuid': 'abc'})
        self.rest_service.redis_conn.set.assert_called_with('rest:poll:abc',
                                                            '{"uuid": "abc"}')

        # throw error
        self.rest_service._spawn_redis_connection_thread = MagicMock()
        self.rest_service.redis_conn.set = MagicMock(side_effect=ConnectionError)
        self.rest_service._send_result_to_redis({'uuid': 'abc'})
        self.assertTrue(self.rest_service._spawn_redis_connection_thread.called)


    def test_check_kafka_disconnect(self):
        # connection setup
        class State(object):
            pass

        d1 = State()
        d1.state = ConnectionStates.DISCONNECTED

        d2 = State()
        d2.state = ConnectionStates.DISCONNECTING

        d3 = State()
        d3.state = ConnectionStates.CONNECTED

        class Client(object):
            pass

        self.rest_service._spawn_kafka_connection_thread = MagicMock()
        self.rest_service.consumer = MagicMock()

        # all connected
        client = Client()
        client._conns = {'1': d3}
        self.rest_service.consumer._client = client
        self.rest_service._check_kafka_disconnect()
        self.assertFalse(self.rest_service._spawn_kafka_connection_thread.called)

        # disconnecting
        client = Client()
        client._conns = {'1': d2}
        self.rest_service.consumer._client = client
        self.rest_service._check_kafka_disconnect()
        self.assertTrue(self.rest_service._spawn_kafka_connection_thread.called)
        self.rest_service._spawn_kafka_connection_thread.reset_mock()

        # disconnected
        client = Client()
        client._conns = {'1': d1}
        self.rest_service.consumer._client = client
        self.rest_service._check_kafka_disconnect()
        self.assertTrue(self.rest_service._spawn_kafka_connection_thread.called)

    @mock.patch('socket.gethostname', return_value='host')
    def test_report_self(self, h):
        # test not connected
        self.rest_service.redis_connected = False
        self.rest_service.logger.warn = MagicMock()
        self.rest_service._report_self()
        self.assertTrue(self.rest_service.logger.warn.called)

        # test connected
        self.rest_service.my_uuid = 'abc999'
        self.rest_service.get_time = MagicMock(return_value=5)
        self.rest_service.redis_connected = True
        self.rest_service.redis_conn = MagicMock()
        self.rest_service.redis_conn.set = MagicMock()
        self.rest_service._report_self()
        self.rest_service.redis_conn.set.assert_called_with('stats:rest:self:host:abc999',
                                                            5)
        # throw error
        self.rest_service._spawn_redis_connection_thread = MagicMock()
        self.rest_service.redis_conn.expire = MagicMock(side_effect=ConnectionError)
        self.rest_service._report_self()
        self.assertTrue(self.rest_service._spawn_redis_connection_thread.called)

    def test_setup_kafka(self):
        self.rest_service._create_producer = MagicMock()
        self.rest_service._spawn_kafka_consumer_thread = MagicMock()

        # consumer/producer != None
        self.rest_service.consumer = MagicMock()
        self.rest_service.consumer.close = MagicMock()
        self.rest_service.producer = MagicMock()
        self.rest_service.producer.close = MagicMock()

        # eary exit to ensure everything is closed
        self.rest_service._create_consumer = MagicMock(side_effect=Exception())

        try:
            self.rest_service._setup_kafka()
        except:
            pass
        self.assertEquals(self.rest_service.consumer, None)
        self.assertEquals(self.rest_service.producer, None)

        # test if everything flows through
        self.rest_service._create_consumer = MagicMock()
        self.rest_service._setup_kafka()
        self.assertTrue(self.rest_service.kafka_connected)
        self.assertTrue(self.rest_service._spawn_kafka_consumer_thread.called)

    def test_create_ret_object(self):
        # failure
        r = {
            "status": "FAILURE",
            "data": None,
            "error": None
        }
        self.assertEquals(self.rest_service._create_ret_object(status=self.rest_service.FAILURE), r)

        # success
        r = {
            "status": "SUCCESS",
            "data": None,
            "error": None
        }
        self.assertEquals(self.rest_service._create_ret_object(status=self.rest_service.SUCCESS), r)

        # data
        r = {
            "status": "SUCCESS",
            "data": 'blah',
            "error": None
        }
        self.assertEquals(self.rest_service._create_ret_object(status=self.rest_service.SUCCESS, data='blah'), r)

        # error message
        r = {
            "status": "FAILURE",
            "data": None,
            "error": {
                "message": 'err'
            }
        }
        self.assertEquals(self.rest_service._create_ret_object(status=self.rest_service.FAILURE,
                                                               error=True,
                                                               error_message='err'), r)

        # error cause
        r = {
            "status": "FAILURE",
            "data": None,
            "error": {
                "message": 'err',
                "cause": "the cause"
            }
        }
        self.assertEquals(self.rest_service._create_ret_object(status=self.rest_service.FAILURE,
                                                               error=True,
                                                               error_message='err',
                                                               error_cause="the cause"), r)

    def test_close_thread(self):
        thread = MagicMock()

        results = [True, False]

        def ret_val(*args):
            return results.pop(0)

        thread.isAlive = MagicMock(side_effect=ret_val)

        # closed fine
        self.rest_service.logger.warn = MagicMock()
        self.rest_service._close_thread(thread, "blah")
        self.assertFalse(self.rest_service.logger.warn.called)

        # didnt close
        results = [True, True]
        self.rest_service.logger.warn = MagicMock()
        self.rest_service._close_thread(thread, "blah2")
        self.assertTrue(self.rest_service.logger.warn.called)

    def test_close(self):
        self.rest_service.consumer = MagicMock()
        self.rest_service.consumer.close = MagicMock()
        self.rest_service.producer = MagicMock()
        self.rest_service.producer.close = MagicMock()

        self.rest_service._close_thread = MagicMock()
        self.rest_service.close()

        self.assertEquals(self.rest_service._close_thread.call_count, 4)
        self.assertTrue(self.rest_service.closed)
        self.assertTrue(self.rest_service.consumer.close.called)
        self.assertTrue(self.rest_service.producer.close.called)

    def test_calculate_health(self):
        self.rest_service.redis_connected = False
        self.rest_service.kafka_connected = False
        self.assertEquals(self.rest_service._calculate_health(), "RED")

        self.rest_service.redis_connected = True
        self.rest_service.kafka_connected = False
        self.assertEquals(self.rest_service._calculate_health(), "YELLOW")

        self.rest_service.redis_connected = False
        self.rest_service.kafka_connected = True
        self.assertEquals(self.rest_service._calculate_health(), "YELLOW")

        self.rest_service.redis_connected = True
        self.rest_service.kafka_connected = True
        self.assertEquals(self.rest_service._calculate_health(), "GREEN")

    # Route decorators --------

    def test_log_call(self):
        pass

    def test_error_catch(self):
        pass

    def test_validate_json(self):
        pass

    def test_validate_schema(self):
        pass

    # Routes ------------------

    def test_index(self):
        pass

    def test_feed(self):
        pass

    def test_pull(self):
        pass
