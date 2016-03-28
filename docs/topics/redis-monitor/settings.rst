Settings
================

This page covers the various settings contained within the Redis Monitor. The sections are broken down by functional component.

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

**KAFKA_CONN_TIMEOUT**

Default: ``5``

How long to wait (in seconds) before timing out when trying to connect to the Kafka cluster.

.. _rm_kafka_appid_topics:

**KAFKA_APPID_TOPICS**

Default: ``False``

Flag to send data to both the firehose and Application ID specific Kafka topics. If set to ``True``, results will be sent to both the ``demo.outbound_firehose`` **and** ``demo.outbound_<appid>`` Kafka topics, where ``<appid>`` is the Application ID used to submit the request. This is useful if you have many applications utilizing your cluster but only would like to listen to results for your specific application.

Plugins
-------

**PLUGIN_DIR**

Default: ``'plugins/'``

The folder containing all of the Kafka Monitor plugins.

.. _rm_plugins:

**PLUGINS**

Default:

::

    {
        'plugins.info_monitor.InfoMonitor': 100,
        'plugins.stop_monitor.StopMonitor': 200,
        'plugins.expire_monitor.ExpireMonitor': 300,
        'plugins.stats_monitor.StatsMonitor': 400,
    }

The default plugins loaded for the Redis Monitor. The syntax for this dictionary of settings is ``'<folder>.<file>.<class_name>': <rank>``. Where lower ranked plugin API's are validated first.

Logging
-------

**LOGGER_NAME**

Default: ``'redis-monitor'``

The logger name.

**LOG_DIR**

Default: ``'logs'``

The directory to write logs into. Only applicable when ``LOG_STDOUT`` is set to ``False``.

**LOG_FILE**

Default: ``'redis_monitor.log'``

The file to write the logs into. When this file rolls it will have ``.1`` or ``.2`` appended to the file name. Only applicable when ``LOG_STDOUT`` is set to ``False``.

**LOG_MAX_BYTES**

Default: ``10 * 1024 * 1024``

The maximum number of bytes to keep in the file based log before it is rolled.

**LOG_BACKUPS**

Default: ``5``

The number of rolled file logs to keep before data is discarded. A setting of ``5`` here means that there will be one main log and five rolled logs on the system, generating six log files total.

**LOG_STDOUT**

Default: ``True``

Log to standard out. If set to ``False``, will write logs to the file given by the ``LOG_DIR/LOG_FILE``

**LOG_JSON**

Default: ``False``

Log messages will be written in JSON instead of standard text messages.

**LOG_LEVEL**

Default: ``'INFO'``

The log level designated to the logger. Will write all logs of a certain level and higher.

.. note:: More information about logging can be found in the utilities :ref:`Log Factory <log_factory>` documentation.

Stats
-----

**STATS_TOTAL**

Default: ``True``

Calculate total receive and fail stats for the Redis Monitor.

**STATS_PLUGINS**

Default: ``True``

Calculate total receive and fail stats for each individual plugin within the Redis Monitor.

**STATS_CYCLE**

Default: ``5``

How often to check for expired keys and to roll the time window when doing stats collection.

**STATS_DUMP**

Default: ``60``

Dump stats to the logger every X seconds. If set to ``0`` will not dump statistics.

**STATS_DUMP_CRAWL**

Default: ``True``

Dump :ref:`statistics <c_stats>` collected by the Scrapy Cluster Crawlers. The crawlers may be spread out across many machines, and the log dump of their statistics is consolidated and done in a single place where the Redis Monitor is installed. Will be dumped at the same interval the ``STATS_DUMP`` is set to.

**STATS_DUMP_QUEUE**

Default: ``True``

Dump queue metrics about the real time backlog of the Scrapy Cluster Crawlers. This includes queue length, and total number of domains currently in the backlog. Will be dumped at the same interval the ``STATS_DUMP`` is set to.

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
