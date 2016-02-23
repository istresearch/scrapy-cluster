Kafka Topics
============

This page explains the different Kafka Topics that will be created in your Kafka Cluster.

Production
----------

For production deployments you will have at a minimum three operational Kafka Topics.

* **demo.incoming** - The incoming Kafka topic to receive valid JSON requests, as read by the Kafka Monitor

* **demo.crawled_firehose** - All of the crawl data collected from your Crawlers is fed into this topic.

* **demo.outbound_firehose** - All of the Action, Stop, Expire, and Statistics based request results will come out of this topic.

If you have configured Application ID specific topics for the :ref:`Redis Monitor <rm_kafka_appid_topics>` or the :ref:`Crawler <c_kafka_appid_topics>`, you will have these topics.

* **demo.crawled_<appid>** - Crawl data specific to the ``appid`` used to submit the request

* **demo.outbound_<appid>** - Info, Stop, Expire, and Stat data specific to the ``appid`` used to submit the request.

Testing
-------

If you run the online integration tests, there will be dummy Kafka Topics that are created, so as to not interfere with production topics.

* **demo.incoming_test** - Used in the online integration test for the Kafka Monitor

* **demo_test.crawled_firehose** - Used for conducting the online integration test for the Crawlers

* **demo_test.outbound_firehose** - Used in the online integration test for the Redis Monitor
