Redis Throttled Queue
=====================

This utility class is a wrapper around the :ref:`Redis Queue <redis_queue>` utility class. Using Redis as a Queue is great, but how do we protect against concurrent data access, if we want more than one process to be pushing and popping from the queue? This is where the RedisThrottleQueue comes in handy.

The ``RedisThrottleQueue`` allows for multi-threaded and/or multiprocess access to the same Redis key being used as a ``RedisQueue``. The throttle acts as a wrapper around the core queue's ``pop()`` method, and permits access to the data only when the throttle allows it. This is highly utilized by Scrapy Cluster's Distributed Scheduler for :ref:`controlling <controlling>` how fast the cluster crawls a particular site.

Redis already has an official `RedLock <http://redis.io/topics/distlock>`_ implementation for doing distributed locks, so why reinvent the wheel? Our locking implementation focuses around Scrapy Cluster's use case, which is rate limiting Request pops to the spiders. We do not need to lock the key when pushing new requests into the queue, only for when we wish to read from it.

If you lock the key, it prevents all other processes from `both` pushing into and popping from the queue. The only guarantee we need to make is that for any particular queue, the transaction to ``pop()`` is `atomic <https://en.wikipedia.org/wiki/Atomicity_(database_systems)>`_. This means that only one process at a time can pop the queue, and it guarantees that no other process was able to pop that same item.

In Scrapy Cluster's use case, it means that when a Spider process says "Give me a Request", we can be certain that no other Spider process has received that exact request. To get a new request, the Throttled Queue tries to execute a series of operations against the lock before any other process can. If another process succeeds in performing the same series of operations before it, that process is returned the item and former is denied. These steps are repeated for all processes trying to pop from the queue at any given time.

In practice, the Redlock algorithm has many safeguards in place to do true concurrent process locking on keys, but as explained above, Scrapy Cluster does not need all of those extra features. Because those features significantly slow down the ``pop()`` mechanism, the ``RedisThrottledQueue`` was born.

.. class:: RedisThrottledQueue(redisConn, myQueue, throttleWindow, throttleLimit, moderate=False, windowName=None, modName=None, elastic=False, elastic_buffer=0)

    :param redisConn: The Redis connection
    :param myQueue: The RedisQueue class instance
    :param int throttleWindow: The time window to throttle pop requests (in seconds).
    :param int throttleLimit: The number of queue pops allows in the time window
    :param int moderation: Queue pop requests are moderated to be evenly distributed throughout the window
    :param str windowName: Use a custom rolling window Redis key name
    :param str modName: Use a custom moderation key name in Redis
    :param elastic: When moderated and falling behind, break moderation to catch up to desired limit
    :param elastic_buffer: The threshold number for how close we should get to the limit when using the elastic catch up

    .. method:: push(*args)

        :param args: The arguments to pass through to the queue's ``push()`` method
        :returns: None

    .. method:: pop(*args)

        :param args: Pop arguments to pass through the the queue's ``pop()`` method
        :returns: None if no object can be found, otherwise returns the object.

    .. method:: clear()

        Removes all data associated with the Throttle and Queue.

        :returns: None

    .. method:: __len__

        :returns: The number of items in the Queue
        :usage: ``len(my_throttled_queue)``

Usage
-----

If you would like to throttle your Redis queue, you need to pass the queue in as part of the ``RedisThrottleQueue`` constructor.

::

    >>> import redis
    >>> from scutils.redis_queue import RedisPriorityQueue
    >>> from scutils.redis_throttled_queue import RedisThrottledQueue
    >>> redis_conn = redis.Redis(host='scdev', port=6379, password=None, decode_responses=True)
    >>> queue = RedisPriorityQueue(redis_conn, 'my_key')
    >>> t = RedisThrottledQueue(redis_conn, queue, 10, 5)
    >>> t.push('item', 5)
    >>> t.push('item2', 10)
    >>> t.pop()
    'item2'
    >>> t.pop()
    'item'

