# Scrapy Cluster

[![Build Status](https://circleci.com/gh/istresearch/scrapy-cluster/tree/dev.svg?style=shield)](https://circleci.com/gh/istresearch/scrapy-cluster) [![Documentation](https://readthedocs.org/projects/scrapy-cluster/badge/?version=dev)](http://scrapy-cluster.readthedocs.io/en/dev/) [![Join the chat at https://gitter.im/istresearch/scrapy-cluster](https://badges.gitter.im/istresearch/scrapy-cluster.svg)](https://gitter.im/istresearch/scrapy-cluster?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge) [![Coverage Status](https://coveralls.io/repos/github/istresearch/scrapy-cluster/badge.svg?branch=dev)](https://coveralls.io/github/istresearch/scrapy-cluster?branch=dev) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/istresearch/scrapy-cluster/blob/dev/LICENSE) [![Docker Pulls](https://img.shields.io/docker/pulls/istresearch/scrapy-cluster.svg)](https://hub.docker.com/r/istresearch/scrapy-cluster/)
                 
This Scrapy project uses Redis and Kafka to create a distributed on demand scraping cluster.

The goal is to distribute seed URLs among many waiting spider instances, whose requests are coordinated via Redis. Any other crawls those trigger, as a result of frontier expansion or depth traversal, will also be distributed among all workers in the cluster.

The input to the system is a set of Kafka topics and the output is a set of Kafka topics. Raw HTML and assets are crawled interactively, spidered, and output to the log. For easy local development, you can also disable the Kafka portions and work with the spider entirely via Redis, although this is not recommended due to the serialization of the crawl requests.

## Dependencies

Please see the ``requirements.txt`` within each sub project for Pip package dependencies.

Other important components required to run the cluster

- Python 2.7 or 3.6: https://www.python.org/downloads/
- Redis: http://redis.io
- Zookeeper: https://zookeeper.apache.org
- Kafka: http://kafka.apache.org

## Core Concepts

This project tries to bring together a bunch of new concepts to Scrapy and large scale distributed crawling in general. Some bullet points include:

- The spiders are dynamic and on demand, meaning that they allow the arbitrary collection of any web page that is submitted to the scraping cluster
- Scale Scrapy instances across a single machine or multiple machines
- Coordinate and prioritize their scraping effort for desired sites
- Persist data across scraping jobs
- Execute multiple scraping jobs concurrently
- Allows for in depth access into the information about your scraping job, what is upcoming, and how the sites are ranked
- Allows you to arbitrarily add/remove/scale your scrapers from the pool without loss of data or downtime
- Utilizes Apache Kafka as a data bus for any application to interact with the scraping cluster (submit jobs, get info, stop jobs, view results)
- Allows for coordinated throttling of crawls from independent spiders on separate machines, but behind the same IP Address
- Enables completely different spiders to yield crawl requests to each other, giving flexibility to how the crawl job is tackled

## Scrapy Cluster test environment

To set up a pre-canned Scrapy Cluster test environment, make sure you have [Docker](https://www.docker.com/).

### Steps to launch the test environment:
1. Build your containers (or omit --build to pull from docker hub)
```
docker-compose up -d --build
```
2. Tail kafka to view your future results
```
docker-compose exec kafka_monitor python kafkadump.py dump -t demo.crawled_firehose -ll INFO
```
3. From another terminal, feed a request to kafka
```
curl localhost:5343/feed -H "content-type:application/json" -d '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"abc123"}'
```
4. Validate you've got data!
```
# wait a couple seconds, your terminal from step 2 should dump json data
{u'body': '...content...', u'crawlid': u'abc123', u'links': [], u'encoding': u'utf-8', u'url': u'http://dmoztools.net', u'status_code': 200, u'status_msg': u'OK', u'response_url': u'http://dmoztools.net', u'request_headers': {u'Accept-Language': [u'en'], u'Accept-Encoding': [u'gzip,deflate'], u'Accept': [u'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'], u'User-Agent': [u'Scrapy/1.5.0 (+https://scrapy.org)']}, u'response_headers': {u'X-Amz-Cf-Pop': [u'IAD79-C3'], u'Via': [u'1.1 82c27f654a5635aeb67d519456516244.cloudfront.net (CloudFront)'], u'X-Cache': [u'RefreshHit from cloudfront'], u'Vary': [u'Accept-Encoding'], u'Server': [u'AmazonS3'], u'Last-Modified': [u'Mon, 20 Mar 2017 16:43:41 GMT'], u'Etag': [u'"cf6b76618b6f31cdec61181251aa39b7"'], u'X-Amz-Cf-Id': [u'y7MqDCLdBRu0UANgt4KOc6m3pKaCqsZP3U3ZgIuxMAJxoml2HTPs_Q=='], u'Date': [u'Tue, 22 Dec 2020 21:37:05 GMT'], u'Content-Type': [u'text/html']}, u'timestamp': u'2020-12-22T21:37:04.736926', u'attrs': None, u'appid': u'testapp'}
```
## Documentation

Please check out the official [Scrapy Cluster documentation](https://scrapy-cluster.readthedocs.io/en/dev/) for more information on how everything works!

## Branches

The `master` branch of this repository contains the latest stable release code for `Scrapy Cluster 1.2`.

The `dev` branch contains bleeding edge code and is currently working towards [Scrapy Cluster 1.3](https://github.com/istresearch/scrapy-cluster/milestone/3). Please note that not everything may be documented, finished, tested, or finalized but we are happy to help guide those who are interested.
