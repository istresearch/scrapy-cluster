from builtins import object
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import signal
"""
A timer class so methods can only execute for a certain amount of seconds,
then returns the default value

@author: Madison Bahmer @ IST Research
         Last Updated 9/1/15
"""


class MethodTimer(object):
    '''
    -------------------------------------
    Initial code from http://pguides.net/python-tutorial/python-timeout-a-function/
    Minor modifications made to work
    with classes, parameters, and new timeout name.

    Use above your function definition:
        @MethodTimer.timeout(seconds_to_wait, default_return_value)
        def myfunc(params):
    '''

    class DecoratorTimeout(Exception):
        '''
        Simple class in order to raise exception
        '''
        pass

    @staticmethod
    def timeout(timeout_time, default):
        '''
        Decorate a method so it is required to execute in a given time period,
        or return a default value.
        '''
        def timeout_function(f):
            def f2(*args):
                def timeout_handler(signum, frame):
                    raise MethodTimer.DecoratorTimeout()

                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                # triger alarm in timeout_time seconds
                signal.alarm(timeout_time)
                try:
                    retval = f(*args)
                except MethodTimer.DecoratorTimeout:
                    return default
                finally:
                    signal.signal(signal.SIGALRM, old_handler)
                signal.alarm(0)
                return retval
            return f2
        return timeout_function
    '''
    -------------------------------------
    '''
    def __init__(self):
        pass
