.. _quickstart:

Quick Start
===========

*This guide does not go into detail as to how everything works, but hopefully will get you scraping quickly. For more information about each process works please see the rest of the documentation.*

Setup
-----

There are a number of different options available to set up Scrapy Cluster. You can chose to provision with `Vagrant Quickstart`_, use the `Docker Quickstart`_, or manually configure via the `Cluster Quickstart`_ yourself.

.. _vagrant_setup:

Vagrant Quickstart
^^^^^^^^^^^^^^^^^^

The Vagrant Quickstart provides you a simple Vagrant Virtual Machine in order to try out Scrapy Cluster. It is not meant to be a production crawling machine, and should be treated more like a test ground for development.

1) Ensure you have Vagrant and VirtualBox installed on your machine. For instructions on setting those up please refer to the official documentation.

2) Download the latest ``master`` branch release via

::

  git clone https://github.com/istresearch/scrapy-cluster.git
  # or
  git clone git@github.com:istresearch/scrapy-cluster.git

You may also use the pre-packaged git `releases <https://github.com/istresearch/scrapy-cluster/releases>`_, however the latest commit on the ``master`` branch will always have to most up to date code or minor tweaks that do not deserve another release.

Lets assume our project is now in ``~/scrapy-cluster``

3) Stand up the Scrapy Cluster Vagrant machine. By default this will start an **Ubuntu** virtual machine. If you would like to us **CentOS**, change the following line in the ``Vagrantfile`` in the root of the project

::

    node.vm.box = 'centos/7'

Bring the machine up.

::

    $ cd ~/scrapy-cluster
    $ vagrant up
    # This will set up your machine, provision it with Ansible, and boot the required services

.. note:: The initial setup may take some time due to the setup of Zookeeper, Kafka, and Redis. This is only a one time setup and is skipped when running it in the future.

4) SSH onto the machine

::

    $ vagrant ssh

5) Ensure everything under supervision is running.

::

    vagrant@scdev:~$ sudo supervisorctl status
    kafka                            RUNNING   pid 1812, uptime 0:00:07
    redis                            RUNNING   pid 1810, uptime 0:00:07
    zookeeper                        RUNNING   pid 1809, uptime 0:00:07

.. note:: If you receive the message ``unix:///var/run/supervisor.sock no such file``, issue the following command to start Supervisord: ``sudo service supervisord start``, then check the status like above.

6) Create a `Virtual Environment <https://virtualenv.pypa.io/en/latest/>`_ for Scrapy Cluster, and activate it. This is where the python packages will be installed to.

::

    vagrant@scdev:~$ virtualenv sc
    ...
    vagrant@scdev:~$ source sc/bin/activate

7) The Scrapy Cluster folder is mounted in the ``/vagrant/`` directory

::

    (sc) vagrant@scdev:~$ cd /vagrant/

8) Install the Scrapy Cluster packages

::

    (sc) vagrant@scdev:/vagrant$ pip install -r requirements.txt

9) Ensure the offline tests pass

::

    (sc) vagrant@scdev:/vagrant$ ./run_offline_tests.sh
    # There should be 5 core pieces, each of them saying all tests passed like so
    ----------------------------------------------------------------------
    Ran 20 tests in 0.034s
    ...
    ----------------------------------------------------------------------
    Ran 9 tests in 0.045s
    ...

10) Ensure the online tests pass

::

    (sc) vagrant@scdev:/vagrant$ ./run_online_tests.sh
    # There should be 5 major blocks here, ensuring your cluster is setup correctly.
    ...
    ----------------------------------------------------------------------
    Ran 2 tests in 0.105s
    ...
    ----------------------------------------------------------------------
    Ran 1 test in 26.489s


.. warning:: If this test fails, it most likely means the Virtual Machine's Kafka is in a finicky state. Issue the following command and then retry the online test to fix Kafka: ``sudo supervisorctl restart kafka``


You now appear to have a working test environment, so jump down to `Your First Crawl`_ to finish the quickstart.

.. _docker_setup:

Docker Quickstart
^^^^^^^^^^^^^^^^^

