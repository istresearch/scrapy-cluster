from __future__ import absolute_import
import scrapy

from scrapy.http import Request
from scrapy_splash import SplashRequest
from crawling.spiders.lxmlhtml import CustomLxmlLinkExtractor as LinkExtractor
from scrapy.conf import settings

from crawling.items import RawResponseItem
from crawling.spiders.redis_spider import RedisSpider


class LinkSpider(RedisSpider):
    '''
    A spider that walks all links from the requested URL. This is
    the entrypoint for generic crawling.
    '''
    name = "link"

    def __init__(self, *args, **kwargs):
        super(LinkSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        final_url = response.url if 'url' not in response.meta else response.meta['url']
        self._logger.debug("crawled url {}".format(final_url))
        cur_depth = 0
        if 'curdepth' in response.meta:
            cur_depth = response.meta['curdepth']

        # capture raw response
        item = RawResponseItem()
        # populated from response.meta
        item['appid'] = response.meta['appid']
        item['crawlid'] = response.meta['crawlid']
        item['attrs'] = response.meta['attrs']

        # populated from raw HTTP response
        item["url"] = final_url
        item["response_url"] = final_url
        item["status_code"] = response.status
        item["status_msg"] = "OK"
        item["response_headers"] = self.reconstruct_headers(response)
        item["request_headers"] = response.request.headers
        item["body"] = response.body
        item["links"] = []

        # determine whether to continue spidering
        if cur_depth >= response.meta['maxdepth']:
            self._logger.debug("Not spidering links in '{}' because" \
                " cur_depth={} >= maxdepth={}".format(
                                                      response.url,
                                                      cur_depth,
                                                      response.meta['maxdepth']))
        else:
            # we are spidering -- yield Request for each discovered link
            link_extractor = LinkExtractor(
                            allow_domains=response.meta['allowed_domains'],
                            allow=response.meta['allow_regex'],
                            deny=response.meta['deny_regex'],
                            deny_extensions=response.meta['deny_extensions'])

            for link in link_extractor.extract_links(response):
                # link that was discovered
                the_url = link.url
                the_url = the_url.replace('\n', '')
                item["links"].append({"url": the_url, "text": link.text, })

                if 'splash' not in response.meta:
                    req = Request(the_url, callback=self.parse)
                else:
                    req = SplashRequest(the_url, callback=self.parse)

                req.meta['priority'] = response.meta['priority'] - 10
                req.meta['curdepth'] = response.meta['curdepth'] + 1

                if 'useragent' in response.meta and \
                        response.meta['useragent'] is not None:
                    req.headers['User-Agent'] = response.meta['useragent']

                self._logger.debug("Trying to follow link '{}'".format(the_url))
                yield req

        # raw response has been processed, yield to item pipeline
        yield item
