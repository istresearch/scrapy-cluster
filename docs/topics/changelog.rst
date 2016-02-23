.. _changelog:

Change Log
=============

This page serves to document any changes made between releases.

Scrapy Cluster 1.1
------------------

Date: 02/23/2016

- Added domain based queue mechanism for better management and control across all components of the cluster

- Added easy offline bash script for running all offline tests

- Added online bash test script for testing if your cluster is integrated with all other external components

- New Vagrant virtual machine for easier development and testing.

- Modified demo incoming kafka topic from ``demo.incoming_urls`` to just ``demo.incoming`` as now all crawl/info/stop requests are serviced through a single topic

- Added new ``scutils`` package for accessing modules across different components.

- Added ``scutils`` documentation

- Added significantly more documentation and improved layout

- Created new ``elk`` folder for sample Elasticsearch, Logstash, Kibana integration

Kafka Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Condensed the Crawler and Actions monitor into a single script

- Renamed ``kafka-monitor.py`` to ``kafka_monitor.py`` for better PEP 8 standards

- Added plugin functionality for easier extension creation

- Improved kafka topic dump utility

- Added both offline and online unit tests

- Improved logging

- Added defaults to ``scraper_schema.json``

- Added Stats Collection and interface for retrieving stats

Redis Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Added plugin functionality for easier extension creation

- Added both offline and online unit tests

- Improved logging

- Added Stats Collection

Crawler Changes
^^^^^^^^^^^^^^^^^^^^^

- Upgraded Crawler to be compatible with Scrapy 1.0

- Improved code structure for overriding url.encode in default LxmlParserLinkExtractor

- Improved logging

- Added ability for the crawling rate to be controlled in a manner that will rate limit the whole crawling cluster based upon the domain, spider type, and public ip address the crawlers have.

- Added ability for the crawl rate to be explicitly defined per domain in Zookeeper, with the ability to dynamically update them on the fly

- Created manual crawler Zookeeper configuration pusher

- Updated offline and added online unit tests

- Added response code stats collection

- Added example Wandering Spider

Scrapy Cluster 1.0
---------------------

Date: 5/21/2015

- Initial Release