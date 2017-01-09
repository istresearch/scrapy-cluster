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