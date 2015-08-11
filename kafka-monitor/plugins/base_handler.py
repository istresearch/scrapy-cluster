class BaseHandler():
    '''
    Base validator for handling incoming requests from kafka
    '''
    # override this with your own 'something.json' schema
    schema = "NONE"

    def setup(self, settings):
        '''
        Setup the handler

        @param settings: The loaded settings file
        '''
        if self.schema == "NONE":
            raise NotImplementedError("Please specify a schema for the kafka monitor")

    def handle(self, dict):
        '''
        Process a valid incoming request dict and handle any logic associated
        with it

        @param dict: The valid request object
        '''
        raise NotImplementedError("Please implement handle() for your handler class")