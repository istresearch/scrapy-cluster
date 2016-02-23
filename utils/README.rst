************************
Scrapy Cluster Utilities
************************

Overview
--------

The ``scutils`` package is a collection of utilities that are used by the Scrapy Cluster project.  These utilities are agnostic enough that they can be used by any application.

Requirements
------------

- Unix based machine (Linux or OS X)
- Python 2.7.x

Installation
------------

Inside a virtualenv, run ``pip install -U scutils``.  This will install the latest version of the Scrapy Cluster Utilities.  If you are running a Scrapy Cluster, ``scutils`` is included inside of the **requirements.txt** so there is no need to install it separately.

Documentation
-------------

Full documentation for the ``scutils`` package is included as part of the Official Scrapy Cluster Documentation, which can be found `here <http://scrapy-cluster.readthedocs.org/en/latest/topics/utils/index.html>`_ under the **Utilities** section.

argparse_helper.py
==================

The ``argparse_helper`` module is used to help print top level ``--help`` arguments from argparse when used with subparsers. Useful for running applications that have multiple combinations of subcommands and command line arguments.

log_factory.py
==============

The ``log_factory`` module provides a standardized way for creating logs for multithreaded and concurrent process log data.  It supports all log levels, stdout or to a file, and various output formats including JSON.

method_timer.py
===============

The ``method_timer`` module provides a simple decorator that can be added to functions or methods requiring an execution timeout period.

redis_queue.py
==============

The ``redis_queue`` module provides 3 core queue classes which use Redis as the place to store data. Includes FIFO, Stack, and Priority Queues.

redis_throttled_queue.py
========================

The ``redis_throttled_queue`` module provides a throttled or moderated Redis queue structure that can be used to mitigate the number of pops from the queue within a given time frame.

settings_wrapper.py
===================

The ``settings_wrapper`` module is a class the handles loading of default python application settings, which can then be overridden or added to by a local settings file. In the end provides a single dictionary object of all your loaded application settings.


stats_collector.py
==================

The ``stats_collector`` module generates Redis based statistics based on time windows or in total. Statistics collection includes time windows, rolling time windows, counters, unique counters, hyperloglog counters, and bitmap counters.

zookeeper_watcher.py
====================

The ``zookeeper_watcher`` module provides an easy way to tell an application that it's watched Zookeeper file has changed. It also handles Zookeeper session disconnects and reconnects behind the scenes of your application.
