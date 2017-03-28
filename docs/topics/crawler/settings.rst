Settings
========

The following settings are Scrapy Cluster specific. For all other Scrapy settings please refer to the official Scrapy documentation `here <http://doc.scrapy.org/en/latest/topics/settings.html>`_.

Redis
-----

**REDIS_HOST**

Default: ``'localhost'``

The Redis host.

**REDIS_PORT**

Default: ``6379``

The port to use when connecting to the ``REDIS_HOST``.

Kafka
-----

**KAFKA_HOSTS**

Default: ``'localhost:9092'``

The Kafka host. May have multiple hosts separated by commas within the single string like ``'h1:9092,h2:9092'``.

**KAFKA_TOPIC_PREFIX**

Default: ``'demo'``

The Kafka Topic prefix to use when generating the outbound Kafka topics.

.. _c_kafka_appid_topics:

**KAFKA_APPID_TOPICS**

Default: ``False``

Flag to send data to both the firehose and Application ID specific Kafka topics. If set to ``True``, results will be sent to both the ``demo.outbound_firehose`` **and** ``demo.outbound_<appid>`` Kafka topics, where ``<appid>`` is the Application ID used to submit the request. This is useful if you have many applications utilizing your cluster but only would like to listen to results for your specific application.

.. _c_base64:

**KAFKA_BASE_64_ENCODE**

Default: ``False``

`Base64 <https://en.wikipedia.org/wiki/Base64>`_ encode the raw crawl body from the crawlers. This is useful when crawling malformed utf8 encoded pages, where json encoding throws an error. If an error occurs when encoding the crawl object in the item pipeline, there will be an error thrown and the result will be dropped.

Zookeeper
---------

**ZOOKEEPER_ASSIGN_PATH**

Default: ``/scrapy-cluster/crawler/``

The location to store Scrapy Cluster domain specific configuration within Zookeeper

**ZOOKEEPER_ID**

Default: ``all``

The file identifier to read crawler specific configuration from. This file is located within the ``ZOOKEEPER_ASSIGN_PATH`` folder above.

**ZOOKEEPER_HOSTS**

Default: ``localhost:2181``

The zookeeper host to connect to.

Scheduler
---------

**SCHEDULER_PERSIST**

Default: ``True``

Determines whether to clear all Redis Queues when the Scrapy Scheduler is shut down. This will wipe all domain queues for a particular spider type.

**SCHEDULER_QUEUE_REFRESH**

Default: ``10``

How many seconds to wait before checking for new domain queues. This is also dictated by internal Scrapy processes, so setting this any lower does not guarantee a quicker refresh time.

.. _c_throttle:

Throttle
--------

**QUEUE_HITS**

Default: ``10``

When encountering an unknown domain, throttle the domain to X number of hits within the ``QUEUE_WINDOW``

**QUEUE_WINDOW**

Default: ``60``

The number of seconds to count and retain cluster hits for a particular domain.

**QUEUE_MODERATED**

Default: ``True``

Moderates the outbound domain request flow to evenly spread the ``QUEUE_HITS`` throughout the ``QUEUE_WINDOW``.

.. _dupe_timeout:

**DUPEFILTER_TIMEOUT**

Default: ``600``

Number of seconds to keep **crawlid** specific duplication filters around after the latest crawl with that id has been conducted. Putting this setting too low may allow crawl jobs to crawl the same page due to the duplication filter being wiped out.

.. _page_per_host_filter:

**PAGE_PER_HOST_LIMIT**

Default: ``None``

The maximum number of pages to crawl for each domain.

**PAGE_PER_HOST_LIMIT_TIMEOUT**

Default: ``600``

Number of seconds to keep **crawlid** specific maximum crawled pages limit filters around after the latest crawl with that id has been conducted. Putting this setting too low may allow crawl jobs to crawl more pages than expected due to the pages limit filter being wiped out.

**SCHEDULER_IP_REFRESH**

Default: ``60``

The number of seconds to wait between refreshing the Scrapy process's public IP address. Used when doing :ref:`IP <throttle_mechanism>` based throttling.

**PUBLIC_IP_URL**

Default: ``'http://ip.42.pl/raw'``

The default URL to grab the Crawler's public IP Address from.

**IP_ADDR_REGEX**

Default: ``(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})``

The regular expression used to find the Crawler's public IP Address from the ``PUBLIC_IP_URL`` response. The first element from the results of this regex will be used as the ip address.

**SCHEDULER_TYPE_ENABLED**

Default: ``True``

If set to true, the crawling process's spider type is taken into consideration when throttling the crawling cluster.

**SCHEDULER_IP_ENABLED**

Default: ``True``

If set to true, the crawling process's public IP Address is taken into consideration when throttling the crawling cluster.

.. note:: For more information about Type and IP throttling, please see the :ref:`throttle <throttle_mechanism>` documentation.

**SCHEUDLER_ITEM_RETRIES**

Default: ``2``

Number of cycles through all known domain queues the Scheduler will take before the Spider is considered idle and waits for Scrapy to retry processing a request.

Logging
-------

**SC_LOGGER_NAME**

Default: ``'sc-crawler'``

The Scrapy Cluster logger name.

**SC_LOG_DIR**

Default: ``'logs'``

The directory to write logs into. Only applicable when ``SC_LOG_STDOUT`` is set to ``False``.

**SC_LOG_FILE**

Default: ``'sc_crawler.log'``

The file to write the logs into. When this file rolls it will have ``.1`` or ``.2`` appended to the file name. Only applicable when ``SC_LOG_STDOUT`` is set to ``False``.

**SC_LOG_MAX_BYTES**

Default: ``10 * 1024 * 1024``

The maximum number of bytes to keep in the file based log before it is rolled.

**SC_LOG_BACKUPS**

Default: ``5``

The number of rolled file logs to keep before data is discarded. A setting of ``5`` here means that there will be one main log and five rolled logs on the system, totaling six log files.

**SC_LOG_STDOUT**

Default: ``True``

Log to standard out. If set to ``False``, will write logs to the file given by the ``LOG_DIR/LOG_FILE``

**SC_LOG_JSON**

Default: ``False``

Log messages will be written in JSON instead of standard text messages.

**SC_LOG_LEVEL**

Default: ``'INFO'``

The log level designated to the logger. Will write all logs of a certain level and higher.

.. note:: More information about logging can be found in the utilities :ref:`Log Factory <log_factory>` documentation.

.. _c_stats:

Stats
-----

**STATS_STATUS_CODES**

Default: ``True``

Collect Response status code metrics

**STATUS_RESPONSE_CODES**

Default:

::

    [
        200,
        404,
        403,
        504,
    ]

Determines the different Response status codes to collect metrics against if metrics collection is turned on.

**STATS_CYCLE**

Default: ``5``

How often to check for expired keys and to roll the time window when doing stats collection.

**STATS_TIMES**

Default:

::

    [
        'SECONDS_15_MINUTE',
        'SECONDS_1_HOUR',
        'SECONDS_6_HOUR',
        'SECONDS_12_HOUR',
        'SECONDS_1_DAY',
        'SECONDS_1_WEEK',
    ]

Rolling time window settings for statistics collection, the above settings indicate stats will be collected for the past 15 minutes, the past hour, the past 6 hours, etc.

.. note:: For more information about stats collection, please see the :ref:`stats_collector` documentation.
