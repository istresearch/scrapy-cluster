Quick Start
===========

This is a complete Scrapy crawling project.

First, make sure your ``settings.py`` is updated with your Kafka and
Redis hosts.

To run the crawler offline test to make sure nothing is broken:

::

    python tests/tests_offline.py -v

Then run the crawler:

::

    scrapy runspider crawling/spiders/link_spider.py

To run multiple crawlers, simply run in the background across X number of machines. Because the crawlers coordinate their efforts through Redis, any one crawler can be brought up/down in order to add crawling capability.

-  To execute a crawl, please refer the :doc:`./kafkamonitor` documentation

-  To learn more about how to see crawl info, please see the :doc:`./redismonitor` documentation