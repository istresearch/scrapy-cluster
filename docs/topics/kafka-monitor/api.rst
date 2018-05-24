API
===

The Kafka Monitor consists of a combination of Plugins that allow for API validation and processing of the object received.

Kafka Topics
------------

**Incoming  Kafka Topic:** ``demo.incoming`` - The topic to feed properly formatted cluster requests.

**Outbound Result Kafka Topics:**

- ``demo.crawled_firehose`` - A firehose topic of all resulting crawls within the system. Any single page crawled by the Scrapy Cluster is guaranteed to come out this pipe.

- ``demo.crawled_<appid>`` - A special topic created for unique applications that submit crawl requests. Any application can listen to their own specific crawl results by listening to the the topic created under the ``appid`` they used to submit the request. These topics are a subset of the crawl firehose data and only contain the results that are applicable to the application who submitted it.

.. note:: The crawl result ``appid`` topics are disabled by default, as they create duplicate data within your Kafka application. You can override the :ref:`setting <c_kafka_appid_topics>` in the Crawler if you wish to turn this on.

- ``demo.outbound_firehose`` - A firehose topic of all the special info, stop, expire, and stat requests. This topic will have all non-crawl data requested from the cluster.

- ``demo.outbound_<appid>`` - A special topic for unique applications to read only their action request data. The ``appid`` used in the submission of the non-crawl API request will be written to both this topic and the firehose topic.

.. note:: The outbound ``appid`` topics are disabled by default, as they create duplicate data within Kafka. You can override the :ref:`setting <rm_kafka_appid_topics>` for the Redis Monitor if you wish to turn this on.

.. _crawl_api:

Crawl API
---------

The crawl API defines the type of crawl you wish to have the cluster execute. The following properties are available to control the crawling cluster:

**Required**

- **appid:** The application ID that submitted the crawl request. This should be able to uniquely identify who submitted the crawl request

- **crawlid:** A unique crawl ID to track the executed crawl through the system. Crawl ID's are passed along when a maxdepth > 0 is submitted, so anyone can track all of the results from a given seed url. Crawl ID's also serve as a temporary duplication filter, so the same crawl ID will not continue to recrawl pages it has already seen.

- **url:** The initial seed url to begin the crawl from. This should be a properly formatted full path url from which the crawl will begin from

**Optional:**

- **spiderid:** The spider to use for the crawl. This feature allows you to chose the spider you wish to execute the crawl from

- **maxdepth:** The depth at which to continue to crawl new links found on pages

- **domain_max_pages:** Set the maximum number of pages to scrape per domain.

- **priority:** The priority of which to given to the url to be crawled. The Spiders will crawl the highest priorities first.

- **allowed_domains:** A list of domains that the crawl should stay within. For example, putting ``[ "cnn.com" ]`` will only continue to crawl links of that domain.

- **allow_regex:** A list of regular expressions to apply to the links to crawl. Any hits within from any regex will allow that link to be crawled next.

- **deny_regex:** A list of regular expressions that will deny links to be crawled. Any hits from these regular expressions will deny that particular url to be crawled next, as it has precedence over ``allow_regex``.

- **deny_extensions:** A list of extensions to deny crawling, defaults to the extensions provided by Scrapy (which are pretty substantial).

- **expires:** A unix timestamp in seconds since epoch for when the crawl should expire from the system and halt. For example, ``1423669147`` means the crawl will expire when the crawl system machines reach 3:39pm on 02/11/2015. This setting does not account for timezones, so if the machine time is set to EST(-5) and you give a UTC time for three minutes in the future, the crawl will run for 5 hours and 3 mins!

- **useragent:** The header request user agent to fake when scraping the page. If none it defaults to the Scrapy default.

- **cookie:** A cookie string to be used when executing the desired crawl.

- **attrs:** A generic object, allowing an application to pass any type of structured information through the crawl in order to be received on the other side. Useful for applications that would like to pass other data through the crawl.

Examples
^^^^^^^^

