from link_spider import LinkSpider
from crawling.items import KeywordsItem

import scrapy
from bs4 import BeautifulSoup

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
        text = BeautifulSoup(response.body).get_text().lower()
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
