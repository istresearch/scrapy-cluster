from __future__ import division
from builtins import str
from builtins import object
from past.utils import old_div
import time

from redis.exceptions import WatchError


class RedisThrottledQueue(object):

    queue = None    # the instantiated queue class
    window = None   # the window to use to limit requests
    limit = None    # number of requests in the given window
    redis_conn = None   # the redis connection
    moderation = None   # whether to use moderation or not
    moderate_key = None     # the last time the moderated queue was pulled
    window_append = ":throttle_window"  # appended to end of window queue key
    time_append = ":throttle_time"  # appended to end to time key
    elastic = False # use elastic catch up
    elastic_buffer = 0 # tolerance
    elastic_kick_in = 0 # counter to get to limit before elastic kicks in

    def __init__(self, redisConn, myQueue, throttleWindow, throttleLimit,
                        moderate=False, windowName=None, modName=None,
                        elastic=False, elastic_buffer=0):
        '''
        For best performance, all instances of a throttled queue should have
            the same settings
        Limits outbound flow (pop) from any Redis Queue, does not hinder pushes
        This queue is also temporary, which is why is is a bit complex

        @param redis: The redis connection to use
        @param queueClass: The instantiated RedisQueue class
            (Queue, Stack, Priority)
        @param throttleWindow: The time window to throttle pop requests (secs)
        @param throttleLimit: The number of pops allows in a given time window
        @param moderation: Set to True if you would like the queue to have
            a more consistent outbound flow.
        @param windowName: Use a different rolling window key name
        @param modName: Use a different moderate time key name
        @param elastic: When moderated and falling behind, break moderation to
            catch up to desired limit
        @param elastic_buffer: The threshold number for how close we should get
            to the limit when using the elastic catch up
        '''
        self.redis_conn = redisConn
        self.queue = myQueue
        self.window = float(throttleWindow)
        self.limit = float(throttleLimit)

        if windowName is None:
            # default window name
            self.window_key = self.queue.key + self.window_append
        else:
            self.window_key = windowName + self.window_append

        # moderation is useless when only grabbing 1 item in x secs
        if moderate and throttleLimit != 1:
            self.moderation = old_div(self.window, self.limit)
            # used for communicating throttle moderation across queue instances
            if modName is None:
                self.moderate_key = self.queue.key + self.time_append
            else:
                self.moderate_key = modName + self.time_append

            self.elastic = elastic
            self.elastic_buffer = elastic_buffer

    def __len__(self):
        '''
        Return the length of the queue
        '''
        return len(self.queue)

    def clear(self):
        '''
        Clears all data associated with the throttled queue
        '''
        self.redis_conn.delete(self.window_key)
        self.redis_conn.delete(self.moderate_key)
        self.queue.clear()

    def push(self, *args):
        '''
        Push a request into the queue
        '''
        self.queue.push(*args)

    def pop(self, *args):
        '''
        Non-blocking from throttled queue standpoint, tries to return a
        queue pop request, only will return a request if
        the given time window has not been exceeded

        @return: The item if the throttle limit has not been hit,
        otherwise None
        '''
        if self.allowed():
            if self.elastic_kick_in < self.limit:
                self.elastic_kick_in += 1
            return self.queue.pop(*args)
        else:
            return None

    '''
    Original Redis Throttle implementation from
    http://opensourcehacker.com/2014/07/09/rolling-time-window-counters-with-redis-and-mitigating-botnet-driven-login-attacks/
    Modified heavily to fit our class needs, plus locking
    mechanisms around the operations
    '''
    def allowed(self):
        '''
        Check to see if the pop request is allowed

        @return: True means the maximum was not been reached for the current
            time window, thus allowing what ever operation follows
        '''
        # Expire old keys (hits)
        expires = time.time() - self.window
        self.redis_conn.zremrangebyscore(self.window_key, '-inf', expires)

        # check if we are hitting too fast for moderation
        if self.moderation:
            with self.redis_conn.pipeline() as pipe:
                try:
                    pipe.watch(self.moderate_key)  # ---- LOCK
                    # from this point onward if no errors are raised we
                    # successfully incremented the counter

                    curr_time = time.time()
                    if self.is_moderated(curr_time, pipe) and not \
                            self.check_elastic():
                        return False

                    # passed the moderation limit, now check time window
                    # If we have less keys than max, update out moderate key
                    if self.test_hits():
                        # this is a valid transaction, set the new time
                        pipe.multi()
                        pipe.set(name=self.moderate_key,
                                 value=str(curr_time),
                                 ex=int(self.window * 2))
                        pipe.execute()
                        return True

                except WatchError:
                    # watch was changed, another thread just incremented
                    # the value
                    return False

        # If we currently have more keys than max,
        # then limit the action
        else:
            return self.test_hits()

        return False

    def check_elastic(self):
        '''
        Checks if we need to break moderation in order to maintain our desired
        throttle limit

        @return: True if we need to break moderation
        '''
        if self.elastic and self.elastic_kick_in == self.limit:
            value = self.redis_conn.zcard(self.window_key)
            if self.limit - value > self.elastic_buffer:
                return True
        return False

    def is_moderated(self, curr_time, pipe):
        '''
        Tests to see if the moderation limit is not exceeded

        @return: True if the moderation limit is exceeded
        '''
        # get key, otherwise default the moderate key expired and
        # we dont care
        value = pipe.get(self.moderate_key)
        if value is None:
            value = 0.0
        else:
            value = float(value)

        # check moderation difference
        if (curr_time - value) < self.moderation:
            return True

        return False

    def test_hits(self):
        '''
        Tests to see if the number of throttle queue hits is within our limit

        @return: True if the queue was below the limit AND atomically updated
        '''
        with self.redis_conn.pipeline() as pipe:
            try:
                pipe.watch(self.window_key)  # ---- LOCK
                value = self.redis_conn.zcard(self.window_key)
                if value < self.limit:
                    # push value into key
                    now = time.time()
                    pipe.multi()
                    pipe.zadd(self.window_key, now, now)
                    # expire it if it hasnt been touched in a while
                    pipe.expire(self.window_key, int(self.window * 2))
                    pipe.execute()

                    return True

            except WatchError:
                # watch was changed, another thread just messed with the
                # queue so we can't tell if our result is ok
                pass

        return False
