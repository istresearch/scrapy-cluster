Quick Start
===========

First, create a ``localsettings.py`` file to track your custom settings. You can override any setting in the normal ``settings.py`` file, and a typical file may look like the following:

::

    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'
    LOG_LEVEL = 'DEBUG'

kafka_monitor.py
----------------

The Kafka Monitor allows two modes of operation.

Run
^^^

Continuous run mode. Will accept incoming Kafka messages from a topic, validate the message as JSON and then against all possible JSON API's, and then allow the valid API Plugin to process the object.

.. attention:: Run mode is the main process you should have running!

::

    $ python kafka_monitor.py run


Feed
^^^^

JSON Object feeder into your desired Kafka Topic. This takes a valid JSON object from the command line and inserts it into the desired Kafka Topic, to then be consumed by the `Run`_ command above.

::

    $ python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"ABC123"}'

The command line feed is very slow and should not be used in production. Instead, you should write your own continuously running application to feed Kafka the desired API requests that you require.

kafkadump.py
------------

A basic kafka topic utility used to check message flows in your Kafka cluster.

Dump
^^^^

Dumps the messages from a particular topic.

::

    $ python kafkadump.py dump -t demo.crawled_firehose

This utility by default consumes from the end of the desired Kafka Topic, and can be useful if left running in helping you debug the messages currently flowing through.

List
^^^^

Lists all the topics within your cluster.

::

    $ python kafkadump.py list

Typical Usage
-------------

Open three terminals.

**Terminal 1:**

Monitor your kafka output

::

    $ python kafkadump.py dump -t demo.crawled_firehose -p

**Terminal 2:**

Run the Kafka Monitor

::

    $ python kafka_monitor.py run

**Terminal 3:**

Feed an item

::

    $ python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"ABC123"}'
    2016-01-05 15:14:44,829 [kafka-monitor] INFO: Feeding JSON into demo.incoming
    {
        "url": "http://dmoztools.net",
        "crawlid": "ABC123",
        "appid": "testapp"
    }
    2016-01-05 15:14:44,830 [kafka-monitor] INFO: Successfully fed item to Kafka

You should see a log message come through Terminal 2 stating the message was received.

::

    2016-01-05 15:14:44,836 [kafka-monitor] INFO: Added crawl to Redis

At this point, your Kafka Monitor is working.

If you have a :ref:`Crawler <crawler>` running, you should see the html come through Terminal 1 in a couple of seconds like so:

::

    {
        "body": "<body omitted>",
        "crawlid": "ABC123",
        "response_headers": {
            <headers omitted>
        },
        "response_url": "http://dmoztools.net",
        "url": "http://dmoztools.net",
        "status_code": 200,
        "status_msg": "OK",
        "appid": "testapp",
        "links": [],
        "request_headers": {
            "Accept-Language": "en",
            "Accept-Encoding": "gzip,deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Scrapy/1.0.3 (+http://scrapy.org)"
        },
        "attrs": null,
        "timestamp": "2016-01-05T20:14:54.653703"
    }

If you can see the html result, it means that both your Kafka Monitor and crawlers are up and running!
