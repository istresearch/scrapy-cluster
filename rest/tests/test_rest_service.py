'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock
from mock import mock_open
from rest_service import RestService
from rest_service import (log_call, error_catch, validate_json,
                          validate_schema)
import mock
import json
import flask

from kafka.common import OffsetOutOfRangeError
from kafka.conn import ConnectionStates
from redis.exceptions import ConnectionError

class Override(RestService):

    @log_call("test logger")
    def test_log_call(self):
        pass

    @error_catch
    def test_error1(self):
        raise Exception()
        pass

    @error_catch
    def test_error2(self):
        return "test data"

    @error_catch
    def test_error3(self):
        return "test data", 109

    @validate_json
    def test_json(self):
        return 'data'

    @validate_schema('key')
    def test_schema(self):
        return 'data'


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

    def test_feed_to_kafka(self):
        self.rest_service.producer = MagicMock()

        # test good
        self.assertTrue(self.rest_service._feed_to_kafka({}))

        # test bad
        self.rest_service._spawn_kafka_connection_thread = MagicMock()
        self.rest_service.logger.error = MagicMock()
        self.rest_service.producer.send = MagicMock(side_effect=Exception)
        self.assertFalse(self.rest_service._feed_to_kafka({}))
        self.assertTrue(self.rest_service.logger.error.called)
        self.assertTrue(self.rest_service._spawn_kafka_connection_thread.called)

    # Route decorators --------

    def test_log_call(self):
        override = Override('settings.py')
        override.logger = MagicMock()
        override.logger.info = MagicMock()
        with self.rest_service.app.test_request_context():
            override.test_log_call()

        self.assertTrue(override.logger.info.called)
        self.assertEquals(override.logger.info.call_args[0][0], "test logger")

    def test_error_catch(self):
        override = Override('settings.py')
        override.logger = MagicMock()

        # test uncaught exception thrown
        with self.rest_service.app.test_request_context():
            override.logger.error = MagicMock()
            results = override.test_error1()
            self.assertTrue(override.logger.error.called)
            self.assertEquals(override.logger.error.call_args[0][0],
                              "Uncaught Exception Thrown")
            d = {
                u'data': None,
                u'error': {
                    u'message': u'An error occurred while processing your request.'
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        # test normal response
        with self.rest_service.app.test_request_context():
            override.logger.error.reset_mock()
            results = override.test_error2()
            self.assertFalse(override.logger.error.called)
            data = json.loads(results[0].data)
            self.assertEquals(data, 'test data')
            self.assertEquals(results[1], 200)

        # test normal response with alternate response code
        with self.rest_service.app.test_request_context():
            override.logger.error.reset_mock()
            results = override.test_error3()
            self.assertFalse(override.logger.error.called)
            data = json.loads(results[0].data)
            self.assertEquals(data, 'test data')
            self.assertEquals(results[1], 109)

    def test_validate_json(self):
        override = Override('settings.py')
        override.logger = MagicMock()

        # bad json
        data = '["a list", ashdasd ,\\ !]'
        with self.rest_service.app.test_request_context(data=data,
                                                        content_type='application/json'):
            results = override.test_json()
            self.assertTrue(override.logger.error.called)
            self.assertEquals(override.logger.error.call_args[0][0],
                              'The payload must be valid JSON.')

            d = {
                u'data': None,
                u'error': {
                    u'message': u'The payload must be valid JSON.'
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 400)

        # no json
        data = '["a list", ashdasd ,\\ !]'
        with self.rest_service.app.test_request_context(data=data):
            self.rest_service.logger.error.reset_mock()
            results = override.test_json()
            self.assertTrue(override.logger.error.called)
            self.assertEquals(override.logger.error.call_args[0][0],
                              'The payload must be valid JSON.')

            d = {
                u'data': None,
                u'error': {
                    u'message': u'The payload must be valid JSON.'
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 400)

        # good json
        data = '["a list", "2", "3"]'
        with self.rest_service.app.test_request_context(data=data,
                                                        content_type='application/json'):
            override.logger.reset_mock()
            results = override.test_json()
            self.assertFalse(override.logger.error.called)
            self.assertEquals(results, 'data')

    def test_validate_schema(self):
        override = Override('settings.py')
        override.logger = MagicMock()
        override.logger.error = MagicMock()

        override.schemas['key'] = {
            "type": "object",
            "properties": {
                "value": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100
                }
            },
            "required": [
                "value"
            ],
            "additionalProperties": False
        }

        # valid schema
        data = '{"value": "data here"}'
        with self.rest_service.app.test_request_context(data=data,
                                                        content_type='application/json'):
            results = override.test_schema()
            self.assertFalse(override.logger.error.called)
            self.assertEquals(results, 'data')

        # invalid schema
        data = '{"otherkey": "bad data"}'
        with self.rest_service.app.test_request_context(data=data,
                                                        content_type='application/json'):
            results = override.test_schema()
            self.assertTrue(override.logger.error.called)
            self.assertEquals(override.logger.error.call_args[0][0],
                              "Invalid Schema")

            d = {
                u'data': None,
                u'error': {
                    u'message': u"JSON did not validate against schema.",
                    u'cause': u"Additional properties are not allowed (u'otherkey' was unexpected)"
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 400)

    # Routes ------------------

    def test_index(self):
        with self.rest_service.app.test_request_context():
            self.rest_service.get_time = MagicMock(return_value=5)
            self.rest_service.my_uuid = 'a908'
            results = self.rest_service.index()
            d = {
                "kafka_connected": False,
                "redis_connected": False,
                "uptime_sec": 5,
                "my_id": 'a908',
                "node_health": 'RED'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)

    def test_feed(self):
        # test not connected
        self.rest_service.kafka_connected = False
        self.rest_service.logger.warn = MagicMock()

        with self.rest_service.app.test_request_context(data='{}',
                                                        content_type='application/json'):
            results = self.rest_service.feed()
            self.assertTrue(self.rest_service.logger.warn.called)
            d = {
                u'data': None,
                u'error': {
                    u'message': u"Unable to connect to Kafka",
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        # connected
        self.rest_service.kafka_connected = True
        # test failed to send to kafka
        self.rest_service._feed_to_kafka = MagicMock(return_value=False)
        with self.rest_service.app.test_request_context(data='{}',
                                                        content_type='application/json'):
            self.rest_service.logger.warn.reset_mock()
            results = self.rest_service.feed()
            self.assertTrue(self.rest_service.logger.warn.called)
            d = {
                u'data': None,
                u'error': {
                    u'message': u"Unable to connect to Kafka",
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        # test no uuid
        self.rest_service._feed_to_kafka = MagicMock(return_value=True)
        with self.rest_service.app.test_request_context(data='{}',
                                                        content_type='application/json'):
            results = self.rest_service.feed()
            d = {
                u'data': None,
                u'error': None,
                u'status': u'SUCCESS'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 200)

        # test with uuid, got response
        time_list = [0, 1, 2, 3, 4, 5]
        def fancy_get_time():
            r = time_list.pop(0)
            # fake multithreaded response from kafka
            if r > 4:
                self.rest_service.uuids['key'] = 'data'
            return r

        with self.rest_service.app.test_request_context(data='{"uuid":"key"}',
                                                        content_type='application/json'):
            self.rest_service.get_time = MagicMock(side_effect=fancy_get_time)
            results = self.rest_service.feed()
            d = {
                u'data': 'data',
                u'error': None,
                u'status': u'SUCCESS'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 200)
            self.assertFalse(self.rest_service.uuids.has_key('key'))

        # test with uuid, no response
        time_list = [0, 1, 2, 3, 4, 5, 6]
        def fancy_get_time2():
            return time_list.pop(0)

        with self.rest_service.app.test_request_context(data='{"uuid":"key"}',
                                                        content_type='application/json'):
            self.rest_service.get_time = MagicMock(side_effect=fancy_get_time2)
            results = self.rest_service.feed()
            d = {
                u'data': {'poll_id': "key"},
                u'error': None,
                u'status': u'SUCCESS'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 200)
            self.assertTrue(self.rest_service.uuids.has_key('key'))
            self.assertEquals(self.rest_service.uuids['key'], 'poll')

    def test_poll(self):
        orig = self.rest_service.validator
        self.rest_service.validator = MagicMock()
        self.rest_service.schemas['poll'] = MagicMock()

        # test not connected
        self.rest_service.redis_connected = False
        self.rest_service.logger.warn = MagicMock()

        with self.rest_service.app.test_request_context(data='{}',
                                                        content_type='application/json'):
            results = self.rest_service.poll()
            self.assertTrue(self.rest_service.logger.warn.called)
            d = {
                u'data': None,
                u'error': {
                    u'message': u"Unable to connect to Redis",
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        # test connected found poll key
        self.rest_service.redis_conn = MagicMock()
        self.rest_service.redis_conn.get = MagicMock(return_value='["data"]')
        self.rest_service.redis_connected = True
        with self.rest_service.app.test_request_context(data='{"poll_id":"key"}',
                                                        content_type='application/json'):
            results = self.rest_service.poll()
            d = {
                u'data': ['data'],
                u'error': None,
                u'status': u'SUCCESS'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 200)

        # test connected didnt find poll key
        self.rest_service.redis_conn.get = MagicMock(return_value=None)
        self.rest_service.redis_connected = True
        with self.rest_service.app.test_request_context(data='{"poll_id":"key"}',
                                                        content_type='application/json'):
            results = self.rest_service.poll()
            d = {
                u'data': None,
                u'error': {
                    "message": "Could not find matching poll_id"
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 404)

        # test connection error
        self.rest_service._spawn_redis_connection_thread = MagicMock()
        self.rest_service.logger.error = MagicMock()
        with self.rest_service.app.test_request_context(data='{"poll_id":"key"}',
                                                        content_type='application/json'):
            self.rest_service.redis_conn.get = MagicMock(side_effect=ConnectionError)
            results = self.rest_service.poll()
            self.assertTrue(self.rest_service.logger.error.called)
            self.assertEquals(self.rest_service.logger.error.call_args[0][0], "Lost connection to Redis")
            self.assertTrue(self.rest_service._spawn_redis_connection_thread.called)

            d = {
                u'data': None,
                u'error': {
                    u'message': u"Unable to connect to Redis",
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        # test value error
        self.rest_service.logger.warning = MagicMock()
        with self.rest_service.app.test_request_context(data='{"poll_id":"key"}',
                                                        content_type='application/json'):
            self.rest_service.redis_conn.get = MagicMock(side_effect=ValueError)
            results = self.rest_service.poll()
            self.assertTrue(self.rest_service.logger.warning.called)
            self.assertEquals(self.rest_service.logger.warning.call_args[0][0], "Unparseable JSON Received from redis")

            d = {
                u'data': None,
                u'error': {
                    u'message': u"Unparseable JSON Received from redis",
                },
                u'status': u'FAILURE'
            }
            data = json.loads(results[0].data)
            self.assertEquals(data, d)
            self.assertEquals(results[1], 500)

        self.rest_service.validator = orig

