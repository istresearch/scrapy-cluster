Quick Start
===========

First, create a ``localsettings.py`` to track your overridden custom settings. You can override any setting you find within the Rest service's ``settings.py``, and a typical file may look like the following:

::

    REST_HOST = 'localhost'

ui_service.py
----------------

The main mode of operation for the Admin UI service is to serve Flask endpoints which return HTML and can be viewed in a browser for interacting with your cluster.

::

    $ python ui_service.py

Typical Usage
-------------

Typical usage of the Admin UI service is done in conjunction with both the Rest service, Kafka Monitor and Redis Monitor. The Admin UI uses the Rest service as a gateway for interacting with both the Kafka Monitor and Redis Monitor, and provides little functionality when used by itself.

.. warning:: This guide assumes you have both a running Rest service, Kafka Monitor and Redis Monitor already. Please see the Kafka Monitor :doc:`../kafka-monitor/quickstart`  or the Redis Monitor :doc:`../redis-monitor/quickstart` for more information.

Open a terminal.

**Terminal 1:**

Run the rest service

::

    $ python rest_service.py


Open a browser.

**Browser:**
::

    http://localhost:5000/


You should see a log message come through Terminal 1 stating the message was received and the data transmitted back.

::

    2016-11-11 09:51:26,358 [ui-service] INFO: 'index' endpoint called