Kafka Request:

    ::

        $ python kafka_monitor.py feed '{"url": "http://www.apple.com/", "appid":"testapp", "crawlid":"myapple"}'

    - Submits a single crawl of the homepage of apple.com

    ::

        $ python kafka_monitor.py feed '{"url": "http://www.dmoztools.net/", "appid":"testapp", "crawlid":"abc123", "maxdepth":2, "priority":90}'

    - Submits a dmoztools.net crawl spidering 2 levels deep with a high priority

    ::

        $ python kafka_monitor.py feed '{"url": "http://aol.com/", "appid":"testapp", "crawlid":"a23bbqwewqe", "maxdepth":3, "allowed_domains":["aol.com"], "expires":1423591888}'

    - Submits an aol.com crawl that runs for (at the time) 3 minutes with a large depth of 3, but limits the crawlers to only the ``aol.com`` domain so as to not get lost in the weeds of the internet.

Kafka Response:

    ::

        {
            "body": "<body string omitted>",
            "crawlid": "ABC123",
            "response_url": "http://istresearch.com",
            "url": "http://istresearch.com",
            "status_code": 200,
            "status_msg": "OK",
            "appid": "testapp",
            "links": [],
            "request_headers": {
                "Accept-Language": "en",
                "Accept-Encoding": "gzip,deflate",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Scrapy/1.0.3 (+http://scrapy.org)"
            },
            "attrs": null,
            "timestamp": "2016-01-05T20:14:54.653703"
        }

    All of your crawl response objects will come in a well formatted JSON object like the above example.

.. _action_api:

Action API
----------

The Action API allows for information to be gathered from the current scrape jobs, as well as stopping crawls while they are executing. These commands are executed by the Redis Monitor, and the following properties are available to control.

Required

- **appid:** The application ID that is requesting the action.

- **spiderid:** The spider used for the crawl (in this case, ``link``)

- **action:** The action to take place on the crawl. Options are either ``info`` or ``stop``

- **uuid:** A unique identifier to associate with the action request. This is used for tracking purposes by the applications who submit action requests.

Optional:

- **crawlid:** The unique ``crawlid`` to act upon. Only needed when stopping a crawl or gathering information about a specific crawl.

Examples
^^^^^^^^

.. _info_action:

**Information Action**

The ``info`` action can be conducted in two different ways.

* **Application Info Request**

    Returns application level information about the crawls being conducted. It is a summarization of various ``crawlid`` statistics

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"action": "info", "appid":"testapp", "crawlid":"ABC123", "uuid":"abc12333", "spiderid":"link"}'

    Kafka Response:

        ::

            {
                "server_time": 1452094322,
                "uuid": "abc12333",
                "total_pending": 2092,
                "total_domains": 130,
                "total_crawlids": 2,
                "spiderid": "link",
                "appid": "testapp",
                "crawlids": {
                    "ist234": {
                        "domains": {
                            "google.com": {
                                "low_priority": -9,
                                "high_priority": -9,
                                "total": 1
                            },
                            "twitter.com": {
                                "low_priority": -9,
                                "high_priority": -9,
                                "total": 6
                            },
                            <domains ommitted for clarity>
                        },
                        "distinct_domains": 4,
                        "expires": "1452094703",
                        "total": 84
                    },
                    "ABC123": {
                        "domains": {
                            "ctvnews.ca": {
                                "low_priority": -19,
                                "high_priority": -19,
                                "total": 2
                            },
                            "quora.com": {
                                "low_priority": -29,
                                "high_priority": -29,
                                "total": 1
                            },
                            <domains omitted for clarity>
                        },
                        "distinct_domains": 129,
                        "total": 2008
                    }
                }
            }

    Here, there were two different ``crawlid``'s in the queue for the ``link`` spider that had the specified ``appid``. The json return value is the basic structure seen above that breaks down the different ``crawlid``'s into their domains, total, their high/low priority in the queue, and if they have an expiration.

* **Crawl ID Information Request**

    This is a very specific request that is asking to poll a specific ``crawlid`` in the ``link`` spider queue. Note that this is very similar to the above request but with one extra parameter.

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"action": "info", "appid":"testapp", "crawlid":"ABC123", "uuid":"abc12333", "spiderid":"link"}'

    Kafka Response:

        ::

            {
                "server_time": 1452094050,
                "crawlid": "ABC123",
                "total_pending": 582,
                "total_domains": 22,
                "spiderid": "link",
                "appid": "testapp",
                "domains": {
                    "duckduckgo.com": {
                        "low_priority": -19,
                        "high_priority": -19,
                        "total": 2
                    },
                    "wikipedia.org": {
                        "low_priority": -19,
                        "high_priority": -19,
                        "total": 1
                    },
                    <domains omitted for clarity>
                },
                "uuid": "abc12333"
            }

    The response to the info request is a simple json object that gives statistics about the crawl in the system, and is very similar to the results for an ``appid`` request. Here we can see that there were 582 requests in the queue yet to be crawled of all the same priority.

