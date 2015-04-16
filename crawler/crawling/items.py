# -*- coding: utf-8 -*-

# Define here the models for your scraped items

from scrapy import Item, Field


class RawResponseItem(Item):
    appid = Field()
    crawlid = Field()
    url = Field()
    response_url = Field()
    status_code = Field()
    status_msg = Field()
    headers = Field()
    body = Field()
    links = Field()
    image_urls = Field()
    ts = Field()
    attrs = Field()
    onion = Field()

class ErrorResponseItem(Item):
    logger = Field()
    error_request = Field()
    error_reason = Field()
    retry_count = Field()
    status_code = Field()
