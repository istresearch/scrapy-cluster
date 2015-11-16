************************
Scrapy Cluster Utilities
************************

Overview
--------

The ``scutils`` package is a collection of utilities that are used by the Scrapy Cluster.  However, these utilities are agnostic enough that they can be used for any distributed application.

Requirements
------------

- Unix based machine (Linux of OS X)
- Python 2.7.x

Installation
------------

Inside a virtualenv, run ``pip install -U scutils``.  This will install the latest version of the Scrapy Cluster Utilities.  If you are running a Scrapy Cluster, ``scutils`` is included inside of the **requirements.txt** so there is no need to install it separately.

Documentation
-------------

Full documentation for ``scutils`` will be included as part of the Scrapy Cluster 1.1 release.  Basic descriptions are below.

log_factory.py
==============

The ``log_factory`` module provides a standardized way for creating log data.  It supports all log levels and various output formats, including JSON.

method_timer.py
===============

The ``method_timer`` module provides a simple decorator that can be added to functions or methods requiring a timeout period.

stats_collector.py
==================

The ``stats_collector`` module generates Redis statistics based on time windows.

zookeeper_watcher.py
====================

The ``zookeeper_watcher.py`` module provides an easy way to tell an application that it's Zookeeper file has changed.
