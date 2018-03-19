import os


class Conf:
    # Schedule
    SCHEDULE_ENABLE = False if os.environ.get('SCHEDULE_ENABLE', 'False').lower() == 'false' else True
    SCHEDULE_CRON_AT = os.environ.get('CRON_AT', '16:00')

    # Persist Database Backend
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = int(os.environ.get('DB_PORT', 27017))

    DB_DATABASE = os.environ.get('DB_DATABASE', 'bangumi')

    DB_ENABLE_AUTH = True if os.environ.get('DB_ENABLE_AUTH', 'True').lower() == 'true' else False
    DB_USERNAME = os.environ.get('DB_USERNAME', 'bangumi')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')

    # Cache Backend
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_DATABASE = int(os.environ.get('REDIS_DATABASE', 0))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_MAX_MEMORY = '%smb' % int(os.environ.get('REDIS_MAX_MEMORY', 1024))

    REDIS_SIMILARITY_TTL = int(os.environ.get('REDIS_KV_TTL', 86400))

    # Logging
    LOGGING_FILENAME = os.environ.get('LOGGING_FILENAME', 'stdout.log')
    LOGGING_MAX_BYTES = int(os.environ.get('LOGGING_MAX_BYTES', 65536))
    LOGGING_BACKUP_COUNT = int(os.environ.get('LOGGING_BACKUP_COUNT', 4))

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
    CRAWL_AUTHOR_FOLLOW = False if os.environ.get('CRAWL_AUTHOR_FOLLOW', 'False') else True
    CRAWL_AUTHOR_TTL = int(os.environ.get('CRAWL_AUTHOR_TTL', 512))
    CRAWL_AUTHOR_MAX_PER_TIME = int(os.environ.get('CRAWL_AUTHOR_MAX_PER_TIME', 65536))

    # Risky, **DO NOT** Use Your Own Account.
    CRAWL_USERNAME = os.environ.get('CRAWL_USERNAME', 'bangumi')
    CRAWL_PASSWORD = os.environ.get('CRAWL_USERNAME', 'password')

    # Analyzer
    ANALYZE_ANIME_TOP_MATCHES_SIZE = int(os.environ.get('ANALYZE_ANIME_TOP_MATCHES_SIZE', 8))
    ANALYZE_AUTHOR_TOP_MATCHES_SIZE = int(os.environ.get('ANALYZE_AUTHOR_TOP_MATCHES_SIZE', 8))
    ANALYZE_AUTHOR_RECOMMENDATION_SIZE = int(os.environ.get('ANALYZE_AUTHOR_RECOMMENDATION_SIZE', 8))

    # Author Whose Reviews More than Threshold Will be Calculate.
    ANALYZE_AUTHOR_REVIEWS_VALID_THRESHOLD = int(os.environ.get('ANALYZE_AUTHOR_REVIEWS_VALID_THRESHOLD', 8))

    ANALYZE_AUTHOR_TTL = int(os.environ.get('ANALYZE_AUTHOR_TTL', 512))

    # HDF5 File
    HDF5_FILENAME = os.environ.get('HDF5_FILENAME', 'bangumi.hdf5')
    # Matrix in HDF5 File Will Be Re-Use If It Not Expired (Hour) Rather than Re-Calculate.
    HDF5_DATA_SET_TTL = int(os.environ.get('HDF5_DATA_SET_TTL', 64))


class Dev(Conf):
    DB_ENABLE_AUTH = False


class Prod(Conf):
    pass


conf = Prod
