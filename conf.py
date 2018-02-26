import os


class Conf:
    CRON_AT = os.environ.get('CRON_AT', '3:00')

    DB_ENABLE_MONGO = True if os.environ.get('DB_ENABLE_MONGO', 'True').lower() == 'true' else False

    DB_MONGO_ENABLE_AUTH = True if os.environ.get('DB_MONGO_ENABLE_AUTH', 'True').lower() == 'true' else False

    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', 27017)
    DB_USERNAME = os.environ.get('DB_USERNAME', 'dev')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')

    DB_DATABASE = os.environ.get('DB_DATABASE', 'bangumi')

    # eg. 0 - 全部, 1 - 正片, 3 - 剧场版, 4 - 其他
    ANIMES_VERSION = int(os.environ.get('ANIMES_VERSION', 0))
    # eg. 0 - 全部, 2 - 日本, 3 - 美国, 4 - 其他
    ANIMES_AREA = int(os.environ.get('ANIMES_AREA', 0))
    # False - 全部, True - 完结
    ANIMES_IS_FINISH = False if os.environ.get('ANIMES_IS_FINISH', 'False') else True
    # eg. 2018
    ANIMES_START_YEAR = int(os.environ.get('ANIMES_START_YEAR', 0))
    # 0 - 全部, 1 - 1月(冬季)番, 2 - 4月(春季)番, 3 - 7月(夏季)番, 4 - 10月(秋季)番
    ANIMES_QUARTER = int(os.environ.get('ANIMES_QUARTER', 0))
    # eg. 0 - 全部, 117 - 轻改, 81 - 萌系, 70 - 搞笑
    ANIMES_TAG_ID = int(os.environ.get('ANIMES_TAG_ID', 0))


class Dev(Conf):
    pass


conf = Dev
