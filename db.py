from datetime import date
from datetime import datetime

from pymongo import MongoClient


# Storage Backend Interface
class DB:
    def truncate_all(self) -> None:
        pass

    def archive(self) -> None:
        pass

    def persist_animes(self, animes) -> None:
        pass

    def persist_reviews(self, media_id, reviews, cursor) -> None:
        pass

    def get_all_entrances(self):
        pass

    def get_reviews_count(self, media_id, is_long=True):
        pass


# Persist solution for MongoDB
class MongoDB(DB):
    def truncate_all(self) -> None:
        self.db.animes.remove({})
        self.db.long_reviews.remove({})
        self.db.short_reviews.remove({})
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
            self.db.animes.update({'season_id': anime['season_id']}, {'$set': anime}, upsert=True)

    def persist_reviews(self, media_id, reviews, cursor=None) -> None:
        if len(reviews) > 0:
            self.db.reviews.insert_many(reviews)
            if cursor is not None:
                reviews_type = 'long' if reviews[0]['is_long'] else 'short'
                self.db.animes.update_one({'media_id': media_id},
                                          {'$set': {'last_%s_reviews_cursor' % reviews_type: cursor}})

    def get_all_entrances(self):
        return [(anime['media_id'],
                 anime.get('last_long_reviews_cursor', None),
                 anime.get('last_short_reviews_cursor', None)
                 ) for anime in self.db.animes.find()]

    def get_reviews_count(self, media_id, is_long=None):
        query = {'media_id': media_id}
        if is_long is not None:
            query.update({'is_long': is_long})
        return self.db.reviews.count(query)

    def __init__(self, conf) -> None:
        self.db = MongoClient(conf.DB_HOST, conf.DB_PORT)[conf.DB_DATABASE]
        if conf.DB_MONGO_ENABLE_AUTH:
            self.db.authenticate(conf.DB_USERNAME, conf.DB_PASSWORD)
