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
    usage: migrate.py [-h] -r REDIS_HOST [-p REDIS_PORT] -sv {1.0} -ev {1.1}

    Scrapy Cluster Migration script. Use to upgrade any part of Scrapy Cluster.
    Not recommended for use while your cluster is running.

    optional arguments:
      -h, --help            show this help message and exit
      -r REDIS_HOST, --redis-host REDIS_HOST
                            The Redis host ip
      -p REDIS_PORT, --redis-port REDIS_PORT
                            The Redis port
      -sv {1.0}, --start-version {1.0}
                            The current cluster version
      -ev {1.1}, --end-version {1.1}
                            The desired cluster version

This script **does not** upgrade any of the applications Scrapy Cluster uses, only core files, keys, and folders used by a deployed cluster.

.. warning:: It is **highly** recommended you shut down all three components of your Scrapy Cluster when upgrading. This is due to the volatile and distributed nature of Scrapy Cluster, as there can be race conditions that develop when the cluster is undergoing an upgrade while scrapers are still inserting new Requests, or the Kafka Monitor is still adding Requests to the Redis Queues.

If you do not chose to shut down the cluster, you need to ensure it is 'quiet'. Meaning, there is no data going into Kafka or into Redis.

Once your cluster is quiet or halted, run the upgrade script to ensure everything is compatible with the newer version. For example, upgrading from Scrapy Cluster 1.0 to Scrapy Cluster 1.1:

::

    $ python migrate.py -r scdev -sv 1.0 -ev 1.1
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
