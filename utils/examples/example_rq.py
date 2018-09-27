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
