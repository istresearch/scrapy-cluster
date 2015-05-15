Redis Monitor
=============

The Redis Monitor serves to moderate the redis based crawling queue. It is used to expire old crawls, stop existing crawls, and gather information about current crawl jobs.

Quick Start
-----------

First, make sure your `settings.py` is updated with your Kafka and Redis hosts.

Then run the redis monitor to monitor your Scrapy Cluster:

::

    python redis_monitor.py

This is a completely optional component to the Scrapy Cluster. If you do not care about getting information about crawls, stopping, or expiring crawls in the cluster then you can leave this component alone.

-  For how to set up the Scrapy crawlers, refer to the :doc:`./crawler` documentation

-  To learn more about how to submit crawls, please see the :doc:`./kafkamonitor` documentation

Design Considerations
---------------------

The Redis Monitor is designed to act as a surgical instrument allows an application to peer into the queues and variables managed by Redis that act upon the Scrapy Cluster. It runs independently of the cluster, and interacts with the items within Redis in three distinct ways:

**Information Retrieval**

    All of the crawl information is contained within Redis, but stored in a way that makes it hard for a human to read. The Redis Monitor makes getting current crawl information about your application's overall crawl statistics or an individual crawl easy. If you would like to know how many urls are in a particular ``crawlid`` queue, or how many urls are in the overall ``appid`` queue then this will be useful.

**Stop Crawls**

    Sometimes crawls get out of control and you would like the Scrapy Cluster to immediately stop what it is doing, but without killing all of the other ongoing crawl jobs. The ``crawlid`` is used to identify exactly what crawl job needs to be stopped, and that ``crawlid`` will both be purged from the request queue, and blacklisted so the spider's know to never crawl urls with that particular ``crawlid`` again.

**Expire Crawls**

    Very large and very broad crawls often can take longer than the time allotted to crawl the domain. In this case, you can set an expiration time for the crawl to automatically expire after X date. The particular crawl job will be purged from the spider's queue while allowing other crawls to continue onward.

These three use cases conducted by the Redis Monitor give a user or an application a great deal of control over their Scrapy Cluster jobs when executing various levels of crawling effort. At any one time the cluster could be doing an arbitrary number of different crawl styles, with different spiders or different crawl parameters, and the design goal of the Redis Monitor is to control the jobs through the same Kafka interface that all of the applications use.

Components
----------

This section explains the individual files located within the redis monitor project.


redis\_monitor.py
^^^^^^^^^^^^^^^^^

The Redis Monitor acts upon two different action requests, and also sends out notifications when a crawl job expires from the queues.

All requests adhere to the following three Kafka topics for input and output:

Incoming Action Request Kafka Topic:

- ``demo.inbound_actions`` - The topic to feed properly formatted action requests to

Outbound Action Result Kafka Topics:

- ``demo.outbound_firehose`` - A firehose topic of all resulting actions within the system. Any single action conducted by the Redis Monitor is guaranteed to come out this pipe.

- ``demo.outbound_<appid>`` - A special topic created for unique applications that submit action requests. Any application can listen to their own specific action results by listening to the the topic created under the ``appid`` they used to submit the request. These topics are a subset of the action firehose data and only contain the results that are applicable to the application who submitted it.

**Information Action**

The ``info`` action can be conducted in two different ways.

Application Info Request

    ::

        python kafka-monitor.py feed -s settings_actions.py '{"action":"info", "appid":"testapp", "uuid":"someuuid", "spiderid":"link"}

    This returns back all information available about the ``appid`` in question. It is a summation of the various ``crawlid`` statistics.

    Application Info Response

    ::

        {
            u'server_time': 1429216294,
            u'uuid': u'someuuid',
            u'total_pending': 12,
            u'total_domains': 0,
            u'total_crawlids': 2,
            u'appid': u'testapp',
            u'crawlids': {
                u'2aaabbb': {
                    u'low_priority': 29,
                    u'high_priority': 29,
                    u'expires': u'1429216389'
                    u'total': 1
                },
                u'1aaabbb': {
                    u'low_priority': 29,
                    u'high_priority': 39,
                    u'total': 11
                }
            }
        }

    Here, there were two different ``crawlid``'s in the queue for the ``link`` spider that had the specified ``appid``. The json return value is the basic structure seen above that breaks down the different ``crawlid``'s into their total, their high/low priority in the queue, and if they have an expiration.

Crawl ID Info Request

    ::

        python kafka-monitor.py feed -s settings_actions.py '{"action":"info", "appid":"myapp", "uuid":"someuuid", "crawlid":"abc123", "spiderid":"link"}'

    This is a very specific request that is asking to poll a specific ``crawlid`` in the ``link`` spider queue. Note that this is very similar to the above request but with one extra parameter. The following example response is generated:

Crawl ID Info Response from Kafka

    ::

        {
            u'server_time': 1429216864,
            u'crawlid': u'abc123',
            u'total_pending': 28,
            u'low_priority': 39,
            u'high_priority': 39,
            u'appid': u'testapp',
            u'uuid': u'someuuid'
        }

    The response to the info request is a simple json object that gives statistics about the crawl in the system, and is very similar to the results for an ``appid`` request. Here we can see that there were 28 requests in the queue yet to be crawled of all the same priority.

**Stop Action**

The ``stop`` action is used to abruptly halt the current crawl job. A request takes the following form:

Stop Request

    ::

        python kafka-monitor.py feed -s settings_actions.py '{"action":"stop", "appid":"testapp", "uuid":"someuuid2", "crawlid":"ABC123", "spiderid":"link"}'

    After the request is processed, only current spiders within the cluster currently in progress of downloading a page will continue. All other spiders will not crawl that same ``crawlid`` past a depth of 0 ever again, and all pending requests will be purged from the queue.

Stop Response from Kafka

    ::

        {
            u'total_purged': 524,
            u'uuid': u'someuuid',
            u'spiderid': u'link',
            u'appid': u'testapp',
            u'action': u'stop',
            u'crawlid': u'ABC123'
        }

    The json response tells the application that the stop request was successfully completed, and states how many requests were purged from the particular queue.

**Expire Notification**

An ``expire`` notification is generated by the Redis Monitor any time an on going crawl is halted because it has exceeded the time it was supposed to stop. A crawl request that includes an ``expires`` attribute will generate an expire notification when it is stopped by the Redis Monitor.

Expire Notification from Kafka

    ::

        {
            u'total_expired': 75,
            u'crawlid': u'abcdef-1',
            u'spiderid': u'link',
            u'appid': u'testapp',
            u'action': u'expired'
        }

    This notification states that the ``crawlid`` of "abcdef-1" expired within the system, and that 75 pending requests were removed.
