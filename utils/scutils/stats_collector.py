from builtins import object
import redis
import time
from threading import Thread


class StatsCollector(object):
    '''
    A redis based statistics generator class. Use the following methods
    below to generate collectors for various statistic gathering.

    Example usage:

    from utils.stats_collector import StatsCollector
    # create a rolling time window that saves the last 24 hours of hits
    counter = StatsCollector.get_rolling_time_window(
            host='localhost',
            port=6379,
            window=StatsCollector.SECONDS_1_DAY)
    counter.increment()
    print counter.value()
    # that's it!
    '''
    # Easy to use time variables
    SECONDS_1_MINUTE = 60
    SECONDS_15_MINUTE = SECONDS_1_MINUTE * 15
    SECONDS_30_MINUTE = SECONDS_1_MINUTE * 30
    SECONDS_1_HOUR = SECONDS_1_MINUTE * 60
    SECONDS_2_HOUR = SECONDS_1_HOUR * 2
    SECONDS_4_HOUR = SECONDS_1_HOUR * 4
    SECONDS_6_HOUR = SECONDS_1_HOUR * 6
    SECONDS_12_HOUR = SECONDS_1_HOUR * 12
    SECONDS_24_HOUR = SECONDS_1_HOUR * 24
    SECONDS_48_HOUR = SECONDS_1_HOUR * 48
    SECONDS_1_DAY = SECONDS_24_HOUR
    SECONDS_2_DAY = SECONDS_1_DAY * 2
    SECONDS_3_DAY = SECONDS_1_DAY * 3
    SECONDS_7_DAY = SECONDS_1_DAY * 7
    SECONDS_1_WEEK = SECONDS_7_DAY
    SECONDS_30_DAY = SECONDS_1_DAY * 30

    @classmethod
    def get_time_window(self, redis_conn=None, host='localhost', port=6379,
                        key='time_window_counter', cycle_time=5,
                        start_time=None, window=SECONDS_1_HOUR, roll=True,
                        keep_max=12):
        '''
        Generate a new TimeWindow
        Useful for collecting number of hits generated between certain times

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key.
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        '''
        counter = TimeWindow(key=key, cycle_time=cycle_time,
                             start_time=start_time, window=window, roll=roll,
                             keep_max=keep_max)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter

    @classmethod
    def get_rolling_time_window(self, redis_conn=None, host='localhost',
                                port=6379, key='rolling_time_window_counter',
                                cycle_time=5, window=SECONDS_1_HOUR):
        '''
        Generate a new RollingTimeWindow
        Useful for collect data about the number of hits in the past X seconds

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param window: the number of seconds behind now() to keep data for
        '''
        counter = RollingTimeWindow(key=key, cycle_time=cycle_time,
                                    window=window)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter

    @classmethod
    def get_counter(self, redis_conn=None, host='localhost', port=6379,
                    key='counter', cycle_time=5, start_time=None,
                    window=SECONDS_1_HOUR, roll=True, keep_max=12, start_at=0):
        '''
        Generate a new Counter
        Useful for generic distributed counters

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key.
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        @param start_at: The integer to start counting at
        '''
        counter = Counter(key=key, cycle_time=cycle_time,
                          start_time=start_time, window=window, roll=roll,
                          keep_max=keep_max)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter

    @classmethod
    def get_unique_counter(self, redis_conn=None, host='localhost', port=6379,
                           key='unique_counter', cycle_time=5, start_time=None,
                           window=SECONDS_1_HOUR, roll=True, keep_max=12):
        '''
        Generate a new UniqueCounter.
        Useful for exactly counting unique objects

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key.
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        '''
        counter = UniqueCounter(key=key, cycle_time=cycle_time,
                                start_time=start_time, window=window,
                                roll=roll, keep_max=keep_max)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter

    @classmethod
    def get_hll_counter(self, redis_conn=None, host='localhost', port=6379,
                        key='hyperloglog_counter', cycle_time=5,
                        start_time=None, window=SECONDS_1_HOUR, roll=True,
                        keep_max=12):
        '''
        Generate a new HyperLogLogCounter.
        Useful for approximating extremely large counts of unique items

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key.
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        '''
        counter = HyperLogLogCounter(key=key, cycle_time=cycle_time,
                                     start_time=start_time, window=window,
                                     roll=roll, keep_max=keep_max)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter

    @classmethod
    def get_bitmap_counter(self, redis_conn=None, host='localhost', port=6379,
                           key='bitmap_counter', cycle_time=5, start_time=None,
                           window=SECONDS_1_HOUR, roll=True, keep_max=12):
        '''
        Generate a new BitMapCounter
        Useful for creating different bitsets about users/items
        that have unique indices

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key.
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        '''
        counter = BitMapCounter(key=key, cycle_time=cycle_time,
                                start_time=start_time, window=window,
                                roll=roll, keep_max=keep_max)
        counter.setup(redis_conn=redis_conn, host=host, port=port)
        return counter


