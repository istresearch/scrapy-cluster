Frequently Asked Questions
==========================

Common questions about Scrapy Cluster organized by category.

General
-------

**I can't get my cluster working, where do I begin?**

    We always recommend using the latest stable release or commit from the ``master`` branch. Code pulled from here should be able to successfully complete all ``./offline_tests.sh``.

    You can then test your online integration settings by running ``./online_tests.sh`` and determining at what point your tests fail. If all of the online tests *pass* then your cluster appears to be ready for use.

    Normally, online test failure is a result of improper settings configuration or network ports not being properly configured. Triple check these!

    If you are still stuck please refer the the :ref:`Docker Quickstart <docker_setup>` guide for setting up an example cluster, or the :ref:`Troubleshooting <debugging>` page for more information.

**How do I debug a component?**

    Both the Kafka Monitor and Redis Monitor can have their log level altered by passing the ``--log-level`` flag to the command of choice. For example, you can see more verbose debug output from the Kafka Monitor's run command with the following command.

    ::

        $ python kafka_monitor.py run --log-level DEBUG

    You can also alter the ``LOG_LEVEL`` setting in your ``localsettings.py`` file to achieve the same effect, or set it as an environment variable in docker-compose.

    If you wish to debug Scrapy Cluster based components in your Scrapy Spiders, use the ``SC_LOG_LEVEL`` setting in your ``localsettings.py`` file to see scrapy cluster based debug output. Normal Scrapy debugging techniques can be applied here as well, as the scrapy cluster debugging is designed to not interfere with Scrapy based debugging.

**What branch should I work from?**

    If you wish to have stable, tested, and documented code please use the ``master`` branch. For untested, undocumented bleeding edge developer code please see the ``dev`` branch. All other branches should be offshoots of the ``dev`` branch and will be merged back in at some point.

**Why do you recommend using a** ``localsettings.py`` **file instead of altering the** ``settings.py`` **file that comes with the components?**

    Local settings allow you to keep your custom settings for your cluster separate from those provided by default. If we decide to change variable names, add new settings, or alter the default value you now have a merge conflict if you pull that new commit down.

    By keeping your settings separate, you can also have more than one setting configuration at a time! For example, you can use the Kafka Monitor to push json into to different Kafka topics for various testing, or have a local debugging vs production setup on your machines. Use the ``--settings`` flag for either the Kafka Monitor or Redis Monitor to alter their configuration.

    .. note:: The local settings override flag does not apply to the Scrapy settings, Scrapy uses its own style for settings overrides that can be found on this `page <http://doc.scrapy.org/en/latest/topics/settings.html>`_

**How do I deploy my cluster in an automated fashion?**

    Deploying a scrapy cluster in an automated fashion is highly dependent on the environment **you** are working in. Because we cannot control the OS you are running, packages installed, or network setup, it is best recommended you use an automated deployment framework that fits your needs. Some suggestions include `Ansible <https://www.ansible.com/>`_, `Puppet <https://puppetlabs.com/>`_, `Chef <https://www.chef.io/chef/>`_, `Salt <http://saltstack.com/>`_, `Anaconda Cluster <http://docs.continuum.io/anaconda-cluster/index>`_, etc.

**Do you support Docker?**

    Docker support is new with the ``1.2`` release, please see the :doc:`advanced/docker` guide for more information.

**Are there other distributed Scrapy projects?**

    Yes! Please see our breakdown at :ref:`other_projects`

**I would like to contribute but do not know where to begin, how can I help?**

    You can find suggestions of things we could use help on :ref:`here <lfstwo>`.

**How do I contact the community surrounding Scrapy Cluster?**

   Feel free to reach out by joining the `Gitter <https://gitter.im/istresearch/scrapy-cluster?utm_source=share-link&utm_medium=link&utm_campaign=share-link>`_ chat room, send an email to scrapy-cluster-tech@istresearch.com, or for more formal issues please :ref:`raise an issue <report_issue>`.


Kafka Monitor
-------------

**How do I extend the Kafka Monitor to fit my needs?**

    Please see the plugin documentation :ref:`here <km_extension>` for adding new plugins to the Kafka Monitor. If you would like to contribute to core Kafka Monitor development please consider looking at our guide for :ref:`pull_requests`.

Crawler
-------

**How do I create a Scrapy Spider that works with the cluster?**

    To use everything scrapy cluster has to offer with your new Spider, you need your class to inherit from our ``RedisSpider`` base class.

    You can also yield new Requests or items like a normal Scrapy Spider. For more information see the :ref:`crawl extension <crawl_extension>` documentation.

**Can I use everything else that the original Scrapy has to offer, like middlewares, pipelines, etc?**

    Yes, you can. Our core logic relies on a heavily customized Scheduler which is not normally exposed to users. If Scrapy Cluster hinders use of a Scrapy ability you need please let us know.

**Do I have to restart my Scrapy Cluster Crawlers when I push a new domain specific configuration?**

    No, the crawlers will receive a notification from Zookeeper that their configuration has changed. They will then automatically update to the new desired settings, without a restart. For more information please see :ref:`here <domain_specific_configuration>`.

**How do I use Scrapy** ``start_urls`` **with Scrapy Cluster?**

    Don't put ``start_urls`` within your Scrapy Cluster spiders! Use the :ref:`Crawl API <crawl_api>` to feed those initial urls into your cluster. This will ensure the crawl is not duplicated by many spiders running and the same time, and that the crawl has all the meta-data it needs to be successful.

Redis Monitor
-------------

**How do I extend the Redis Monitor to fit my needs?**

    Please see the plugin documentation :ref:`here <rm_extension>` for adding new plugins to the Redis Monitor. If you would like to contribute to core Redis Monitor development please consider looking at our guide for :ref:`pull_requests`.

Rest
----

**My rest endpoint reports RED or YELLOW, how do I fix this?**

    A red or yellow status indicates the service cannot connect to one or more components. There should be error logs indicating a failure or loss of connection to a particular component.

Utilities
---------

**Are the utilities dependent on Scrapy Cluster?**

    No! The utilities package is located on PyPi `here <https://pypi.python.org/pypi/scutils/>`_ and can be downloaded and used independently of this project.

----

Have a question that isn't answered here or in our documentation? Feel free to read our :ref:`report_issue` guidelines about opening an issue.