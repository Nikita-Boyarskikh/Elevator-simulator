import time
from functools import wraps

sleeps = []
origin_time_sleep = time.sleep


def _stub_time_sleep(seconds):
    sleeps.append(seconds)


def stub_time_sleep(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        time.sleep = _stub_time_sleep
        result = func(*args, **kwargs)
        time.sleep = origin_time_sleep
        return result

    return wrapper
