from __future__ import absolute_import
# Example Wandering Spider
import scrapy

from scrapy.http import Request
from .lxmlhtml import CustomLxmlLinkExtractor as LinkExtractor
from scrapy.conf import settings

from crawling.items import RawResponseItem
from .redis_spider import RedisSpider

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
        item["encoding"] = response.encoding
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
