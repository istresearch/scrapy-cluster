.. _crawl_extension:

Extension
=========

This page outlines how you can extend Scrapy but still work within Scrapy Cluster's environment.

General
-------

In general, Scrapy Cluster embraces the extension and flexibility of Scrapy, while providing new hooks and frameworks in order to do highly distributed crawling and orchestration. You can see some instances of this within the Scrapy project, as Scrapy Cluster by default needs to use some middlewares and item pipelines to fit things together.

The most heavily customized components of the Scrapy Cluster project involve a distributed scheduler and base spider class. These two classes work together to allow for distributed crawling, but otherwise do not interfere with normal Scrapy processes.

Additional Info
^^^^^^^^^^^^^^^

There is a Scrapy Cluster logger available throughout the project, and there should be plenty of examples on how to create a logger at any one part of your Scrapy Project. You should see examples for how to create a logger in the ``pipelines.py`` file and the ``log_retry_middleware.py`` file.

.. note:: Spiders that use the base ``RedisSpider`` class already have a Scrapy Cluster logger, located at ``self._logger``.

Spiders
-------

Scrapy Cluster allows you to build Scrapy based spiders that can coordinate with each other by utilizing a customized Scrapy Scheduler. Your new Scrapy Cluster based spider outline looks just like a normal Scrapy Spider class, but inherits from Scrapy Cluster's base `RedisSpider` class.

Below is an outline of the spider file.

::

    from redis_spider import RedisSpider


    class MySpider(RedisSpider):
        name = "myspider"

        def __init__(self, *args, **kwargs):
            super(MySpider, self).__init__(*args, **kwargs)

        def parse(self, response):
            # used for collecting statistics about your crawl
            self._increment_status_code_stat(response)

            # process your response here
            # yield Scrapy Requests and Items like normal

That is it! Your spider is now hooked into your scraping cluster, and can do any kind of processing with your responses like normal.

Additional Info
^^^^^^^^^^^^^^^

All Spiders that inherit from the base spider class ``RedisSpider`` will have access to a Scrapy Cluster logger found at ``self._logger``. This is not the same as the Scrapy logger, but can be used in conjunction with it. The following extra functions are provided to the spider as well.

* **reconstruct_headers(response)** - A patch that fixes malformed header responses seen in some websites. This error surfaces when you go to debug or look at the headers sent to Kafka, and you find some of the headers present in the spider are non-existent in the item sent to Kafka. Returns a ``dict``.

You can ``yield`` requests from your Spider just like a normal Scrapy Spider. Thanks to the built in in Scrapy Cluster ``MetaPassthroughMiddleware``, you don't have to worry about the additional overhead required for distributed crawling. If you look at both the ``WanderingSpider`` and ``LinkSpider`` examples, you will see that the only extra information passed into the request via the ``meta`` fields are related to what we actually want to do with the spider.

**Don't want to use the ``RedisSpider`` base class?** That's okay, as long as your spider can adhere to the following guidelines:

* Connect a signal to your crawler so it does not stop when idle.

::

        ...
        self.crawler.signals.connect(self.spider_idle, signal=signals.spider_idle)

    def spider_idle(self):
        raise DontCloseSpider

* Implement the logging and parse methods

::

    def set_logger(self, logger):
        # would allow you to set the Scrapy Cluster logger
        pass

    def parse(self, response):
        # your normal parse method
        pass

With that, in combination with the settings, middlewares, and pipelines already provided by Scrapy Cluster, you should be able to use a customer spider with little effort.

.. _ws_example:

Example
-------

Let's create a new Spider that integrates within Scrapy Cluster. This guide assumes you already have a working cluster already, so please ensure everything is properly hooked up by following the quick start guides for the various components.

We are going to create a Wandering Spider. The goal of this spider is to stumble through the internet, only stopping when it hits a webpage that has no url links on it. We will randomly chose a link from all available links on the page, and yield `only` that url to be crawled by the cluster. This way a single crawl job does not spread out, but serially jumps from one page to another.

Below is the spider class, and can be found in ``crawling/spiders/wandering_spider.py``.

