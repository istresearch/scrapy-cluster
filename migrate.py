import sys


def main():

    import argparse
    import redis
    import time
    import pickle
    import traceback
    import tldextract
    import ujson

    from scutils.redis_queue import RedisPriorityQueue
    from scutils.redis_throttled_queue import RedisThrottledQueue

    parser = argparse.ArgumentParser(description="Scrapy Cluster Migration "
                                     "script. Use to upgrade any part of "
                                     "Scrapy Cluster. Not  recommended for "
                                     "use while your cluster"
                                     " is running.")
    parser.add_argument('-ir', '--input-redis-host', action='store', required=True,
                        help="The input Redis host ip")
    parser.add_argument('-ip', '--input-redis-port', action='store', default='6379',
                        help="The input Redis port")
    parser.add_argument('-id', '--input-redis-db', action='store', default='0',
                        help="The input Redis db")
    parser.add_argument('-iP', '--input-redis-password', action='store', default=None,
                        help="The input Redis password")
    parser.add_argument('-or', '--output-redis-host', action='store', required=False,
                        help="The output Redis host ip, defaults to input", default=None)
    parser.add_argument('-op', '--output-redis-port', action='store', default=None,
                        help="The output Redis port, defaults to input")
    parser.add_argument('-od', '--output-redis-db', action='store', default=None,
                        help="The output Redis db, defaults to input")
    parser.add_argument('-oP', '--output-redis-password', action='store', default=None,
                        help="The output Redis password")
    parser.add_argument('-sv', '--start-version', action='store', type=float,
                        help="The current cluster version", required=True,
                        choices=[1.0, 1.1])
    parser.add_argument('-ev', '--end-version', action='store', default=1.2,
                        help="The desired cluster version", required=True,
                        choices=[1.1, 1.2], type=float)
    parser.add_argument('-v', '--verbosity', action='store',
                        required=False, default=0,
                        help="Increases output text verbosity",
                        choices=[0, 1, 2], type=int)
    parser.add_argument('-y', '--yes', action='store_const',
                        required=False, default=False, const=True,
                        help="Answer 'yes' to any prompt")

    args = vars(parser.parse_args())
    current_version = args['start_version']
    end_version = args['end_version']

    if end_version < current_version:
        vprint("Downgrading is not supported at this time")
        sys.exit(1)

    verbose = args['verbosity']

    irh = args['input_redis_host']
    irp = args['input_redis_port']
    ird = args['input_redis_db']
    irP = args['input_redis_password']
    orh = args['output_redis_host'] if args['output_redis_host'] is not None else irh
    orp = args['output_redis_port'] if args['output_redis_port'] is not None else irp
    ord = args['output_redis_db'] if args['output_redis_db'] is not None else ird
    orP = args['output_redis_password']

    def vprint(s, v=0):
        if v <= args['verbosity']:
            print s

    # from http://stackoverflow.com/questions/3041986/python-command-line-yes-no-input
    def query_yes_no(question, default="yes"):
        """Ask a yes/no question via raw_input() and return their answer.

        "question" is a string that is presented to the user.
        "default" is the presumed answer if the user just hits <Enter>.
            It must be "yes" (the default), "no" or None (meaning
            an answer is required of the user).

        The "answer" return value is True for "yes" or False for "no".
        """
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")

    drop_queue = False
    if irh == orh and ird == ord and irp == orp and args['end_version'] >= 1.2:
        print "Warning! Exact same Redis settings detected, migration will "\
            "need to delete data before it is complete in order to "\
            "be successful."

        print args['yes']
        result = query_yes_no("Continue?") if not args['yes'] else True
        if result:
            drop_queue = True
        else:
            sys.exit(0)

    start_time = time.time()
    i_redis_conn = redis.Redis(host=irh, port=irp, db=ird, password=irP)
    o_redis_conn = redis.Redis(host=orh, port=orp, db=ord, password=orP)

    try:
        # Upgrade 1.0 to 1.1
        if current_version == 1.0 and end_version > current_version:
            vprint("Upgrading Cluster from 1.0 to 1.1")
            extract = tldextract.TLDExtract()
            queue_keys = i_redis_conn.keys("*:queue")

            for queue in queue_keys:
                elements = queue.split(":")
                spider = elements[0]

                if len(elements) == 2:
                    vprint("Upgrading " + spider + "spider")

                    old_count = i_redis_conn.zcard(queue)

                    current_count = 0
                    # loop through all elements
                    for item in i_redis_conn.zscan_iter(queue):
                        current_count += 1

                        if current_count % 10 == 0:
                            vprint("count: " + str(current_count), 2)

                        item_key = item[0]
                        try:
                            item = pickle.loads(item_key)
                        except:
                            vprint("Found unloadable item, skipping", 1)
                            continue

                        # format key
                        ex_res = extract(item['url'])
                        key = "{sid}:{dom}.{suf}:queue".format(
                            sid=item['spiderid'],
                            dom=ex_res.domain,
                            suf=ex_res.suffix)

                        val = pickle.dumps(item, protocol=-1)

                        # shortcut to shove stuff into the priority queue
                        o_redis_conn.zadd(key, {val: -item['priority']})

                    # loop through all new keys
                    new_count = 0
                    for key in o_redis_conn.keys('{s}:*:queue'.format(s=spider)):
                        new_count = new_count + i_redis_conn.zcard(key)

                    if new_count == old_count:
                        vprint("Successfully migrated " + str(new_count) + "requests for"
                            + spider + "spider")
                        i_redis_conn.delete(queue)
                    else:
                        vprint("Unknown error when migrating requests {o}/{n}"
                                .format(o=old_count, n=new_count))
                        result = query_yes_no("Continue?") if not args['yes'] else True
                        if result:
                            pass
                        else:
                            sys.exit(0)

            current_version = 1.1

        # Upgrade 1.1 to 1.2
        if current_version == 1.1 and end_version > current_version:
            vprint("Upgrading Cluster from 1.1 to 1.2")
            queue_keys = i_redis_conn.keys("*:*:queue")

            for queue in queue_keys:
                elements = queue.split(":")
                cache = []

                if len(elements) == 3:
                    spider = elements[0]
                    domain = elements[1]

                    old_count = i_redis_conn.zcard(queue)

                    vprint("Working on key " + queue, 1)

                    # loop through all elements
                    current_count = 0
                    for item in i_redis_conn.zscan_iter(queue):
                        current_count += 1
                        if current_count % 10 == 0:
                            vprint("count: " + str(current_count), 2)

                        item_key = item[0]

                        # load and cache request
                        try:
                            item = pickle.loads(item_key)
                            cache.append(item)
                        except:
                            vprint("Found unloadable item, skipping", 1)
                            continue

                    # done geting all elements, drop queue if needed
                    if drop_queue:
                        vprint("Dropping queue " + queue, 1)
                        i_redis_conn.delete(queue)

                    # insert cached items back in
                    vprint("Updating queue " + queue, 1)
                    current_count = 0
                    for item in cache:
                        current_count += 1
                        if current_count % 10 == 0:
                            vprint("count: " + str(current_count), 2)
                        val = ujson.dumps(item)
                        # shortcut to shove stuff into the priority queue
                        o_redis_conn.zadd(queue, {val: -item['priority']})

                    new_count = o_redis_conn.zcard(queue)

                    if new_count == old_count:
                        vprint("Successfully migrated " + str(new_count) +
                            " requests for " + domain + " " + spider + "spider")
                    else:
                        vprint("Unknown error when migrating requests {o}/{n}"
                                .format(o=old_count, n=new_count))
                        result = query_yes_no("Continue?") if not args['yes'] else True
                        if result:
                            pass
                        else:
                            sys.exit(0)

            current_version = 1.2

    except Exception as e:
        vprint("Error Upgrading Cluster.")
        vprint(traceback.print_exc())
        sys.exit(1)

    completion_time = int(time.time() - start_time)
    print "Cluster upgrade complete in", "%.2f" % completion_time, "seconds."
    vprint("Upgraded cluster from " + str(args['start_version']) + " to "
          + str(args['end_version']))

if __name__ == "__main__":
    sys.exit(main())
