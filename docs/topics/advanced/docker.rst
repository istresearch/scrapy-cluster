.. _adv_docker:

Docker
======

Scrapy Cluster supports `Docker <https://docker.com>`_ by ensuring each individual component is contained within a different docker image. You can find the docker compose files in the root of the project, and the Dockerfiles themselves and related configuration are located within the ``/docker/`` folder. This page is not meant as an introduction to Docker, but as a supplement for those comfortable working with Docker already.

A container could either contain:

* A single spider
* A single kafka monitor
* A single redis monitor
* A single rest service

Thanks to the ability to scale each component independently of each other, we utilize `Docker Compose <https://docs.docker.com/compose/>`_ to allow for scaling of Scrapy Cluster and management of the containers. You can use this in conjunction with things like `Docker Swarm <https://docs.docker.com/swarm/>`_, `Apache Mesos <http://mesos.apache.org/>`_, `Kubernetes <http://kubernetes.io/>`_, `Amazon EC2 Container Service <https://aws.amazon.com/ecs/>`_, or any other container manager of your choice.

You can find the latest images on the Scrapy Cluster Docker hub page `here <https://hub.docker.com/r/istresearch/scrapy-cluster/>`_.

.. note:: Docker support for Scrapy Cluster is fairly new, and large-scale deployments of Scrapy Cluster have not been fully tested at the time of writing.

Images
------

Each component for Scrapy Cluster is designated as a tag within the root docker repository. Unlike a lot of projects, we chose to keep the dockerized Scrapy Cluster within the same github repository in order to stay consistent with how the project is used. This means that there will be no ``latest`` tag for Scrapy Cluster, instead, the tags are defined as follows.

Kafka Monitor: ``istresearch/scrapy-cluster:kafka-monitor-{release/build}``

Redis Monitor: ``istresearch/scrapy-cluster:redis-monitor-{release/build}``

Crawler: ``istresearch/scrapy-cluster:crawler-{release/build}``

Rest: ``istresearch/scrapy-cluster:rest-{release/build}``

For example ``istresearch/scrapy-cluster:redis-monitor-1.2`` would be the official stable 1.2 release of the Redis Monitor, but ``istresearch/scrapy-cluster:redis-monitor-dev`` would be tied to the latest ``dev`` branch release. Typically numeric releases will be paired with the ``master`` branch, while ``-dev`` releases will be paired with the ``dev`` branch.

Code Layout
-----------

Each container contains only code for that particular component, located at ``/usr/src/app``. By default, a ``localsettings.py`` file will supply the override to provide the container the configuration to work with the native docker compose files. You are free to use docker volumes to mount a different settings file on top of the ``localsettings.py`` file in order to configure the component with your particular setup.

However, if you look at the component's local settings file, you may see some slight alterations based on environment variable overrides. The following snippet shows some of the alterations you would find in the project's ``docker/*/settings.py`` files, or within the container at ``/usr/src/app/localsettings.py``:

::

    REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    KAFKA_INCOMING_TOPIC = os.getenv('KAFKA_INCOMING_TOPIC', 'demo.incoming')
    LOG_JSON = str2bool(os.getenv('LOG_JSON', False))

Commonly altered variables can be overridden with a docker environment variable of the same name. Here, you can override ``REDIS_DB`` with ``1`` to specify a different redis database.

If you find a variable you would like to override that does not already have an environment variable applied, you can use the following to make it available.

String: ``os.getenv('PARAM_NAME', 'default_value')``

Integer: ``int(os.getenv('PARAM_NAME', default_value))``

Boolean: ``str2bool(os.getenv('PARAM_NAME', default_value))``

Where ``default_value`` is your specified default, and ``PARAM_NAME`` is the name of the configuration you are overriding. Note that you will need to rebuild your containers if you alter code within the project.

The environment overrides can then be applied to your component within the normal ``-e`` flag from Docker, or in the ``docker-compose.yml`` files as shown below.

::

    environment:
      - REDIS_HOST=other-redis
      - REDIS_DB=1
      - LOG_JSON=True

It is important to either look at the ``localsettings.py`` files within the container or at the ``settings.py`` files as denoted above to find the environment variables you wish to tweak.

Running
-------

It is recommended you use docker compose to orchestrate your cluster with all of the other components, and simply issuing ``docker-compose up`` will bring your cluster online. If you wish to build the containers from scratch or insert custom code, please use add the following lines, customized for each component.

::

    image: istresearch/scrapy-cluster:kafka-monitor-1.2
    build:
      context: .
      dockerfile: docker/kafka-monitor/Dockerfile

You will then be able to issue the following:

::

    docker-compose -f docker-compose.yml up --build --force-recreate

This will rebuild your containers and bring everything online.

.. warning:: The Kafka container does not like being stopped and started over and over again, and will sometimes fail to start cleanly. You can mitigate this by issuing ``docker-compose down`` (note this will clean out all data).

Compose ELK Stack
-----------------

You can use Docker Compose to configure both Scrapy Cluster and an associated ELK stack to view your log data from the 4 core components.

The docker compose file is located in ``elk/docker-compose.elk.yml``, and contains all of the necessary ingredients to bring up

* Scrapy Cluster

  * Kafka Monitor

  * Redis Monitor

  * Crawler

  * Rest

* Infrastructure

  * Kafka

  * Zookeeper

  * Redis

* ELK

  * Elasticsearch

  * Logstash

  * Kibana

Bring it up by issuing the following command from within the ``elk`` folder:

::

  $ docker-compose -f docker-compose.elk.yml up -d

You can ensure everything started up via:

::

  $ docker-compose -f docker-compose.elk.yml ps
          Name                   Command                  State                   Ports
  ---------------------------------------------------------------------------------------------
  elk_crawler_1           scrapy                  Up
                          runspider c ...
  elk_elasticsearch_1     /docker-entrypoint.sh   Up                      0.0.0.0:9200->9200/tc
                          elas ...                                        p, 0.0.0.0:9300->9300
                                                                          /tcp
  elk_kafka_1             start-kafka.sh          Up                      0.0.0.0:9092->9092/tc
                                                                          p
  elk_kafka_monitor_1     python                  Up
                          kafka_monit ...
  elk_kibana_1            /docker-entrypoint.sh   Up                      0.0.0.0:5601->5601/tc
                          kibana                                          p
  elk_logstash_1          /docker-entrypoint.sh   Up                      0.0.0.0:5000->5000/tc
                          logs ...                                        p
  elk_redis_1             docker-entrypoint.sh    Up                      0.0.0.0:32776->6379/t
                          redis ...                                       cp
  elk_redis_monitor_1     python                  Up
                          redis_monit ...
  elk_rest_1              python rest_service.py  Up                      0.0.0.0:5343->5343/tcp
  elk_zookeeper_1         /bin/sh -c              Up                      0.0.0.0:2181->2181/tc
                          /usr/sbin/sshd  ...                             p, 22/tcp, 2888/tcp,
                                                                          3888/tcp

TIP

In the unfortunate case that elasticsearch is not running and the following message shows up into the logs:

::

  ERROR: bootstrap checks failed max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]

you have to edit the virtual memory settings of the machine you are running docker onto. 

For more info about the needed edits you can follow the link to the `official Elasticsearch documentation <https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html>`_ .


From here, please continue to the :ref:`Kibana <elk_kibana>` portion of the :doc:`ELK <integration>` integration guide.

------

As we continue to expand into the docker world this page is subject to change. If you have a novel or different way you would like to use Scrapy Cluster in your container-based application we would love to hear about it.
