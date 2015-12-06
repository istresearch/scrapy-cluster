Redis Queue
===========

A utility class that utilizes Pickle encoding to store and retrieve arbitrary sets of data in Redis. The queues come in three basic forms:

- ``RedisQueue`` - A FIFO queue utilizing a Redis List

- ``RedisStack`` - A Stack implementation utilizing a Redis List

- ``RedisPriorityQueue`` - A prioritized queue utilizing a Redis Sorted Set. This is the queue utilized by the scheduler for prioritized crawls

All three of these classes can handle arbitrary sets of data, and handle the pickle encoding and decoding for you.

Usage
-----