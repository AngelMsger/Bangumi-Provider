from pymongo import MongoClient


# Interface
class DB:
    def persist_animes(self, animes):
        pass

    def persist_long_reviews(self, long_reviews):
        pass

    def persist_short_reviews(self, short_reviews):
        pass

    def get_all_media_ids(self):
        pass

    def is_anime_finished(self, season_id):
        pass

    def is_reviews_finished(self, media_id):
        pass


# Persist solution for MongoDB
class MongoDB(DB):
    def persist_animes(self, animes):
        if len(animes) > 0:
            self.db.animes.insert_many(animes)

    def persist_long_reviews(self, long_reviews):
        if len(long_reviews) > 0:
            self.db.long_reviews.insert_many(long_reviews)

    def persist_short_reviews(self, short_reviews):
        if len(short_reviews) > 0:
            self.db.short_reviews.insert_many(short_reviews)

    def get_all_media_ids(self):
        return [anime['media_id'] for anime in self.db.animes.find()]

    def is_anime_finished(self, season_id):
        return self.db.animes.find_one({'season_id': season_id}) is not None

    def is_reviews_finished(self, media_id):
        return self.db.long_reviews.find_one({'review_id': media_id}) is not None \
               or self.db.short_reviews.find_one({'review_id': media_id}) is not None

    def __init__(self, conf) -> None:
        self.db = MongoClient(conf.DB_HOST, conf.DB_PORT)[conf.DB_DATABASE]
        if conf.DB_MONGO_ENABLE_AUTH:
            self.db.authenticate(conf.DB_USERNAME, conf.DB_PASSWORD)


# TODO: MySQL Support

# TODO: Migration
