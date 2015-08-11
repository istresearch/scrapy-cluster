from kafka import KafkaClient, SimpleConsumer
import json
import sys
import traceback
import logging
import time

from docopt import docopt

def main():
    """kafkadump: Kafka topic dump utility for debugging.

    Usage:
        kafkadump list --host=<host>
        kafkadump dump <topic> --host=<host> [--consumer=<consumer>] [--from-beginning]

    Examples:

        List all the topics on your local Kafka instance:

            python kafkadump.py list --host=<kafkahost>:9092

        Dump the new contents of a single topic:

            python kafkadump.py dump test.crawled_firehose --host=<kafkahost>:9092

        Use CTRL+C (SIGINT, KeyboardInterrupt) to stop it from polling Kafka.
        It will end by printing the total records serviced and the raw output
        of the most recent record.

    Options:
        -h --host <host>            Kafka host name where Kafka cluster will be resolved
        -c --consumer <consumer>    Consumer group ID to use for reading messages
        -b --from-beginning         Dump everything in the topic from the beginning
    """
    args = docopt(main.__doc__)
    host = args["--host"]

    logging.basicConfig()

    print "=> Connecting to {0}...".format(host)
    kafka = KafkaClient(host)
    print "=> Connected."

    if args["list"]:
        for topic in kafka.topic_partitions.keys():
            print topic
        return 0
    elif args["dump"]:
        topic = args["<topic>"]
        consumer_id = args["--consumer"] or "default"
        consumer = SimpleConsumer(kafka, consumer_id, topic,
                            buffer_size=1024*100,      # 100kb
                            fetch_size_bytes=1024*100, # 100kb
                            max_buffer_size=None       # eliminate big message errors
                            )
        kafka.ensure_topic_exists(topic)
        if args["--from-beginning"]:
            consumer.seek(0, 0)
        else:
            consumer.seek(0, 2)
        num_records = 0
        total_bytes = 0
        item = None
        while True:
            try:
                message = consumer.get_message()
                if message is None:
                    time.sleep(1)
                    continue
                val = message.message.value
                item = json.loads(val)
                body_bytes = len(item)
                print item
                num_records = num_records + 1
                total_bytes = total_bytes + body_bytes
            except:
                traceback.print_exc()
                break
        total_mbs = float(total_bytes) / (1024*1024)
        print
        if item is not None:
            print json.dumps(item, indent=4)
        if num_records == 0:
            num_records = 1
        print num_records, "records", total_mbs, "megabytes", (float(total_bytes) / num_records / 1024), "kb per msg"
        kafka.close()
        return 0

if __name__ == "__main__":
    sys.exit(main())