class AbstractCounter(object):

    def __init__(self, key=None):
        self.redis_conn = None
        if key is not None:
            self.key = key
        else:
            self.key = 'default_counter'

    def setup(self, redis_conn=None, host='localhost', port=6379):
        '''
        Set up the redis connection
        '''
        if redis_conn is None:
            if host is not None and port is not None:
                self.redis_conn = redis.Redis(host=host, port=port)
            else:
                raise Exception("Please specify some form of connection "
                                    "to Redis")
        else:
            self.redis_conn = redis_conn

        self.redis_conn.info()

    def increment(self, **kwargs):
        '''
        Increments the counter by 1 if possible
        '''
        raise NotImplementedError("increment() method not implemented")

    def value(self, **kwargs):
        '''
        Returns the current count
        '''
        raise NotImplementedError("value() method not implemented")

    def expire(self, **kwargs):
        '''
        Expires items from the counter
        '''
        raise NotImplementedError("expire() method not implemented")

    def delete_key(self):
        '''
        Deletes the key being used
        '''
        self.redis_conn.delete(self.get_key())

    def _time(self):
        '''
        Returns the time
        '''
        return time.time()

    def get_key(self):
        '''
        Returns the key string
        '''
        return self.key


class ThreadedCounter(AbstractCounter):

    date_format = '%Y-%m-%d_%H:%M:%S'

    def __init__(self, key='default_counter', cycle_time=5, start_time=None,
                 window=None, roll=False, keep_max=5):
        '''
        A threaded counter, used to help roll time slots

        @param key: the key for your stats collection
        @param cycle_time: how often to check for expiring counts
        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds (if rolling)
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key. Not applicable to the RollingWindow
        @keep_max: If rolling the static window, the max number of prior
            windows to keep
        '''
        AbstractCounter.__init__(self, key=key)

        if start_time is None and window is not None:
            # special case to auto generate correct start time
            the_time = int(self._time())
            floor_time = the_time % window
            self.start_time = the_time - floor_time
        else:
            self.start_time = start_time

        self.keep_max = None
        self.window = None
        self.cycle_time = cycle_time

        if window is not None:
            self.window = window
            self.roll = roll
            if self.roll and keep_max is not None and keep_max > 0:
                self.keep_max = keep_max
        else:
            self.roll = False

        self._set_key()

    def setup(self, redis_conn=None, host='localhost', port=6379):
        '''
        Set up the counting manager class

        @param redis_conn: A premade redis connection (overrides host and port)
        @param host: the redis host
        @param port: the redis port
        '''
        AbstractCounter.setup(self, redis_conn=redis_conn, host=host,
                              port=port)

        self._threaded_start()

    def _threaded_start(self):
        '''
        Spawns a worker thread to do the expiration checks
        '''
        self.active = True
        self.thread = Thread(target=self._main_loop)
        self.thread.setDaemon(True)
        self.thread.start()

    def stop(self):
        '''
        Call to shut down the threaded stats collector
        '''
        self.active = False
        self.thread.join()

    def _main_loop(self):
        '''
        Main loop for the stats collector
        '''
        while self.active:
            self.expire()
            if self.roll and self.is_expired():
                self.start_time = self.start_time + self.window
                self._set_key()
            self.purge_old()
            time.sleep(self.cycle_time)
        self._clean_up()

    def _clean_up(self):
        '''
        Called after the main daemon thread is stopped
        '''
        pass

    def _set_key(self):
        '''
        sets the final key to be used currently
        '''
        if self.roll:
            self.date = time.strftime(self.date_format,
                                      time.gmtime(self.start_time))

            self.final_key = '{}:{}'.format(self.key, self.date)
        else:
            self.final_key = self.key

    def is_expired(self):
        '''
        Returns true if the time is beyond the window
        '''
        if self.window is not None:
            return (self._time() - self.start_time) >= self.window
        return False

    def purge_old(self):
        '''
        Removes keys that are beyond our keep_max limit
        '''
        if self.keep_max is not None:
            keys = self.redis_conn.keys(self.get_key() + ':*')
            keys.sort(reverse=True)
            while len(keys) > self.keep_max:
                key = keys.pop()
                self.redis_conn.delete(key)

    def get_key(self):
        return self.final_key