.. _stop_action:

**Stop Action**

The ``stop`` action is used to abruptly halt the current crawl job. A request takes the following form:

Kafka Request

    ::

        $ python kafka_monitor.py feed '{"action": "stop", "appid":"testapp", "crawlid":"ist234",  "uuid":"1ist234", "spiderid":"link"}'

After the request is processed, only spiders within the cluster currently in progress of downloading a page will continue. All other spiders will not crawl that same ``crawlid`` past a depth of 0 ever again, and all pending requests will be purged from the queue.

Kafka Response:

    ::

        {
            "total_purged": 2008,
            "server_time": 1452095096,
            "crawlid": "ABC123",
            "uuid": "1ist234",
            "spiderid": "link",
            "appid": "testapp",
            "action": "stop"
        }

The json response tells the application that the stop request was successfully completed, and states how many requests were purged from the particular queue.

.. _expire_action:

**Expire Notification**

An ``expire`` notification is generated by the Redis Monitor any time an on going crawl is halted because it has exceeded the time it was supposed to stop. A crawl request that includes an ``expires`` attribute will generate an expire notification when it is stopped by the Redis Monitor.

Kafka Response:

    ::

        {
            "total_expired": 84,
            "server_time": 1452094847,
            "crawlid": "ist234",
            "spiderid": "link",
            "appid": "testapp",
            "action": "expired"
        }

This notification states that the ``crawlid`` of "ist234" expired within the system, and that 84 pending requests were removed.

.. _stats_api:

Stats API
---------

The Stats API allows you to gather metrics, health, and general crawl statistics about your cluster. This is not the same as the `Action API`_, which allows you to alter or gather information about specific jobs within the cluster.

**Required:**

- **uuid:** The unique identifier associated with the request. This is useful for tracking purposes by the application who submitted the request.

- **appid:** The application ID that is requesting the action.

**Optional:**

- **stats:** The type of stats you wish to receive. Defaults to **all**, includes:

    * **all** - Gathers **kafka-monitor**, **redis-monitor**, and **crawler** stats.
    * **kafka-monitor** - Gathers information about the Kafka Monitor
    * **redis-monitor** - Gathers information about the Redis Monitor
    * **crawler** - Gathers information about the crawlers in the cluster. Includes both the **spider**, **machine**, and **queue** information below
    * **spider** - Gathers information about the existing spiders in your cluster
    * **machine** - Gathers information about the different spider machines in your cluster
    * **queue** - Gathers information about the various spider queues within your Redis instance
    * **rest** - Gathers information about the Rest services in your cluster


Stats request results typically have numeric values for dictionary keys, like ``900``, ``3600``, ``86400``, or in the special case ``lifetime``. These numbers indicate **rolling time windows** in seconds for processing throughput. So if you see a value like ``"3600":14`` you can interpret this as `in the last 3600 seconds, the kafka-monitor saw 14 requests"`. In the case of lifetime, it is the total count over the cluster's operation.

Examples
^^^^^^^^

**Kafka Monitor**

Stats Request:

The Kafka Monitor stats gives rolling time windows of incoming requests, failed requests, and individual plugin processing. An example request and response is below.

    ::

        $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"cdefgh1", "stats":"kafka-monitor"}'

Response from Kafka:

    ::

        {
            "server_time": 1452102876,
            "uuid": "cdefghi",
            "nodes": {
                "Madisons-MacBook-Pro-2.local": [
                    "e2be29329410",
                    "60295fece216"
                ]
            },
            "plugins": {
                "ActionHandler": {
                    "604800": 11,
                    "lifetime": 17,
                    "43200": 11,
                    "86400": 11,
                    "21600": 11
                },
                "ScraperHandler": {
                    "604800": 10,
                    "lifetime": 18,
                    "43200": 5,
                    "86400": 10,
                    "21600": 5
                },
                "StatsHandler": {
                    "900": 2,
                    "3600": 2,
                    "604800": 3,
                    "43200": 3,
                    "lifetime": 10,
                    "86400": 3,
                    "21600": 3
                }
            },
            "appid": "testapp",
            "fail": {
                "604800": 4,
                "lifetime": 7,
                "43200": 4,
                "86400": 4,
                "21600": 4
            },
            "stats": "kafka-monitor",
            "total": {
                "900": 2,
                "3600": 2,
                "604800": 28,
                "43200": 23,
                "lifetime": 51,
                "86400": 28,
                "21600": 23
            }
        }

