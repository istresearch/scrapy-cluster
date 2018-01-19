.. _changelog:

Change Log
=============

This page serves to document any changes made between releases.

Scrapy Cluster 1.2.1
--------------------

Date: 01/19/2018

- Fixes unit test syntax for link spider

- Fixes docker version upgrade on Travis for continuous integration tests

Scrapy Cluster 1.2
------------------

Date: 03/29/2017

- Added `Coveralls <https://coveralls.io/github/istresearch/scrapy-cluster>`_ code coverage integration

- Added full stack offline unit tests and online integration testing in `Travis CI <https://travis-ci.org/istresearch/scrapy-cluster>`_

- Upgraded all components to newest Python packages

- Switched example Virtual Machine from Miniconda to Virtualenv

- Add setting to specify Redis db across all components

- `Docker <https://hub.docker.com/r/istresearch/scrapy-cluster/>`_ support

- Improved RedisThrottledQueue implementation to allow for rubber band catch up while under moderation

- Added support for Centos and Ubuntu Virtual Machines

Kafka Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Updated stats schema to accept ``queue``, ``rest`` statistics requests.

- Added plugin API for managing Zookeeper domain configuration

- Added ability to scale horizontally with multiple processes for redundancy

Redis Monitor Changes
^^^^^^^^^^^^^^^^^^^^^

- Added ``close()`` method to plugin base class for clean shutdown

- Added queue statistics response object

- Added plugin for executing Zookeeper configuration updates

- Added ability to scale horizontally with multiple processes for redundancy

- New limited retry ability for failed actions

Crawler Changes
^^^^^^^^^^^^^^^

- Added ability to control cluster wide blacklists via Zookeeper

- Improved memory management in scheduler for domain based queues

- Added two new spider middlewares for stats collection and meta field passthrough

- Removed excess pipeline middleware

Rest Service
^^^^^^^^^^^^

- New component that allows for restful integration with Scrapy Cluster

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