class TimeWindow(ThreadedCounter):

    def __init__(self, key='time_window_counter', cycle_time=5,
                 start_time=None, window=3600, roll=False, keep_max=None):
        '''
        A static window counter, is only valid for the initialized time range.

        @param start_time: the time to start valid collection
        @param window: how long to collect data for in seconds
        @param roll: Roll the window after it expires, to continue collecting
            on a new date based key
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=start_time, window=window,
                                 roll=roll, keep_max=keep_max)

    def increment(self):
        curr_time = self._time()
        if curr_time - self.start_time < self.window:
            self.redis_conn.zadd(self.final_key, curr_time, curr_time)

    def value(self):
        return self.redis_conn.zcard(self.final_key)

    def expire(self):
        self.redis_conn.zremrangebyscore(self.final_key, '-inf',
                                         self.start_time - 1)
        self.redis_conn.zremrangebyscore(self.final_key,
                                         self.start_time + self.window, 'inf')


class RollingTimeWindow(ThreadedCounter):

    def __init__(self, key='rolling_time_window_counter', cycle_time=5,
                 window=60):
        '''
        A rolling time window. This continuously will have the number of hits
        within X seconds behind the current time.

        @param window: the collection window in seconds
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=None, window=window, roll=False,
                                 keep_max=None)
        self.window = window

    def increment(self):
        now = self._time()
        self.redis_conn.zadd(self.key, now, now)

    def value(self):
        return self.redis_conn.zcard(self.key)

    def expire(self):
        expires = self._time() - self.window
        self.redis_conn.zremrangebyscore(self.key, '-inf', expires)


class Counter(ThreadedCounter):

    def __init__(self, key='counter', cycle_time=5, start_time=None,
                 window=None, roll=False, keep_max=None, start_at=0):
        '''
        A simple integer counter

        @param start_at: where to start the counter
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=start_time, window=window,
                                 roll=roll, keep_max=keep_max)

        self.init = False
        self.start_at = start_at

    def increment(self):
        if not self.init:
            self.redis_conn.set(self.final_key, self.start_at)
            self.init = True
        self.redis_conn.incr(self.final_key)

    def value(self):
        return int(self.redis_conn.get(self.final_key))

    def expire(self):
        pass


class UniqueCounter(ThreadedCounter):

    def __init__(self, key='unique_counter', cycle_time=5, start_time=None,
                 window=None, roll=False, keep_max=None):
        '''
        A unique item counter. Guarantees accuracy at the cost of storage
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=start_time, window=window,
                                 roll=roll, keep_max=keep_max)

    def increment(self, item):
        '''
        Tries to increment the counter by 1, if the item is unique

        @param item: the potentially unique item
        '''
        self.redis_conn.sadd(self.final_key, item)

    def value(self):
        return self.redis_conn.scard(self.final_key)

    def expire(self):
        pass


class HyperLogLogCounter(ThreadedCounter):

    def __init__(self, key='hyperloglog_counter', cycle_time=5,
                 start_time=None, window=None, roll=False, keep_max=None):
        '''
        A unique item counter. Accurate within 1%, max storage of 12k
        http://redis.io/topics/data-types-intro#hyperloglogs
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=start_time, window=window,
                                 roll=roll, keep_max=keep_max)

    def increment(self, item):
        '''
        Tries to increment the counter by 1, if the item is unique

        @param item: the potentially unique item
        '''
        self.redis_conn.execute_command("PFADD", self.final_key, item)

    def value(self):
        return self.redis_conn.execute_command("PFCOUNT", self.final_key)

    def expire(self):
        pass


class BitMapCounter(ThreadedCounter):

    def __init__(self, key='bitmap_counter', cycle_time=5, start_time=None,
                 window=None, roll=False, keep_max=None):
        '''
        A unique counter via bitmaps, see
        http://blog.getspool.com/2011/11/29/fast-easy-realtime-metrics-using-redis-bitmaps/
        for example usages
        '''
        ThreadedCounter.__init__(self, key=key, cycle_time=cycle_time,
                                 start_time=start_time, window=window,
                                 roll=roll, keep_max=keep_max)

    def increment(self, index):
        '''
        @param index: the index to set the flag on
        '''
        self.redis_conn.setbit(self.final_key, index, 1)

    def value(self):
        return self.redis_conn.execute_command("BITCOUNT", self.final_key)

    def expire(self):
        pass
