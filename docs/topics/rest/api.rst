API
===

The Rest service component exposes both the Kafka Monitor :doc:`../kafka-monitor/api` and a mechanism for getting information that may take a significant amount of time.

Standardization
---------------

Aside from the ``Index`` endpoint which provides information about the service itself, all objects receive the following wrapper:

::

    {
        "status": <status>,
        "data": <data>,
        "error" <error>
    }

The ``status`` key is a human readable ``SUCCESS`` or ``FAILURE`` string, used for quickly understanding what happened. The ``data`` key provides the data that was requested, and the ``error`` object contains information about any internal errors that occurred while processing your request.

Accompanying this object are standard ``200``, ``400``, ``404``, or ``500`` response codes. Whenever you encounter non-standard response codes from the Rest service you should receive the accompanying information provided both in the response from the service itself and/or in the service logs. Problems might include:

* Improperly formatted JSON or content headers are incorrect

    ::

        {
          "data": null,
          "error": {
            "message": "The payload must be valid JSON."
          },
          "status": "FAILURE"
        }

* Invalid JSON structure for desired endpoint

    ::

        {
          "data": null,
          "error": {
            "cause": "Additional properties are not allowed (u'crazykey' was unexpected)",
            "message": "JSON did not validate against schema."
          },
          "status": "FAILURE"
        }

* Unexpected Exception within the service itself

    ::

        {
          "data": null,
          "error": {
            "message": "Unable to connect to Kafka"
          },
          "status": "FAILURE"
        }

* The desired endpoint does not exist

    ::

        {
          "data": null,
          "error": {
            "message": "The desired endpoint does not exist"
          },
          "status": "FAILURE"
        }

For all of these and any other error, you should expect diagnostic information to be either in the response or in the logs.

Index Endpoint
--------------

The index endpoint allow you to obtain basic information about the status of the Rest Service, its uptime, and connection to critical components.

**Headers Expected:** ``None``

**Method Types:** ``GET``, ``POST``

**URI:** ``/``

Example
^^^^^^^

::

    $ curl scdev:5343

Responses
^^^^^^^^^

Unable to connect to Redis or Kafka

::

    {
      "kafka_connected": false,
      "my_id": "d209adf2aa01",
      "node_health": "RED",
      "redis_connected": false,
      "uptime_sec": 143
    }

Able to connect to Redis or Kafka, but not both at the same time

::

    {
      "kafka_connected": false,
      "my_id": "d209adf2aa01",
      "node_health": "YELLOW",
      "redis_connected": true,
      "uptime_sec": 148
    }

Able to connect to both Redis and Kafka, fully operational

::

    {
      "kafka_connected": true,
      "my_id": "d209adf2aa01",
      "node_health": "GREEN",
      "redis_connected": true,
      "uptime_sec": 156
    }

Here, a human readable ``node_health`` field is provided, as well as information about which service is unavailable at the moment. If the component is not ``GREEN`` in health you should troubleshoot your configuration.

.. _feed_endpoint:

Feed Endpoint
-------------

The feed endpoint transmits your request into JSON that will be sent to Scrapy Cluster. It follows the :doc:`../kafka-monitor/api` exposed by the Kafka Monitor, and acts as a pass-through to that service. The assumptions made are as follows:

* Crawl requests made to the cluster do not expect a response back via Kafka

* Other requests like Action or Stat expect a response within a designated period of time. If a response is expected but not received, a :ref:`Poll <poll>` is used to further poll for the desired response.

**Headers Expected:** ``Content-Type: application/json``

**Method Types:** ``POST``

**URI:** ``/feed``

**Data:** Valid JSON data for the request

Examples
^^^^^^^^

Feed a crawl request

::

    $ curl scdev:5343/feed -H "Content-Type: application/json" -d '{"url":"http://dmoztools.net", "appid":"madisonTest", "crawlid":"abc123"}'

Feed a Stats request

::

    $ curl scdev:5343/feed -H "Content-Type: application/json" -d '{"uuid":"abc123", "appid":"stuff"}'

In both of these cases, we are translating the JSON required by the Kafka Monitor into a Restful interface request. You may use all of the API's exposed by the Kafka Monitor here when creating your request.

Responses
^^^^^^^^^

The responses from the feed endpoint should match both the standardized object and the expected return value from the Kafka Monitor API.

Successful submission of a crawl request.

::

    {
      "data": null,
      "error": null,
      "status": "SUCCESS"
    }

Successful response from a Redis Monitor request

::

    {
      "data": {... data here ...},
      "error": null,
      "status": "SUCCESS"
    }

Unsuccessful response from a Redis Monitor request

::

    {
      "data": {
        "poll_id": <uuid of request>
      },
      "error": null,
      "status": "SUCCESS"
    }

In this case, the response was unable to be obtained within the :ref:`response time <wait_for_response_time>` and the ``poll_id`` should be used in the :ref:`poll <poll>` request below.

.. _poll:

Poll Endpoint
-------------

The Poll endpoint provides the ability to retrieve data from long running requests that might take longer than the desired :ref:`response time <wait_for_response_time>` configured for the service. This is useful when conducting statistics gathering or pruning data via action requests.

**Headers Expected:** ``Content-Type: application/json``

**Method Types:** ``POST``

**URI:** ``/poll``

**Data:** Valid JSON data for the request

JSON Schema
^^^^^^^^^^^

::

    {
        "type": "object",
        "properties": {
            "poll_id": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100,
                "description": "The poll id to retrieve"
            }
        },
        "required": [
            "poll_id"
        ],
        "additionalProperties": false
    }

Example
^^^^^^^

::

    $ curl scdev:5343/poll -XPOST -H "Content-Type: application/json" -d '{"poll_id":"abc123"}'

Responses
^^^^^^^^^

Successfully found a poll that has been completed, but was not returned initially during the request

::

    {
      "data": {... data here ...},
      "error": null,
      "status": "SUCCESS"
    }

Did not find the results for the ``poll_id``

::

    {
      "data": null,
      "error": {
        "message": "Could not find matching poll_id"
      },
      "status": "FAILURE"
    }

Note that a failure to find the ``poll_id`` may indicate one of two things:

* The request has not completed yet

* The request incurred a failure within another component of Scrapy Cluster
