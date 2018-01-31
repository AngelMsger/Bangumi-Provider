class Conf:
    DB_ENABLE_MONGO = True

    DB_MONGO_ENABLE_AUTH = True

    DB_HOST = '127.0.0.1'
    DB_PORT = 27017
    DB_USERNAME = 'dev'
    DB_PASSWORD = 'password'

    DB_DATABASE = 'bangumi'

    # eg. 0 - 全部, 1 - 正片, 3 - 剧场版, 4 - 其他
    ANIMES_VERSION = 0
    # eg. 0 - 全部, 2 - 日本, 3 - 美国, 4 - 其他
    ANIMES_AREA = 0
    # False - 全部, True - 完结
    ANIMES_IS_FINISH = False
    # eg. 2018
    ANIMES_START_YEAR = 0
    # 0 - 全部, 1 - 1月(冬季)番, 2 - 4月(春季)番, 3 - 7月(夏季)番, 4 - 10月(秋季)番
    ANIMES_QUARTER = 0
    # eg. 0 - 全部, 117 - 轻改, 81 - 萌系, 70 - 搞笑
    ANIMES_TAG_ID = 0


class Dev(Conf):
    pass


conf = Dev
