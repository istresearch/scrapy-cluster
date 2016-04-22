'''
Offline utility tests
'''
from unittest import TestCase
from scutils.stats_collector import AbstractCounter


class TestStatsAbstract(TestCase):

    def test_default_key(self):
        ac = AbstractCounter()
        self.assertEqual('default_counter', ac.get_key())

    def test_overloaded_key(self):
        ac = AbstractCounter('aKey')
        self.assertEqual('aKey', ac.get_key())

    def test_not_implemented(self):
        ac = AbstractCounter()

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.value()
            self.fail("value should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.expire()
            self.fail("expire should be abstract")
        except NotImplementedError:
            pass

        try:
            ac.increment()
            self.fail("increment should be abstract")
        except NotImplementedError:
            pass
