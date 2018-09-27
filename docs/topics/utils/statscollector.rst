.. _stats_collector:

Stats Collector
===============

The Stats Collector Utility consists of a series of Redis based counting mechanisms, that allow a program to do distributed counting for particular time periods.

There are many useful types of keys within Redis, and this counting Stats Collector allow you to use the following styles of keys:

* Integer values
* Unique values
* HyperLogLog values
* Bitmap values

You can also specify the style of time window you wish to do your collection in. The Stats Collect currently supports the following use cases:

* Sliding window integer counter
* Step based counter for all other types

The sliding window counter allows you to determine `"How many hits have occurred in the last X seconds?"`. This is useful if you wish to know how many hits your API has had in the last hour, or how many times you have handled a particular exception in the past day.

The step based counter allows you to to collect counts based on a rounded time range chunks. This allows you to collect counts of things in meaningful time ranges, like from ``9-10 am``, ``10-11 am``, ``11-12 pm``, etc. The counter incrementally steps through the day, mapping your counter to the aggregated key for your desired time range. If you wanted to collect in 15 minute chunks, the counter steps through any particular hour from ``:00-:15``, ``:15-:30``, ``:30-:45``, and ``:45-:00``. This applies to all time ranges available. When using the step style counters, you can also specify the number of previous steps to keep.

.. note:: The step based counter does not map to the same key once all possible steps have been accounted for. ``9:00 - 9:15 am`` is **not** the same thing as ``10:00 - 10:15am``. or ``9-10 am`` on Monday is **not** the same thing as ``9-10am`` on Tuesday (or next Monday). All steps have a unique key associated with them.

You should use the following static class methods to generate your counter objects.

