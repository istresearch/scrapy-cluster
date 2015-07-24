class BaseMonitor():
    '''
    Base monitor for handling incoming requests seen within redis
    These classes have an implied redis_conn variable for manipulating
    a redis connection
    '''
    # override this with your own regex to look for in redis
    regex = "NONE"

    def setup(self, settings):
        '''
        Setup the handler

        @param settings: The loaded settings file
        @param redis_conn: The redis connection for further processing
        '''
        if self.regex == "NONE":
            raise NotImplementedError("Please specify a regex for the plugin")

    def handle(self, key, value):
        '''
        Process a valid incoming tuple and handle any logic associated
        with it

        @param @param key: The key that matched the request
        @param value: The value associated with the key
        '''
        raise NotImplementedError("Please implement handle() for your handler class")