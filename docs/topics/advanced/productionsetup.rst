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

- Kafka Monitor(s)

- Redis Monitor(s)

- Rest service(s)

Spider Complexity
-----------------

Spider complexity plays a bigger role than you might think in how fast your cluster can crawl. The two single most important things to worry about are:

**How fast your Spider can process a Response**

Any single response from Scrapy is going to hog that spider process until all of the items are yielded appropriately. How fast your literal ``spider.py`` script can execute cleanly is important to getting high throughput from your Spiders. Sure, you can up the number of `concurrent requests <http://doc.scrapy.org/en/latest/topics/settings.html#concurrent-requests>`_ but in the end an inefficient Spider is going to slow you down.

**How fast your Item Pipeline can process an Item**

Scrapy item pipelines are not distributed, and you should not be doing processing with your items that requires that kind of scalability. You can up the `maximum <http://doc.scrapy.org/en/latest/topics/settings.html#concurrent-items>`_ number of items in your item pipeline, but in the end if your pipeline is trying to do too much your whole crawling architecture will begin to slow down. That is why Scrapy Cluster is built around Kafka, so that you may do really large and scaled processing of your items in another architecture, like `Storm <http://storm.apache.org>`_.

Hardware
--------

Many that are new to Scrapy Cluster do not quite understand how to get the most out of it. Improperly configured core data components like Zookeeper, Kafka, and Redis, or even where you put your crawling machines can have an impact on how fast you can crawl. **The most important thing you can do is to have a massive internet pipe available to your crawler machines**, with a good enough network card(s) to keep up.

Nothing here can substitute for a poor network connection, so no matter if you are crawling behind a proxy, through some service, or to the open internet, your rate of collection is depending on how fast you can get the data.

In production, we typically run everything on their own boxes, or a little overlap depending on your limitations.

**Zookeeper** - 3 nodes to help ensure Kafka is running smoothly, with a little overhead for the crawlers. These boxes typically can be all around or 'general' boxes; with decent IO, RAM, and disk.

**Kafka** - 5 nodes to ensure your cluster is able to pump and read as much data as you can throw at it. Setting up Kafka can be its own art form, so you want to make sure your data packet size is fairly large, and that you make sure your settings on how much data you store are properly configured. These boxes rely heavily on the internal network, so high IO and no crawlers on these machines.

**Redis** - 1 node, since Redis is an in memory database you will want a lot of RAM on this box. Your database should only become a problem if your periodic back up files are too large to fit on your machine. This means either that you cannot crawl fast enough and your database is filling up, or you have that much stuff to where it fills your disk. Either way, disk and RAM are the important things here

.. note:: Scrapy Cluster has not been tested against `Redis Cluster <http://redis.io/topics/cluster-spec>`_. If you would like to run Redis as a Cluster used by Scrapy Cluster please take caution as there may be key manipulations that do not scale well across Redis instances.

**Kafka Monitors** - This is a lightweight process that reads from your Kafka topic of choice. It can be sprinkled on any number of machines you see fit, as long as you have the number of Kafka topics paritions to scale. We would recommend deployment on machines that are close to either Kafka or Redis.

**Redis Monitors** - Another very lightweight process that can be sprinkled around on any number of machines. Prefers to be close to Redis.

**Crawlers** - As many small machines as you see fit. Your crawlers need to hit the internet, so put them on machines that have really good network cards or lots of IO. Scale these machines wider, rather than trying to stack a large number of processes on each machine.

**Rests** - If you need multiple rest endpoints, put them behind a load balancer that allows the work to be spread across multiple hosts. Prefers to be close to Kafka.

Crawler Configuration
---------------------

Crawler configuration is very important, and it can take some time to find settings that are correct for your setup. Here are some general guidelines for a large Scrapy Cluster:

* Spiders should be spread **thin**, not thick across your machines. How thin? Consider only running 5 to 10 spider process on each machine. This allows you to keep your machine size small, and to scale horizontally on the number of machines you run. This allows for better per-ip rate limits, and to enable the cluster to be more efficient when crawling sites while at the same time not getting your IP blocked. You would be surprised how fast a 5 machine 5 process setup can crawl!

* Have as many different IP addresses as you can. If you can get one IP Address per machine - awesome. The more you stack machines out the same IP Address, the lower the throughput will be on your cluster due to the domain throttling.

* Run the IP Address throttle only (no Spider Type) if you have many different spiders coming from your cluster. It will allow them to orchestrate themselves across spider types to crawl at your desired rate limits. Turning on the Spider Type throttle will eliminate this benefit.

* Don't set your ``QUEUE_WINDOW`` and ``QUEUE_HITS`` too high. There is a reason the defaults are ``60`` and ``10``. If you can scale horizontally, you can get your throughput to ``10 * (num machines)`` and should be able to fit your throughput needs.

* Flip the :ref:`Base 64 <c_base64>` encode flag on your crawlers. You **will** run across malformed utf-8 characters that breaks ``json.dumps()``. It will save you headaches in the long run by ensuring your html is always transmitted to Kafka.

Stats Collection
----------------

Stats Collection by Scrapy Cluster is meant to allow users to get a better understanding of what is happening in their cluster without adding additional components. In production, it may be redundant to have *both* Stats Collection and Elasticsearch logging, and you will want to turn off or greatly reduce the number of stats collected by the cluster.

Retaining lots of different stats about every machine and every process is very memory intensive. We recommend reducing the default ``STATS_TIMES`` to eliminate ``SECONDS_1_WEEK`` and ``SECONDS_1_DAY`` at the very least in order to reduce your Redis memory footprint.

The last point about Stats Collection is that it becomes inconsistent with :doc:`docker` style deployments without a defined ``hostname`` for your container. In some circumstances the stats collection needs the hostname, and when docker autogenerates hostanames for the containers this can create excess data within Redis. In this case, we recommend eliminating Stats Collection from your cluster if you plan on continuously redeploying, or bringing your docker container up and down frequently without a defined hostname.
