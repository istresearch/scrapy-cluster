# coding=utf-8
from builtins import object
from unittest import TestCase
import mock
import ujson
import base64
from mock import MagicMock
from crawling.pipelines import (LoggingBeforePipeline, KafkaPipeline)
from crawling.items import RawResponseItem
from copy import deepcopy
from scrapy import Item
from kafka.errors import KafkaTimeoutError


class ItemMixin(object):

    def _get_item(self):
        item = RawResponseItem()
        item['appid'] = 'app'
        item['crawlid'] = 'crawlid'
        item['attrs'] = {}
        item["url"] = "http://dumb.com"
        item["response_url"] = "http://dumb.com"
        item["status_code"] = 200
        item["status_msg"] = "OK"
        item["response_headers"] = {}
        item["request_headers"] = {}
        item["body"] = "text"
        item["links"] = []
        item["encoding"] = "utf-8"

        return item

    def _get_internationalized_utf8_item(self):
        item = RawResponseItem()
        item['appid'] = 'app'
        item['crawlid'] = 'crawlid'
        item['attrs'] = {}
        item["url"] = "http://dumb.com"
        item["response_url"] = "http://dumb.com"
        item["status_code"] = 200
        item["status_msg"] = "OK"
        item["response_headers"] = {}
        item["request_headers"] = {}
        item["body"] = u"This is a test - Αυτό είναι ένα τεστ - 这是一个测试 - これはテストです"
        item["links"] = []
        item["encoding"] = "utf-8"

        return item

    def _get_internationalized_iso_item(self):
        item = RawResponseItem()
        item['appid'] = 'app'
        item['crawlid'] = 'crawlid'
        item['attrs'] = {}
        item["url"] = "http://dumb.com"
        item["response_url"] = "http://dumb.com"
        item["status_code"] = 200
        item["status_msg"] = "OK"
        item["response_headers"] = {}
        item["request_headers"] = {}
        # Fill the item["body"] with the string 'αυτό είναι ένα τεστ' that was encoded in iso-8859-7
        # using iconv and further encoded in base64 in order to store it inside this file.
        item["body"] = base64.b64decode('4fX0/CDl3+3h6SDd7eEg9OXz9Ao=')
        item["links"] = []
        item["encoding"] = "iso-8859-7"

        return item


class TestLoggingBeforePipeline(TestCase, ItemMixin):

    def setUp(self):
        self.pipe = LoggingBeforePipeline(MagicMock())
        self.pipe.logger.name = "crawler"

    def test_process_item(self):
        item = self._get_item()

        spider = MagicMock()
        spider.name = "link"

        self.pipe.logger.info = MagicMock(side_effect=Exception("info"))
        try:
            self.pipe.process_item(item, spider)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "info")

        # test unknown item
        class WeirdItem(Item):
            pass
        item2 = WeirdItem()

        self.pipe.logger.warn = MagicMock(side_effect=Exception("warn"))
        try:
            self.pipe.process_item(item2, spider)
            self.assertFalse(True)
        except Exception as e:
            self.assertEqual(str(e), "warn")


