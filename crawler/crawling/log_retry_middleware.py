import logging

from scrapy.xlib.tx import ResponseFailed
from twisted.internet import defer
from twisted.internet.error import TimeoutError, DNSLookupError, \
        ConnectionRefusedError, ConnectionDone, ConnectError, \
        ConnectionLost, TCPTimedOutError


class LogRetryMiddleware(object):

    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError)

    def __init__(self, settings):
        # set up the default sc logger
        self.logger = logging.getLogger('scrapy-cluster')
        self.logger.setLevel(logging.DEBUG)
        self.retry_http_codes = set(int(x) for x in
                                    settings.getlist('RETRY_HTTP_CODES'))

    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    @classmethod
    def from_crawler(cls, crawler):
        return cls.from_settings(crawler.settings)

    def process_exception(self, request, exception, spider):
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            self._log_retry(request, exception, spider)

    def _log_retry(self, request, exception, spider):
        extras = {}
        extras['logger'] = self.logger.name
        extras['error_request'] = request
        extras['error_reason'] = exception
        extras['retry_count'] = request.meta.get('retry_times', 0)
        extras['status_code'] = 504
        extras['appid'] = request.meta['appid']
        extras['crawlid'] = request.meta['crawlid']
        extras['url'] = request.url

        self.logger.error('Scraper Retry', extra=extras)