The Docker Quickstart will help you spin up a complete standalone cluster thanks to Docker and `Docker Compose <https://docs.docker.com/compose/>`_. All individual components will run in standard docker containers, and be controlled through the ``docker-compose`` command line interface.

1) Ensure you have Docker Engine and Docker Compose installed on your machine. For more information about installation please refer to Docker's official documentation.

2) Download and unzip the latest release `here <https://github.com/istresearch/scrapy-cluster/releases>`_.

Lets assume our project is now in ``~/scrapy-cluster``

3) Run docker compose

::

  $ docker-compose up -d

This will pull the latest stable images from Docker hub and build your scraping cluster.

At time of writing, there is no Docker container to interface and run all of the tests within your compose-based cluster. Instead, if you wish to run the unit and integration tests plese see the following steps.

4) To run the integration tests, get into the bash shell on any of the containers.

  Kafka monitor

  ::

    $ docker exec -it scrapycluster_kafka_monitor_1 bash

  Redis monitor

  ::

    $ docker exec -it scrapycluster_redis_monitor_1 bash

  Crawler

  ::

    $ docker exec -it scrapycluster_crawler_1 bash

  Rest

  ::

    $ docker exec -it scrapycluster_rest_1 bash

5) Run the unit and integration test for that component. Note that your output may be slightly different but your tests should pass consistently.

::

  $ ./run_docker_tests.sh
  ...

  ----------------------------------------------------------------------
  Ran 20 tests in 5.742s

  OK
  ...

  ----------------------------------------------------------------------
  Ran 1 test in 27.583s

  OK

This script will run both of offline unit tests and the online integration tests for your particular container. You will want to do this on all three component containers.

You now appear to have a working docker environment, so jump down to `Your First Crawl`_ to finish the quickstart. Note that since this is a precanned cluster thanks to docker compose, you have everything already spun up except the dump utilities.

.. _cluster_setup:

Cluster Quickstart
^^^^^^^^^^^^^^^^^^

The Cluster Quickstart will help you set up your components across a number of different machines. Here, we assume everything runs on a single box with external Kafka, Zookeeper, and Redis.

1) Make sure you have Apache Zookeeper, Apache Kafka, and Redis up and running on your cluster. For more information about standing those up, please refer to the official project documentation.

2) Download and unzip the latest release `here <https://github.com/istresearch/scrapy-cluster/releases>`_.

Lets assume our project is now in ``~/scrapy-cluster``

3) Install the requirements on every machine

::

    $ cd ~/scrapy-cluster
    $ pip install -r requirements.txt

4) Run the offline unit tests to ensure everything seems to be functioning correctly.

::

    $ ./run_offline_tests.sh
    # There should be 5 core pieces, each of them saying all tests passed like so
    ----------------------------------------------------------------------
    Ran 20 tests in 0.034s
    ...
    ----------------------------------------------------------------------
    Ran 9 tests in 0.045s
    ...

Lets now setup and ensure our cluster can talk with Redis, Kafka, and Zookeeper

5) Add a new file called ``localsettings.py`` in the Kafka Monitor folder.

::

    $ cd kafka-monitor/
    $ vi localsettings.py

Add the following to your new custom local settings.

::

    # Here, 'scdev' is the host with Kafka and Redis
    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'

It is recommended you use this 'local' override instead of altering the default ``settings.py`` file, in order to preserve the original configuration the cluster comes with in case something goes wrong, or the original settings need updated.

6) Now, lets run the online integration test to see if our Kafka Monitor is set up correctly

::

    $ python tests/online.py -v
    test_feed (__main__.TestKafkaMonitor) ... ok
    test_run (__main__.TestKafkaMonitor) ... ok

    ----------------------------------------------------------------------
    Ran 2 tests in 0.104s

    OK

This integration test creates a dummy Kafka topic, writes a JSON message to it, ensures the Kafka Monitor reads the message, and puts the request into Redis.

.. warning:: If your integration test fails, please ensure the port(s) are open on the machine your Kafka cluster and your Redis host resides on, and that the particular machine this is set up on can access the specified hosts.

