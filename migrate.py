import sys


def main():

    import argparse
    import redis
    import time
    import pickle
    import traceback
    import tldextract

    from scutils.redis_queue import RedisPriorityQueue
    from scutils.redis_throttled_queue import RedisThrottledQueue

    parser = argparse.ArgumentParser(description="Scrapy Cluster Migration "
                                     "script. Use to upgrade any part of "
                                     "Scrapy Cluster. Not  recommended for "
                                     "use while your cluster"
                                     " is running.")
    parser.add_argument('-r', '--redis-host', action='store', required=True,
                        help="The Redis host ip")
    parser.add_argument('-p', '--redis-port', action='store', default='6379',
                        help="The Redis port")

    parser.add_argument('-sv', '--start-version', action='store',
                        help="The current cluster version", required=True,
                        choices=['1.0'])
    parser.add_argument('-ev', '--end-version', action='store', default='1.1',
                        help="The desired cluster version", required=True,
                        choices=['1.1'])

    args = vars(parser.parse_args())
    current_version = args['start_version']
    start_time = time.time()
    redis_conn = redis.Redis(args['redis_host'], args['redis_port'])

    try:
        # in the future there may be more versions that need upgraded

        # Upgrade 1.0 to 1.1
        if current_version == '1.0':
            print "Upgrading Cluster from 1.0 to 1.1"
            extract = tldextract.TLDExtract()
            queue_keys = redis_conn.keys("*:queue")

            for queue in queue_keys:
                elements = queue.split(":")
                spider = elements[0]

                if len(elements) == 2:
                    print "Upgrading", spider, "spider"

                    old_count = redis_conn.zcard(queue)

                    # loop through all elements
                    for item in redis_conn.zscan_iter(queue):
                        item_key = item[0]
                        item = pickle.loads(item_key)

                        # format key
                        ex_res = extract(item['url'])
                        key = "{sid}:{dom}.{suf}:queue".format(
                            sid=item['spiderid'],
                            dom=ex_res.domain,
                            suf=ex_res.suffix)

                        val = pickle.dumps(item, protocol=-1)

                        # shortcut to shove stuff into the priority queue
                        redis_conn.zadd(key, val, -item['priority'])

                    # loop through all new keys
                    new_count = 0
                    for key in redis_conn.keys('{s}:*:queue'.format(s=spider)):
                        new_count = new_count + redis_conn.zcard(key)

                    if new_count == old_count:
                        print "Successfully migrated", new_count, "requests for",\
                            spider, "spider"
                        redis_conn.delete(queue)
                    else:
                        print "Unknown error when migrating requessts {o}/{n}"\
                                .format(o=old_count, n=new_count)
                        sys.exit(1)

            current_version = '1.1'

    except Exception as e:
        print "Error Upgrading Cluster."
        print traceback.print_exc()
        sys.exit(1)

    completion_time = int(start_time - time.time())
    print "Cluster upgrade complete in", "%.2f" % completion_time, "seconds."
    print "Upgraded cluster from " + args['start_version'] + " to " \
          + args['end_version']

if __name__ == "__main__":
    sys.exit(main())