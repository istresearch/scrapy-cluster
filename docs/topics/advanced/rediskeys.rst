Redis Keys
==========

The following keys within Redis are used by the Scrapy Cluster:

- ``timeout:<spiderid>:<appid>:<crawlid>`` - The timeout value of the crawl in the system, used by the Redis Monitor. The actual value of the key is the date in seconds since epoch that the crawl with that particular ``spiderid``, ``appid``, and ``crawlid`` will expire.

- ``<spiderid>:queue`` - The queue that holds all of the url requests for a spider type. Within this sorted set is any other data associated with the request to be crawled, which is stored as a Json object that is Pickle encoded.

- ``<spiderid>:dupefilter:<crawlid>`` - The duplication filter for the spider type and ``crawlid``. This Redis Set stores a scrapy url hash of the urls the crawl request has already seen. This is useful for coordinating the ignoring of urls already seen by the current crawl request.

- ``<spiderid>:blacklist`` - A permanent blacklist of all stopped and expired ``crawlid``'s . This is used by the Scrapy scheduler prevent crawls from continuing once they have been halted via a stop request or an expiring crawl. Any subsequent crawl requests with a ``crawlid`` in this list will not be crawled past the initial request url.

.. warning:: The Duplication Filter is only temporary, otherwise every single crawl request will continue to fill up the Redis instance! Since the the goal is to utilize Redis in a way that does not consume too much memory, the filter utilizes Redis's `EXPIRE <http://redis.io/commands/expire>`_ feature, and the key will self delete after a specified time window. The default window provided is 60 seconds, which means that if your crawl job with a unique ``crawlid`` goes for more than 60 seconds without a request, the key will be deleted and you may end up crawling pages you have already seen. Since there is an obvious increase in memory used with an increased timeout window, that is up to the application using Scrapy Cluster to determine what a safe tradeoff is.

