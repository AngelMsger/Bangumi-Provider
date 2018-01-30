class Conf:
    DB_ENABLE_MONGO = True

    DB_MONGO_ENABLE_AUTH = False

    DB_HOST = '127.0.0.1'
    DB_PORT = 27017
    DB_USERNAME = 'dev'
    DB_PASSWORD = 'password'

    DB_DATABASE = 'bangumi'

    ANIMES_VERSION = 0
    ANIMES_AREA = 0
    ANIMES_IS_FINISH = False
    ANIMES_START_YEAR = 0
    ANIMES_QUARTER = 0
    ANIMES_TAG_ID = 0


class Dev(Conf):
    pass


conf = Dev
