from scrapy.http import Request
from scutils.log_factory import LogFactory


class MetaPassthroughMiddleware(object):

    def __init__(self, settings):
        self.setup(settings)

    def setup(self, settings):
        '''
        Does the actual setup of the middleware
        '''
        # set up the default sc logger
        my_level = settings.get('SC_LOG_LEVEL', 'INFO')
        my_name = settings.get('SC_LOGGER_NAME', 'sc-logger')
        my_output = settings.get('SC_LOG_STDOUT', True)
        my_json = settings.get('SC_LOG_JSON', False)
        my_dir = settings.get('SC_LOG_DIR', 'logs')
        my_bytes = settings.get('SC_LOG_MAX_BYTES', '10MB')
        my_file = settings.get('SC_LOG_FILE', 'main.log')
        my_backups = settings.get('SC_LOG_BACKUPS', 5)

        self.logger = LogFactory.get_instance(json=my_json,
                                         name=my_name,
                                         stdout=my_output,
                                         level=my_level,
                                         dir=my_dir,
                                         file=my_file,
                                         bytes=my_bytes,
                                         backups=my_backups)

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_spider_output(self, response, result, spider):
        '''
        Ensures the meta data from the response is passed
        through in any Request's generated from the spider
        '''
        self.logger.debug("processing meta passthrough middleware")
        for x in result:
            # only operate on requests
            if isinstance(x, Request):
                self.logger.debug("found request")
                # pass along all known meta fields, only if
                # they were not already set in the spider's new request
                for key in list(response.meta.keys()):
                    if key not in x.meta:
                        x.meta[key] = response.meta[key]
            yield x