class TestKafkaPipeline(TestCase, ItemMixin):

    def setUp(self):
        self.pipe = KafkaPipeline(MagicMock(), 'prefix', MagicMock(), False, False)
        self.pipe.producer.send = MagicMock()
        self.pipe._get_time = MagicMock(return_value='the time')

    @mock.patch('traceback.format_exc', return_value='traceback')
    def test_process_item(self, e):
        item = self._get_item()
        spider = MagicMock()
        spider.name = "link"

        # test normal send, no appid topics
        self.pipe.process_item(item, spider)
        expected = '{"appid":"app","attrs":{},"body":"text","crawlid":"crawlid","encoding":"utf-8","links":[],"request_headers":{},"response_headers":{},"response_url":"http:\\/\\/dumb.com","status_code":200,"status_msg":"OK","timestamp":"the time","url":"http:\\/\\/dumb.com"}'
        self.pipe.producer.send.assert_called_once_with('prefix.crawled_firehose',
                                                        expected)
        self.pipe.producer.send.reset_mock()

        # test normal send, with appids
        item = self._get_item()
        self.pipe.appid_topics = True
        self.pipe.process_item(item, spider)
        self.pipe.producer.send.assert_called_with('prefix.crawled_app',
                                                    expected)
        self.pipe.producer.send.reset_mock()

        # test base64 encode
        item = self._get_item()
        self.pipe.appid_topics = False
        self.pipe.use_base64 = True
        self.pipe.process_item(item, spider)
        expected = '{"appid":"app","attrs":{},"body":"dGV4dA==","crawlid":"crawlid","encoding":"utf-8","links":[],"request_headers":{},"response_headers":{},"response_url":"http:\\/\\/dumb.com","status_code":200,"status_msg":"OK","timestamp":"the time","url":"http:\\/\\/dumb.com"}'
        self.pipe.producer.send.assert_called_with('prefix.crawled_firehose',
                                                        expected)

        # test base64 encode/decode with utf-8 encoding
        item = self._get_internationalized_utf8_item()
        self.pipe.appid_topics = False
        self.pipe.use_base64 = True
        self.pipe.process_item(item, spider)
        expected = '{"appid":"app","attrs":{},"body":"VGhpcyBpcyBhIHRlc3QgLSDOkc+Fz4TPjCDOtc6vzr3Osc65IM6tzr3OsSDPhM61z4PPhCAtIOi\\/meaYr+S4gOS4qua1i+ivlSAtIOOBk+OCjOOBr+ODhuOCueODiOOBp+OBmQ==","crawlid":"crawlid","encoding":"utf-8","links":[],"request_headers":{},"response_headers":{},"response_url":"http:\\/\\/dumb.com","status_code":200,"status_msg":"OK","timestamp":"the time","url":"http:\\/\\/dumb.com"}'
        self.pipe.producer.send.assert_called_with('prefix.crawled_firehose',
                                                        expected)
        # unpack the arguments used for the previous assertion call
        call_args, call_kwargs = self.pipe.producer.send.call_args
        crawl_args_dict = ujson.loads(call_args[1])
        decoded_string = base64.b64decode(crawl_args_dict['body']).decode(crawl_args_dict['encoding'])
        self.assertEquals(decoded_string, item.get('body'))

        # test base64 encode/decode with iso encoding
        item = self._get_internationalized_iso_item()
        self.pipe.appid_topics = False
        self.pipe.use_base64 = True
        self.pipe.process_item(item, spider)
        expected = '{"appid":"app","attrs":{},"body":"4fX0\\/CDl3+3h6SDd7eEg9OXz9Ao=","crawlid":"crawlid","encoding":"iso-8859-7","links":[],"request_headers":{},"response_headers":{},"response_url":"http:\\/\\/dumb.com","status_code":200,"status_msg":"OK","timestamp":"the time","url":"http:\\/\\/dumb.com"}'
        self.pipe.producer.send.assert_called_with('prefix.crawled_firehose',
                                                   expected)
        # unpack the arguments used for the previous assertion call
        call_args, call_kwargs = self.pipe.producer.send.call_args
        crawl_args_dict = ujson.loads(call_args[1])
        decoded_string = base64.b64decode(crawl_args_dict['body']).decode(crawl_args_dict['encoding'])
        self.assertEquals(decoded_string, item.get('body').decode(item.get('encoding')))
        # Test again against the original (before it was encoded in iso) string
        self.assertEquals(decoded_string, u"αυτό είναι ένα τεστ\n")

        # test kafka exception
        item = self._get_item()
        copy = deepcopy(item)
        copy['success'] = False
        copy['exception'] = 'traceback'

        # send should not crash the pipeline
        self.pipe.producer.send = MagicMock(side_effect=KafkaTimeoutError('bad kafka'))
        ret_val = self.pipe.process_item(item, spider)

