DNS Cache
=========

The default for Scrapy is to cache DNS queries in memory, but there is no TTL handling as of Scrapy v1.0. While this is fine for short-lived spiders, any persistent spiders can accumulate stale DNS data until the next time they are restarted, potentially resulting in bad page crawls. An example scenario is with Amazon's Elastic Load Balancer, which auto-adds public IPs to the load balancer during high activity. These IPs could later be re-allocated to another website, causing your crawler to get the wrong data.

Scrapy Cluster spiders have the potential to stay up for weeks or months at a time, causing this backlog of bad IPs to grow significantly. We recommend that you set ``DNSCACHE_ENABLED = False`` in your ``localsettings.py`` for all of your crawlers in order to prevent this caching and use the system DNS resolver for all queries.

Your system will instead need a DNS cache on the localhost, such as ``nscd`` or ``dnsmasq``, as this will increase requests to your DNS server.

.. warning:: Ubuntu 12.04 and 14.04 server editions do not come with a preconfigured DNS cache. Turning this setting off without a DNS cache will result in errors from Scrapy.
