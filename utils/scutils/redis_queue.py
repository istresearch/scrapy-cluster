from future import standard_library
standard_library.install_aliases()
from builtins import object
try:
    import pickle as pickle
except ImportError:
    import pickle


class Base(object):
    '''
    Queue/Stack base class
    '''

    def __init__(self, server, key, encoding=pickle):
        '''Initialize the redis queue.

        @param server: the redis connection
        @param key: the key for this queue
        @param encoding: The encoding module to use.

        Note that if you wish to use any other encoding besides pickle, it
        is assumed you have already imported that module in your code before
        calling this constructor.
        '''
        self.server = server
        self.key = key
        self.encoding = encoding

        if not hasattr(self.encoding, 'dumps'):
            raise NotImplementedError("encoding does not support dumps()")
        if not hasattr(self.encoding, 'loads'):
            raise NotImplementedError("encoding does not support loads()")

    def _encode_item(self, item):
        '''
        Encode an item object

        @requires: The object be serializable
        '''
        if self.encoding.__name__ == 'pickle':
            return self.encoding.dumps(item, protocol=-1)
        else:
            return self.encoding.dumps(item)

    def _decode_item(self, encoded_item):
        '''
        Decode an item previously encoded
        '''
        return self.encoding.loads(encoded_item)

    def __len__(self):
        '''
        Return the length of the queue
        '''
        raise NotImplementedError

    def push(self, item):
        '''
        Push an item
        '''
        raise NotImplementedError

    def pop(self, timeout=0):
        '''
        Pop an item
        '''
        raise NotImplementedError

    def clear(self):
        '''
        Clear queue/stack
        '''
        self.server.delete(self.key)


class RedisQueue(Base):
    '''
    FIFO queue
    '''

    def __len__(self):
        '''
        Return the length of the queue
        '''
        return self.server.llen(self.key)

    def push(self, item):
        '''
        Push an item
        '''
        # ignore priority
        self.server.lpush(self.key, self._encode_item(item))

    def pop(self, timeout=0):
        '''
        Pop an item
        '''
        if timeout > 0:
            data = self.server.brpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            data = self.server.rpop(self.key)
        if data:
            return self._decode_item(data)


class RedisPriorityQueue(Base):
    '''
    Priority queue abstraction using redis' sorted set
    '''

    def __len__(self):
        '''Return the length of the queue'''
        return self.server.zcard(self.key)

    def push(self, item, priority):
        '''
        Push an item

        @param priority: the priority of the item
        '''
        data = self._encode_item(item)
        pairs = {data: -priority}
        self.server.zadd(self.key, **pairs)

    def pop(self, timeout=0):
        '''
        Pop an item
        timeout not support in this queue class
        '''
        # use atomic range/remove using multi/exec
        pipe = self.server.pipeline()
        pipe.multi()
        pipe.zrange(self.key, 0, 0).zremrangebyrank(self.key, 0, 0)
        results, count = pipe.execute()
        if results:
            return self._decode_item(results[0])


class RedisStack(Base):
    '''
    Stack
    '''

    def __len__(self):
        '''
        Return the length of the stack
        '''
        return self.server.llen(self.key)

    def push(self, item):
        '''
        Push an item
        '''
        self.server.lpush(self.key, self._encode_item(item))

    def pop(self, timeout=0):
        '''
        Pop an item
        '''
        if timeout > 0:
            data = self.server.blpop(self.key, timeout)
            if isinstance(data, tuple):
                data = data[1]
        else:
            data = self.server.lpop(self.key)

        if data:
            return self._decode_item(data)


__all__ = ['RedisQueue', 'RedisPriorityQueue', 'RedisStack']
