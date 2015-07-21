Advanced Topics
===============

This section describes more advanced topics about the Scrapy Cluster and other miscellaneous items.

Crawling Responsibly
--------------------

Scrapy Cluster is a very high throughput web crawling architecture that allows you to spread the web crawling load across an arbitrary number of machines. It is up the the end user to scrape pages responsibly, and to not crawl sites that do not want to be crawled. As a start, most sites today have a `robots.txt <http://www.robotstxt.org/robotstxt.html>`_ file that will tell you how to crawl the site, how often, and where not to go.

You can very easily max out your internet pipe(s) on your crawling machines by feeding them high amounts of crawl requests. In regular use we have seen a single machine with five crawlers running sustain almost 1000 requests per minute! We were not banned from any site during that test, simply because we obeyed every site's robots.txt file and only crawled at a rate that was safe for any single site.

Abuse of Scrapy Cluster can have the following things occur:

- An investigation from your ISP about the amount of data you are using

- Exceeding the data cap of your ISP

- Semi-permanent and permanent bans of your IP Address from sites you crawl too fast

**With great power comes great responsibility.**

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

Scrapy Cluster Response Time
----------------------------

The Scrapy Cluster Response time is dependent on a number of factors:

- How often the Kafka Monitor polls for new messages

- How often any one spider polls redis for new requests

- How many spiders are polling

- How fast the spider can fetch the request


With the Kafka Monitor constantly monitoring the topic, there is very little latency for getting a request into the system. The bottleneck occurs mainly in the core Scrapy crawler code.

The more crawlers you have running and spread across the cluster, the lower the average response time will be for a crawler to receive a request. For example if a single spider goes idle and then polls every 5 seconds, you would expect a your maximum response time to be 5 seconds, the minimum response time to be 0 seconds, but on average your response time should be 2.5 seconds for one spider. As you increase the number of spiders in the system the likelihood that one spider is polling also increases, and the cluster performance will go up.

The final bottleneck in response time is how quickly the request can be conducted by Scrapy, which depends on the speed of the internet connection(s) you are running the Scrapy Cluster behind. This final part is out of control of the Scrapy Cluster itself.

Redis Keys
----------

The following keys within Redis are used by the Scrapy Cluster:

- ``timeout:<spiderid>:<appid>:<crawlid>`` - The timeout value of the crawl in the system, used by the Redis Monitor. The actual value of the key is the date in seconds since epoch that the crawl with that particular ``spiderid``, ``appid``, and ``crawlid`` will expire.

- ``<spiderid>:queue`` - The queue that holds all of the url requests for a spider type. Within this sorted set is any other data associated with the request to be crawled, which is stored as a Json object that is Pickle encoded.

- ``<spiderid>:dupefilter:<crawlid>`` - The duplication filter for the spider type and ``crawlid``. This Redis Set stores a scrapy url hash of the urls the crawl request has already seen. This is useful for coordinating the ignoring of urls already seen by the current crawl request.

- ``<spiderid>:blacklist`` - A permanent blacklist of all stopped and expired ``crawlid``'s . This is used by the Scrapy scheduler prevent crawls from continuing once they have been halted via a stop request or an expiring crawl. Any subsequent crawl requests with a ``crawlid`` in this list will not be crawled past the initial request url.

.. warning:: The Duplication Filter is only temporary, otherwise every single crawl request will continue to fill up the Redis instance! Since the the goal is to utilize Redis in a way that does not consume too much memory, the filter utilizes Redis's `EXPIRE <http://redis.io/commands/expire>`_ feature, and the key will self delete after a specified time window. The default window provided is 60 seconds, which means that if your crawl job with a unique ``crawlid`` goes for more than 60 seconds without a request, the key will be deleted and you may end up crawling pages you have already seen. Since there is an obvious increase in memory used with an increased timeout window, that is up to the application using Scrapy Cluster to determine what a safe tradeoff is.

