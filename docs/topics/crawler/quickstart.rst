.. _crawler:

Quick Start
===========

This is a complete Scrapy crawling project located in ``crawler/``.

First, create a ``crawling/localsettings.py`` file to track your custom settings. You can override any setting in the normal ``settings.py`` file, and a typical file may look like the following:

::

    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'
    ZOOKEEPER_HOSTS = 'scdev:2181'
    SC_LOG_LEVEL = 'DEBUG'

Scrapy
------

Then run the Scrapy spider like normal:

::

    scrapy runspider crawling/spiders/link_spider.py

To run multiple crawlers, simply run in the background across X number of machines. Because the crawlers coordinate their efforts through Redis, any one crawler can be brought up/down on any machine in order to add crawling capacity.

Typical Usage
-------------

Open four terminals.

**Terminal 1:**

Monitor your kafka output

::

    $ python kafkadump.py dump -t demo.crawled_firehose -p

**Terminal 2:**

Run the Kafka Monitor

::

    $ python kafka_monitor.py run

.. note:: This assumes you have your :doc:`Kafka Monitor <../kafka-monitor/quickstart>` already working.

**Terminal 3:**

Run your Scrapy spider

::

    scrapy runspider crawling/spiders/link_spider.py

**Terminal 4:**

Feed an item

::

    $ python kafka_monitor.py feed '{"url": "http://dmoztools.net/", "appid":"testapp", "crawlid":"09876abc"}'
    2016-01-21 23:22:23,830 [kafka-monitor] INFO: Feeding JSON into demo.incoming
    {
        "url": "http://dmoztools.net/",
        "crawlid": "09876abc",
        "appid": "testapp"
    }
    2016-01-21 23:22:23,832 [kafka-monitor] INFO: Successfully fed item to Kafka

You should see a log message come through Terminal 2 stating the message was received.

::

    2016-01-21 23:22:23,859 [kafka-monitor] INFO: Added crawl to Redis

Next, you should see your Spider in Terminal 3 state the crawl was successful.

::

    2016-01-21 23:22:35,976 [scrapy-cluster] INFO: Scraped page
    2016-01-21 23:22:35,979 [scrapy-cluster] INFO: Sent page to Kafka

At this point, your Crawler is up and running!

If you are still listening to the Kafka Topic in Terminal 1, the following should come through.

::

    {
        "body": "<body ommitted>",
        "crawlid": "09876abc",
        "response_headers": {
            <headers omitted>
        },
        "response_url": "http://dmoztools.net/",
        "url": "http://dmoztools.net/",
        "status_code": 200,
        "status_msg": "OK",
        "appid": "testapp",
        "links": [],
        "request_headers": {
            "Accept-Language": "en",
            "Accept-Encoding": "gzip,deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Scrapy/1.0.4 (+http://scrapy.org)"
        },
        "attrs": null,
        "timestamp": "2016-01-22T04:22:35.976672"
    }

This completes the crawl submission, execution, and receival of the requested data.
