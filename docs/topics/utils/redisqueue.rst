.. _redis_queue:

Redis Queue
===========

A utility class that utilizes `Pickle <https://docs.python.org/2/library/pickle.html>`_ serialization by default to store and retrieve arbitrary sets of data in Redis. You may use another encoding mechanism as long as it supports both ``dumps()`` and ``loads()`` methods. The queues come in three basic forms:

- ``RedisQueue`` - A `FIFO <https://en.wikipedia.org/wiki/FIFO_(computing_and_electronics)>`_ queue utilizing a Redis List

- ``RedisStack`` - A `Stack <https://en.wikipedia.org/wiki/Stack_(abstract_data_type)>`_ implementation utilizing a Redis List

- ``RedisPriorityQueue`` - A `Priority Queue <https://en.wikipedia.org/wiki/Priority_queue>`_ utilizing a Redis Sorted Set. This is the queue utilized by the scheduler for prioritized crawls

All three of these classes can handle arbitrary sets of data, and handle the encoding and decoding for you.

.. class:: RedisQueue(server, key, encoding=pickle)

    :param server: The established redis connection
    :param key: The key to use in Redis to store your data
    :param encoding: The serialization module to use

    .. method:: push(item)

        Pushes an item into the Queue

        :param item: The item to insert into the Queue
        :returns: None

    .. method:: pop(timeout=0)

        Removes and returns an item from the Queue

        :param int timeout: If greater than 0, use the Redis blocking pop method for the specified timeout.
        :returns: None if no object can be found, otherwise returns the object.

    .. method:: clear()

        Removes all data in the Queue.

        :returns: None

    .. method:: __len__

        Get the number of items in the Queue.

        :returns: The number of items in the RedisQueue
        :usage: ``len(my_queue_instance)``

.. class:: RedisStack(server, key, encoding=pickle)

    :param server: The established redis connection
    :param key: The key to use in Redis to store your data
    :param encoding: The serialization module to use

    .. method:: push(item)

        Pushes an item into the Stack

        :param item: The item to insert into the Stack
        :returns: None

    .. method:: pop(timeout=0)

        Removes and returns an item from the Stack

        :param int timeout: If greater than 0, use the Redis blocking pop method for the specified timeout.
        :returns: None if no object can be found, otherwise returns the object.

    .. method:: clear()

        Removes all data in the Stack.

        :returns: None

    .. method:: __len__

        Get the number of items in the Stack.

        :returns: The number of items in the RedisStack
        :usage: ``len(my_stack_instance)``

.. class:: RedisPriorityQueue(server, key, encoding=pickle)

    :param server: The established redis connection
    :param key: The key to use in Redis to store your data
    :param encoding: The serialization module to use

    .. method:: push(item, priority)

        Pushes an item into the PriorityQueue

        :param item: The item to insert into the Priority Queue
        :param int priority: The priority of the item. Higher numbered items take precedence over lower priority items.
        :returns: None

    .. method:: pop(timeout=0)

        Removes and returns an item from the PriorityQueue

        :param int timeout: Not used
        :returns: None if no object can be found, otherwise returns the object.

    .. method:: clear()

        Removes all data in the PriorityQueue.

        :returns: None

    .. method:: __len__

        Get the number of items in the PriorityQueue.

        :returns: The number of items in the RedisPriorityQueue
        :usage: ``len(my_pqueue_instance)``

Usage
-----

You can use any of the three classes in the following way, you just need to have a valid Redis connection variable.

::

    >>> import redis
    >>> import ujson
    >>> from scutils.redis_queue import RedisStack
    >>> redis_conn = redis.Redis(host='scdev', port=6379, password=None, decode_responses=True)
    >>> queue = RedisStack(redis_conn, "stack_key", encoding=ujson))
    >>> queue.push('item1')
    >>> queue.push(['my', 'array', 'here'])
    >>> queue.pop()
    [u'my', u'array', u'here']
    >>> queue.pop()
    u'item1'

In the above example, we now have a host at ``scdev`` that is using the key called ``stack_key`` to store our data encoded using the ``ujson`` module.

Example
-------

In this example lets create a simple script that changes what type of Queue we use when pushing three items into it.

::

    import sys
    import redis
    from scutils.redis_queue import RedisStack, RedisQueue, RedisPriorityQueue
    import argparse


    def main():
        parser = argparse.ArgumentParser(description='Example Redis Queues.')
        parser.add_argument('-r', '--redis-host', action='store', default='scdev',
                            help="The Redis host ip")
        parser.add_argument('-rp', '--redis-port', action='store', default='6379',
                            help="The Redis port")
        parser.add_argument('-rP', '--redis-password', action='store', default=None,
                            help="The Redis password")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('-q', '--queue', action='store_true', help="Use a RedisQueue")
        group.add_argument('-s', '--stack', action='store_true',
                            help="Use a RedisStack")
        group.add_argument('-p', '--priority', action='store_true',
                            help="Use a RedisPriorityQueue")

        args = vars(parser.parse_args())

        host = args['redis_host']
        port = args['redis_port']
        password = args['redis_password']
        redis_conn = redis.Redis(host=host, port=port, password=password, decode_responses=True)

        if args['queue']:
            queue = RedisQueue(redis_conn, "my_key")
        elif args['stack']:
            queue = RedisStack(redis_conn, "my_key")
        elif args['priority']:
            queue = RedisPriorityQueue(redis_conn, "my_key")

        print("Using " + queue.__class__.__name__)

        if isinstance(queue, RedisPriorityQueue):
            queue.push("item1", 50)
            queue.push("item2", 100)
            queue.push("item3", 20)
        else:
            queue.push("item1")
            queue.push("item2")
            queue.push("item3")

        print("Pop 1 " + queue.pop())
        print("Pop 2 " + queue.pop())
        print("Pop 3 " + queue.pop())


    if __name__ == "__main__":
        sys.exit(main())

Save the file as ``example_rq.py`` or use the one located at ``utils/examples/example_rq.py``, and now lets run the different tests.

As a queue:

::

    $ python example_rq.py -q
    Using RedisQueue
    Pop 1 item1
    Pop 2 item2
    Pop 3 item3

As a stack:

::

    $ python example_rq.py -s
    Using RedisStack
    Pop 1 item3
    Pop 2 item2
    Pop 3 item1

As a priority queue:

::

    $ python example_rq.py -p
    Using RedisPriorityQueue
    Pop 1 item2
    Pop 2 item1
    Pop 3 item3

The great thing about these Queue classes is that if your process dies, your data still remains in Redis! This allows you to restart your process and it can continue where it left off.
