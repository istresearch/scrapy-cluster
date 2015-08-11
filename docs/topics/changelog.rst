Change Log
=============

This page serves to document any changes made between releases.

Scrapy Cluster 1.1
-----------

Date: ??/??/????

- Added domain based queue mechanism for better management and control across all components of the cluster

- Added easy offline bash script for running all offline tests

- Modified demo incoming kafka topic from ``demo.incoming_urls`` to just ``demo.incoming`` as now all crawl/info/stop requests are serviced through a single topic

Kafka Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Condensed the Crawler and Actions monitor into a single script

- Renamed ``kafka-monitor.py`` to ``kafka_monitor.py`` for better PEP 8 standards

- Added plugin functionality for easier extension creation

- Improved kafka topic dump utility

- Added both offline and online unit tests

Redis Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Added plugin functionality for easier extension creation

Crawler Changes
^^^^^^^^^^^^^^^^^^^^^

- tdb

Scrapy Cluster 1.0
---------------------

Date: 5/21/2015

- Initial Release