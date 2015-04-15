# scrapy-cluster

## CURRENTLY UNDER CONSTRUCTION

This Scrapy project uses Redis and Kafka to create a distributed on demand scraping
cluster.

The goal is to distribute seed URLs among many waiting spider instances, whose
requests are coordinated via Redis. Any other crawls those trigger, as a result
of frontier expansion or depth traversal, will also be distributed among all
workers in the cluster.

The input to the system is a Kafka topic and the output is a set of Kafka
topics. Raw HTML and assets are crawled interactively, spidered, and output to
the log. For easy local development, you can also disable the Kafka portions
and work with the spider entirely via Redis.

## Dependencies

- redis: http://redis.io
- kafka-python: https://github.com/mumrah/kafka-python
- kafka: http://kafka.apache.org

## Quick start

Coming Soon

