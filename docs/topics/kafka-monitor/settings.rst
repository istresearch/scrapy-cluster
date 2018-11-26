Settings
================

This page covers all of the various settings contained within the Kafka Monitor. The sections are broken down by functional component.

Core
----

**SLEEP_TIME**

Default: ``0.01``

The number of seconds the main process will sleep between checking for new crawl requests to take care of.

**HEARTBEAT_TIMEOUT**

Default: ``120``

The amount of time the statistics key the Kafka Monitor instance lives to self identify to the rest of the cluster. Used for retrieving stats about the number of Kafka Monitor instances currently running.

Redis
-----

**REDIS_HOST**

Default: ``'localhost'``

The Redis host.

**REDIS_PORT**

Default: ``6379``

The port to use when connecting to the ``REDIS_HOST``.

**REDIS_DB**

Default: ``0``

The Redis database to use when connecting to the ``REDIS_HOST``.

**REDIS_PASSWORD**

Default: ``None``

The password to use when connecting to the ``REDIS_HOST``.

**REDIS_SOCKET_TIMEOUT**

Default: ``10``

The number of seconds to wait while establishing a TCP connection, or to wait for a response from an existing TCP connection before timing out.

Kafka
-----

**KAFKA_HOSTS**

Default: ``'localhost:9092'``

The Kafka host. May have multiple hosts separated by commas within the single string like ``'h1:9092,h2:9092'``.

**KAFKA_INCOMING_TOPIC**

Default: ``'demo.incoming'``

The Kafka Topic to read API requests from.

**KAFKA_GROUP**

Default: ``'demo-group'``

The Kafka Group to identify the consumer.

**KAFKA_FEED_TIMEOUT**

Default: ``5``

How long to wait (in seconds) before timing out when trying to feed a JSON string into the ``KAFKA_INCOMING_TOPIC``

**KAFKA_CONSUMER_AUTO_OFFSET_RESET**

Default: ``'earliest'``

When the Kafka Consumer encounters and unexpected error, move the consumer offset to the 'latest' new message, or the 'earliest' available.

**KAFKA_CONSUMER_TIMEOUT**

Default: ``50``

Time in ms spent to wait for a new message during a ``feed`` call that expects a response from the Redis Monitor

**KAFKA_CONSUMER_COMMIT_INTERVAL_MS**

Default: ``5000``

How often to commit Kafka Consumer offsets to the Kafka Cluster

**KAFKA_CONSUMER_AUTO_COMMIT_ENABLE**

Default: ``True``

Automatically commit Kafka Consumer offsets.

**KAFKA_CONSUMER_FETCH_MESSAGE_MAX_BYTES**

Default: ``10 * 1024 * 1024``

The maximum size of a single message to be consumed by the Kafka Consumer. Defaults to 10 MB

**KAFKA_PRODUCER_BATCH_LINGER_MS**

Default: ``25``

The time to wait between batching multiple requests into a single one sent to the Kafka cluster.

**KAFKA_PRODUCER_BUFFER_BYTES**

Default: ``4 * 1024 * 1024``

The size of the TCP send buffer when transmitting data to Kafka

Plugins
-------

**PLUGIN_DIR**

Default: ``'plugins/'``

The folder containing all of the Kafka Monitor plugins.

.. _km_plugins:

**PLUGINS**

Default:

::

    {
        'plugins.scraper_handler.ScraperHandler': 100,
        'plugins.action_handler.ActionHandler': 200,
        'plugins.stats_handler.StatsHandler': 300,
        'plugins.zookeeper_handler.ZookeeperHandler': 400,
    }

The default plugins loaded for the Kafka Monitor. The syntax for this dictionary of settings is ``'<folder>.<file>.<class_name>': <rank>``. Where lower ranked plugin API's are validated first.

Logging
-------

**LOGGER_NAME**

Default: ``'kafka-monitor'``

The logger name.

**LOG_DIR**

Default: ``'logs'``

The directory to write logs into. Only applicable when ``LOG_STDOUT`` is set to ``False``.

**LOG_FILE**

Default: ``'kafka_monitor.log'``

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

Calculate total receive and fail stats for the Kafka Monitor.

**STATS_PLUGINS**

Default: ``True``

Calculate total receive and fail stats for each individual plugin within the Kafka Monitor.

**STATS_CYCLE**

Default: ``5``

How often to check for expired keys and to roll the time window when doing stats collection.

**STATS_DUMP**

Default: ``60``

Dump stats to the logger every X seconds. If set to ``0`` will not dump statistics.

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
