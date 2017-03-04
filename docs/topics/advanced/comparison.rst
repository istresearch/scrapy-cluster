.. _other_projects:

Other Distributed Scrapy Projects
=================================

Scrapy Cluster is not the only project that attempts to use Scrapy in a distributed fashion. Here are some other notable projects:

Scrapy Redis
------------

**Github:** https://github.com/rolando/scrapy-redis

**Description:** Scrapy Cluster was born from Scrapy Redis, which offloads Requests to a Redis instance. This allows for spiders to coordinate their crawling efforts via Redis, and pushes the results back into Redis. Scrapy Cluster ended up going in a different enough direction that it was no longer the same project, but if you look closely enough you will see reminents still there.

Frontera
--------

**Github:** https://github.com/scrapinghub/frontera

**Description:** Built by the Scrapinghub Team, Frontera is designed to allow agnostic crawl frontier expansion. In particular, it helps determine what a series of crawlers should crawl next via some kind of logic or processing. This shares many of the same features as Scrapy Cluster, including a message bus and the ability to use many popular big data stack applications.

Scrapy RT
---------

**Github:** https://github.com/scrapinghub/scrapyrt

**Description:** Scrapy Real Time provides an HTTP interface for working with and scheduling crawls. It provides an HTTP rest server with a series of endpoints to submit and retrieve crawls. Scrapy RT is similar to Scrapy Cluster in that it provides a single API to interact with your crawlers.

Scrapyd
-------

**Github:** https://github.com/scrapy/scrapyd

**Description:** Scrapyd is a daemon service for running spiders. It allows you the unique ability to deploy whole spider projects to your Scrapyd instance and run or monitor your crawls. This is similar to Scrapy Cluster in that the spiders are spread across machines, but inherently do not do any orchestration with other crawler machines.

Arachnado
---------

**Github:** https://github.com/TeamHG-Memex/arachnado

**Description:** Arachnado is a Tornado based HTTP API and Web UI for using a Scrapy spider to crawl a target website. It allows you to create crawl jobs, execute them, and see aggregate statistics based on your Spider results. It has similar themes to Scrapy Cluster, like statistics and crawl jobs, but does not appear to orchestrate multiple spiders without additional work.

Others
------

Do you know of another distributed Scrapy project not listed here? Please feel free to :ref:`contribute <report_issue>` to make our documentation better.