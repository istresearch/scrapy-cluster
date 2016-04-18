'''
Offline tests
'''
from unittest import TestCase
from mock import MagicMock

from crawling.spiders.redis_spider import RedisSpider


class OverrideSpider(RedisSpider):
        name = 'OverrideSpider'


class TestRedisSpider(TestCase):

    def setUp(self):
        self.spider = OverrideSpider()
        self.spider.settings = {}
        self.spider.redis_conn = MagicMock()
        self.spider._logger = MagicMock()
        self.spider.settings['STATS_CYCLE'] = 5
        self.spider.settings['STATS_TIMES'] = []
        self.spider.settings['STATS_RESPONSE_CODES'] = []
        self.spider._get_hostname = MagicMock(return_value='host1')

    def test_load_stats_codes(self):
        self.spider.stats_dict = {}

        # test nothing
        self.spider._setup_stats_status_codes()
        self.assertEquals(self.spider.stats_dict['status_codes'].keys(), [])

        # test status codes only
        self.spider.settings['STATS_RESPONSE_CODES'] = [200, 403]
        self.spider._setup_stats_status_codes()
        self.assertEquals(
            sorted(self.spider.stats_dict['status_codes'].keys()),
            sorted([200, 403]))
        self.assertEqual(self.spider.stats_dict['status_codes'][200].keys(),
                         ['lifetime'])
        self.assertEqual(self.spider.stats_dict['status_codes'][403].keys(),
                         ['lifetime'])

        # test good/bad rolling stats
        self.spider.stats_dict = {}
        self.spider.settings['STATS_TIMES'] = [
            'SECONDS_15_MINUTE',
            'SECONDS_1_HOUR',
            'SECONDS_DUMB',
        ]
        good = [
            'lifetime',  # for totals, not DUMB
            900,
            3600,
        ]

        # check that both keys are set up
        self.spider._setup_stats_status_codes()
        self.assertEquals(
            sorted(self.spider.stats_dict['status_codes'][200].keys()),
            sorted(good))
        self.assertEquals(
            sorted(self.spider.stats_dict['status_codes'][403].keys()),
            sorted(good))

        k1 = 'stats:crawler:host1:OverrideSpider:200'
        k2 = 'stats:crawler:host1:OverrideSpider:403'

        for time_key in self.spider.stats_dict['status_codes'][200]:
            if time_key == 0:
                self.assertEquals(
                    self.spider.stats_dict['status_codes'][200][0].key,
                    '{k}:lifetime'.format(k=k1)
                    )
            else:
                self.assertEquals(
                    self.spider.stats_dict['status_codes'][200][time_key].key,
                    '{k}:{t}'.format(k=k1, t=time_key)
                    )

        for time_key in self.spider.stats_dict['status_codes'][403]:
            if time_key == 0:
                self.assertEquals(
                    self.spider.stats_dict['status_codes'][403][0].key,
                    '{k}:lifetime'.format(k=k2)
                    )
            else:
                self.assertEquals(
                    self.spider.stats_dict['status_codes'][403][time_key].key,
                    '{k}:{t}'.format(k=k2, t=time_key)
                    )
