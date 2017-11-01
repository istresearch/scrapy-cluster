'''
Offline tests
'''
from unittest import TestCase
import mock
from mock import MagicMock
from crawling.log_retry_middleware import LogRetryMiddleware


class TestLogRetryMiddlewareStats(TestCase):

    @mock.patch('crawling.log_retry_middleware.LogRetryMiddleware' \
                '.setup')
    def setUp(self, s):
        self.lrm = LogRetryMiddleware(MagicMock())
        self.lrm.settings = {}
        self.lrm.name = 'OverrideSpider'
        self.lrm.redis_conn = MagicMock()
        self.lrm.logger = MagicMock()
        self.lrm.settings['STATS_CYCLE'] = 5
        self.lrm.settings['STATS_TIMES'] = []
        self.lrm._get_hostname = MagicMock(return_value='host1')

    def test_lrm_stats_setup(self):
        self.lrm.stats_dict = {}

        # test nothing
        self.lrm._setup_stats_status_codes()
        self.assertEqual([str(x) for x in self.lrm.stats_dict.keys()], ['lifetime'])

        # test good/bad rolling stats
        self.lrm.stats_dict = {}
        self.lrm.settings['STATS_TIMES'] = [
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
        self.lrm._setup_stats_status_codes()
        self.assertEqual(
            sorted([str(x) for x in self.lrm.stats_dict.keys()]),
            sorted(good))

        k1 = 'stats:crawler:host1:OverrideSpider:504'

        for time_key in self.lrm.stats_dict:
            if time_key == 0:
                self.assertEqual(
                    self.lrm.stats_dict[0].key,
                    '{k}:lifetime'.format(k=k1)
                    )
            else:
                self.assertEqual(
                    self.lrm.stats_dict[time_key].key,
                    '{k}:{t}'.format(k=k1, t=time_key)
                    )