7) We now need to do the same thing for the Redis Monitor

::

    $ cd ../redis-monitor
    $ vi localsettings.py

Add the following to your new custom local settings.

::

    # Here, 'scdev' is the host with Kafka and Redis
    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'

8) Run the online integration tests

::

  $ python tests/online.py -v
  test_process_item (__main__.TestRedisMonitor) ... ok
  test_sent_to_kafka (__main__.TestRedisMonitor) ... ok

  ----------------------------------------------------------------------
  Ran 2 tests in 0.028s

  OK

This integration test creates a dummy entry in Redis, ensures the Redis Monitor processes it, and writes the result to a dummy Kafka Topic.

.. warning:: If your integration test fails, please ensure the port(s) are open on the machine your Kafka cluster and your Redis host resides on, and that the particular machine this is set up on can access the specified hosts.

9) Now let's setup our crawlers.

::

    $ cd ../crawlers/crawling/
    $ vi localsettings.py

Add the following fields to override the defaults

::

    # Here, 'scdev' is the host with Kafka, Redis, and Zookeeper
    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'
    ZOOKEEPER_HOSTS = 'scdev:2181'

10) Run the online integration tests to see if the crawlers work.

::

  $ cd ../
  $ python tests/online.py -v
  ...
  ----------------------------------------------------------------------
  Ran 1 test in 23.191s

  OK

This test spins up a spider using the internal Scrapy API, directs it to a real webpage to go crawl, then ensures it writes the result to Kafka.

.. note:: This test takes around 20 - 25 seconds to complete, in order to compensate for server response times or potential crawl delays.

.. note:: You may see 'Deprecation Warnings' while running this test! This is okay and may be caused by irregularities in Scrapy or how we are using or overriding packages.

.. warning:: If your integration test fails, please ensure the port(s) are open on the machine your Kafka cluster, your Redis host, and your Zookeeper hosts. Ensure that the machines the crawlers are set up on can access the desired hosts, and that your machine can successfully access the internet.

11) If you would like, you can set up the rest service as well

::

    $ cd ../rest/
    $ vi localsettings.py

Add the following fields to override the defaults

::

    # Here, 'scdev' is the host with Kafka and Redis
    REDIS_HOST = 'scdev'
    KAFKA_HOSTS = 'scdev:9092'

12) Run the online integration tests to see if the rest service works.

::

  $ python tests/online.py -v
  test_status (__main__.TestRestService) ...  * Running on http://0.0.0.0:62976/ (Press CTRL+C to quit)
  127.0.0.1 - - [11/Nov/2016 17:09:17] "GET / HTTP/1.1" 200 -
  ok

  ----------------------------------------------------------------------
  Ran 1 test in 15.034s

    OK

Your First Crawl
----------------

At this point you should have a Scrapy Cluster setup that has been tested and appears to be operational. We can choose to start up either a bare bones cluster, or a fully operational cluster.

.. note:: You can append ``&`` to the end of the following commands to run them in the background, but we recommend you open different terminal windows to first get a feel of how the cluster operates.

The following commands outline what you would run in a traditional environment. If using a container based solution these commands are ran when you run the container itself.

**Bare Bones:**

-  The Kafka Monitor:

   ::

       python kafka_monitor.py run

-  A crawler:

   ::

       scrapy runspider crawling/spiders/link_spider.py

-  The dump utility located in Kafka Monitor to see your crawl results

   ::

       python kafkadump.py dump -t demo.crawled_firehose


**Fully Operational:**

-  The Kafka Monitor (1+):

    ::

        python kafka_monitor.py run

-  The Redis Monitor (1+):

    ::

        python redis_monitor.py

-  A crawler (1+):

    ::

        scrapy runspider crawling/spiders/link_spider.py

- The rest service (1+):

    ::

        python rest_service.py

-  The dump utility located in Kafka Monitor to see your crawl results

    ::

        python kafkadump.py dump -t demo.crawled_firehose

-  The dump utility located in Kafka Monitor to see your action results

    ::

       python kafkadump.py dump -t demo.outbound_firehose

