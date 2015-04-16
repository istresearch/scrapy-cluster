#import redis

from scrapy import signals
from scrapy.exceptions import DontCloseSpider
from scrapy.spider import Spider
#from scrapy.conf import settings

class RedisSpider(Spider):
    '''
    Base Spider for doing distributed crawls coordinated through Redis
    '''

    def set_crawler(self, crawler):
        super(RedisSpider, self).set_crawler(crawler)
        self.crawler.signals.connect(self.spider_idle,
                                        signal=signals.spider_idle)

    def spider_idle(self):
        raise DontCloseSpider

    def parse(self, response):
        '''
        Parse a page of html, and yield items into the item pipeline

        @param response: The response object of the scrape
        '''
        raise NotImplementedError("Please implement parse() for your spider")

    def reconstruct_headers(self, response):
        """
        Purpose of this method is to reconstruct the headers dictionary that
        is normally passed in with a "response" object from scrapy.

        Args:
            response: A scrapy response object

        Returns: A dictionary that mirrors the "response.headers" dictionary
        that is normally within a response object

        Raises: None
        Reason: Originally, there was a bug where the json.dumps() did not
        properly serialize the headers. This is method is way to circumvent
        the known issue
        """

        header_dict = {}
        # begin reconstructing headers from scratch...
        for key in response.headers.keys():
            key_item_list = []
            key_list = response.headers.getlist(key)
            for item in key_list:
                key_item_list.append(item)
            header_dict[key] = key_item_list
        return header_dict


