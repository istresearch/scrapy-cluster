DNS Cache
=========

The default for Scrapy is to cache DNS queries in memory, but there is no TTL handling as of scrapy v1.0. While this is fine for short-lived spiders, any persistent spiders can accumulate stale DNS data until the next time they are restarted, potentially resulting in bad page crawls. An example scenario is with Amazon's Elastic Load Balancer, which auto-adds public IPs to the load balancer during high activity. These IPs could later be re-allocated to another website, causing your crawler to get the wrong data.

Scrapy-cluster has changed ``DNSCACHE_ENABLED = False`` in ``settings.py`` in order to prevent this caching and use the system DNS resolver for all queries. If your system does not have a DNS cache on the localhost, such as ``nscd`` or ``dnsmasq``, this will increase requests to your DNS server. Noteably, Ubuntu 12.04 and 14.04 server editions do not come with a preconfigured DNS cache.