Which ever setup you chose, every process within should stay running for the remainder that your cluster is in an operational state.

.. note:: If you chose to set the Rest service up, this section may also be performed via the :doc:`../rest/index` endpoint. You just need to ensure the JSON identified in the following section is properly fed into the :ref:`feed <feed_endpoint>` rest endpoint.

*The follwing commands can be ran from the command line, whether that is on the machine itself or inside the Kafka Monitor container depends on the setup chosen above.*

1) We now need to feed the cluster a crawl request. This is done via the same Kafka Monitor python script, but with different command line arguements.

::

    python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"abc123"}'

You will see the following output on the command line for that successful request:

::

    2015-12-22 15:45:37,457 [kafka-monitor] INFO: Feeding JSON into demo.incoming
    {
        "url": "http://dmoztools.net",
        "crawlid": "abc123",
        "appid": "testapp"
    }
    2015-12-22 15:45:37,459 [kafka-monitor] INFO: Successfully fed item to Kafka

You will see an error message in the log if the script cannot connect to Kafka in time.

2) After a successful request, the following chain of events should occur in order:

  #. The Kafka monitor will receive the crawl request and put it into Redis
  #. The spider periodically checks for new requests, and will pull the request from the queue and process it like a normal Scrapy spider.
  #. After the scraped item is yielded to the Scrapy item pipeline, the Kafka Pipeline object will push the result back to Kafka
  #. The Kafka Dump utility will read from the resulting output topic, and print out the raw scrape object it received

3) The Redis Monitor utility is useful for learning about your crawl while it is being processed and sitting in redis, so we will pick a larger site so we can see how it works (this requires a full deployment).

Crawl Request:

::

    python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"abc1234", "maxdepth":1}'

Now send an ``info`` action request to see what is going on with the
crawl:

::

    python kafka_monitor.py feed '{"action":"info", "appid":"testapp", "uuid":"someuuid", "crawlid":"abc1234", "spiderid":"link"}'

The following things will occur for this action request:

  1. The Kafka monitor will receive the action request and put it into Redis
  2. The Redis Monitor will act on the info request, and tally the current pending requests for the particular ``spiderid``, ``appid``, and ``crawlid``
  3. The Redis Monitor will send the result back to Kafka
  4. The Kafka Dump utility monitoring the actions will receive a result similar to the following:

  ::

      {u'server_time': 1450817666, u'crawlid': u'abc1234', u'total_pending': 25, u'total_domains': 2, u'spiderid': u'link', u'appid': u'testapp', u'domains': {u'twitter.com': {u'low_priority': -9, u'high_priority': -9, u'total': 1}, u'dmoz.org': {u'low_priority': -9, u'high_priority': -9, u'total': 24}}, u'uuid': u'someuuid'}

In this case we had 25 urls pending in the queue, so yours may be slightly different.

4) If the crawl from step 1 is still running, lets stop it by issuing a ``stop`` action request (this requires a full deployment).

Action Request:

::

    python kafka_monitor.py feed  '{"action":"stop", "appid":"testapp", "uuid":"someuuid", "crawlid":"abc1234", "spiderid":"link"}'

The following things will occur for this action request:

    1. The Kafka monitor will receive the action request and put it into Redis
    2. The Redis Monitor will act on the stop request, and purge the current pending requests for the particular ``spiderid``, ``appid``, and ``crawlid``
    3. The Redis Monitor will blacklist the ``crawlid``, so no more pending requests can be generated from the spiders or application
    4. The Redis Monitor will send the purge total result back to Kafka
    5. The Kafka Dump utility monitoring the actions will receive a result similar to the following:

    ::

        {u'total_purged': 90, u'server_time': 1450817758, u'crawlid': u'abc1234', u'spiderid': u'link', u'appid': u'testapp', u'action': u'stop'}

In this case we had 90 urls removed from the queue. Those pending requests are now completely removed from the system and the spider will go back to being idle.

--------------

Hopefully you now have a working Scrapy Cluster that allows you to submit jobs to the queue, receive information about your crawl, and stop a crawl if it gets out of control. For a more in depth look, please continue reading the documentation for each component.