.. class:: StatsCollector

    These easy to use variables are provided for convenience for setting up your collection windows. Note that some are duplicates for naming convention only.

    :var SECONDS_1_MINUTE: The number of seconds in 1 minute
    :var SECONDS_15_MINUTE: The number of seconds in 15 minutes
    :var SECONDS_30_MINUTE: The number of seconds in 30 minutes
    :var SECONDS_1_HOUR: The number of seconds in 1 hour
    :var SECONDS_2_HOUR: The number of seconds in 2 hours
    :var SECONDS_4_HOUR: The number of seconds in 4 hours
    :var SECONDS_6_HOUR: The number of seconds in 6 hours
    :var SECONDS_12_HOUR: The number of seconds in 12 hours
    :var SECONDS_24_HOUR: The number of seconds in 24 hours
    :var SECONDS_48_HOUR: The number of seconds in 48 hours
    :var SECONDS_1_DAY: The number of seconds in 1 day
    :var SECONDS_2_DAY: The number of seconds in 2 days
    :var SECONDS_3_DAY: The number of seconds in 3 day
    :var SECONDS_7_DAY: The number of seconds in 7 days
    :var SECONDS_1_WEEK:  The number of seconds in 1 week
    :var SECONDS_30_DAY:  The number of seconds in 30 days

    .. method:: get_time_window(redis_conn=None, host='localhost', port=6379, password=None, key='time_window_counter', cycle_time=5, start_time=None, window=SECONDS_1_HOUR, roll=True, keep_max=12)

        Generates a new TimeWindow Counter.
        Useful for collecting number of hits generated between certain times

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int start_time: the time to start valid collection
        :param int window: how long to collect data for in seconds (if rolling)
        :param bool roll: Roll the window after it expires, to continue collecting on a new date based key.
        :param bool keep_max: If rolling the static window, the max number of prior windows to keep
        :returns: A :class:`TimeWindow` counter object.

    .. method:: get_rolling_time_window(redis_conn=None, host='localhost', port=6379, password=None, key='rolling_time_window_counter', cycle_time=5, window=SECONDS_1_HOUR)

        Generates a new RollingTimeWindow.
        Useful for collect data about the number of hits in the past X seconds

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int window: the number of seconds behind now() to keep data for
        :returns: A :class:`RollingTimeWindow` counter object.

    .. method:: get_counter(redis_conn=None, host='localhost', port=6379, password=None, key='counter', cycle_time=5, start_time=None, window=SECONDS_1_HOUR, roll=True, keep_max=12, start_at=0)

        Generate a new Counter.
        Useful for generic distributed counters

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int start_time: the time to start valid collection
        :param int window: how long to collect data for in seconds (if rolling)
        :param bool roll: Roll the window after it expires, to continue collecting on a new date based key.
        :param int keep_max: If rolling the static window, the max number of prior windows to keep
        :param int start_at: The integer to start counting at
        :returns: A :class:`Counter` object.

    .. method:: get_unique_counter(redis_conn=None, host='localhost', port=6379, password=None, key='unique_counter', cycle_time=5, start_time=None, window=SECONDS_1_HOUR, roll=True, keep_max=12)

        Generate a new UniqueCounter.
        Useful for exactly counting unique objects

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int start_time: the time to start valid collection
        :param int window: how long to collect data for in seconds (if rolling)
        :param bool roll: Roll the window after it expires, to continue collecting on a new date based key.
        :param int keep_max: If rolling the static window, the max number of prior windows to keep
        :returns: A :class:`UniqueCounter` object.

    .. method:: get_hll_counter(redis_conn=None, host='localhost', port=6379, password=None, key='hyperloglog_counter', cycle_time=5, start_time=None, window=SECONDS_1_HOUR, roll=True, keep_max=12)

        Generate a new HyperLogLogCounter.
        Useful for approximating extremely large counts of unique items

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int start_time: the time to start valid collection
        :param int window: how long to collect data for in seconds (if rolling)
        :param bool roll: Roll the window after it expires, to continue collecting on a new date based key.
        :param int keep_max: If rolling the static window, the max number of prior windows to keep
        :returns: A :class:`HyperLogLogCounter` object.

    .. method:: get_bitmap_counter(redis_conn=None, host='localhost', port=6379, password=None, key='bitmap_counter', cycle_time=5, start_time=None, window=SECONDS_1_HOUR, roll=True, keep_max=12)

        Generate a new BitMapCounter.
        Useful for creating different bitsets about users/items that have unique indices.

        :param redis_conn: A premade redis connection (overrides host, port and password)
        :param str host: the redis host
        :param int port: the redis port
        :param str password: the redis password
        :param str key: the key for your stats collection
        :param int cycle_time: how often to check for expiring counts
        :param int start_time: the time to start valid collection
        :param int window: how long to collect data for in seconds (if rolling)
        :param bool roll: Roll the window after it expires, to continue collecting on a new date based key.
        :param int keep_max: If rolling the static window, the max number of prior windows to keep
        :returns: A :class:`BitmapCounter` object.

Each of the above methods generates a counter object that works in slightly different ways.

.. class:: TimeWindow

    .. method:: increment()

        Increments the counter by 1.

    .. method:: value()

        :returns: The value of the counter

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

.. class:: RollingTimeWindow

    .. method:: increment()

        Increments the counter by 1.

    .. method:: value()

        :returns: The value of the counter

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

.. class:: Counter

    .. method:: increment()

        Increments the counter by 1.

    .. method:: value()

        :returns: The value of the counter

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

.. class:: UniqueCounter

    .. method:: increment(item)

        Tries to increment the counter by 1, if the item is unique

        :param item: the potentially unique item

    .. method:: value()

        :returns: The value of the counter

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

.. class:: HyperLogLogCounter

    .. method:: increment(item)

        Tries to increment the counter by 1, if the item is unique

        :param item: the potentially unique item

    .. method:: value()

        :returns: The value of the counter

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

.. class:: BitmapCounter

    .. method:: increment(index)

        Sets the bit at the particular index to 1

        :param item: the potentially unique item

    .. method:: value()

        :returns: The number of bits set to 1 in the key

    .. method:: get_key()

        :returns: The string of the key being used

    .. method:: delete_key()

        Deletes the key being used from Redis

