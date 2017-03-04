Plugins
=======

Plugins give the Redis Monitor additional functionality for monitoring your Redis instance. They evaluate all the keys within your Redis instance, and act upon the key/value when the expression matches.

The Redis Monitor loads the desired :ref:`Plugins <rm_plugins>` in the order specified in the settings file, and will evaluate them starting with the lowest ranked plugin.

Each plugin consists of a class inherited from the base plugin class, and a couple different methods for setup and processing.

Default Plugins
---------------

By default, plugins live in the ``plugins`` directory within the Redis Monitor. The following plugins come standard.

Info Monitor
^^^^^^^^^^^^

The ``info_monitor.py`` provides all of the Information Action responses from Scrapy Cluster.

For more information please see the :ref:`Information Action <info_action>` API.

Expire Monitor
^^^^^^^^^^^^^^

The ``expire_monitor.py`` provides Scrapy Cluster the ability to continuously monitor crawls that need to be expired at a designated time.

For more information please see the :ref:`Expire Action <expire_action>` API.

Stop Monitor
^^^^^^^^^^^^

The ``stop_monitor.py`` allows API requests to stop a crawl that is in process.

For more information please see the :ref:`Stop Action <stop_action>` API.

Stats Monitor
^^^^^^^^^^^^^

The ``stats_monitor.py`` gives access to stats collected across all three major components of Scrapy Cluster.

For more information please see the :ref:`Stats API <stats_api>`

Zookeeper Monitor
^^^^^^^^^^^^^^^^^

The ``zookeeper_monitor.py`` adds the ability to update the crawler blacklist once the request is recieved.

For more information please see the :ref:`Zookeeper API <zookeeper_api>`

.. _rm_extension:

Extension
---------

Creating your own Plugin for the Redis Monitor allows you to add new functionality to monitor your Redis instance, and act when certain keys are seen. You will need to add a new file in the ``plugins`` directory that will define your Redis key regular expression and how you process your results.

If you would like only default functionality, the following python code template should be used when creating a new plugin:

**plugins/my_monitor.py**

::

    from base_monitor import BaseMonitor


    class MyMonitor(BaseMonitor):
        '''
        My custom monitor
        '''

        regex = "<my_key_regex_here>"

        def setup(self, settings):
            '''
            Setup the handler

            @param settings: The loaded settings file
            '''
            pass

        def check_precondition(self, key, value):
            '''
            Override if special conditions need to be met
            '''
            pass

        def handle(self, key, value):
            '''
            Processes a vaild action info request

            @param key: The key that matched the request
            @param value: The value associated with the key
            '''
            pass

        def close(self):
            '''
            Called when the over arching Redis Monitor is closed
            '''
            pass

If you would like to send messages back out to Kafka, use the following template.

::

    from kafka_base_monitor import KafkaBaseMonitor


    class MyMonitor(KafkaBaseMonitor):

        regex = "<my_key_regex_here>"

        def setup(self, settings):
            '''
            Setup kafka
            '''
            KafkaBaseMonitor.setup(self, settings)

        def check_precondition(self, key, value):
            '''
            Override if special conditions need to be met
            '''
            pass

        def handle(self, key, value):
            '''
            Processes a vaild action info request

            @param key: The key that matched the request
            @param value: The value associated with the key
            '''
            # custom code here builds a result dictionary `results`
            # ...
            # now, send to kafka
            if self._send_to_kafka(results):
                self.logger.info('Sent results to kafka')
            else:
                self.logger.error('Failed to send results to kafka')

Regardless of either template you choose, you will inherit from a base class that provides easy integration into the plugin framework. The ``regex`` variable at the top of each class should contain the Redis `key <http://redis.io/commands/KEYS>`_ pattern your plugin wishes to operate on.

The ``setup()`` method is passed a dictionary created from the settings loaded from your local and default settings files. You can set up connections, variables, or other items here to be used in your handle method.

The ``check_precondition()`` method is called for every potential key match, and gives the plugin the opportunity to determine whether it actually wants to process that object at the given time. For example, this is used in the ``expire_monitor.py`` file to check whether the expire timestamp value stored in the key is greater than the current time. If it is, return ``True`` and your plugin's ``handle()`` method will be called, otherwise, return ``False``.

When the ``handle()`` method is called, it is passed both the key that matched your pattern, and the value stored within the key. You are free to do whatever you want with the data, but once you are done the key is removed from Redis. The key will be removed if an exception is thrown consitently when trying to process our action within any of the two plugin methods, or if the ``handle()`` method completes as normal. This is to prevent reprocessing of matched keys, so use the ``check_precondition()`` method to prevent a key from getting deleted too early.

If you need to tear down anything within your plugin, you can use the ``close()`` method to ensure proper clean up of the data inside the plugin. Once you are ready to add your plugin to the Redis Monitor, edit your ``localsettings.py`` file and add the following lines.

::

    PLUGINS = {
        'plugins.my_monitor.MyMonitor': 500,
    }

You have now told the Redis Monitor to not only load the default plugins, but to add your new plugin as well with a rank of 500. Restart the Redis Monitor for it to take effect.

Additional Info
^^^^^^^^^^^^^^^

Every Redis Monitor plugin is provided a Scrapy Cluster logger, under the variable name ``self.logger``. You can use this logger to generate debug, info, warnings, or any other log output you need to help gather information from your plugin. This is the same logger that the core Redis Monitor uses, so your desired settings will be preserved.

Each Plugin is also provided a default Redis Connection variable, named ``self.redis_conn``. This variable is an instance of a Redis Connection thanks to the `redis-py <https://redis-py.readthedocs.org>`_ library and can be used to manipulate anything within your Redis instance.





