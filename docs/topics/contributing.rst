Contributing
============

There are a number of ways to contribute to Scrapy Cluster.

.. _report_issue:

Raising Issues
----------------

If you're thinking about raising an issue because you think you've found a problem with Scrapy Cluster, you'd like to make a request for a new feature in the codebase, or any other reason… please read this first.

The GitHub issue tracker is the preferred channel for `Bug Reports`_, `Feature Requests`_, or `Change Requests`_, but please respect the following restrictions:

* Please **search for existing issues**. Help us keep duplicate issues to a minimum by checking to see if someone has already reported your problem or requested your idea.

* Please **do not** use the issue tracker for personal setup or support requests. If the symptom doesn't appear in the :ref:`docker_setup` but appears in your production setup, it is not a Scrapy Cluster issue.

For all other chatter, feel free to join the `Community Chat`_ set up for Scrapy Cluster.

Bug Reports
^^^^^^^^^^^

A bug is a *demonstrable problem* that is caused by the code in the repository.
Good bug reports are extremely helpful - thank you!

Guidelines for bug reports:

    #. **Use the GitHub issue search**, check if the issue has already been reported.

    #. **Check if the issue has been fixed**, try to reproduce it using the
       latest `dev` branch or look for closed issues in the current milestone.

    #. **Isolate the problem**, ideally create a minimal test case to demonstrate a problem with the current build.

    #. **Include as much info as possible!** This includes but is not limited to, version of Kafka, Zookeeper, Redis, Scrapy Cluster (release, branch, or commit), OS, Pip Packages, or anything else that may impact the issue you are raising.

A good bug report shouldn't leave others needing to chase you up for more information.

Feature Requests
^^^^^^^^^^^^^^^^

If you've got a great idea, we want to hear about it! Please label the issue you create with ``feature request`` to distinguish it from other issues.

Before making a suggestion, here are a few handy tips on what to consider:

#. Visit the `Milestones <https://github.com/istresearch/scrapy-cluster/milestones>`_ and search through the known `feature requests <https://github.com/istresearch/scrapy-cluster/issues?utf8=%E2%9C%93&q=label%3A%22feature+request%22+>`_ to see if the feature has already been requested, or is on our roadmap already.

#. Check out `Working on Scrapy Cluster Core`_ - this explains the guidelines for what fits into the scope and aims of the project.

#. Think about whether your feature is for the Kafka Monitor, Redis Monitor, the Crawlers, or does it affect multiple areas? This can help when describing your idea.

#. Remember, it's up to *you* to make a strong case to convince the project's leaders of the merits of a new feature. Please provide as much detail and context as possible - this means explaining the use case and why it is likely to be common.

Change Requests
^^^^^^^^^^^^^^^

Change requests cover both architectural and functional changes to how Scrapy Cluster works. If you have an idea for a new or different dependency, a refactor, or an improvement to a feature, etc - please be sure to:

1. **Use the GitHub search** and check someone else didn't get there first

2. Take a moment to think about the best way to make a case for, and explain what you're thinking as it's up to you to convince the project's leaders the change is worthwhile. Some questions to consider are:

    - Is it really one idea or is it many?
    - What problem are you solving?
    - Why is what you are suggesting better than what's already there?

3. Label your issue with ``change request`` to help identify it within the issue tracker.

Community Chat
^^^^^^^^^^^^^^

If you would like to add a comment about Scrapy Cluster or to interact with the community surrounding and supporting Scrapy Cluster, feel free to join our `Gitter <https://gitter.im/istresearch/scrapy-cluster?utm_source=share-link&utm_medium=link&utm_campaign=share-link>`_ chat room. This is a place where both developers and community users can get together to talk about and discuss Scrapy Cluster.

.. _pull_requests:

Submitting Pull Requests
------------------------

Pull requests are awesome! Sometimes we simply do not have enough time in the day to get to everything we want to cover, or did not think of a different use case for Scrapy Cluster.

If you're looking to raise a PR for something which doesn't have an open issue, please think carefully about raising an issue which your PR can close, especially if you're fixing a bug. This makes it more likely that there will be enough information available for your PR to be properly tested and merged.

