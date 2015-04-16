from scrapy.contrib.downloadermiddleware.retry import RetryMiddleware
from scrapy import log

class RedisRetryMiddleware(RetryMiddleware):

    def __init__(self, settings):
        RetryMiddleware.__init__(self, settings)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1
        if retries <= self.max_retry_times:
            log.msg(format="Retrying %(request)s " \
                            "(failed %(retries)d times): %(reason)s",
                    level=log.DEBUG, spider=spider, request=request,
                    retries=retries, reason=reason)
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            # our priority setup is different from super
            retryreq.meta['priority'] = retryreq.meta['priority'] - 10

            return retryreq
        else:
            log.msg(format="Gave up retrying %(request)s "\
                            "(failed %(retries)d times): %(reason)s",
                    level=log.DEBUG, spider=spider, request=request,
                    retries=retries, reason=reason)
