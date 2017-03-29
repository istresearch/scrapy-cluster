Quick Start
===========

First, create a ``localsettings.py`` to track your overridden custom settings. You can override any setting you find within the Rest service's ``settings.py``, and a typical file may look like the following:

::

    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'

rest_service.py
----------------

The main mode of operation for the Rest service is to generate a Restful endpoint for external applications to interact with your cluster.

::

    $ python rest_service.py

Typical Usage
-------------

Typical usage of the Rest service is done in conjunction with both the Kafka Monitor and Redis Monitor. The Rest service is a gateway for interacting with both of those components, and provides little functionality when used by itself.

.. warning:: This guide assumes you have both a running Kafka Monitor and Redis Monitor already. Please see the Kafka Monitor :doc:`../kafka-monitor/quickstart`  or the Redis Monitor :doc:`../redis-monitor/quickstart` for more information.

Open two terminals.

**Terminal 1:**

Run the rest service

::

    $ python rest_service.py

**Terminal 2:**

Curl the basic endpoint of the component.

::

    $ curl scdev:5343
    {
      "kafka_connected": true,
      "my_id": "34806877e13f",
      "node_health": "GREEN",
      "redis_connected": true,
      "uptime_sec": 23
    }

You should see a log message come through Terminal 1 stating the message was received and the data transmitted back.

::

    2016-11-11 09:51:26,358 [rest-service] INFO: 'index' endpoint called

Feed a request

::

    $ curl scdev:5343/feed -H "Content-Type: application/json" -d '{"uuid":"abc123", "appid":"stuff"}'

The request provided is outlined at the Kafka Monitor's :doc:`../kafka-monitor/api`, when using the ``feed`` endpoint you need to ensure your request conforms to specification outlined on that page.

You should see a log message come through Terminal 1 stating the message was received and the data transmitted back.

::

    2016-11-06 14:26:05,621 [rest-service] INFO: 'feed' endpoint called

After a short time, you should see the result come through your curl command in terminal 2.

::


    {
      "data": {
        "appid": "stuff",
        "crawler": {
          "machines": {
            "count": 0
          },
          "queue": {
            "total_backlog": 0
          },
          "spiders": {
            "link": {
              "count": 1
            },
            "total_spider_count": 1,
            "unique_spider_count": 1
          }
        },
        "kafka-monitor": {
          "fail": {
            "21600": 1,
            "3600": 1,
            "43200": 1,
            "604800": 1,
            "86400": 1,
            "900": 1,
            "lifetime": 1
          },
          "plugins": {
            "StatsHandler": {
              "21600": 2,
              "3600": 2,
              "43200": 2,
              "604800": 2,
              "86400": 2,
              "900": 2,
              "lifetime": 2
            }
          },
          "total": {
            "21600": 3,
            "3600": 3,
            "43200": 3,
            "604800": 3,
            "86400": 3,
            "900": 3,
            "lifetime": 3
          }
        },
        "redis-monitor": {
          "nodes": {
            "afa660f7e348": [
              "3333a4d63704"
            ]
          },
          "plugins": {
            "StatsMonitor": {
              "21600": 2,
              "3600": 2,
              "43200": 2,
              "604800": 2,
              "86400": 2,
              "900": 2,
              "lifetime": 2
            }
          },
          "total": {
            "21600": 2,
            "3600": 2,
            "43200": 2,
            "604800": 2,
            "86400": 2,
            "900": 2,
            "lifetime": 2
          }
        },
        "server_time": 1478714930,
        "stats": "all",
        "uuid": "abc123"
      },
      "error": null,
      "status": "SUCCESS"
    }

At this point, your Rest service is operational.