.. _log_factory:

Log Factory
===========

The LogFactory is a `Singleton Factory <http://www.oodesign.com/singleton-pattern.html>`_ design that allows you to use a single logger across your python application.

This single log instance allows you to:

    - Write to a file or standard out

    - Write your logs in JSON or in a standard print format

    - Can handle multiple independent processes writing to the same file

    - Automatically handle rotating the file logs so they do not build up

    - Not worry about multi threaded applications creating too many loggers resulting in duplicated data

    - Register callbacks to provide additional functionality when certain logging levels or criteria are met

It is designed to be easy to use throughout your application, giving you a standard and flexible way to write your log data.

.. method:: LogFactory.get_instance(json=False, stdout=True, name='scrapy-cluster',dir='logs', file='main.log', bytes=25000000, backups=5, level='INFO', format='%(asctime)s [%(name)s] %(levelname)s: %(message)s', propagate=False, include_extra=False)

    :param stdout: Flag to write logs to stdout or file
    :param json: Flag to write json logs with objects or just the messages
    :param name: The logger name
    :param dir: The directory to write logs into
    :param file: The file name
    :param bytes: The max file size in bytes
    :param backups: The number of backups to keep of the file
    :param level: The logging level string ['DEBUG', 'INFO', 'WARNING', 'ERROR' 'CRITICAL']
    :param format: The log format
    :param propagate: Allow the log to propagate to other ancestor loggers
    :param include_extra: When not logging json, include the 'extra' param in the output
    :return: The log instance to use

Usage
-----

Basic Usage of the LogFactory:

::

    >>> from scutils.log_factory import LogFactory
    >>> logger = LogFactory.get_instance()
    >>> logger.info("Hello")
    2015-11-17 15:55:29,807 [scrapy-cluster] INFO: Hello

Please keep in mind the default values above, and be sure to set them correctly the **very first time** the LogFactory is called. Below is an example of **incorrect** usage.

    >>> from scutils.log_factory import LogFactory
    >>> logger = LogFactory.get_instance(json=True, name='logger1', level='DEBUG')
    >>> logger.debug("test")
    {"message": "Logging to stdout", "logger": "logger1", "timestamp": "2015-11-17T21:13:59.816441Z", "level": "DEBUG"}
    >>> # incorrectly changing the logger in mid program
    ...
    >>> new_logger = LogFactory.get_instance(name='newlogger', json=False)
    >>> new_logger.info("test")
    {"message": "test", "logger": "logger1", "timestamp": "2015-11-17T21:14:47.657768Z", "level": "INFO"}

Why does this happen? Behind the scenes, the LogFactory is trying to ensure that no matter where or when you call the ``get_instance()`` method, it returns to you the same logger you asked for originally. This allows multithreaded applications to instantiate the logger all the same way, without having to worry about duplicate logs showing up in your output. Once you have your logger object, the following standard logger methods are available:

.. method:: debug(message, extra={})

    Tries to write a debug level log message

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

.. method:: info(message, extra={})

    Tries to write an info level log message

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

.. method:: warn(message, extra={})

    Tries to write a warning level log message

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

.. method:: warning(message, extra={})

    Tries to write a warning level log message. Both of these warning methods are only supplied for convenience

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

.. method:: error(message, extra={})

    Tries to write an error level log message

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

.. method:: critical(message, extra={})

    Tries to write a critical level log message

    :param message: The message to write to the logs
    :param extra: A dictionary of extra fields to include with the written object if writing in json

When setting you application log level, you determine what amount of logs it will produce. Typically the most verbose logging is done in ``DEBUG``, and increasing the log level decreases the amount of logs generated.

