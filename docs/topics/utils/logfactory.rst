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

It is designed to be easy to use throughout your application, giving you a standard and flexible way to write your log data.

.. method:: LogFactory.get_instance(json=False, stdout=True, name='scrapy-cluster',dir='logs', file='main.log', bytes=25000000, backups=5, level='INFO', format='%(asctime)s [%(name)s] %(levelname)s: %(message)s', propagate=False)

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

Example
-------

Add the following python code to a new file:

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
    args = vars(parser.parse_args())
    logger = LogFactory.get_instance(level=args['log_level'], stdout=args['log_file'],
                        json=args['log_json'])
    logger.debug("debug output 1")
    logger.warn("warn output", extra={"key":"value"})
    logger.debug("debug output 2")
    logger.critical("critical fault, closing")
    logger.debug("debug output 3")
    sum = 2 + 2
    logger.info("Info output closing.", extra={"sum":sum})

Now, lets save that file as ``log_example.py`` and run the following commands:

::

    $ python log_example.py --help
    usage: log_example.py [-h] [-ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-lf]
                          [-lj]

    Example logger.

    optional arguments:
      -h, --help            show this help message and exit
      -ll {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                            The log level
      -lf, --log-file       Log the output to the file. Otherwise logs to stdout
      -lj, --log-json       Log the data in JSON format

::

    $ python log_example.py --log-level DEBUG
    # Should write all log messages above
    2015-11-17 16:49:06,957 [scrapy-cluster] DEBUG: Logging to stdout
    2015-11-17 16:49:06,958 [scrapy-cluster] DEBUG: debug output 1
    2015-11-17 16:49:06,958 [scrapy-cluster] WARNING: warn output
    2015-11-17 16:49:06,958 [scrapy-cluster] DEBUG: debug output 2
    2015-11-17 16:49:06,958 [scrapy-cluster] CRITICAL: critical fault, closing
    2015-11-17 16:49:06,958 [scrapy-cluster] DEBUG: debug output 3
    2015-11-17 16:49:06,958 [scrapy-cluster] INFO: Info output closing.

::

    $ python log_example.py --log-level INFO --log-json
    # Should log json object of "INFO" level or higher
    {"message": "warn output", "logger": "scrapy-cluster", "timestamp": "2015-11-17T21:52:28.407833Z", "key": "value", "level": "WARNING"}
    {"message": "critical fault, closing", "logger": "scrapy-cluster", "timestamp": "2015-11-17T21:52:28.408323Z", "level": "CRITICAL"}
    {"message": "Info output closing.", "sum": 4, "logger": "scrapy-cluster", "timestamp": "2015-11-17T21:52:28.408421Z", "level": "INFO"}

Notice that the extra dictionary object we passed into the two logs above is now in our json logging output

::

    $ python log_example.py --log-level CRITICAL --log-json --log-file
    # Should log only one critical message to our file located at logs/
    $ tail logs/main.log
    {"message": "critical fault, closing", "logger": "scrapy-cluster", "timestamp": "2015-11-17T21:56:28.318056Z", "level": "CRITICAL"}

----

The LogFactory hopefully will allow you to easily debug your application while at the same time be compatible with JSON based log architectures and production based deployments. For more information please refer to :doc:`../advanced/integration`