import functools
import logging
import sys
from datetime import datetime

from conf import conf, Dev


def log_duration(func):
    @functools.wraps(func)
    def timed(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        print('[DEBUG] %s Start at %s, End at %s. Duration: %s.' % (func.__name__, start, end, end - start))
        return result
    return timed


def get_logger(name='Bangumi-Provider', filename='provider.log', enable_debug=True):
    logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')

    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)
    return logger


logger = get_logger(enable_debug=(conf == Dev))
