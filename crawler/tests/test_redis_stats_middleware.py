from unittest import TestCase
from mock import MagicMock
from crawling.redis_stats_middleware import RedisStatsMiddleware
from scrapy.http import Response
from scrapy import Item
import mock

class TestRedisStatsMiddleware(TestCase):

    @mock.patch('crawling.redis_stats_middleware' \
                '.RedisStatsMiddleware.setup')
    def setUp(self, s):
        self.rsm = RedisStatsMiddleware(MagicMock())
        self.rsm.logger = MagicMock()
        self.rsm.logger.debug = MagicMock()
        self.rsm.redis_conn = MagicMock()
        self.rsm.stats_dict = {}
        self.rsm.settings = {}
        self.rsm.settings['STATS_CYCLE'] = 5
        self.rsm.settings['STATS_TIMES'] = []
        self.rsm.settings['STATS_RESPONSE_CODES'] = []
        self.rsm._get_hostname = MagicMock(return_value='host1')

    def test_load_stats_codes(self):
        # test nothing
        spider_name = 'link'
        self.rsm._setup_stats_status_codes(spider_name)
        self.assertEqual(list(self.rsm.stats_dict[spider_name]['status_codes'].keys()), [])

        # test status codes only
        self.rsm.settings['STATS_RESPONSE_CODES'] = [200, 403]
        self.rsm._setup_stats_status_codes(spider_name)
        self.assertEqual(
            sorted(self.rsm.stats_dict[spider_name]['status_codes'].keys()),
            sorted([200, 403]))
        self.assertEqual(list(self.rsm.stats_dict[spider_name]['status_codes'][200].keys()),
                         ['lifetime'])
        self.assertEqual(list(self.rsm.stats_dict[spider_name]['status_codes'][403].keys()),
                         ['lifetime'])

        # test good/bad rolling stats
        self.rsm.stats_dict = {}
        self.rsm.settings['STATS_TIMES'] = [
            'SECONDS_15_MINUTE',
            'SECONDS_1_HOUR',
            'SECONDS_DUMB',
        ]
        good = [
            'lifetime',  # for totals, not DUMB
            '900',
            '3600',
        ]

        # check that both keys are set up
        self.rsm._setup_stats_status_codes(spider_name)
        self.assertEqual(
            sorted([str(x) for x in self.rsm.stats_dict[spider_name]['status_codes'][200].keys()]),
            sorted(good))
        self.assertEqual(
            sorted([str(x) for x in self.rsm.stats_dict[spider_name]['status_codes'][403].keys()]),
            sorted(good))

        k1 = 'stats:crawler:host1:link:200'
        k2 = 'stats:crawler:host1:link:403'

        for time_key in self.rsm.stats_dict[spider_name]['status_codes'][200]:
            if time_key == 0:
                self.assertEqual(
                    self.rsm.stats_dict[spider_name]['status_codes'][200][0].key,
                    '{k}:lifetime'.format(k=k1)
                    )
            else:
                self.assertEqual(
                    self.rsm.stats_dict[spider_name]['status_codes'][200][time_key].key,
                    '{k}:{t}'.format(k=k1, t=time_key)
                    )

        for time_key in self.rsm.stats_dict[spider_name]['status_codes'][403]:
            if time_key == 0:
                self.assertEqual(
                    self.rsm.stats_dict[spider_name]['status_codes'][403][0].key,
                    '{k}:lifetime'.format(k=k2)
                    )
            else:
                self.assertEqual(
                    self.rsm.stats_dict[spider_name]['status_codes'][403][time_key].key,
                    '{k}:{t}'.format(k=k2, t=time_key)
                    )

    def test_rsm_input(self):
        responses = [
            Response('http://istresearch.com', status=200),
            Response('http://istresearch.com', status=400),
            Response('http://istresearch.com', status=404),
            Response('http://istresearch.com', status=200),
            Response('http://istresearch.com', status=999),
        ]

        self.rsm.settings['STATS_TIMES'] = [
            'lifetime'
        ]
        self.rsm.settings['STATS_RESPONSE_CODES'] = [200, 400, 404]
        self.rsm.settings['STATS_STATUS_CODES'] = True

        fake_stats = MagicMock()
        fake_stats.increment = MagicMock()

        self.rsm.stats_dict = {
            'link': {
                'status_codes': {
                    200: {
                        'lifetime': fake_stats
                    },
                    400: {
                        'lifetime': fake_stats
                    },
                    404: {
                        'lifetime': fake_stats
                    }
                }
            },
            'wandering': {
                'status_codes': {
                    200: {
                        'lifetime': fake_stats
                    },
                    400: {
                        'lifetime': fake_stats
                    },
                    404: {
                        'lifetime': fake_stats
                    }
                }
            }
        }

        for name in ['link', 'wandering']:
            spider = MagicMock()
            spider.name = name
            for response in responses:
                self.rsm.process_spider_input(response, spider)

        # 4 calls for link, 4 calls for wandering
        self.assertEqual(fake_stats.increment.call_count, 8)