The throttle merely acts as a wrapper around your queue, returning items only when allowed. You can use the same methods the original ``RedisQueue`` provides, like ``push()``, ``pop()``, ``clear()``, and ``__len__``.

.. note:: Due to the distributed nature of the throttled queue, when using the ``elastic=True`` argument the queue must successfully pop the number of ``limit`` items before the elastic catch up will take effect.

Example
-------

The Redis Throttled Queue really shines when multiple processes are trying to pop from the queue. There is a small test script under ``utils/examples/example_rtq.py`` that allows you to tinker with all of the different settings the throttled queue provides. The script is shown below for convenience.

::

    import sys


    def main():

        import argparse
        import redis
        import time
        import random

        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

        from scutils.redis_queue import RedisPriorityQueue
        from scutils.redis_throttled_queue import RedisThrottledQueue

        parser = argparse.ArgumentParser(description="Throttled Queue Test Script."
                        " Start either a single or multiple processes to see the "
                    " throttled queue mechanism in action.")
        parser.add_argument('-r', '--redis-host', action='store', required=True,
                            help="The Redis host ip")
        parser.add_argument('-p', '--redis-port', action='store', default='6379',
                            help="The Redis port")
        parser.add_argument('-P', '--redis-password', action='store', default=None,
                            help="The Redis password")
        parser.add_argument('-m', '--moderate', action='store_const', const=True,
                            default=False, help="Moderate the outbound Queue")
        parser.add_argument('-w', '--window', action='store', default=60,
                            help="The window time to test")
        parser.add_argument('-n', '--num-hits', action='store', default=10,
                            help="The number of pops allowed in the given window")
        parser.add_argument('-q', '--queue', action='store', default='testqueue',
                            help="The Redis queue name")
        parser.add_argument('-e', '--elastic', action='store_const', const=True,
                            default=False, help="Test variable elastic catch up"
                            " with moderation")

        args = vars(parser.parse_args())

        window = int(args['window'])
        num = int(args['num_hits'])
        host = args['redis_host']
        port = args['redis_port']
        password = args['redis_password']
        mod = args['moderate']
        queue = args['queue']
        elastic = args['elastic']

        conn = redis.Redis(host=host, port=port, password=password, decode_responses=True)

        q = RedisPriorityQueue(conn, queue)
        t = RedisThrottledQueue(conn, q, window, num, mod, elastic=elastic)

        def push_items(amount):
            for i in range(0, amount):
                t.push('item-'+str(i), i)

        print("Adding", num * 2, "items for testing")
        push_items(num * 2)

        def read_items():
            print("Kill when satisfied ^C")
            ti = time.time()
            count = 0
            while True:
                item = t.pop()
                if item:
                    print("My item", item, "My time:", time.time() - ti)
                    count += 1

                if elastic:
                    time.sleep(int(random.random() * (t.moderation * 3)))

        try:
            read_items()
        except KeyboardInterrupt:
            pass
        t.clear()
        print("Finished")

    if __name__ == "__main__":
        sys.exit(main())

The majority of this script allows you to alter how the throttled queue is created, most importantly allowing you to change the window, hits, and moderation flag. If you spin up more than one process, you will find that any single 'item' popped from the queue is given to only one process. The latter portion of the script either pushes items into the queue (``item-0`` - ``item-29``) or sits there and tries to ``pop()`` it.

Spinning up two instances with exactly the same settings will give you similar results to the following.

.. warning:: When spinning up multiple processes acting upon the same throttled queue, it is **extremely** important they have the exact same settings! Otherwise your processes will impose different restrictions on the throttle lock with undesired results.

.. note:: Note that each process inserts exactly the same items into the priority queue.

**Process 1**