Here we can see the various totals broken down by total, fail, and each loaded plugin.

**Crawler**

A Crawler stats request can consist of rolling time windows of spider stats, machine stats, queue stats, or all of them combined. The following examples serve to illustrate this.

* **Spider**

    Spider stats requests gather information about the crawl results from your cluster, and other information about the number of spiders running.

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"hij1", "stats":"spider"}'

    Kafka Response:

        ::

            {
                "stats": "spider",
                "appid": "testapp",
                "server_time": 1452103525,
                "uuid": "hij1",
                "spiders": {
                    "unique_spider_count": 1,
                    "total_spider_count": 2,
                    "link": {
                        "count": 2,
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                }
            }

    Here, we see that there have been many 200 responses within our collection time periods, but the 504 response rolling time window has dropped off, leaving only the lifetime stat remaining. We can also see that we are currently running 2 ``link`` spiders in the cluster.

    If there were different types of spiders running, we could also see their stats based off of the key within the spider dictionary.

* **Machine**

    Machine stats give information about the crawl machines your spiders are running on. They aggregate the total crawl results for their host, and disregard the spider type(s) running on the machine.

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"hij12", "stats":"machine"}'

    Kafka Response:

        ::

            {
                "stats": "machine",
                "server_time": 1452104037,
                "uuid": "hij12",
                "machines": {
                    "count": 1,
                    "Madisons-MacBook-Pro-2.local": {
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                },
                "appid": "testapp"
            }

    You can see we only have a local machine running those 2 crawlers, but if we had more machines their aggregated stats would be displayed in the same manner.

* **Queue**

    Queue stats give you information about the current queue backlog for each spider, broken down by spider type and domain.

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"stats":"queue", "appid":"test", "uuid":"1234567890"}'

    Kafka Response:

        ::

            {
                "stats": "queue",
                "queues": {
                    "queue_link": {
                        "domains": [
                            {
                                "domain": "istresearch.com",
                                "backlog": 229
                            }
                        ],
                        "spider_backlog": 229,
                        "num_domains": 1
                    },
                    "total_backlog": 229
                },
                "server_time": 1461700519,
                "uuid": "1234567890",
                "appid": "test"
            }

    Here, we have only one active spider queue with one domain. If there were more domains or more spiders that data would be displayed in the same format.

* **Crawler**

    The crawler stat is a combination of the **machine**, **spider**, and **queue** requests.

    Kafka Request:

        ::

            $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"hij1", "stats":"crawler"}'

    Kafka Response:

        ::

            {
                "stats": "crawler",
                "uuid": "hij1",
                "spiders": {
                    "unique_spider_count": 1,
                    "total_spider_count": 2,
                    "link": {
                        "count": 2,
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                },
                "appid": "testapp",
                "server_time": 1452104450,
                "machines": {
                    "count": 1,
                    "Madisons-MacBook-Pro-2.local": {
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                },
                "queues": {
                    "queue_link": {
                        "domains": [
                            {
                                "domain": "istresearch.com",
                                "backlog": 229
                            }
                        ],
                        "spider_backlog": 229,
                        "num_domains": 1
                    },
                    "total_backlog": 229
                }
            }

    There is no new data returned in the **crawler** request, just an aggregation.

**Redis Monitor**

The Redis Monitor stat request returns rolling time window statistics about totals, failures, and plugins like the Kafka Monitor stat requests above.

Stats Request:

    ::

        $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"2hij1", "stats":"redis-monitor"}'

Response from Kafka:

    ::

        {
            "stats": "redis-monitor",
            "uuid": "2hij1",
            "nodes": {
                "Madisons-MacBook-Pro-2.local": [
                    "918145625a1e"
                ]
            },
            "plugins": {
                "ExpireMonitor": {
                    "604800": 2,
                    "lifetime": 2,
                    "43200": 2,
                    "86400": 2,
                    "21600": 2
                },
                "StopMonitor": {
                    "604800": 5,
                    "lifetime": 6,
                    "43200": 5,
                    "86400": 5,
                    "21600": 5
                },
                "StatsMonitor": {
                    "900": 4,
                    "3600": 8,
                    "604800": 9,
                    "43200": 9,
                    "lifetime": 16,
                    "86400": 9,
                    "21600": 9
                },
                "InfoMonitor": {
                    "604800": 6,
                    "lifetime": 11,
                    "43200": 6,
                    "86400": 6,
                    "21600": 6
                }
            },
            "appid": "testapp",
            "server_time": 1452104685,
            "total": {
                "900": 4,
                "3600": 8,
                "604800": 22,
                "43200": 22,
                "lifetime": 35,
                "86400": 22,
                "21600": 22
            }
        }

In the above response, note that the ``fail`` key is omitted because there have been no failures in processing the requests to the redis monitor. All other plugins and totals are represented in the same format as usual.

**Rest**

The Rest stat request returns some basic information about the number of Rest services running within your cluster.

Stats Request:

    ::

        $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"2hij1", "stats":"rest"}'

