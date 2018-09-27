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