::

    $ python example_rtq.py -r scdev -w 30 -n 15 -m
    Adding 30 items for testing
    Kill when satisfied ^C
    My item item-29 My time: 0.00285792350769
    My item item-29 My time: 1.99865794182
    My item item-27 My time: 6.05912590027
    My item item-26 My time: 8.05791592598
    My item item-23 My time: 14.0749168396
    My item item-21 My time: 18.078263998
    My item item-20 My time: 20.0878069401
    My item item-19 My time: 22.0930709839
    My item item-18 My time: 24.0957789421
    My item item-14 My time: 36.1192228794
    My item item-13 My time: 38.1225728989
    My item item-11 My time: 42.1282589436
    My item item-8 My time: 48.1387839317
    My item item-5 My time: 54.1379349232
    My item item-2 My time: 64.5046479702
    My item item-1 My time: 66.508150816
    My item item-0 My time: 68.5079059601


**Process 2**

::

    # this script was started slightly after process 1
    $ python example_rtq.py -r scdev -w 30 -n 15 -m
    Adding 30 items for testing
    Kill when satisfied ^C
    My item item-28 My time: 2.95087885857
    My item item-25 My time: 9.01049685478
    My item item-24 My time: 11.023993969
    My item item-22 My time: 15.0343868732
    My item item-17 My time: 28.9568138123
    My item item-16 My time: 31.0645618439
    My item item-15 My time: 33.4570579529
    My item item-12 My time: 39.0780348778
    My item item-10 My time: 43.0874598026
    My item item-9 My time: 45.0917098522
    My item item-7 My time: 49.0903818607
    My item item-6 My time: 51.0908298492
    My item item-4 My time: 59.0306549072
    My item item-3 My time: 61.0654230118

Notice there is a slight drift due to the queue being moderated (most noticeable in process 1), meaning that the throttle `only allows` the queue to be popped after the moderation time has passed. In our case, 30 seconds divided by 15 hits means that the queue should be popped only after 2 seconds has passed.

If we did not pass the ``-m`` for moderated flag, your process output may look like the following.

**Process 1**

::

    $ python example_rtq.py -r scdev -w 10 -n 10
    Adding 20 items for testing
    Kill when satisfied ^C
    My item item-19 My time: 0.00159978866577
    My item item-18 My time: 0.0029239654541
    My item item-17 My time: 0.00445079803467
    My item item-16 My time: 0.00595998764038
    My item item-15 My time: 0.00703096389771
    My item item-14 My time: 0.00823283195496
    My item item-13 My time: 0.00951099395752
    My item item-12 My time: 0.0107297897339
    My item item-11 My time: 0.0118489265442
    My item item-10 My time: 0.0128898620605
    My item item-13 My time: 10.0101749897
    My item item-11 My time: 10.0123429298
    My item item-10 My time: 10.0135369301
    My item item-9 My time: 20.0031509399
    My item item-8 My time: 20.0043399334
    My item item-6 My time: 20.0072448254
    My item item-5 My time: 20.0084438324
    My item item-4 My time: 20.0097179413

**Process 2**

::

    $ python example_rtq.py -r scdev -w 10 -n 10
    Adding 20 items for testing
    Kill when satisfied ^C
    My item item-19 My time: 9.12855100632
    My item item-18 My time: 9.12996697426
    My item item-17 My time: 9.13133692741
    My item item-16 My time: 9.13272404671
    My item item-15 My time: 9.13406801224
    My item item-14 My time: 9.13519310951
    My item item-12 My time: 9.13753604889
    My item item-7 My time: 19.1323649883
    My item item-3 My time: 19.1368720531
    My item item-2 My time: 19.1381940842
    My item item-1 My time: 19.1394021511
    My item item-0 My time: 19.1405911446

Notice that when unmoderated, Process 1 pops all available items in about one hundredth of a second. By the time we switched terminals, Process 2 doesn't have any items to pop and re-adds the 20 items to the queue. In the next 10 second increments, you can see each process receiving items when it is able to successfully pop from the same Redis Queue.

Feel free to mess with the arguments to ``example_rtq.py``, and figure out what kind of pop throttling works best for your use case.

