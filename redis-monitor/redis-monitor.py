import redis
import sys
import time
import re

from settings import (REDIS_HOST, REDIS_PORT, POLL_INTERVAL)

def main():
    redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    while True:
        # for timeout filtering
        timeout_keys = redis_conn.keys("timeout:*:value")

        if len(timeout_keys) > 0:
            queue_dict = {}
            # so we have one time for everything
            curr_time = time.time()

            for time_key in timeout_keys:
                timeout = float(redis_conn.get(time_key))

                if curr_time > timeout:
                    # everything stored in the queue is now expired
                    crawl_id = re.split(':', time_key)[1]
                    list_name = "timeout:{crawlid}:list".format(
                                                            crawlid=crawl_id)
                    # iterate through list, prepare to remove all values
                    for item in redis_conn.sscan_iter(list_name):
                        queue, key = item.split('||', 1)

                        if queue not in queue_dict:
                            queue_dict[queue] = []

                        queue_dict[queue].append(key)

                    # delete value key
                    redis_conn.delete(time_key)
                    # expire list incase of current crawls that repopulate list
                    redis_conn.expire(list_name, 300)

            # finally wipe everything
            for queue_key in queue_dict:
                redis_conn.zrem(queue_key, *queue_dict[queue_key])

        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # this is just supposed to run in the background
    sys.exit(main())
