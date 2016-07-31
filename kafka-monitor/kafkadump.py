from kafka import KafkaClient, SimpleConsumer
from kafka.common import KafkaUnavailableError

import json
import sys
import traceback
import time
import argparse
import base64

from scutils.settings_wrapper import SettingsWrapper
from scutils.log_factory import LogFactory
from scutils.method_timer import MethodTimer
from scutils.argparse_helper import ArgparseHelper

def main():
    # initial main parser setup
    parser = argparse.ArgumentParser(
        description='Kafka Dump: Scrapy Cluster Kafka topic dump utility for '
                    'debugging.', add_help=False)
    parser.add_argument('-h', '--help', action=ArgparseHelper,
                        help='show this help message and exit')

    subparsers = parser.add_subparsers(help='commands', dest='command')

    # args to use for all commands
    base_parser = argparse.ArgumentParser(add_help=False)
    base_parser.add_argument('-kh', '--kafka-host', action='store', required=False,
                        help="The override Kafka host")
    base_parser.add_argument('-s', '--settings', action='store', required=False,
                        help="The settings file to read from",
                        default="localsettings.py")
    base_parser.add_argument('-ll', '--log-level', action='store', required=False,
                        help="The log level", default=None,
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])

    # list command
    list_parser = subparsers.add_parser('list', help='List all Kafka topics',
                                        parents=[base_parser])

    # dump command
    dump_parser = subparsers.add_parser('dump', help='Dump a Kafka topic',
                                        parents=[base_parser])
    dump_parser.add_argument('-t', '--topic', action='store', required=True,
                             help="The Kafka topic to read from")
    dump_parser.add_argument('-c', '--consumer', action='store',
                             required=False, default='default',
                             help="The Kafka consumer id to use")
    dump_parser.add_argument('-b', '--from-beginning', action='store_const',
                             required=False, const=True,
                             help="Read the topic from the beginning")
    dump_parser.add_argument('-nb', '--no-body', action='store_const',
                             required=False, const=True, default=False,
                             help="Do not include the raw html 'body' key in"
                             " the json dump of the topic")
    dump_parser.add_argument('-p', '--pretty', action='store_const',
                             required=False, const=True, default=False,
                             help="Pretty print the json objects consumed")
    dump_parser.add_argument('-d', '--decode-base64', action='store_const',
                             required=False, const=True, default=False,
                             help="Decode the base64 encoded raw html body")

    args = vars(parser.parse_args())

    wrapper = SettingsWrapper()
    settings = wrapper.load(args['settings'])

    kafka_host = args['kafka_host'] if args['kafka_host'] else settings['KAFKA_HOSTS']
    log_level = args['log_level'] if args['log_level'] else settings['LOG_LEVEL']
    logger = LogFactory.get_instance(level=log_level, name='kafkadump')

    logger.debug("Connecting to {0}...".format(kafka_host))
    try:
        kafka = KafkaClient(kafka_host)
        logger.info("Connected to {0}".format(kafka_host))
    except KafkaUnavailableError as ex:
        message = "An exception '{0}' occured. Arguments:\n{1!r}" \
            .format(type(ex).__name__, ex.args)
        logger.error(message)
        sys.exit(1)

    if args['command'] == 'list':
        logger.debug('Running list command')
        print "Topics:"
        for topic in kafka.topic_partitions.keys():
            print "-", topic
        return 0
    elif args['command'] == 'dump':
        logger.debug('Running dump command')
        topic = args["topic"]
        consumer_id = args["consumer"]

        @MethodTimer.timeout(5, None)
        def _hidden():
            try:
                logger.debug("Ensuring topic {t} exists".format(t=topic))
                kafka.ensure_topic_exists(topic)

                logger.debug("Getting Kafka consumer")
                consumer = SimpleConsumer(kafka, consumer_id, topic,
                                      buffer_size=1024*100,
                                      fetch_size_bytes=1024*100,
                                      max_buffer_size=None
                                      )
                return consumer
            except KafkaUnavailableError as ex:
                    message = "An exception '{0}' occured. Arguments:\n{1!r}" \
                        .format(type(ex).__name__, ex.args)
                    logger.error(message)
                    sys.exit(1)

        consumer = _hidden()

        if consumer is None:
            logger.error("Could not fully connect to Kafka within the timeout")
            sys.exit(1)

        if args["from_beginning"]:
            logger.debug("Seeking to beginning")
            consumer.seek(0, 0)
        else:
            logger.debug("Reading from the end")
            consumer.seek(0, 2)

        num_records = 0
        total_bytes = 0
        item = None

        while True:
            try:
                for message in consumer.get_messages():
                    if message is None:
                        logger.debug("no message")
                        break
                    logger.debug("Received message")
                    val = message.message.value
                    try:
                        item = json.loads(val)
                        if args['decode_base64'] and 'body' in item:
                            item['body'] = base64.b64decode(item['body'])

                        if args['no_body'] and 'body' in item:
                            del item['body']
                    except ValueError:
                        logger.info("Message is not a JSON object")
                        item = val
                    body_bytes = len(item)

                    if args['pretty']:
                        print json.dumps(item, indent=4)
                    else:
                        print item
                    num_records = num_records + 1
                    total_bytes = total_bytes + body_bytes
            except KeyboardInterrupt:
                logger.debug("Keyboard interrupt received")
                break
            except:
                logger.error(traceback.print_exc())
                break

        total_mbs = float(total_bytes) / (1024*1024)
        if item is not None:
            print "Last item:"
            print json.dumps(item, indent=4)
        if num_records > 0:
            logger.info("Num Records: {n}, Total MBs: {m}, kb per message: {kb}"
                    .format(n=num_records, m=total_mbs,
                            kb=(float(total_bytes) / num_records / 1024)))
        else:
            logger.info("No records consumed")
            num_records = 0

        logger.info("Closing Kafka connection")
        kafka.close()
        return 0

if __name__ == "__main__":
    sys.exit(main())
