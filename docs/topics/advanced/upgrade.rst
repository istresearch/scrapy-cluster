Upgrade Scrapy Cluster
======================

This page will walk you through how to upgrade your Scrapy Cluster from one version to the next. This assumes you have a fully functioning, stable, and deployed cluster already and would like to run the latest version of Scrapy Cluster.

Upgrades
--------

Pre Upgrade
^^^^^^^^^^^

Before you shut down your current crawling cluster. You should build and test the desired version of Scrapy Cluster you wish to upgrade to. This means looking over documentation, or trying the cluster out in a Virtual Machine. You should be familiar with the tutorials on how to stand a new cluster version up, and be prepared for when the time comes to upgrade your existing cluster.

Preparation is key so you do not lose data or get malformed data into your cluster.

The Upgrade
^^^^^^^^^^^

For all upgrades you should use the ``migrate.py`` script at the root level of the Scrapy Cluster project.

::

  $ python migrate.py -h
  usage: migrate.py [-h] -ir INPUT_REDIS_HOST [-ip INPUT_REDIS_PORT]
                    [-id INPUT_REDIS_DB] [-iP INPUT_REDIS_PASSWORD]
                    [-or OUTPUT_REDIS_HOST] [-op OUTPUT_REDIS_PORT]
                    [-od OUTPUT_REDIS_DB] [-oP OUTPUT_REDIS_PASSWORD]
                    -sv {1.0,1.1} -ev {1.1,1.2} [-v {0,1,2}] [-y]

  Scrapy Cluster Migration script. Use to upgrade any part of Scrapy Cluster.
  Not recommended for use while your cluster is running.

  optional arguments:
    -h, --help            show this help message and exit
    -ir INPUT_REDIS_HOST, --input-redis-host INPUT_REDIS_HOST
                          The input Redis host ip
    -ip INPUT_REDIS_PORT, --input-redis-port INPUT_REDIS_PORT
                          The input Redis port
    -id INPUT_REDIS_DB, --input-redis-db INPUT_REDIS_DB
                          The input Redis db
    -iP INPUT_REDIS_PASSWORD, --input-redis-password INPUT_REDIS_PASSWORD
                          The input Redis password
    -or OUTPUT_REDIS_HOST, --output-redis-host OUTPUT_REDIS_HOST
                          The output Redis host ip, defaults to input
    -op OUTPUT_REDIS_PORT, --output-redis-port OUTPUT_REDIS_PORT
                          The output Redis port, defaults to input
    -od OUTPUT_REDIS_DB, --output-redis-db OUTPUT_REDIS_DB
                          The output Redis db, defaults to input
    -oP OUTPUT_REDIS_PASSWORD, --output-redis-password OUTPUT_REDIS_PASSWORD
                          The output Redis password
    -sv {1.0,1.1}, --start-version {1.0,1.1}
                          The current cluster version
    -ev {1.1,1.2}, --end-version {1.1,1.2}
                          The desired cluster version
    -v {0,1,2}, --verbosity {0,1,2}
                          Increases output text verbosity
    -y, --yes             Answer 'yes' to any prompt

The script also provides the ability to migrate between Redis instances, change the verbosity of the logging within the migration script, and can also prompt the user in case of failure or potentially dangerous situations.

This script **does not** upgrade any of the actual code or applications Scrapy Cluster uses! Only behind the scenes keys and datastores used by a deployed cluster. You are still responsible for deploying the new Crawlers, Kafka Monitor, and Redis Monitor.

.. warning:: It is **highly** recommended you shut down all three components of your Scrapy Cluster when upgrading. This is due to the volatile and distributed nature of Scrapy Cluster, as there can be race conditions that develop when the cluster is undergoing an upgrade while scrapers are still inserting new Requests, or the Kafka Monitor is still adding Requests to the Redis Queues.

If you do not chose to shut down the cluster, you need to ensure it is 'quiet'. Meaning, there is no data going into Kafka or into Redis.

Once your cluster is quiet or halted, run the upgrade script to ensure everything is compatible with the newer version. For example, upgrading from Scrapy Cluster 1.0 to Scrapy Cluster 1.1:

::

    $ python migrate.py -ir scdev -sv 1.0 -ev 1.1 -y
    Upgrading Cluster from 1.0 to 1.1
    Cluster upgrade complete in 0.01 seconds.
    Upgraded cluster from 1.0 to 1.1

In the future, this script will manage all upgrades to any component needed. For the time being, we only need to upgrade items within Redis.

Post Upgrade
^^^^^^^^^^^^

After upgrading, you should use the various version quick start documentations for each component, to ensure it is properly configured, restarted, and running. Afterwards in your production level run mode, you should begin to monitor log output to check for any anomalies within your cluster.

Upgrade Notes
-------------

This section holds any comments or notes between versions.

1.0 -> 1.1
^^^^^^^^^^

The primary upgrade here is splitting the individual spider queues with keys like ``<spider>:queue`` into a more generic queue system ``<spider>:<domain>:queue``. This allows us to do controlled domain throttling across the cluster, better explained :ref:`here <controlling>`.

1.1 -> 1.2
^^^^^^^^^^

Upgrades the cluster for an inefficient use of ``pickle`` encoding to a more efficient use of ``ujson``. The primary keys impacted by this upgrade are the spider domain queues.
