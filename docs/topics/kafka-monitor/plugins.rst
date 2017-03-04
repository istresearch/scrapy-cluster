Plugins
=======

Plugins serve as a way to validate and process incoming JSON to the Kafka Monitor. Each plugin consists of the JSON Schema it will validate against, and the resulting code to process a valid object.

The Kafka Monitor loads the desired :ref:`Plugins <km_plugins>` in the order specified in the settings file, and will evaluate them starting with the lowest ranked plugin.

Each plugin consists of a class inherited from the base plugin class, and one or two python methods to accommodate setup and processing.

Default Plugins
---------------

By default, plugins live in the ``plugins`` directory within the Kafka Monitor. The following plugins come with the Kafka Monitor.

Action Handler
^^^^^^^^^^^^^^

The ``action_handler.py`` and the ``action_schema.json`` create an actions API that accepts information and stop requests about specific crawls within Scrapy Cluster.

For more information please see the :ref:`Action API <action_api>`.

Scraper Handler
^^^^^^^^^^^^^^^

The ``scraper_handler.py`` and the ``scraper_schema.json`` files combine to create an API that allows for crawl requests to be made to the Kafka Monitor.

For more information about the API, please refer to the documentation :ref:`here <crawl_api>`.

Stats Handler
^^^^^^^^^^^^^

The ``stats_handler.py`` and the ``stats_schema.json`` files create the validating and processing API for statistics gathering.

For more information please refer to the :ref:`Stats API <stats_api>`.


Zookeeper Handler
^^^^^^^^^^^^^^^^^

The ``zookeeper_handler.py`` and the ``zookeeper_schema.json`` files enable the ability to update the crawl domain blacklist.

For more information please see the :ref:`Zookeeper API <zookeeper_api>`

.. _km_extension:

Extension
---------

Creating your own Plugin for the Kafka Monitor allows you to customize your own Kafka API's or processing python scripts to allow new functionality to be added to the Kafka Monitor. You will need two new files in the ``plugins`` directory, a **json** file for schema validation, and a **python** plugin file to define how you would like to process valid incoming objects.

The following python code template should be used when creating a new plugin:

**plugins/new_plugin.py**

::

    from base_handler import BaseHandler


    class NewPlugin(BaseHandler):

        schema = "new_schema.json"

        def setup(self, settings):
            '''
            Setup your plugin here
            '''
            pass

        def handle(self, dict):
            '''
            Processes a valid API request

            @param dict: a valid dictionary object
            '''
            pass

The plugin class should inherit from the BaseHandler plugin class, which will allow easy integration into the plugin framework. The ``setup()`` method is passed a dictionary created from the settings loaded from your local and default settings files. You should set up connections or other variables here to be used in your handle method.

The ``handle()`` method is passed a dictionary object when a valid object comes into the Kafka Monitor. It will **not** receive invalid objects, so you can assume that any object passed into the function is valid according to your json schema file defined in the ``schema`` variable at the top of the class.

The `JSON Schema <http://spacetelescope.github.io/understanding-json-schema/>`_ defines the type of objects you would like to to process. Below is an example:

**plugins/new_schema.json**

::

    {
        "type": "object",
        "properties": {
            "uuid": {
                "type": "string",
                "minLength": 1,
                "maxLength": 40
            },
            "my_string": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            }
        },
        "required": [
            "uuid",
            "my_string"
        ]
    }

In the ``handle()`` method, you would receive objects that have both a ``uuid`` field and a ``my_string`` field. You are now free to do any additional processing, storage, or manipulation of the object within your plugin! You now should add it to your ``localsettings.py`` file.

**localsettings.py**

::

    PLUGINS = {
        'plugins.new_plugin.NewPlugin': 400,
    }

You have now told the Kafka Monitor to load not only the default plugins, but your new plugin as well with a rank of 400. If you restart your Kafka Monitor the plugin will be loaded.

Additional Info
^^^^^^^^^^^^^^^

Every Kafka Monitor plugin is provided a Scrapy Cluster logger, under the variable name ``self.logger``. You can use this logger to generate debug, info, warnings, or any other log output you need to help gather information from your plugin. This is the same logger that the Kafka Monitor uses, so your desired settings will be preserved.
