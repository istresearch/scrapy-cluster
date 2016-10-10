from builtins import str
from scrapy.exceptions import DontCloseSpider
from scrapy.spiders import Spider
from scrapy import signals


class RedisSpider(Spider):
    '''
    Base Spider for doing distributed crawls coordinated through Redis
    '''

    def _set_crawler(self, crawler):
        super(RedisSpider, self)._set_crawler(crawler)
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

    def set_logger(self, logger):
        '''
        Set the logger for the spider, different than the default Scrapy one

        @param logger: the logger from the scheduler
        '''
        self._logger = logger

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
        properly serialize the headers. This method is a way to circumvent
        the known issue
        """

        header_dict = {}
        # begin reconstructing headers from scratch...
        for key in list(response.headers.keys()):
            key_item_list = []
            key_list = response.headers.getlist(key)
            for item in key_list:
                key_item_list.append(item)
            header_dict[key] = key_item_list
        return header_dict
