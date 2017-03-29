import argparse
from functools import wraps
from flask import (Flask, jsonify, request)
from werkzeug.exceptions import BadRequest
from copy import deepcopy
import sys
import signal
import os
from retrying import retry
from threading import Thread
import time
import traceback
import uuid
import socket
import redis
import logging
import json
import threading

from kafka import KafkaConsumer, KafkaProducer
from kafka.common import KafkaError
from kafka.common import OffsetOutOfRangeError
from kafka.common import KafkaUnavailableError
from kafka.common import NodeNotReadyError
from kafka.common import NoBrokersAvailable
from redis.exceptions import ConnectionError
from kafka.conn import ConnectionStates

from scutils.log_factory import LogFactory
from scutils.settings_wrapper import SettingsWrapper
from scutils.method_timer import MethodTimer

from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators

# Route Decorators --------------------

def log_call(call_name):
    """Log the API call to the logger."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            instance = args[0]
            instance.logger.info(call_name, {"content": request.get_json()})
            return f(*args, **kw)
        return wrapper
    return decorator


def error_catch(f):
    """Handle unexpected errors within the rest function."""
    @wraps(f)
    def wrapper(*args, **kw):
        instance = args[0]
        try:
            result = f(*args, **kw)
            if isinstance(result, tuple):
                return jsonify(result[0]), result[1]
            else:
                return jsonify(result), 200
        except Exception as e:
            ret_dict = instance._create_ret_object(instance.FAILURE, None,
                                                   True,
                                                   instance.UNKNOWN_ERROR)
            log_dict = deepcopy(ret_dict)
            log_dict['error']['cause'] = e.message
            log_dict['error']['exception'] = str(e)
            log_dict['error']['ex'] = traceback.format_exc()
            instance.logger.error("Uncaught Exception Thrown", log_dict)
            return jsonify(ret_dict), 500
    return wrapper


def validate_json(f):
    """Validate that the call is JSON."""
    @wraps(f)
    def wrapper(*args, **kw):
        instance = args[0]
        try:
            if request.get_json() is None:
                ret_dict = instance._create_ret_object(instance.FAILURE,
                                                       None, True,
                                                       instance.MUST_JSON)
                instance.logger.error(instance.MUST_JSON)
                return jsonify(ret_dict), 400
        except BadRequest:
            ret_dict = instance._create_ret_object(instance.FAILURE, None,
                                                   True,
                                                   instance.MUST_JSON)
            instance.logger.error(instance.MUST_JSON)
            return jsonify(ret_dict), 400
        instance.logger.debug("JSON is valid")
        return f(*args, **kw)
    return wrapper


def validate_schema(schema_name):
    """Validate the JSON against a required schema_name."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kw):
            instance = args[0]
            try:
                instance.validator(instance.schemas[schema_name]).validate(request.get_json())
            except ValidationError, e:
                ret_dict = instance._create_ret_object(instance.FAILURE,
                                                       None, True,
                                                       instance.BAD_SCHEMA,
                                                       e.message)
                instance.logger.error("Invalid Schema", ret_dict)
                return jsonify(ret_dict), 400
            instance.logger.debug("Schema is valid")
            return f(*args, **kw)
        return wrapper
    return decorator


