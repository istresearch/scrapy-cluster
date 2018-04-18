.. _debugging:

Troubleshooting
===============

This document will help you in debugging problems seen in the components of Scrapy Cluster, by utilizing the :ref:`Log Factory <log_factory>` utility class.

General Debugging
-----------------

Logging
^^^^^^^^^^

For all three components, you may set the Scrapy Cluster log level for the component to ``DEBUG`` in order to see more verbose output. These logs are hopefully verbose enough to help you figure out where things are breaking, or help you trace through the code to find where the bug lies.

    * **Kafka Monitor** - use the ``--log-level DEBUG`` flag when executing either the ``run`` or ``feed`` command, or in your ``localsettings.py`` set ``LOG_LEVEL="DEBUG"``

    * **Redis Monitor** - use the ``--log-level DEBUG`` flag when executing either the main command, or in your ``localsettings.py`` set ``LOG_LEVEL="DEBUG"``

    * **Crawler** - use the ``localsettings.py`` file to set ``SC_LOG_LEVEL="DEBUG"``. Note this is **different** so as to not interfere with normal Scrapy log levels.

    * **Rest** - use the ``--log-level DEBUG`` flag when executing either the main command, or in your ``localsettings.py`` set ``LOG_LEVEL="DEBUG"``

You can alter the Log Factory settings to log your data in JSON, to write your Scrapy Cluster logs to a file, or to write only important ``CRITICAL`` log messages to your desired output. JSON based logs will show all of the extra data passed into the log message, and can be useful for debugging python dictionaries without contaminating your log message itself.

.. note:: Command line arguments take precedence over ``localsettings.py``, which take precedence over the default settings. This is useful if you need quick command line changes to your logging output, but want to keep production settings the same.

Offline Testing
^^^^^^^^^^^^^^^

All of the different components in Scrapy Cluster have offline tests, to ensure correct method functionality and error handling. You can run all of the offline tests in the top level of this project by issuing the following command.

::

    $ ./run_offline_tests.sh

If you are making modifications to core components, or wish to add new functionality to Scrapy Cluster, please ensure that all the tests pass for your component. Upgrades and changes happen, but these tests should always pass in the end.

If you are modifying a single component, you can run its individual offline test by using `nose <http://nose.readthedocs.org/en/latest/>`_. The following commands should be run from within the component you are interested in, and will run both the nosetests and provide code coverage information to you:

::

    # utilities
    nosetests -v --with-coverage --cover-erase

    # kafka monitor
    nosetests -v --with-coverage --cover-erase --cover-package=../kafka-monitor/

    # redis monitor
    nosetests -v --with-coverage --cover-erase --cover-package=../redis-monitor/

    # crawler
    nosetests -v --with-coverage --cover-erase --cover-package=crawling/

    # rest
    nosetests -v --with-coverage --cover-erase --cover-package=../rest/

This runs the individual component's offline tests. You can do this in the Kafka Monitor, Crawler, Redis Monitor, Rest, and the Utilities folders.

Online Testing
^^^^^^^^^^^^^^

Online tests serve to ensure functionality between components is working smoothly. These 'integration tests' are strictly for testing and debugging new setups one component at a time.

Running ``./run_online_tests.sh`` right away when you download Scrapy Cluster will most likely result in a failure. Instead, you should create small ``localsettings.py`` files in the three core components that will override Scrapy Cluster's built in default settings. A typical file might look like this:

::

    REDIS_HOST = '<your_host>'
    KAFKA_HOSTS = '<your_host>:9092'

Where ``<your_host>`` is the machine where Redis, Kafka, or Zookeeper would reside. Once you set this up, each of the three main components can run their online tests like so:

::

    $ python tests/online.py -v

If your system is properly configured you will see the test pass, otherwise, the debug and error log output should indicate what is failing.

.. note:: The Crawler online test takes a little over 20 seconds to complete, so be patient!

If you would like to debug the Utilities package, the online test is slightly different as we need to pass the redis host as a flag.

::

    python tests/online.py -r <your_host>

If all your online tests pass, that means that the Scrapy Cluster component was successfully able to talk with its dependencies and deems itself operational.


Kafka Monitor
^^^^^^^^^^^^^

If you need to add extra lines to debug the Kafka Monitor, the LogFactory logger is in the following variables.

