Quick Start
-----------

*This guide does not go into detail as to how everything works, but hopefully will get you scraping quickly. For more information about each process works please see the rest of the documentation.*

1) Make sure you have Apache Zookeeper, Apache Kafka, and Redis up and running on your cluster. For more information about standing those up, please refer to the official project documentation.

2) Download and unzip the project `here`_.

.. _here: https://github.com/istresearch/scrapy-cluster/archive/master.zip

Lets assume our project is now in ``~/scrapy-cluster``

3) You will now need to configure the following four settings files:

a) ``~/scrapy-cluster/kafka-monitor/settings-crawling.py``

Add your specific configuraiton to ``REDIS_HOST``, ``REDIS_PORT``, and ``KAFKA_HOSTS``.

For example:

::

    REDIS_HOST = 'server-1'
    REDIS_PORT = 6379
    KAFKA_HOSTS = 'server-2:9092'

This is used to determine where the Kafka Monitor will listen to incoming crawl requests and where send them. For this example, lets assume ``server-1`` houses Redis and ``server-2`` houses Kafka.

b) ``~/scrapy-cluster/kafka-monitor/settings-actions.py``

Add your specific configuraiton to ``REDIS_HOST``, ``REDIS_PORT``, and ``KAFKA_HOSTS``.

For example:

::

    REDIS_HOST = 'server-1'
    REDIS_PORT = 6379
    KAFKA_HOSTS = 'server-2:9092'

Notice this is very similar to the first settings file, but the other parameters are different. This settings file is used to listen for action requests and determines where to send them.

c) ``~/scrapy-cluster/crawler/crawling/settings.py``

Add your specific configuraiton to ``REDIS_HOST``, ``REDIS_PORT``, and ``KAFKA_HOSTS``.

For example:

::

    REDIS_HOST = 'server-1'
    REDIS_PORT = 6379
    KAFKA_HOSTS = 'server-2:9092'

This settings file is used to configure Scrapy. It uses all of the configurations already built in with the project, with a few more to get us into cluster mode. The new settings are utilized by the scheduler and item pipeline.

d) ``~/scrapy-cluster/redis-monitor/settings.py``

Add your specific configuraiton to ``REDIS_HOST``, ``REDIS_PORT``, and ``KAFKA_HOSTS``.

For example:

::

    REDIS_HOST = 'server-1'
    REDIS_PORT = 6379
    KAFKA_HOSTS = 'server-2:9092'

This last settings file is used to get information out of the redis queue, and tells the redis monitor where to point.

4) At this point we can start up either a bare bones cluster, or a fully operational cluster:

.. note:: You can append ``&`` to the end of the following commands to run them in the background, but we recommend you open different terminal windows to first get a feel of how the cluster operates.

**Bare Bones:**

-  The Kafka Monitor for Crawling:

   ::

       python kafka-monitor.py run -s settings_crawling.py

-  A crawler:

   ::

       scrapy runspider crawling/spiders/link_spider.py

-  The dump utility located in Kafka-Monitor to see your results

   ::

       python kafkadump.py dump demo.crawled_firehose --host=server-2:9092


**Fully Operational:**

-  The Kafka Monitor for Crawling:

   ::

       python kafka-monitor.py run -s settings_crawling.py

-  The Kafka Monitor for Actions:

   ::

       python kafka-monitor.py run -s settings_actions.py

-  The Redis Monitor:

   ::

       python redis-monitor.py

-  A crawler (1+):

   ::

       scrapy runspider crawling/spiders/link_spider.py

-  The dump utility located in Kafka Monitor to see your crawl results

   ::

       python kafkadump.py dump demo.crawled_firehose --host=server-2:9092

-  The dump utility located in Kafka Monitor to see your action results

   ::

       python kafkadump.py dump demo.outbound_firehose --host=server-2:9092

5) We now need to feed the cluster a crawl request. This is done via the same kafka-monitor python script, but with different command line arguements.

::

    python kafka-monitor.py feed '{"url": "http://istresearch.com", "appid":"testapp", "crawlid":"abc123"}' -s settings_crawling.py

You will see the following output on the command line for that successful request:

::

    => feeding JSON request into demo.incoming_urls...
    {
        "url": "http://istresearch.com",
        "crawlid": "abc123",
        "appid": "testapp"
    }
    => done feeding request.

-  If this command hangs, it means the script cannot connect to Kafka

6) After a successful request, the following chain of events should occur in order:

  #. The Kafka monitor will receive the crawl request and put it into Redis
  #. The spider periodically checks for new requests, and will pull the request from the queue and process it like a normal Scrapy spider.
  #. After the scraped item is yielded to the Scrapy item pipeline, the Kafka Pipeline object will push the result back to Kafka
  #. The Kafka Dump utility will read from the resulting output topic, and print out the raw scrape object it received

7) The Redis Monitor utility is useful for learning about your crawl while it is being processed and sitting in redis, so we will pick a larger site so we can see how it works (this requires a full deployment).

Crawl Request:

::

    python kafka-monitor.py feed '{"url": "http://dmoz.org", "appid":"testapp", "crawlid":"abc1234", "maxdepth":1}' -s settings_crawling.py

Now send an ``info`` action request to see what is going on with the
crawl:

::

    python kafka-monitor.py feed -s settings_actions.py '{"action":"info", "appid":"testapp", "uuid":"someuuid", "crawlid":"abc1234", "spiderid":"link"}'

The following things will occur for this action request:

1. The Kafka monitor will receive the action request and put it into Redis
2. The Redis Monitor will act on the info request, and tally the current pending requests for the particular ``spiderid``, ``appid``, and ``crawlid``
3. The Redis Monitor will send the result back to Kafka
4. The Kafka Dump utility monitoring the actions will receive a result similar to the following:

::

    {u'server_time': 1430170027, u'crawlid': u'abc1234', u'total_pending': 48, u'low_priority': -19, u'high_priority': -9, u'appid': u'testapp', u'uuid': u'someuuid'}

In this case we had 48 urls pending in the queue, so yours may be slightly different.

8) If the crawl from step 7 is still running, lets stop it by issuing a ``stop`` action request (this requires a full deployment).

Action Request:

``python kafka-monitor.py feed -s settings_actions.py '{"action":"stop", "appid":"testapp", "uuid":"someuuid", "crawlid":"abc1234", "spiderid":"link"}'``

The following things will occur for this action request:

1. The Kafka monitor will receive the action request and put it into Redis
2. The Redis Monitor will act on the stop request, and purge the current pending requests for the particular ``spiderid``, ``appid``, and ``crawlid``
3. The Redis Monitor will blacklist the ``crawlid``, so no more pending requests can be generated from the spiders or application
4. The Redis Monitor will send the purge total result back to Kafka
5. The Kafka Dump utility monitoring the actions will receive a result similar to the following:

::

    {u'action': u'stop', u'total_purged': 48, u'spiderid': u'link', u'crawlid': u'abc1234', u'appid': u'testapp'}

In this case we had 48 urls removed from the queue. Those pending requests are now completely removed from the system and the spider will go back to being idle.

--------------

Hopefully you now have a working Scrapy Cluster that allows you to submit jobs to the queue, receive information about your crawl, and stop a crawl if it gets out of control. For a more in depth look at each of the components, please continue reading the documentation for each component.