Response from Kafka:

    ::

        {
          "data": {
            "appid": "testapp",
            "nodes": {
              "scdev": [
                "c4ec35bf9c1a"
              ]
            },
            "server_time": 1489343194,
            "stats": "rest",
            "uuid": "2hij1"
          },
          "error": null,
          "status": "SUCCESS"
        }

The response above shows the number of unique nodes running on each machine. Here, we see only one Rest service is running on the host ``scdev``.

**All**

The All stat request is an aggregation of the **kafka-monitor**, **crawler**, and **redis-monitor** stat requests. It does not contain any new information that the API does not already provide.

Kafka Request:

    ::

        $ python kafka_monitor.py feed '{"appid":"testapp", "uuid":"hij3", "stats":"all"}'

Kafka Response:

    ::

        {
            "kafka-monitor": {
                "nodes": {
                    "Madisons-MacBook-Pro-2.local": [
                        "e2be29329410",
                        "60295fece216"
                    ]
                },
                "fail": {
                    "604800": 4,
                    "lifetime": 7,
                    "43200": 4,
                    "86400": 4,
                    "21600": 4
                },
                "total": {
                    "900": 3,
                    "3600": 9,
                    "604800": 35,
                    "43200": 30,
                    "lifetime": 58,
                    "86400": 35,
                    "21600": 30
                },
                "plugins": {
                    "ActionHandler": {
                        "604800": 11,
                        "lifetime": 17,
                        "43200": 11,
                        "86400": 11,
                        "21600": 11
                    },
                    "ScraperHandler": {
                        "604800": 10,
                        "lifetime": 18,
                        "43200": 5,
                        "86400": 10,
                        "21600": 5
                    },
                    "StatsHandler": {
                        "900": 3,
                        "3600": 9,
                        "604800": 10,
                        "43200": 10,
                        "lifetime": 17,
                        "86400": 10,
                        "21600": 10
                    }
                }
            },
            "stats": "all",
            "uuid": "hij3",
            "redis-monitor": {
                "nodes": {
                    "Madisons-MacBook-Pro-2.local": [
                        "918145625a1e"
                    ]
                },
                "total": {
                    "900": 3,
                    "3600": 9,
                    "604800": 23,
                    "43200": 23,
                    "lifetime": 36,
                    "86400": 23,
                    "21600": 23
                },
                "plugins": {
                    "ExpireMonitor": {
                        "604800": 2,
                        "lifetime": 2,
                        "43200": 2,
                        "86400": 2,
                        "21600": 2
                    },
                    "StopMonitor": {
                        "604800": 5,
                        "lifetime": 6,
                        "43200": 5,
                        "86400": 5,
                        "21600": 5
                    },
                    "StatsMonitor": {
                        "900": 3,
                        "3600": 9,
                        "604800": 10,
                        "43200": 10,
                        "lifetime": 17,
                        "86400": 10,
                        "21600": 10
                    },
                    "InfoMonitor": {
                        "604800": 6,
                        "lifetime": 11,
                        "43200": 6,
                        "86400": 6,
                        "21600": 6
                    }
                }
            },
            "rest": {
                "nodes": {
                    "Madisons-MacBook-Pro-2.local": [
                        "c4ec35bf9c1a"
                    ]
                }
            },
            "appid": "testapp",
            "server_time": 1452105176,
            "crawler": {
                "spiders": {
                    "unique_spider_count": 1,
                    "total_spider_count": 2,
                    "link": {
                        "count": 2,
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                },
                "machines": {
                    "count": 1,
                    "Madisons-MacBook-Pro-2.local": {
                        "200": {
                            "604800": 44,
                            "lifetime": 61,
                            "43200": 39,
                            "86400": 44,
                            "21600": 39
                        },
                        "504": {
                            "lifetime": 4
                        }
                    }
                },
                "queues": {
                    "queue_link": {
                        "domains": [
                            {
                                "domain": "istresearch.com",
                                "backlog": 229
                            }
                        ],
                        "spider_backlog": 229,
                        "num_domains": 1
                    },
                    "total_backlog": 229
                }
            }
        }

.. _zookeeper_api:

Zookeeper API
-------------

The Zookeeper API allows you to update and remove cluster wide blacklists or crawl rates for domains. A **domain** based update will apply a cluster wide throttle against the domain, and a **blacklist** update will apply a cluster wide ban on crawling that domain. Any blacklist domain or crawl setting will automatically be applied to all currently running spiders.

**Required:**

- **uuid:** The unique identifier associated with the request. This is useful for tracking purposes by the application who submitted the request.

- **appid:** The application ID that is requesting the action.

- **action:** The type of action you wish to apply. May be any of the following:

    * **domain-update** - Update or add a domain specific throttle (requires both **hits** and **window** below)
    * **domain-remove** - Removes a cluster wide domain throttle from Zookeeper
    * **blacklist-update** - Completely ban a domain from being crawled by the cluster
    * **blacklist-remove** - Remove a crawl ban within the cluster


- **domain:** The domain to apply the **action** to. This must be the same as the domain portion of the queue key generated in Redis, like ``ebay.com``.

**Optional:**

- **hits:** The number of hits allowed for the domain within the time window

- **window:** The number of seconds the hits is applied to

- **scale:** A scalar between 0 and 1 to apply the number of hits to the domain.

.. note:: For more information on controlling the Crawlers, please see :ref:`here <general_domain_settings>`

Examples
^^^^^^^^

**Domain Update**

Zookeeper Request:

    Updates or adds the domain specific configuration

    ::

        $ python kafka_monitor.py feed '{"uuid":"abc123", "appid":"madisonTest", "action":"domain-update", "domain":"dmoztools.net", "hits":60, "window":60, "scale":0.9}'

Response from Kafka:

    ::

        {
            "action": "domain-update",
            "domain": "dmoztools.net",
            "server_time": 1464402128,
            "uuid": "abc123",
            "appid": "madisonTest"
        }

The response reiterates what has been done to the cluster wide settings.

**Domain Remove**

Zookeeper Request:

    Removes the domain specific configuration

    ::

        $ python kafka_monitor.py feed '{"uuid":"abc123", "appid":"madisonTest", "action":"domain-remove", "domain":"dmoztools.net"}'

Response from Kafka:

    ::

        {
            "action": "domain-remove",
            "domain": "dmoztools.net",
            "server_time": 1464402146,
            "uuid": "abc123",
            "appid": "madisonTest"
        }

The response reiterates what has been done to the cluster wide settings.

**Blacklist Update**

Zookeeper Request:

    Updates or adds to the cluster blacklist

    ::

        $ python kafka_monitor.py feed '{"uuid":"abc123", "appid":"madisonTest", "action":"blacklist-update", "domain":"ebay.com"}'

Response from Kafka:

    ::

        {
            "action": "blacklist-update",
            "domain": "ebay.com",
            "server_time": 1464402173,
            "uuid": "abc123",
            "appid": "madisonTest"
        }

The response reiterates what has been done to the cluster wide settings.

**Blacklist Remove**

Zookeeper Request:

    Removes the blacklist from the cluster, allowing it to revert back to normal operation on that domain

    ::

        $ python kafka_monitor.py feed '{"uuid":"abc123", "appid":"madisonTest", "action":"blacklist-remove", "domain":"ebay.com"}'

Response from Kafka:

    ::

        {
            "action": "blacklist-remove",
            "domain": "ebay.com",
            "server_time": 1464402160,
            "uuid": "abc123",
            "appid": "madisonTest"
        }

The response reiterates what has been done to the cluster wide settings.
