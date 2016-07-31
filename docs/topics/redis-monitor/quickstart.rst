Quick Start
===========

First, create a ``localsettings.py`` to track your overridden custom settings. You can override any setting you find within the Redis Monitor's ``settings.py``, and a typical file may look like the following:

::

    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'

redis_monitor.py
----------------

The main mode of operation for the Redis Monitor is to run the python script to begin monitoring the Redis instance your cluster is interacting with.

::

    $ python redis_monitor.py

Typical Usage
-------------

Typical usage of the Redis Monitor is done in conjunction with the Kafka Monitor, since the Kafka Monitor is the gateway into the cluster.

.. warning:: This guide assumes you have a running Kafka Monitor already. Please see the Kafka Monitor :doc:`../kafka-monitor/quickstart` for more information.

Open three terminals.

**Terminal 1:**

Monitor your kafka output

::

    $ python kafkadump.py dump -t demo.outbound_firehose -p

**Terminal 2:**

Run the Redis Monitor

::

    $ python redis_monitor.py

**Terminal 3:**

Feed an item

::

    $ python kafka_monitor.py feed '{"stats": "kafka-monitor", "appid":"testapp", "uuid":"myuuidhere"}'
    2016-01-18 20:58:18,130 [kafka-monitor] INFO: Feeding JSON into demo.incoming
    {
        "stats": "kafka-monitor",
        "uuid": "myuuidhere",
        "appid": "testapp"
    }
    2016-01-18 20:58:18,131 [kafka-monitor] INFO: Successfully fed item to Kafka

You should see a log message come through Terminal 2 stating the message was received.

::

    2016-01-18 20:58:18,228 [redis-monitor] INFO: Received kafka-monitor stats request
    2016-01-18 20:58:18,233 [redis-monitor] INFO: Sent stats to kafka

After a short time, you should see the result come through your Kafka topic in Terminal 1.

::


    {
        "server_time": 1453168698,
        "uuid": "myuuidhere",
        "plugins": {
            "StatsHandler": {
                "900": 2,
                "3600": 2,
                "604800": 2,
                "43200": 2,
                "lifetime": 19,
                "86400": 2,
                "21600": 2
            },
            "ScraperHandler": {
                "604800": 6,
                "lifetime": 24
            },
            "ActionHandler": {
                "604800": 7,
                "lifetime": 24
            }
        },
        "appid": "testapp",
        "fail": {
            "lifetime": 7
        },
        "stats": "kafka-monitor",
        "total": {
            "900": 2,
            "3600": 2,
            "604800": 15,
            "43200": 2,
            "lifetime": 73,
            "86400": 2,
            "21600": 2
        }
    }

At this point, your Redis Monitor is functioning.