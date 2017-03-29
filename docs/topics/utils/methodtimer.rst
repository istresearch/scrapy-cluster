Method Timer
============

The Method Timer module is for executing python methods that need to be cancelled after a certain period of execution. This module acts as a `decorator <https://en.wikipedia.org/wiki/Decorator_pattern>`_ to existing functions with or without arguments, allowing you to escape out of the method if it does not finish within your desired time period.

.. method:: timeout(timeout_time, default)

    :param timeout_time: The number of seconds to wait before returning the default value
    :param default: The default value returned by the method if the timeout is called

Usage
-----

Use above a function definition like so:

::

    >>> from scutils.method_timer import MethodTimer
    >>> @MethodTimer.timeout(5, "timeout")
    >>> def my_function():
    >>>     # your complex function here

The Method Timer module relies on python signals to alert the process that the method has not completed within the desired time window. This means that it is not designed to be run within a multi-threaded application, as the signals raised are not depended on the thread that called it.

Use this class as a convenience for connection establishment, large processing that is time dependent, or any other use case where you need to ensure your function completes within a desired time window.

Example
-------

Put the following code into a file named ``example_mt.py``, or use the one located at ``utils/examples/example_my.py``

::

    from scutils.method_timer import MethodTimer
    from time import sleep

    @MethodTimer.timeout(3, "did not finish")
    def timeout():
        sleep(5)
        return "finished!"

    return_value = timeout()
    print return_value

::

    $ python example_mt.py
    did not finish

Within the decorator declaration if you set the timeout value to 6, you will see ``finished!`` displayed instead.

You can also dynamically adjust how long you would like your method to sleep, by defining your function underneath an existing one. Take the following code as an example:

::

    from scutils.method_timer import MethodTimer
    from time import sleep

    def timeout(sleep_time, wait_time, default, mul_value):
        # define a hidden method to sleep and wait based on parameters
        @MethodTimer.timeout(wait_time, default)
        def _hidden(m_value):
            sleep(sleep_time)
            return m_value * m_value
        # call the newly declared function
        return _hidden(mul_value)

    print timeout(5, 3, "did not finish 2*2", 2)
    print timeout(3, 5, "did not finish 3*3", 3)
    print timeout(2, 1, "did not finish 4*4", 4)

Now we have a hidden method underneath our main one that will adjust both its timeout period and return value based on parameters passed into the parent function. In this case, we try to compute the square of ``mul_value`` and return the result.

::

    $ python example_mt.py
    did not finish 2*2
    9
    did not finish 4*4

