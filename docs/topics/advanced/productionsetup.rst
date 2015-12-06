Production Setup
================

System Fragility
----------------

Scrapy Cluster is built on top of many moving parts, and likely you will want some kind of assurance that you cluster is continually up and running. Instead of manually ensuring the processes are running on each machine, it is highly recommended that you run every component under some kind of process supervision.

We have had very good luck with `Supervisord <http://supervisord.org/>`_ but feel free to put the processes under your process monitor of choice.

As a friendly reminder, the following processes should be monitored:

- Zookeeper

- Kafka

- Redis

- Crawler(s)

- Kafka Monitor for Crawl Requests

- Kafka Monitor for Action Requests

- Redis Monitor

Spider Complexity
-----------------