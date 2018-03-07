import os


class Conf:
    # Schedule
    CRON_AT = os.environ.get('CRON_AT', '3:00')

    # Persist Database Backend
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 27017))

    DB_DATABASE = os.environ.get('DB_DATABASE', 'bangumi')

    DB_ENABLE_AUTH = True if os.environ.get('DB_ENABLE_AUTH', 'True').lower() == 'true' else False
    DB_USERNAME = os.environ.get('DB_USERNAME', 'bangumi')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')

    CACHE_HOST = os.environ.get('DB_HOST', 'localhost')
    CACHE_PORT = int(os.environ.get('CACHE_PORT', 6379))

    CACHE_ENABLE_AUTH = False if os.environ.get('DB_ENABLE_AUTH', 'False').lower() == 'false' else True

    # Crawler
    CRAWL_MAX_RETRY = int(os.environ.get('CRAWL_MAX_RETRY', 32))

    # eg. 0 - 全部, 1 - 正片, 3 - 剧场版, 4 - 其他
    CRAWL_VERSION = int(os.environ.get('CRAW_VERSION', 0))
    # eg. 0 - 全部, 2 - 日本, 3 - 美国, 4 - 其他
    CRAWL_AREA = int(os.environ.get('CRAW_AREA', 0))
    # False - 全部, True - 完结
    CRAWL_IS_FINISH = False if os.environ.get('CRAW_IS_FINISH', 'False') else True
    # eg. 2018
    CRAWL_START_YEAR = int(os.environ.get('CRAW_START_YEAR', 0))
    # 0 - 全部, 1 - 1月(冬季)番, 2 - 4月(春季)番, 3 - 7月(夏季)番, 4 - 10月(秋季)番
    CRAWL_QUARTER = int(os.environ.get('CRAW_QUARTER', 0))
    # eg. 0 - 全部, 117 - 轻改, 81 - 萌系, 70 - 搞笑
    CRAWL_TAG_ID = int(os.environ.get('CRAW_TAG_ID', 0))

    # Author Expired Will Be Considered to Update Next Time (Hour).
    CRAWL_AUTHOR_TTL = int(os.environ.get('CRAWL_AUTHOR_TTL', 720))
    CRAWL_AUTHOR_MAX_PER_TIME = int(os.environ.get('CRAWL_AUTHOR_MAX_PER_TIME', 50000))

    # Risky, **DO NOT** Use Your Own Account.
    CRAWL_USERNAME = os.environ.get('CRAWL_USERNAME', 'bangumi')
    CRAWL_PASSWORD = os.environ.get('CRAWL_USERNAME', 'password')


class Dev(Conf):
    DB_ENABLE_AUTH = False


class Prod(Conf):
    pass


conf = Dev
