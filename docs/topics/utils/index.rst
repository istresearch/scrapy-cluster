.. _scutils:

Utilites
=======================

These documents provide information about the agnostic utility classes used within Scrapy Cluster that may be useful in other applications.

.. toctree::
   :hidden:

   argparsehelper
   logfactory
   methodtimer
   redisqueue
   redisthrottledqueue
   settingswrapper
   statscollector
   zookeeperwatcher

:doc:`argparsehelper`
    Simple module to assist in argument parsing with subparsers.

:doc:`logfactory`
    Module for logging multithreaded or concurrent processes to files, stdout, and/or json.

:doc:`methodtimer`
    A method decorator to timeout function calls.

:doc:`redisqueue`
    A module for creating easy redis based FIFO, Stack, and Priority Queues.

:doc:`redisthrottledqueue`
    A wrapper around the :doc:`redisqueue` module to enable distributed throttled pops from the queue.

:doc:`settingswrapper`
    Easy to use module to load both default and local settings for your python application and provides a dictionary object in return.

:doc:`statscollector`
    Module for statistics based collection in Redis, including counters, rolling time windows, and hyperloglog counters.

:doc:`zookeeperwatcher`
    Module for watching a zookeeper file and handles zookeeper session connection troubles and re-establishment of watches.