* **Core**: ``self.logger``
* **Plugins**: ``self.logger``

**Typical Issues**

* Cannot connect to Redis/Kafka, look into your network configuration.
* Kafka is in an unhappy state, debugging should be done for Kafka.

Crawler
^^^^^^^

If you need to add extra lines to debug an item within the Scrapy Project, you can find the LogFactory logger in the following variables.

* **Scheduler**: ``self.logger``
* **Kafka and Logging Pipelines**: ``self.logger``
* **Spiders**: ``self._logger`` (We can't override the spider's ``self.logger``)
* **Log Retry Middleware**: ``self.logger``

.. note:: It is important that you always use the ``LogFactory.get_instance()`` method if you need another Scrapy Cluster logger elsewhere in your project. Due to the way Twisted instantiates each of the threads you can end up with multiple loggers which ends up duplicating your log data.

The LogFactory does not interfere with the Scrapy based logger, so if you are more comfortable using it then you are free to tinker with the Scrapy logging settings `here <http://doc.scrapy.org/en/latest/topics/logging.html>`_.

**Typical Issues**

* Continuous 504 Timeouts may indicate your spider machines cannot reach the public internet
* Cannot connect to Redis/Kafka/Zookeeper, look into your network configuration.
* Lots of errors when writing to a Kafka topic - Kafka is in an unhappy state and should be looked at.

Redis Monitor
^^^^^^^^^^^^^

To add further debug lines within the Redis Monitor, you can use the following variables within the classes.

* **Core**: ``self.logger``
* **Plugins**: ``self.logger``

**Typical Issues**

* Cannot connect to Redis/Kafka, look into your network configuration.
* Lots of errors when writing to a Kafka topic - Kafka is in an unhappy state and should be looked at.

Rest
^^^^

To add further debug lines within the Rest, you can use the following variables within the classes.

* **Core**: ``self.logger``

**Typical Issues**

* Cannot connect to Redis/Kafka, look into your network configuration.
* Improperly formatted requests - please ensure your request matches either the Kafka Monitor or Rest service API
* All Redis Monitor requests come back as a ``poll_id`` - Ensure you have the Kafka Monitor and Redis Monitor properly set up and running.

Utilities
^^^^^^^^^

The utilities do not instantiate a LogFactory based logger, as that would create a cyclic dependency on itself. Instead, you can use your standard logging methods or print statements to debug things you think are not working within the utilities.

If you wish to test your changes, you can run the offline/online tests and then run

::

    python setup.py install

To overwrite your existing pip package installation with your updated code.

Data Stack
----------

This project is not meant to help users in debugging the big data applications it relies upon, as they do it best. You should refer to the following references for more help.

Zookeeper
^^^^^^^^^

You should refer to the official `Zookeeper <https://cwiki.apache.org/confluence/display/ZOOKEEPER/Index>`_ documentation for help in setting up Zookeeper. From all your machines, you should be able to run the following command to talk to Zookeeper

::

    $ echo ruok | nc scdev 2181
    imok

**Main Port:** 2181

Kafka
^^^^^

Please refer to the official `Kafka <http://kafka.apache.org/documentation.html>`_ documentation for instructions and help on setting up your Kafka cluster. You can use the following command in the Kafka Monitor to check access to your Kafka machines. For example:

::

    $ python kafkadump.py list
    2016-01-04 17:30:03,634 [kafkadump] INFO: Connected to scdev:9092
    Topics:
    - demo.outbound_firehose
    - demo.outbound_testapp
    - demo.crawled_firehose
    - demo.outbound_testApp
    - demo_test.outbound_firehose
    - demo_test.crawled_firehose
    - demo.outbound_testapp
    - demo.incoming

**Main Port:** 9092

Redis
^^^^^

Refer to the official `Redis <http://redis.io/documentation>`_ documentation for more information on how to set up your Redis instance. A simple test of your redis instance can be done with the following commands.

::

    $ vagrant ssh
    vagrant@scdev:~$ /opt/redis/default/bin/redis-cli
    127.0.0.1:6379> info
    # Server
    redis_version:3.0.5
    redis_git_sha1:00000000
    redis_git_dirty:0
    redis_build_id:71f1349fddec31b1
    redis_mode:standalone
    os:Linux 3.13.0-66-generic x86_64
    ...

**Main Port:** 6379

