import redis
from scutils.redis_queue import RedisStack, RedisQueue, RedisPriorityQueue
import argparse

# change these for your Redis host
host = 'scdev'
port = 6379
redis_conn = redis.Redis(host=host, port=port)

parser = argparse.ArgumentParser(description='Example Redis Queues.')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-q', '--queue', action='store_true', help="Use a RedisQueue")
group.add_argument('-s', '--stack', action='store_true',
                       help="Use a RedisStack")
group.add_argument('-p', '--priority', action='store_true',
                       help="Use a RedisPriorityQueue")

args = vars(parser.parse_args())

if args['queue']:
    queue = RedisQueue(redis_conn, "my_key")
elif args['stack']:
    queue = RedisStack(redis_conn, "my_key")
elif args['priority']:
    queue = RedisPriorityQueue(redis_conn, "my_key")

print "Using " + queue.__class__.__name__

if isinstance(queue, RedisPriorityQueue):
    queue.push("item1", 50)
    queue.push("item2", 100)
    queue.push("item3", 20)
else:
    queue.push("item1")
    queue.push("item2")
    queue.push("item3")

print "Pop 1 " + queue.pop()
print "Pop 2 " + queue.pop()
print "Pop 3 " + queue.pop()