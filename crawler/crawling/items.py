# -*- coding: utf-8 -*-

# Define here the models for your scraped items

import scrapy


class RawResponseItem(scrapy.Item):
    appid = scrapy.Field()
    crawlid = scrapy.Field()
    url = scrapy.Field()
    response_url = scrapy.Field()
    status_code = scrapy.Field()
    status_msg = scrapy.Field()
    response_headers = scrapy.Field()
    request_headers = scrapy.Field()
    body = scrapy.Field()
    links = scrapy.Field()
    attrs = scrapy.Field()
    success = scrapy.Field()
    exception = scrapy.Field()
    encoding = scrapy.Field()