::

    # Example Wandering Spider
    import scrapy

    from scrapy.http import Request
    from lxmlhtml import CustomLxmlLinkExtractor as LinkExtractor
    from scrapy.conf import settings

    from crawling.items import RawResponseItem
    from redis_spider import RedisSpider

    import random


    class WanderingSpider(RedisSpider):
        '''
        A spider that randomly stumbles through the internet, until it hits a
        page with no links on it.
        '''
        name = "wandering"

        def __init__(self, *args, **kwargs):
            super(WanderingSpider, self).__init__(*args, **kwargs)

        def parse(self, response):
            # debug output for receiving the url
            self._logger.debug("crawled url {}".format(response.request.url))
            # collect stats

            # step counter for how many pages we have hit
            step = 0
            if 'step' in response.meta:
                step = response.meta['step']

            # Create Item to send to kafka
            # capture raw response
            item = RawResponseItem()
            # populated from response.meta
            item['appid'] = response.meta['appid']
            item['crawlid'] = response.meta['crawlid']
            item['attrs'] = response.meta['attrs']
            # populated from raw HTTP response
            item["url"] = response.request.url
            item["response_url"] = response.url
            item["status_code"] = response.status
            item["status_msg"] = "OK"
            item["response_headers"] = self.reconstruct_headers(response)
            item["request_headers"] = response.request.headers
            item["body"] = response.body
            item["links"] = []
            # we want to know how far our spider gets
            if item['attrs'] is None:
                item['attrs'] = {}

            item['attrs']['step'] = step

            self._logger.debug("Finished creating item")

            # determine what link we want to crawl
            link_extractor = LinkExtractor(
                                allow_domains=response.meta['allowed_domains'],
                                allow=response.meta['allow_regex'],
                                deny=response.meta['deny_regex'],
                                deny_extensions=response.meta['deny_extensions'])

            links = link_extractor.extract_links(response)

            # there are links on the page
            if len(links) > 0:
                self._logger.debug("Attempting to find links")
                link = random.choice(links)
                req = Request(link.url, callback=self.parse)

                # increment our step counter for this crawl job
                req.meta['step'] = step + 1

                # pass along our user agent as well
                if 'useragent' in response.meta and \
                            response.meta['useragent'] is not None:
                        req.headers['User-Agent'] = response.meta['useragent']

                # debug output
                self._logger.debug("Trying to yield link '{}'".format(req.url))

                # yield the Request to the scheduler
                yield req
            else:
                self._logger.info("Did not find any more links")

            # raw response has been processed, yield to item pipeline
            yield item

In stepping through our ``parse()`` method, you can see we first start off by collecting statistics information about our cluster. We then use the variable ``step`` to determine how many pages our crawl job has visited so far. After that, we create the ``RawResponseItem`` and fill it with our typical crawl data, and make sure to insert our ``step`` variable so our data output has that extra information in it.

After that, we create a link extractor and do a ``random.choice()`` from our extracted links, and yield the request. At the bottom we finally yeild our response item to the item pipeline.

You can now spin a few spiders up by running the following command.

::

    scrapy runspider crawling/spiders/wandering_spider.py

Then, feed your cluster.

::

    python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"test123456", "spiderid":"wandering"}'

If you are looking at your ``demo.crawled_firehose`` Kafka Topic using the ``kafkadump.py`` script, you will begin to see output like so...

::

    {
        "body": <omitted>,
        "crawlid": "test123456",
        "response_url": "http://www.dmoztools.net/",
        "url": "http://www.dmoztools.net/",
        "status_code": 200,
        "status_msg": "OK",
        "appid": "testapp",
        "links": [],
        "request_headers": {
            "Accept-Language": "en",
            "Accept-Encoding": "gzip,deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Scrapy/1.0.4 (+http://scrapy.org)"
        },
        "attrs": {
            "step": 0
        },
        "timestamp": "2016-01-23T22:01:33.379721"
    }
    {
        "body": <omitted>,
        "crawlid": "test123456",
        "response_url": "http://www.dmoztools.net/Computers/Hardware/",
        "url": "http://www.dmoztools.net/Computers/Hardware/",
        "status_code": 200,
        "status_msg": "OK",
        "appid": "testapp",
        "links": [],
        "request_headers": {
            "Accept-Language": "en",
            "Accept-Encoding": "gzip,deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Scrapy/1.0.4 (+http://scrapy.org)"
        },
        "attrs": {
            "step": 1
        },
        "timestamp": "2016-01-23T22:01:35.566280"
    }

Notice the ``attrs`` field has our step value, and we can now track all of the hops the Scrapy Cluster is making. Your cluster is now serially working on that particular crawl job until it hits a page it has already seen, or does not find any links in the response.

You can also fire up more than one crawl job at a time, and track the steps that job makes. After creating some more jobs and letting the cluster run for a while, here is a snapshot of the Redis Monitor crawl data dump.

::

    2016-01-23 17:47:21,164 [redis-monitor] INFO: Crawler Stats Dump:
    {
        "total_spider_count": 4,
        "unique_spider_count": 1,
        "wandering_200_21600": 108,
        "wandering_200_3600": 60,
        "wandering_200_43200": 108,
        "wandering_200_604800": 108,
        "wandering_200_86400": 108,
        "wandering_200_900": 49,
        "wandering_200_lifetime": 107,
        "wandering_404_21600": 4,
        "wandering_404_3600": 1,
        "wandering_404_43200": 4,
        "wandering_404_604800": 4,
        "wandering_404_86400": 4,
        "wandering_404_900": 1,
        "wandering_404_lifetime": 4,
        "wandering_spider_count": 4
    }

You now have two different examples of how Scrapy Cluster extends Scrapy to give you distributed crawling capabilities.
