from datetime import date
from datetime import datetime
from datetime import timedelta

from pymongo import MongoClient


# Storage Backend Interface
class DB:
    def truncate_all(self) -> None:
        pass

    def archive(self) -> None:
        pass

    def persist_animes(self, animes) -> None:
        pass

    def persist_reviews(self, media_id, reviews, cursor=None, is_long=True) -> None:
        pass

    def get_all_entrances(self):
        pass

    def get_reviews_count(self, media_id, is_long=True):
        pass

    def get_author_tasks(self):
        pass

    def push_to_follow(self, mid, season_ids):
        pass


# Persist solution for MongoDB
class MongoDB(DB):
    def truncate_all(self) -> None:
        self.db.animes.remove({})
        self.db.authors.remove({})
        self.db.archives.remove({})

    def archive(self) -> None:
        today = datetime.combine(date.today(), datetime.min.time())
        if self.db.archives.find_one({'date': today}) is None:
            outdated = self.db.animes.find()
            archives = []
            for anime in outdated:
                archive = {
                    'season_id': anime['season_id'],
                    'favorites': anime['favorites'],
                    'danmaku_count': anime['danmaku_count'],
                    'long_reviews_count': self.get_reviews_count(anime['media_id']),
                    'short_reviews_count': self.get_reviews_count(anime['media_id'], is_long=False)
                }
                if 'rating' in anime:
                    archive.update({'rating': anime['rating']})
                archives.append(archive)
            self.db.archives.insert_one({
                'date': today,
                'archives': archives
            })

    def persist_animes(self, animes) -> None:
        for anime in animes:
            self.db.animes.update_one({'season_id': anime['season_id']}, {'$set': anime}, upsert=True)

    def persist_reviews(self, media_id, reviews, cursor=None, is_long=True) -> None:
        for review in reviews:
            author = review.pop('author')
            self.db.authors.update_one({'mid': author['mid']},
                                       {'$set': author, '$push': {'reviews': review}}, upsert=True)
        if cursor is not None:
            reviews_type = 'long' if is_long else 'short'
            self.db.animes.update_one({'media_id': media_id},
                                      {'$set': {'last_%s_reviews_cursor' % reviews_type: cursor}})

    def get_all_entrances(self):
        return [(anime['media_id'],
                 anime.get('last_long_reviews_cursor', None),
                 anime.get('last_short_reviews_cursor', None)
                 ) for anime in self.db.animes.find()]

    # TODO: Update implementation of this method.
    # def get_reviews_count(self, media_id, is_long=None):
        # query = {'media_id': media_id}
        # if is_long is not None:
        #     query.update({'is_long': is_long})
        # return self.db.authors.count(query)

    def get_author_tasks(self):
        threshold = datetime.now() - timedelta(hours=self.conf.CRAWL_AUTHOR_TTL)
        return self.db.authors.find({
            'last_update': {'$not': {'$gt': threshold}}
        }, {'mid': 1}).limit(self.conf.CRAWL_AUTHOR_MAX_PER_TIME)

    def push_to_follow(self, mid, season_ids):
        self.db.authors.update_one({'mid': mid}, {'$set': {'follow': season_ids, 'last_update': datetime.now()}})

    def __init__(self, conf) -> None:
        self.conf = conf
        self.db = MongoClient(conf.DB_HOST, conf.DB_PORT)[conf.DB_DATABASE]
        if conf.DB_ENABLE_AUTH:
            self.db.authenticate(conf.DB_USERNAME, conf.DB_PASSWORD)

        # Init Index
        collections = set(self.db.collection_names())
        if 'animes' not in collections:
            self.db.animes.create_indexes([{'season_id': 1}, {'media_id': 1}])
        if 'authors' not in collections:
            self.db.authors.create_indexes([{'mid': 1}, {'reviews.media_id': 1}])
        if 'archives' not in collections:
            self.db.archives.create_index({'date': -1, 'archives.media_id': 1})
