Redis Keys
==========

The following keys within Redis are used by the Scrapy Cluster:

Production
----------

- **timeout:<spiderid>:<appid>:<crawlid>** - The timeout value of the crawl in the system, used by the Redis Monitor. The actual value of the key is the date in seconds since epoch that the crawl with that particular ``spiderid``, ``appid``, and ``crawlid`` will expire.

- **<spiderid>:<domain>:queue** - The queue that holds all of the url requests for a spider type of a particular domain. Within this sorted set is any other data associated with the request to be crawled, which is stored as a Json object that is ujson encoded.

- **<spiderid>:dupefilter:<crawlid>** - The duplication filter for the spider type and ``crawlid``. This Redis Set stores a scrapy url hash of the urls the crawl request has already seen. This is useful for coordinating the ignoring of urls already seen by the current crawl request.

- **<spiderid>:blacklist** - A permanent blacklist of all stopped and expired ``crawlid``'s . This is used by the Scrapy scheduler prevent crawls from continuing once they have been halted via a stop request or an expiring crawl. Any subsequent crawl requests with a ``crawlid`` in this list will not be crawled past the initial request url.

.. warning:: The Duplication Filter is only temporary, otherwise every single crawl request will continue to fill up the Redis instance! Since the the goal is to utilize Redis in a way that does not consume too much memory, the filter utilizes Redis's `EXPIRE <http://redis.io/commands/expire>`_ feature, and the key will self delete after a specified time window. The :ref:`default <dupe_timeout>` window provided is 600 seconds, which means that if your crawl job with a unique ``crawlid`` goes for more than 600 seconds without a request, the key will be deleted and you may end up crawling pages you have already seen. Since there is an obvious increase in memory used with an increased timeout window, that is up to the application using Scrapy Cluster to determine what a safe tradeoff is.

- **<spiderid>:<ip_address>:<domain>:throttle_time** - Stores the value for the future calculation on when the next time a moderated throttle key is available to pop. Both ``<spiderid>`` and ``<ip_address>`` are dependent on the :ref:`throttle style <throttle_mechanism>`, and may not be present depending on configuration.

- **<spiderid>:<ip_address>:<domain>:throttle_window** - Stores the number of hits for a particular domain given the Type and IP Throttle Style. Is used by the Scrapy Scheduler to do coordinated throttling across a particular domain. Both ``<spiderid>`` and ``<ip_address>`` are dependent on the :ref:`throttle style <throttle_mechanism>`, and may not be present depending on configuration.

- **rest:poll:<uuid>** - Allows a response caught by a separate Rest service to be stored within Redis to be later retrived by a ``poll`` request to another. Useful when running multiple Rest processes behind a load balancer with jobs that are longer than the initial call timeout.

- **<spiderid>:domain_max_page_filter:<domain>:<crawlid>** - Used by the per crawl job page count domain filter to ensure the maximum number of pages to crawl per domain for any single crawlid are not exceeded.

- **<spiderid>:global_page_count_filter:<domain>:<crawlid>** - Used by the global page count domain filter to ensure the cluster-wide settings for the maximum number of pages to crawl per domain are not exceeded for any given request.


Redis Monitor Jobs
^^^^^^^^^^^^^^^^^^

- **zk:<action>:<domain>:<appid>** - Stores job info for the Zookeeper plugin

- **stop:<spiderid>:<appid>:<crawlid>** - Used to stop a crawl via the Stop plugin

- **statsrequest:<stats-type>:<appid>** - Used by the Stats plugin to fetch statistics requests

- **info:<spiderid>:<appid>:<crawlid>** - Used by the Info plugin to gather information about an active crawl

- **timeout:<spiderid>:<appid>:<crawlid>** - Used to stop an active crawl when the crawl time window has expired

Statistics
^^^^^^^^^^

- **stats:kafka-monitor:<plugin>:<window>** - Used to collect plugin statistics of requests that are received by the Kafka Monitor. These keys hold information about the number of successful hits on that plugin in a specific time window.

- **stats:kafka-monitor:total:<window>** - Holds statistics on the total number of requests received by the Kafka Monitor. This contains both successful and unsuccessful API requests.

- **stats:kafka-monitor:fail:<window>** - Holds statistics on the total number of failed API validation attempts by the Kafka Monitor for requests it receives. The value here is based on the defined statistics collection time window.

- **stats:kafka-monitor:self:<machine>:<id>** - Self reporting mechanism for the Kafka Monitor

- **stats:redis-monitor:<plugin>:<window>** - Used to collect plugin statistics of requests that are received by the Redis Monitor. These keys hold information about the number of successful hits on that plugin in a specific time window.

- **stats:redis-monitor:total:<window>** - Holds statistics on the total number of requests received by the Redis Monitor. This contains both successful and unsuccessful attempts at processing in monitored key.

- **stats:redis-monitor:fail:<window>** - Holds statistics on the total number of failed attempts by the Redis Monitor for requests it receives. The value here is based on the defined statistics collection time window.

- **stats:redis-monitor:self:<machine>:<id>** - Self reporting mechanism for the Redis Monitor

- **stats:crawler:<hostname>:<spiderid>:<status_code>** - Holds metrics for the different response codes the crawlers have seen. This key is split by the machine, spider, and response code type to allow you to further examine your different crawler success rates.

- **stats:crawler:self:<machine>:<spiderid>:<id>** - Self reporting mechanism for each individual crawler

- **stats:rest:self:<machine>:<id>** - Self reporting mechanism for each individual Rest service

Testing
-------

If you run the integration tests, there may be temporary Redis keys created that do not interfere with production level deployments.

- **info-test:blah** - Used when testing Redis Monitor has the ability to process and send messages to kafka

- **cluster:test** - Used when testing the Kafka Monitor can act and set a key in Redis

- **test-spider:dmoztools.net:queue** - Used when testing the crawler installation can interact with Redis and Kafka

- **stats:crawler:<hostname>:test-spider:<window>** - Automatically created and destoryed during crawler testing by the stats collection mechanism settings.
