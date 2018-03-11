import functools
import logging
import sys
from datetime import datetime

from conf import conf, Dev


def get_logger(name='Bangumi-Provider', filename='provider.log', enable_debug=True):
    custom_logger = logging.getLogger(name)
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s: %(message)s')
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    custom_logger.addHandler(file_handler)
    custom_logger.addHandler(console_handler)
    custom_logger.setLevel(logging.DEBUG if enable_debug else logging.INFO)
    return custom_logger


logger = get_logger(enable_debug=(conf == Dev))


def log_duration(func):
    @functools.wraps(func)
    def timed(*args, **kwargs):
        start = datetime.now()
        result = func(*args, **kwargs)
        end = datetime.now()
        logger.info('%s Start at %s, End at %s. Duration: %s.' % (func.__name__, start, end, end - start))
        return result
    return timed
