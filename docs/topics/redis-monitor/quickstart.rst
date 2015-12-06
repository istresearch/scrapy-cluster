Quick Start
===========

First, make sure your `localsettings.py` is updated with your Kafka and Redis hosts.

Then run the redis monitor to monitor your Scrapy Cluster:

::

    python redis_monitor.py

This is a completely optional component to the Scrapy Cluster. If you do not care about getting information about crawls, stopping, or expiring crawls in the cluster then you can leave this component alone.

-  For how to set up the Scrapy crawlers, refer to the :doc:`./crawler` documentation

-  To learn more about how to submit crawls, please see the :doc:`./kafkamonitor` documentation