class RestService(object):

    # static strings
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    UNKNOWN_ERROR = "An error occurred while processing your request."
    MUST_JSON = "The payload must be valid JSON."
    DOES_NOT_EXIST = "The desired endpoint does not exist"
    BAD_SCHEMA = "JSON did not validate against schema."

    consumer = None
    producer = None
    closed = False
    start_time = 0
    _consumer_thread = None
    _kafka_thread = None
    _heartbeat_thread = None
    _redis_thread = None

    def __init__(self, settings_name):
        """
        @param settings_name: the local settings file name
        """
        self.settings_name = settings_name
        self.wrapper = SettingsWrapper()
        self.logger = None
        self.app = Flask(__name__)
        self.kafka_connected = False
        self.redis_connected = False
        self.my_uuid = str(uuid.uuid4()).split('-')[4]
        self.uuids = {}
        self.uuids_lock = threading.Lock()
        self.validator = self._extend_with_default(Draft4Validator)
        self.schemas = {}

    def setup(self, level=None, log_file=None, json=None):
        """
        Load everything up. Note that any arg here will override both
        default and custom settings

        @param level: the log level
        @param log_file: boolean t/f whether to log to a file, else stdout
        @param json: boolean t/f whether to write the logs in json
        """
        self.settings = self.wrapper.load(self.settings_name)

        my_level = level if level else self.settings['LOG_LEVEL']
        # negate because logger wants True for std out
        my_output = not log_file if log_file else self.settings['LOG_STDOUT']
        my_json = json if json else self.settings['LOG_JSON']
        self.logger = LogFactory.get_instance(json=my_json, stdout=my_output,
                                              level=my_level,
                                              name=self.settings['LOGGER_NAME'],
                                              dir=self.settings['LOG_DIR'],
                                              file=self.settings['LOG_FILE'],
                                              bytes=self.settings['LOG_MAX_BYTES'],
                                              backups=self.settings['LOG_BACKUPS'])

        self._decorate_routes()
        self._spawn_redis_connection_thread()
        self._spawn_kafka_connection_thread()

        # spawn heartbeat processing loop
        self._heartbeat_thread = Thread(target=self._heartbeat_loop)
        self._heartbeat_thread.setDaemon(True)
        self._heartbeat_thread.start()

        self.start_time = self.get_time()

        # disable flask logger
        if self.settings['FLASK_LOGGING_ENABLED'] == False:
            log = logging.getLogger('werkzeug')
            log.disabled = True

        self._load_schemas()

    def get_time(self):
        """Returns the current time"""
        return time.time()

    def _load_schemas(self):
        """Loads any schemas for JSON validation"""
        for filename in os.listdir(self.settings['SCHEMA_DIR']):
            if filename[-4:] == 'json':
                name = filename[:-5]
                with open(self.settings['SCHEMA_DIR'] + filename) as the_file:
                    self.schemas[name] = json.load(the_file)
                    self.logger.debug("Successfully loaded " + filename + " schema")

    def _extend_with_default(self, validator_class):
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

            for property, subschema in list(properties.items()):
                if "default" in subschema:
                    instance.setdefault(property, subschema["default"])

        return validators.extend(
            validator_class, {"properties": set_defaults},
        )

    def _spawn_redis_connection_thread(self):
        """Spawns a redis connection thread"""
        self.logger.debug("Spawn redis connection thread")
        self.redis_connected = False
        self._redis_thread = Thread(target=self._setup_redis)
        self._redis_thread.setDaemon(True)
        self._redis_thread.start()

    def _spawn_kafka_connection_thread(self):
        """Spawns a kafka connection thread"""
        self.logger.debug("Spawn kafka connection thread")
        self.kafka_connected = False
        self._kafka_thread = Thread(target=self._setup_kafka)
        self._kafka_thread.setDaemon(True)
        self._kafka_thread.start()

    def _spawn_kafka_consumer_thread(self):
        """Spawns a kafka continuous consumer thread"""
        self.logger.debug("Spawn kafka consumer thread""")
        self._consumer_thread = Thread(target=self._consumer_loop)
        self._consumer_thread.setDaemon(True)
        self._consumer_thread.start()

    def _consumer_loop(self):
        """The main consumer loop"""
        self.logger.debug("running main consumer thread")
        while not self.closed:
            if self.kafka_connected:
                self._process_messages()
            time.sleep(self.settings['KAFKA_CONSUMER_SLEEP_TIME'])

    def _process_messages(self):
        """Processes messages received from kafka"""
        try:
            for message in self.consumer:
                try:
                    if message is None:
                        self.logger.debug("no message")
                        break
                    loaded_dict = json.loads(message.value)
                    self.logger.debug("got valid kafka message")

                    with self.uuids_lock:
                        if 'uuid' in loaded_dict:
                            if loaded_dict['uuid'] in self.uuids and \
                                    self.uuids[loaded_dict['uuid']] != 'poll':
                                self.logger.debug("Found Kafka message from request")
                                self.uuids[loaded_dict['uuid']] = loaded_dict
                            else:
                                self.logger.debug("Got poll result")
                                self._send_result_to_redis(loaded_dict)
                        else:
                            self.logger.debug("Got message not intended for this process")
                except ValueError:
                    extras = {}
                    if message is not None:
                            extras["data"] = message.value
                    self.logger.warning('Unparseable JSON Received from kafka',
                                                extra=extras)

            self._check_kafka_disconnect()

        except OffsetOutOfRangeError:
            # consumer has no idea where they are
            self.consumer.seek_to_end()
            self.logger.error("Kafka offset out of range error")

    def _send_result_to_redis(self, result):
        """Sends the result of a poll to redis to be used potentially by
        another process

        @param result: the result retrieved from kafka"""
        if self.redis_connected:
            self.logger.debug("Sending result to redis")
            try:
                key = "rest:poll:{u}".format(u=result['uuid'])
                self.redis_conn.set(key, json.dumps(result))
            except ConnectionError:
                self.logger.error("Lost connection to Redis")
                self._spawn_redis_connection_thread()
        else:
            self.logger.warning("Unable to send result to redis, not connected")

    def _check_kafka_disconnect(self):
        """Checks the kafka connection is still valid"""
        for node_id in self.consumer._client._conns:
            conn = self.consumer._client._conns[node_id]
            if conn.state == ConnectionStates.DISCONNECTED or \
                    conn.state == ConnectionStates.DISCONNECTING:
                self._spawn_kafka_connection_thread()
                break

    def _heartbeat_loop(self):
        """A main run loop thread to do work"""
        self.logger.debug("running main heartbeat thread")
        while not self.closed:
            time.sleep(self.settings['SLEEP_TIME'])
            self._report_self()

    def _report_self(self):
        """
        Reports the crawler uuid to redis
        """
        if self.redis_connected:
            self.logger.debug("Reporting self to redis")
            try:
                key = "stats:rest:self:{m}:{u}".format(
                    m=socket.gethostname(),
                    u=self.my_uuid)
                self.redis_conn.set(key, self.get_time())
                self.redis_conn.expire(key, self.settings['HEARTBEAT_TIMEOUT'])
            except ConnectionError:
                self.logger.error("Lost connection to Redis")
                self._spawn_redis_connection_thread()
        else:
            self.logger.warn("Cannot report self to redis, not connected")


    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _setup_redis(self):
        """Returns a Redis Client"""
        if not self.closed:
            try:
                self.logger.debug("Creating redis connection to host " +
                                  str(self.settings['REDIS_HOST']))
                self.redis_conn = redis.StrictRedis(host=self.settings['REDIS_HOST'],
                                              port=self.settings['REDIS_PORT'],
                                              db=self.settings['REDIS_DB'])
                self.redis_conn.info()
                self.redis_connected = True
                self.logger.info("Successfully connected to redis")
            except KeyError as e:
                self.logger.error('Missing setting named ' + str(e),
                                   {'ex': traceback.format_exc()})
            except:
                self.logger.error("Couldn't initialize redis client.",
                                   {'ex': traceback.format_exc()})
                raise

    def _setup_kafka(self):
        """
        Sets up kafka connections
        """
        # close older connections
        if self.consumer is not None:
            self.logger.debug("Closing existing kafka consumer")
            self.consumer.close()
            self.consumer = None
        if self.producer is not None:
            self.logger.debug("Closing existing kafka producer")
            self.producer.flush()
            self.producer.close(timeout=10)
            self.producer = None

        # create new connections
        self._consumer_thread = None
        self.logger.debug("Creating kafka connections")
        self.consumer = self._create_consumer()
        if not self.closed:
            self.logger.debug("Kafka Conumer created")
        self.producer = self._create_producer()
        if not self.closed:
            self.logger.debug("Kafka Producer created")

        if not self.closed:
            self.kafka_connected = True
            self.logger.info("Connected successfully to Kafka")
            self._spawn_kafka_consumer_thread()

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_consumer(self):
        """Tries to establing the Kafka consumer connection"""
        if not self.closed:
            try:
                self.logger.debug("Creating new kafka consumer using brokers: " +
                                   str(self.settings['KAFKA_HOSTS']) + ' and topic ' +
                                   self.settings['KAFKA_TOPIC_PREFIX'] +
                                   ".outbound_firehose")

                return KafkaConsumer(
                    self.settings['KAFKA_TOPIC_PREFIX'] + ".outbound_firehose",
                    group_id=None,
                    bootstrap_servers=self.settings['KAFKA_HOSTS'],
                    consumer_timeout_ms=self.settings['KAFKA_CONSUMER_TIMEOUT'],
                    auto_offset_reset=self.settings['KAFKA_CONSUMER_AUTO_OFFSET_RESET'],
                    auto_commit_interval_ms=self.settings['KAFKA_CONSUMER_COMMIT_INTERVAL_MS'],
                    enable_auto_commit=self.settings['KAFKA_CONSUMER_AUTO_COMMIT_ENABLE'],
                    max_partition_fetch_bytes=self.settings['KAFKA_CONSUMER_FETCH_MESSAGE_MAX_BYTES'])
            except KeyError as e:
                self.logger.error('Missing setting named ' + str(e),
                                   {'ex': traceback.format_exc()})
            except:
                self.logger.error("Couldn't initialize kafka consumer for topic",
                                   {'ex': traceback.format_exc()})
                raise

    @retry(wait_exponential_multiplier=500, wait_exponential_max=10000)
    def _create_producer(self):
        """Tries to establish a Kafka consumer connection"""
        if not self.closed:
            try:
                self.logger.debug("Creating new kafka producer using brokers: " +
                                   str(self.settings['KAFKA_HOSTS']))

                return KafkaProducer(bootstrap_servers=self.settings['KAFKA_HOSTS'],
                                     value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                                     retries=3,
                                     linger_ms=self.settings['KAFKA_PRODUCER_BATCH_LINGER_MS'],
                                     buffer_memory=self.settings['KAFKA_PRODUCER_BUFFER_BYTES'])
            except KeyError as e:
                self.logger.error('Missing setting named ' + str(e),
                                   {'ex': traceback.format_exc()})
            except:
                self.logger.error("Couldn't initialize kafka producer.",
                                   {'ex': traceback.format_exc()})
                raise

    def run(self):
        """Main flask run loop"""
        self.logger.info("Running main flask method on port " +
                         str(self.settings['FLASK_PORT']))
        self.app.run(host='0.0.0.0', port=self.settings['FLASK_PORT'])

    def _create_ret_object(self, status=SUCCESS, data=None, error=False,
                           error_message=None, error_cause=None):
        """
        Create generic reponse objects.

        :param str status: The SUCCESS or FAILURE of the request
        :param obj data: The data to return
        :param bool error: Set to True to add Error response
        :param str error_message: The generic error message
        :param str error_cause: The cause of the error
        :returns: A dictionary of values
        """
        ret = {}
        if status == self.FAILURE:
            ret['status'] = self.FAILURE
        else:
            ret['status'] = self.SUCCESS
        ret['data'] = data

        if error:
            ret['error'] = {}
            if error_message is not None:
                ret['error']['message'] = error_message
            if error_cause is not None:
                ret['error']['cause'] = error_cause
        else:
            ret['error'] = None
        return ret

    def _close_thread(self, thread, thread_name):
        """Closes daemon threads

        @param thread: the thread to close
        @param thread_name: a human readable name of the thread
        """
        if thread is not None and thread.isAlive():
            self.logger.debug("Waiting for {} thread to close".format(thread_name))
            thread.join(timeout=self.settings['DAEMON_THREAD_JOIN_TIMEOUT'])
            if thread.isAlive():
                self.logger.warn("{} daemon thread unable to be shutdown"
                                 " within timeout".format(thread_name))

    def close(self):
        """
        Cleans up anything from the process
        """
        self.logger.info("Closing Rest Service")
        self.closed = True

        # close threads
        self._close_thread(self._redis_thread, "Redis setup")
        self._close_thread(self._heartbeat_thread, "Heartbeat")
        self._close_thread(self._kafka_thread, "Kafka setup")
        self._close_thread(self._consumer_thread, "Consumer")

        # close kafka
        if self.consumer is not None:
            self.logger.debug("Closing kafka consumer")
            self.consumer.close()
        if self.producer is not None:
            self.logger.debug("Closing kafka producer")
            self.producer.close(timeout=10)

    def _calculate_health(self):
        """Returns a string representation of the node health

        @returns: GREEN if fully connected, YELLOW if partially connected,
                  RED if not connected
        """
        if self.redis_connected and self.kafka_connected:
            return "GREEN"
        elif self.redis_connected or self.kafka_connected:
            return "YELLOW"
        else:
            return "RED"

    def _kafka_success(self, response):
        '''
        Callback for successful send
        '''
        self.logger.debug("Sent message to Kafka")

    def _kafka_failure(self, response):
        '''
        Callback for failed send
        '''
        self.logger.error("Failed to send message to Kafka")
        self._spawn_kafka_connection_thread()

    def _feed_to_kafka(self, json_item):
        """Sends a request to Kafka

        :param json_item: The json item to send
        :returns: A boolean indicating whther the data was sent successfully or not
        """
        @MethodTimer.timeout(self.settings['KAFKA_FEED_TIMEOUT'], False)
        def _feed(json_item):
            try:
                self.logger.debug("Sending json to kafka at " +
                                  str(self.settings['KAFKA_PRODUCER_TOPIC']))
                future = self.producer.send(self.settings['KAFKA_PRODUCER_TOPIC'],
                                   json_item)
                future.add_callback(self._kafka_success)
                future.add_errback(self._kafka_failure)

                self.producer.flush()

                return True

            except Exception as e:
                self.logger.error("Lost connection to Kafka")
                self._spawn_kafka_connection_thread()
                return False

        return _feed(json_item)

    # Routes --------------------

    def _decorate_routes(self):
        """
        Decorates the routes to use within the flask app
        """
        self.logger.debug("Decorating routes")
        # self.app.add_url_rule('/', 'catch', self.catch, methods=['GET'],
        #                        defaults={'path': ''})
        self.app.add_url_rule('/<path:path>', 'catch', self.catch,
                              methods=['GET', 'POST'], defaults={'path': ''})
        self.app.add_url_rule('/', 'index', self.index,
                              methods=['POST', 'GET'])
        self.app.add_url_rule('/feed', 'feed', self.feed,
                              methods=['POST'])
        self.app.add_url_rule('/poll', 'poll', self.poll,
                              methods=['POST'])

    @log_call('Non-existant route called')
    @error_catch
    def catch(self, path):
        return self._create_ret_object(self.FAILURE, None, True,
                                       self.DOES_NOT_EXIST), 404

    @log_call('\'index\' endpoint called')
    @error_catch
    def index(self):
        data = {
            "kafka_connected": self.kafka_connected,
            "redis_connected": self.redis_connected,
            "uptime_sec": int(self.get_time() - self.start_time),
            "my_id": self.my_uuid,
            "node_health": self._calculate_health()
        }

        return data

    @validate_json
    @log_call('\'feed\' endpoint called')
    @error_catch
    def feed(self):
        # proof of concept to write things to kafka
        if self.kafka_connected:
            json_item = request.get_json()
            self.wait_for_response = False
            result = self._feed_to_kafka(json_item)

            if 'uuid' in json_item:
                    self.wait_for_response = True
                    with self.uuids_lock:
                        self.uuids[json_item['uuid']] = None

            if result:
                true_response = None
                if self.wait_for_response:
                    self.logger.debug("expecting kafka response for request")
                    the_time = self.get_time()
                    found_item = False
                    while not found_item and int(self.get_time() - the_time) <= self.settings['WAIT_FOR_RESPONSE_TIME']:
                        if self.uuids[json_item['uuid']] is not None:
                            found_item = True
                            true_response = self.uuids[json_item['uuid']]
                            with self.uuids_lock:
                                del self.uuids[json_item['uuid']]
                    else:
                        with self.uuids_lock:
                            # key still exists, means we didnt find get our
                            # response in time
                            if json_item['uuid'] in self.uuids:
                                self.uuids[json_item['uuid']] = 'poll'
                                self.logger.debug("Did not find response, "
                                                  "adding to poll")
                    if found_item:
                        self.logger.debug("Got successful reponse back from kafka")
                    else:
                        self.logger.warn("Did not get response within timeout "
                                         "from kafka. If the request is still "
                                         "running, use the `/poll` API")
                        true_response = {
                            "poll_id": json_item['uuid']
                        }
                else:
                    self.logger.debug("Not expecting response from kafka")

                return self._create_ret_object(self.SUCCESS, true_response)

        self.logger.warn("Unable to write request to Kafka, not connected")
        return self._create_ret_object(self.FAILURE, None, True,
                                       "Unable to connect to Kafka"), 500

    @validate_json
    @validate_schema('poll')
    @log_call('\'poll\' endpoint called')
    @error_catch
    def poll(self):
        """Retrieves older requests that may not make it back quick
        enough"""
        if self.redis_connected:
            json_item = request.get_json()
            result = None
            try:
                key = "rest:poll:{u}".format(u=json_item['poll_id'])
                result = self.redis_conn.get(key)

                if result is not None:
                    result = json.loads(result)
                    self.logger.debug("Found previous poll")
                    self.redis_conn.delete(key)
                    return self._create_ret_object(self.SUCCESS, result)
                else:
                    self.logger.debug("poll key does not exist")
                    return self._create_ret_object(self.FAILURE, None, True,
                                       "Could not find matching poll_id"), 404
            except ConnectionError:
                self.logger.error("Lost connection to Redis")
                self._spawn_redis_connection_thread()
            except ValueError:
                extras = {
                    "value": result
                }
                self.logger.warning('Unparseable JSON Received from redis',
                                                extra=extras)
                self.redis_conn.delete(key)
                return self._create_ret_object(self.FAILURE, None, True,
                                               "Unparseable JSON Received "
                                               "from redis"), 500
        self.logger.warn("Unable to poll redis, not connected")
        return self._create_ret_object(self.FAILURE, None, True,
                                       "Unable to connect to Redis"), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Rest Service: Used for interacting and feeding Kafka'
        ' requests to the cluster and returning data back\n')

    parser.add_argument('-s', '--settings', action='store',
                        required=False,
                        help="The settings file to read from",
                        default="localsettings.py")
    parser.add_argument('-ll', '--log-level', action='store',
                        required=False, help="The log level",
                        default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR',
                                 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=True, default=None,
                        help='Log the output to the file specified in '
                        'settings.py. Otherwise logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=None,
                        help="Log the data in JSON format")

    args = vars(parser.parse_args())

    rest_service = RestService(args['settings'])
    rest_service.setup(level=args['log_level'], log_file=args['log_file'],
                       json=args['log_json'])

    try:
        rest_service.run()
    finally:
        rest_service.close()
