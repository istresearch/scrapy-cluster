Quick Start
===========

First, make sure your `settings_crawler.py` and `settings_actions.py` are updated with your Kafka and Redis hosts.

Then run the kafka monitor for crawl requests:

::

    python kafka-monitor.py run -s settings_crawling.py

Then run the kafka monitor for action requests:

::

    python kafka-monitor.py run -s settings_actions.py

Finally, submit a new crawl request:

::

    python kafka-monitor.py feed -s settings_crawling.py '{"url": "http://istresearch.com", "appid":"testapp", "crawlid":"ABC123"}'

If you have everything else in the pipeline set up correctly you should now see the raw html of the IST Research home page come through. You need both of these to run the full cluster, but at a minimum you should have the ``-s settings_crawling`` monitor running.

-  For how to set up the Scrapy crawlers, refer to the :doc:`./crawler` documentation

-  To learn more about how to see crawl info, please see the :doc:`./redismonitor` documentation