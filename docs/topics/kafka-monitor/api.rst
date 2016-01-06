API
===

The Kafka Monitor consists of a combination of Plugins that allow for API validation and processing of the object received.

Kafka Topics
------------

**Incoming  Kafka Topic:** ``demo.incoming`` - The topic to feed properly formatted cluster requests.

**Outbound Result Kafka Topics:**

- ``demo.crawled_firehouse`` - A firehose topic of all resulting crawls within the system. Any single page crawled by the Scrapy Cluster is guaranteed to come out this pipe.

- ``demo.crawled_<appid>`` - A special topic created for unique applications that submit crawl requests. Any application can listen to their own specific crawl results by listening to the the topic created under the ``appid`` they used to submit the request. These topics are a subset of the crawl firehose data and only contain the results that are applicable to the application who submitted it.

.. note:: The crawl result ``appid`` topics are disabled by default, as they create duplicate data within your Kafka application. You can override the :ref:`setting <c_kafka_appid_topics>` in the Crawler if you wish to turn this on.

- ``demo.outbound_firehose`` - A firehose topic of all the special info, stop, expire, and stat requests. This topic will have all non-crawl data requested from the cluster.

- ``demo.outbound_<appid>`` - A special topic for unique applications to read only their action request data. The ``appid`` used in the submission of the non-crawl API request will be written to both this topic and the firehose topic.

.. note:: The outbound ``appid`` topics are disabled by default, as they create duplicate data within Kafka. You can override the :ref:`setting <rm_kafka_appid_topics>` for the Redis Monitor if you wish to turn this on.


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

- **priority:** The priority of which to given to the url to be crawled. The Spiders will crawl the highest priorities first.

- **allowed_domains:** A list of domains that the crawl should stay within. For example, putting ``[ "cnn.com" ]`` will only continue to crawl links of that domain.

- **allow_regex:** A list of regular expressions to apply to the links to crawl. Any hits within from any regex will allow that link to be crawled next.

- **deny_regex:** A list of regular expressions that will deny links to be crawled. Any hits from these regular expressions will deny that particular url to be crawled next, as it has precedence over allow_regex.

- **deny_extensions:** A list of extensions to deny crawling, defaults to the extensions provided by Scrapy (which are pretty substantial).

- **expires:** A unix timestamp in seconds since epoch for when the crawl should expire from the system and halt. For example, ``1423669147`` means the crawl will expire when the crawl system machines reach 3:39pm on 02/11/2015. This setting does not account for timezones, so if the machine time is set to EST(-5) and you give a UTC time for three minutes in the future, the crawl will run for 5 hours and 3 mins!

- **useragent:** The header request user agent to fake when scraping the page. If none it defaults to the Scrapy default.

- **cookie:** A cookie string to be used when executing the desired crawl.

- **attrs:** A generic object, allowing an application to pass any type of structured information through the crawl in order to be received on the other side. Useful for applications that would like to pass other data through the crawl.

Examples
^^^^^^^^

::

    python kafka_monitor.py feed '{"url": "http://www.apple.com/", "appid":"testapp", "crawlid":"myapple"}'

- Submits a single crawl of the homepage of apple.com

::

    python kafka_monitor.py feed '{"url": "http://www.dmoz.org/", "appid":"testapp", "crawlid":"abc123", "maxdepth":2, "priority":90}'

- Submits a dmoz.org crawl spidering 2 levels deep with a high priority

::

    python kafka_monitor.py feed '{"url": "http://aol.com/", "appid":"testapp", "crawlid":"a23bbqwewqe", "maxdepth":3, "allowed_domains":["aol.com"], "expires":1423591888}'

- Submits an aol.com crawl that runs for (at the time) 3 minutes with a large depth of 3, but limits the crawlers to only the ``aol.com`` domain so as to not get lost in the weeds of the internet.

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

**Information Action**

The ``info`` action can be conducted in two different ways.

Application Info Request

    ::

        python kafka_monitor.py feed '{"action": "info", "appid":"testapp", "crawlid":"ABC123", "uuid":"abc12333", "spiderid":"link"}'

    This returns back all information available about the ``appid`` in question. It is a summation of the various ``crawlid`` statistics.

    Application Info Response

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

Crawl ID Info Request

    ::

        python kafka_monitor.py feed '{"action": "info", "appid":"testapp", "crawlid":"ABC123", "uuid":"abc12333", "spiderid":"link"}'

    This is a very specific request that is asking to poll a specific ``crawlid`` in the ``link`` spider queue. Note that this is very similar to the above request but with one extra parameter. The following example response is generated:

Crawl ID Info Response from Kafka

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

**Stop Action**

The ``stop`` action is used to abruptly halt the current crawl job. A request takes the following form:

Stop Request

    ::

        python kafka_monitor.py feed '{"action": "stop", "appid":"testapp", "crawlid":"ist234",  "uuid":"1ist234", "spiderid":"link"}'

    After the request is processed, only current spiders within the cluster currently in progress of downloading a page will continue. All other spiders will not crawl that same ``crawlid`` past a depth of 0 ever again, and all pending requests will be purged from the queue.

Stop Response from Kafka

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

**Expire Notification**

An ``expire`` notification is generated by the Redis Monitor any time an on going crawl is halted because it has exceeded the time it was supposed to stop. A crawl request that includes an ``expires`` attribute will generate an expire notification when it is stopped by the Redis Monitor.

Expire Notification from Kafka

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

Stats API
--------

Examples
^^^^^^^^
























scraper\_schema.json
^^^^^^^^^^^^^^^^^^

The Scraper Schema defines the level of interaction an application gets with the Scrapy Cluster. The following properties are available to control the crawling cluster:




action\_schema.json
^^^^^^^^^^^^^^^^^^

The Action Schema allows for extra information to be gathered from the Scrapy Cluster, as well as stopping crawls while they are executing. These commands are executed by the Redis Monitor, and the following properties are available to control.



Redis Monitor
-------------

All requests adhere to the following three Kafka topics for input and output:

Incoming Action Request Kafka Topic:

- ``demo.inbound_actions`` - The topic to feed properly formatted action requests to

Outbound Action Result Kafka Topics:

- ``demo.outbound_firehose`` - A firehose topic of all resulting actions within the system. Any single action conducted by the Redis Monitor is guaranteed to come out this pipe.

- ``demo.outbound_<appid>`` - A special topic created for unique applications that submit action requests. Any application can listen to their own specific action results by listening to the the topic created under the ``appid`` they used to submit the request. These topics are a subset of the action firehose data and only contain the results that are applicable to the application who submitted it.



Examples
--------

Example Crawl Requests:



Example Crawl Request Output from the kafkadump utility:

::

    {
        u'body': u'<real raw html source here>',
        u'crawlid': u'abc1234',
        u'links': [],
        u'response_url': u'http://www.dmoz.org/Recreation/Food/',
        u'url': u'http://www.dmoz.org/Recreation/Food/',
        u'status_code': 200,
        u'status_msg': u'OK',
        u'appid': u'testapp',
        u'headers': {
            u'Cteonnt-Length': [u'40707'],
            u'Content-Language': [u'en'],
            u'Set-Cookie': [u'JSESSIONID=FB02F2BBDBDBDDE8FBE5E1B81B4219E6; Path=/'],
            u'Server': [u'Apache'],
            u'Date': [u'Mon, 27 Apr 2015 21:26:24 GMT'],
            u'Content-Type': [u'text/html;charset=UTF-8']
        },
        u'attrs': {},
        u'timestamp': u'2015-04-27T21:26:24.095468'
    }