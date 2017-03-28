from link_spider import LinkSpider

import scrapy

import re, json
from collections import Counter


class KeywordSpider(LinkSpider):
    """
    Extends LinkSpider. This spider first sends the counts of keywords found at
    the URL to a database. Then is does the work of a LinkSpider.
    """
    name = "keyword"
    _words_regex = re.compile('[a-z]+')

    def __init__(self, *args, **kwargs):
        super(KeywordSpider, self).__init__(*args, **kwargs)
        self._mm_keywords = self._get_merchant_monitoring_keywords()

    def parse(self, response):
        self._report_keywords(response)
        return super(KeywordSpider, self).parse(response)

    def _report_keywords(self, response):
        text = ' '.join(response.xpath("//body//text()").extract())
        # [RMW -- 2/14/2017] This is a far from perfect use of response.xpath,
        # but it shows us how we can use response to extract text, from which
        # we can extract keywords.
        # response is this type:
        # https://doc.scrapy.org/en/latest/topics/request-response.html#textresponse-objects
        # The return value of response.xpath is this type:
        # https://doc.scrapy.org/en/latest/topics/selectors.html#selectorlist-objects
        words = self._words_regex.findall(text)
        counts = Counter(w for w in words if w in self._mm_keywords)
        result = {response.request.url: counts}

        with open('/tmp/keywords.txt', 'a') as f:
            f.write(json.dumps(result))
            f.write('\n\n')

    def _get_merchant_monitoring_keywords(self):
        return {
            'a',
            'and',
            'the',
            'legitscript'
        }
