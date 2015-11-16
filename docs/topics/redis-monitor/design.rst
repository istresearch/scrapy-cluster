Design
==============

The Redis Monitor is designed to act as a surgical instrument allows an application to peer into the queues and variables managed by Redis that act upon the Scrapy Cluster. It runs independently of the cluster, and interacts with the items within Redis in three distinct ways:

**Information Retrieval**

    All of the crawl information is contained within Redis, but stored in a way that makes it hard for a human to read. The Redis Monitor makes getting current crawl information about your application's overall crawl statistics or an individual crawl easy. If you would like to know how many urls are in a particular ``crawlid`` queue, or how many urls are in the overall ``appid`` queue then this will be useful.

**Stop Crawls**

    Sometimes crawls get out of control and you would like the Scrapy Cluster to immediately stop what it is doing, but without killing all of the other ongoing crawl jobs. The ``crawlid`` is used to identify exactly what crawl job needs to be stopped, and that ``crawlid`` will both be purged from the request queue, and blacklisted so the spider's know to never crawl urls with that particular ``crawlid`` again.

**Expire Crawls**

    Very large and very broad crawls often can take longer than the time allotted to crawl the domain. In this case, you can set an expiration time for the crawl to automatically expire after X date. The particular crawl job will be purged from the spider's queue while allowing other crawls to continue onward.

These three use cases conducted by the Redis Monitor give a user or an application a great deal of control over their Scrapy Cluster jobs when executing various levels of crawling effort. At any one time the cluster could be doing an arbitrary number of different crawl styles, with different spiders or different crawl parameters, and the design goal of the Redis Monitor is to control the jobs through the same Kafka interface that all of the applications use.
