#!/usr/bin/env python
from kafka import KafkaConsumer, KafkaProducer
from jsonschema import ValidationError
from jsonschema import Draft4Validator, validators
import threading
import time
import json


def extend_with_default(validator_class):

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


class Producer(threading.Thread):
    daemon = True

    def run(self):
        producer = KafkaProducer(bootstrap_servers='localhost:9092')

        while True:
            producer.send('my-topic', b"{'appid': 'testapp', 'uuid': 'hij3', 'stats': 'all'}")
            time.sleep(1)


class Consumer(threading.Thread):
    daemon = True

    def run(self):
        consumer = KafkaConsumer(bootstrap_servers='localhost:9092',
                                 auto_offset_reset='earliest')
        consumer.subscribe(['my-topic'])

        validator = extend_with_default(Draft4Validator)

        for message in consumer:
            json_message = json.loads(message.value)
            valid = False
            try:
                validator("stats_schema").validate(json_message)
                valid = True
            except ValidationError:
                pass

            if valid:
                with open("stats/data.json", 'w') as stats_cache:
                    json.dump(json_message['stats'], stats_cache)


def main():
    threads = [
        Producer(),
        Consumer()
    ]

    for t in threads:
        t.start()

    time.sleep(10)

if __name__ == "__main__":
    main()