Usage
-----

To use any counter, you should import the StatsCollector and use one of the static methods to generate your counting object. From there you can call ``increment()`` to increment the counter and ``value()`` to get the current count of the Redis key being used.

::

    >>> from scutils.stats_collector import StatsCollector
    >>> counter = StatsCollector.get_counter(host='scdev')
    >>> counter.increment()
    >>> counter.increment()
    >>> counter.increment()
    >>> counter.value()
    3
    >>> counter.get_key()
    'counter:2016-01-31_19:00:00'

The key generated by the counter is based off of the UTC time of the machine it is running on. Note here since the default ``window`` time range is ``SECONDS_1_HOUR``, the counter rounded the key down to the appropriate step.

.. warning:: When doing multi-threaded or multi-process counting on the **same key**, all counters operating on that key should be created with the counter style and the same parameters to avoid unintended behavior.

Example
-------

In this example we are going count the number of times a user presses the Space bar while our program continuously runs.

.. note:: You will need the ``py-getch`` module from pip to run this example. ``pip install py-getch``

::

    import argparse
    from getch import getch
    from time import time
    from scutils.stats_collector import StatsCollector

    # set up arg parser
    parser = argparse.ArgumentParser(
        description='Example key press stats collector.\n')
    parser.add_argument('-rw', '--rolling-window', action='store_true',
                        required=False, help="Use a RollingTimeWindow counter",
                        default=False)
    parser.add_argument('-r', '--redis-host', action='store', required=True,
                        help="The Redis host ip")
    parser.add_argument('-p', '--redis-port', action='store', default='6379',
                        help="The Redis port")
    parser.add_argument('-P', '--redis-password', action='store', default=None,
                        help="The Redis password")

    args = vars(parser.parse_args())

    the_window = StatsCollector.SECONDS_1_MINUTE

    if args['rolling_window']:
        counter = StatsCollector.get_rolling_time_window(host=args['redis_host'],
                                                         port=args['redis_port'],
                                                         password=args['redis_password'],
                                                         window=the_window,
                                                         cycle_time=1)
    else:
        counter = StatsCollector.get_time_window(host=args['redis_host'],
                                                         port=args['redis_port'],
                                                         password=args['redis_password'],
                                                         window=the_window,
                                                         keep_max=3)

    print("Kill this program by pressing `ENTER` when done")

    the_time = int(time())
    floor_time = the_time % the_window
    final_time = the_time - floor_time

    pressed_enter = False
    while not pressed_enter:
        print("The current counter value is " + str(counter.value()))
        key = getch()

        if key == '\r' or key == '\n':
            pressed_enter = True
        elif key == ' ':
            counter.increment()

        if not args['rolling_window']:
            new_time = int(time())
            floor_time = new_time % the_window
            new_final_time = new_time - floor_time

            if new_final_time != final_time:
                print("The counter window will roll soon")
                final_time = new_final_time

    print("The final counter value is " + str(counter.value()))
    counter.delete_key()

This code either creates a :class:`TimeWindow` counter, or a :class:`RollingTimeWindow` counter to collect the number of space bar presses that occurs while the program is running (press ``Enter`` to exit). With these two different settings, you can view the count for a specific minute or the count from the last 60 seconds.

Save the above code snippet, or use the example at ``utils/examples/example_sc.py``. When running this example you will get similar results to the following.

::

    $ python example_sc.py -r scdev
    Kill this program by pressing `ENTER` when done
    The current counter value is 0
    The current counter value is 1
    The current counter value is 2
    The current counter value is 3
    The current counter value is 4
    The current counter value is 5
    The current counter value is 6
    The current counter value is 7
    The final counter value is 7

It is fairly straightforward to increment the counter and to get the current value, and with only a bit of code tweaking you could use the other counters that the StatsCollector provides.
