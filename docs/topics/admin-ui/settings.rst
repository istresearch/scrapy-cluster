Settings
========

This page covers the various settings contained within the Admin UI service. The sections are broken down by functional component.

Core
----

**FLASK_LOGGING_ENABLED**

Default: ``True``

Enable Flask application logging, independent of Scrapy Cluster logging.

**FLASK_PORT**

Default: ``5343``

The default port for the Rest service to listen on. The abbreviation ``SC`` equals ``5343`` in hexidecimal.

**DEBUG**

Default: ``False``

Turns on Flask debugging while running the application.

**STAT_REQ_FREQ**

Default: ``910``

The amount of time to wait in between statistics requests to build graphs or gather other metrics

**STAT_START_DELAY**

Default: ``10``

The amount of time to wait before first executing stats requests to the rest endpoint


**DAEMON_THREAD_JOIN_TIMEOUT**

Default: ``10``

The amount of time the UI will wait to join daemon threads it spawns to conduct background tasks

Rest
----

**REST_HOST**

Default: ``'localhost:5343'``


Logging
-------

**LOGGER_NAME**

Default: ``'ui-service'``

The logger name.

**LOG_DIR**

Default: ``'logs'``

The directory to write logs into. Only applicable when ``LOG_STDOUT`` is set to ``False``.

**LOG_FILE**

Default: ``'ui_service.log'``

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