To make sure your PR is accepted as quickly as possible, please ensure you hit the following points:

    * You can run ``./run_tests_offline.sh`` **and** ``./run_tests_online.sh`` in your test environment to ensure nothing is broken.

    * Did you add new code? That means it is probably unit-testable and should have a new unit test associated with it.

    * Your PR encapsulates a single alteration or enhancement to Scrapy Cluster, please do not try to fix multiple issues with a single PR without raising it on Github first.

    * If you are adding a significant feature, please put it in the :ref:`changelog` for the current Milestone we are driving towards.

Once you have a minimal pull request please submit it to the ``dev`` branch. That is where our core development work is conducted and we would love to have it in the latest bleeding edge build.

Testing and Quality Assurance
-----------------------------

Never underestimate just how useful quality assurance is. If you're looking to get involved with the code base and don't know where to start, checking out and testing a pull requests or the latest ``dev`` branch is one of the most useful things you can help with.

Essentially:

    1. Checkout the latest ``dev`` branch.
    2. Follow one of our :ref:`quickstart` guides to get your cluster up and running.
    3. Poke around our documentation, try to follow any of the other guides or ensure that we are explaining ourselves as clear as possible.
    4. Find anything odd? Please follow the `Bug Reports`_ guidelines and let us know!

Documentation
^^^^^^^^^^^^^

Scrapy Cluster's documentation can be found on `Read the Docs <http://scrapy-cluster.readthedocs.org/en/latest/>`_. If you have feedback or would like to write some user documentation, please let us know in our `Community Chat`_ room or by raising and issue and submitting a PR on how our documentation could be improved.

Working on Scrapy Cluster Core
------------------------------

Are you looking to help develop core functionality for Scrapy Cluster? Awesome!
Please see the :ref:`docker_setup` guide to test small scale deployments of Scrapy Cluster. If you are looking to do large scale testing and development, please first ensure you can work with the Vagrant Image first.

If something goes wrong, please see the :ref:`debugging` guide first.

.. _lfstwo:

Looking for something to work on?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you're interested in contributing to Scrapy Cluster and don't know where to start, here's a few things to consider.

* **We are trying to build an generic framework for large scale, distributed web crawling.** Code that is applicable only to your setup, installation, or use case may not be helpful to everyone else. The framework and code we create should be extendable, helpful, and improve the ability to succeed in this mission.

* Look for issues that are labeled with the **current** milestone and see if someone is already working on it. Leave a comment stating why you would like to work on this or the skills you can contribute to help complete the task.

* **Do not** begin development on features or issues outside of the current milestone. If you must, please submit an issue or comment and explain your motivation for working on something that we haven't quite gotten to yet.

* Do you have a neat idea or implementation for a new plugin or extenstion to any of the three core areas? We would love to hear about it or help guide you in building it.

* Test and use the `Scrapy Cluster Utils Package <https://pypi.python.org/pypi/scutils>`_ in your other projects! We would love feedback on how to improve the utilities package, it has been extremely helpful to us in developing Scrapy Cluster. More documentation can be found in the :ref:`scutils` section.

* Feel like you have a pretty good grasp with Scrapy Cluster? Please consider doing **large scale testing** of crawlers (10-20 machines at least, with 10-20 spiders per machine), and have the cluster crawl what ever your heart desires. Where are the runtime bottlenecks? Where can our algorithms be improved? Does certain cluster setups slow down crawling considerably? We are always looking to improve.

* Are you an expert in some other field where we lack? (Docker, Mesos, Conda, Python 3, etc) Please consider how you you can contribute to the project and talk with us on where we think you can best help.

If you're still stuck, feel free to send any of the core developers an message in the `Community Chat`_ as we are always happy to help.

Key Branches
^^^^^^^^^^^^

* ``master`` - (`link to master <https://github.com/istresearch/scrapy-cluster>`_) this branch reflects the lastest stable release. Hotfixes done to this branch should also be reflected in the ``dev`` branch

* ``dev`` - (`link to dev <https://github.com/istresearch/scrapy-cluster/tree/dev>`_) the main developer branch. Go here for the latest bleeding edge code

Other branches represent other features core developers are working on and will be merged back into the main ``dev`` branch once the feature is complete.