+----------------+------------------------------------------+
| App Log Level  | Output Log levels                        |
+================+==========================================+
| DEBUG          | DEBUG, INFO, WARNING, ERROR, CRITICAL    |
+----------------+------------------------------------------+
| INFO           | INFO, WARNING, ERROR, CRITICAL           |
+----------------+------------------------------------------+
| WARNING        | WARNING, ERROR, CRITICAL                 |
+----------------+------------------------------------------+
| ERROR          | ERROR, CRITICAL                          |
+----------------+------------------------------------------+
| CRITICAL       | CRITICAL                                 |
+----------------+------------------------------------------+

Scrapy Cluster's many components use arguments from the command line to set common properties of the its logger. You may want to use an argument parser in your application to set common things like:

    - The log level

    - Whether to write in JSON output or formatted print statements

    - Whether to write to a file or not

If you would like to register a callback for extra functionality, you can use the following function on your logger object.

.. method:: register_callback(log_level, fn, criteria=None):

    :param log_level: The log level expression the callback should act on
    :param fn: the function to call
    :param criteria: a dictionary of values providing additional matching criteria before the callback is called

The callback takes arguments in the form of the log level and a criteria dictionary. The log level may be of the following forms:

* ``'INFO'``, ``'ERROR'``, ``'DEBUG'``, etc - the callback is only called when the exact log level message is used

* ``'<=INFO'``, ``'>DEBUG'``, ``'>=WARNING'``, etc - parameterized callbacks, allowing the callback to execute in greater than or less than the desired log level

* ``'*'`` - the callback is called regardless of log level

For additional filtering requirements you may also use the ``criteria`` parameter, in which the criteria **must be a subset** of the ``extras`` originally passed into the logging method of choice.

For example:

::

    {'a': 1} subset of {'a': 1, 'b': 2, 'c': 3}

Both the log level and criteria are considered before executing the callback, basic usage is as follows:

::

    >>> from scutils.log_factory import LogFactory
    >>> logger = LogFactory.get_instance()
    >>> def call_me(message, extras):
    ...   print("callback!", message, extras)
    ...
    >>> logger.register_callback('>=INFO', call_me)
    >>> logger.debug("no callback")
    >>> logger.info("check callback")
    2017-02-01 15:19:48,466 [scrapy-cluster] INFO: check callback
    ('callback!', 'check callback', {})

In this example both the log message was written, the callback was called, and the three values were printed.

.. note:: Your callback function must be declared outside of your Class scope, or use the ``@staticmethod`` decorator. Typically this means putting the function at the top of your python file outside of any class declarations.

Example
-------

Add the following python code to a new file, or use the script located at ``utils/examples/example_lf.py``:

::

    import argparse
    from scutils.log_factory import LogFactory
    parser = argparse.ArgumentParser(description='Example logger.')
    parser.add_argument('-ll', '--log-level', action='store', required=False,
                        help="The log level", default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
    parser.add_argument('-lf', '--log-file', action='store_const',
                        required=False, const=False, default=True,
                        help='Log the output to the file. Otherwise logs to stdout')
    parser.add_argument('-lj', '--log-json', action='store_const',
                        required=False, const=True, default=False,
                        help="Log the data in JSON format")
    parser.add_argument('-ie', '--include-extra', action='store_const', const=True,
                            default=False, help="Print the 'extra' dict if not logging"
                            " to json")
    args = vars(parser.parse_args())
    logger = LogFactory.get_instance(level=args['log_level'], stdout=args['log_file'],
                        json=args['log_json'], include_extra=args['include_extra'])

    my_var = 1

    def the_callback(log_message, log_extras):
        global my_var
        my_var += 5

    def the_callback_2(log_message, log_extras):
        global my_var
        my_var *= 2

    logger.register_callback('DEBUG', the_callback)
    logger.register_callback('WARN', the_callback_2, {'key':"value"})

    logger.debug("debug output 1")
    logger.warn("warn output", extra={"key":"value", "key2":"value2"})
    logger.warn("warn output 2")
    logger.debug("debug output 2")
    logger.critical("critical fault, closing")
    logger.debug("debug output 3")
    sum = 2 + 2
    logger.info("Info output closing.", extra={"sum":sum})
    logger.error("Final var value", extra={"value": my_var})

Let's assume you now have a file named ``example_lf.py``, run the following commands:

::

    $ python example_lf.py --help
    usage: example_lf.py [-h] [-ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-lf]
                          [-lj]

    Example logger.

    optional arguments:
      -h, --help            show this help message and exit
      -ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            The log level
      -lf, --log-file       Log the output to the file. Otherwise logs to stdout
      -lj, --log-json       Log the data in JSON format

::

    $ python example_lf.py --log-level DEBUG
    # Should write all log messages above
    2017-02-01 15:27:48,814 [scrapy-cluster] DEBUG: Logging to stdout
    2017-02-01 15:27:48,814 [scrapy-cluster] DEBUG: debug output 1
    2017-02-01 15:27:48,814 [scrapy-cluster] WARNING: warn output
    2017-02-01 15:27:48,814 [scrapy-cluster] WARNING: warn output 2
    2017-02-01 15:27:48,814 [scrapy-cluster] DEBUG: debug output 2
    2017-02-01 15:27:48,814 [scrapy-cluster] CRITICAL: critical fault, closing
    2017-02-01 15:27:48,814 [scrapy-cluster] DEBUG: debug output 3
    2017-02-01 15:27:48,814 [scrapy-cluster] INFO: Info output closing.
    2017-02-01 15:27:48,814 [scrapy-cluster] ERROR: Final var value

::

    $ python example_lf.py --log-level INFO --log-json
    # Should log json object of "INFO" level or higher
    {"message": "warn output", "key2": "value2", "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:29:24.548895Z", "key": "value", "level": "WARNING"}
    {"message": "warn output 2", "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:29:24.549302Z", "level": "WARNING"}
    {"message": "critical fault, closing", "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:29:24.549420Z", "level": "CRITICAL"}
    {"message": "Info output closing.", "sum": 4, "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:29:24.549510Z", "level": "INFO"}
    {"message": "Final var value", "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:29:24.549642Z", "level": "ERROR", "value": 2}

Notice that the extra dictionary object we passed into the two logs above is now in our json logging output

::

    $ python example_lf.py --log-level CRITICAL --log-json --log-file
    # Should log only one critical message to our file located at logs/
    $ tail logs/main.log
    {"message": "critical fault, closing", "logger": "scrapy-cluster", "timestamp": "2017-02-01T20:30:05.484337Z", "level": "CRITICAL"}

You can also use the ``include_extra`` flag when instantiating the logger to print the dictionary even if you are not logging via json.

::

    $ python example_lf.py -ll DEBUG -ie
    2017-02-01 15:31:07,284 [scrapy-cluster] DEBUG: Logging to stdout
    2017-02-01 15:31:07,284 [scrapy-cluster] DEBUG: debug output 1
    2017-02-01 15:31:07,284 [scrapy-cluster] WARNING: warn output {'key2': 'value2', 'key': 'value'}
    2017-02-01 15:31:07,284 [scrapy-cluster] WARNING: warn output 2
    2017-02-01 15:31:07,284 [scrapy-cluster] DEBUG: debug output 2
    2017-02-01 15:31:07,284 [scrapy-cluster] CRITICAL: critical fault, closing
    2017-02-01 15:31:07,284 [scrapy-cluster] DEBUG: debug output 3
    2017-02-01 15:31:07,284 [scrapy-cluster] INFO: Info output closing. {'sum': 4}
    2017-02-01 15:31:07,285 [scrapy-cluster] ERROR: Final var value {'value': 22}

Notice here that both our ``DEBUG`` callback was called three times, and the single ``WARN`` callback was called once, causing our final ``my_var`` variable to equal ``22``.

----

The LogFactory hopefully will allow you to easily debug your application while at the same time be compatible with JSON based log architectures and production based deployments. For more information please refer to :doc:`../advanced/integration`