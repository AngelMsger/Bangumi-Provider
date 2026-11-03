import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

from bson import BSON
import numpy as np
from pymongo import MongoClient
from redis import Redis

from analyzer import BangumiAnalyzer
from conf import Conf
from db import MongoDB


class AnalyzerTests(unittest.TestCase):
    def test_numpy_scalars_can_be_written_to_mongodb(self):
        document = {
            'mid': BangumiAnalyzer.asscalar(np.int64(42)),
            'similarity': BangumiAnalyzer.asscalar(np.float64(0.75)),
            'media_id': BangumiAnalyzer.asscalar(np.array(7)),
        }
        self.assertEqual(BSON(BSON.encode(document)).decode(),
                         {'mid': 42, 'similarity': 0.75, 'media_id': 7})
        self.assertIs(type(document['mid']), int)

    def test_hdf5_round_trip_and_recommendation_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            class TestConf(Conf):
                HDF5_FILENAME = str(Path(directory) / 'matrix.hdf5')
                ANALYZE_ANIME_TOP_MATCHES_SIZE = 1

            db = Mock()
            db.get_all_entrances.return_value = [{'media_id': i} for i in (11, 12, 13)]
            db.get_authors_count.return_value = 3
            db.get_valid_author_ratings_follow_pairs.return_value = [
                (mid, [{'media_id': media, 'score': score}
                       for media, score in zip((11, 12, 13), scores)], [])
                for mid, scores in zip((21, 22, 23), ((1, 2, 3), (2, 4, 1), (3, 6, 2)))
            ]
            with patch('analyzer.Redis'):
                analyzer = BangumiAnalyzer(db, TestConf)
            matrix, media_ids, mids = analyzer.get_animes_authors_refs_matrix()
            np.testing.assert_array_equal(matrix, [[1, 2, 3], [2, 4, 1], [3, 6, 2]])
            similarities = analyzer.get_similarity_matrix(matrix, 'animes_similarity_matrix')
            self.assertAlmostEqual(similarities[0, 1], 1.0)
            np.testing.assert_array_equal(np.diag(similarities), [-1, -1, -1])

            db.get_all_entrances.side_effect = AssertionError('fresh cache should avoid the database')
            cached_matrix, cached_media, cached_mids = analyzer.get_animes_authors_refs_matrix()
            np.testing.assert_array_equal(cached_matrix, matrix)
            np.testing.assert_array_equal(cached_media, media_ids)
            np.testing.assert_array_equal(cached_mids, mids)
            analyzer.process_animes_top_matches(cached_matrix, cached_media)
            self.assertEqual(db.update_anime_top_matches.call_count, 3)
            for call in db.update_anime_top_matches.call_args_list:
                BSON.encode({'media_id': call.args[0], 'matches': call.args[1]})


@unittest.skipUnless(os.environ.get('BANGUMI_TEST_MONGO_URI'), 'requires a disposable MongoDB server')
class MongoIntegrationTests(unittest.TestCase):
    def setUp(self):
        admin = MongoClient(os.environ['BANGUMI_TEST_MONGO_URI'], serverSelectionTimeoutMS=10000)
        self.addCleanup(admin.close)
        admin.admin.command('ping')
        name = 'bangumi_test_' + uuid4().hex
        self.addCleanup(admin.drop_database, name)
        admin[name].command('createUser', 'compat-test', pwd='test-only', roles=['readWrite'])
        self.addCleanup(admin[name].command, 'dropUser', 'compat-test')

        class TestConf(Conf):
            DB_HOST, DB_PORT = admin.address
            DB_DATABASE = name
            DB_ENABLE_AUTH = True
            DB_USERNAME = 'compat-test'
            DB_PASSWORD = 'test-only'
            ANALYZE_AUTHOR_REVIEWS_VALID_THRESHOLD = 2

        self.store = MongoDB(TestConf)
        self.addCleanup(self.store.client.close)

    def test_authenticated_initialization_creates_indexes(self):
        self.assertIn('media_id_1', self.store.db.animes.index_information())
        self.assertIn('mid_1', self.store.db.authors.index_information())
        self.assertIn('date_-1_archives.media_id_1', self.store.db.archives.index_information())

    def test_valid_count_matches_rows_including_missing_reviews(self):
        self.store.db.animes.insert_one({'season_id': 101, 'media_id': 11})
        self.store.db.authors.insert_many([
            {'mid': 1, 'reviews': [{'media_id': 11, 'score': 5}] * 3, 'follow': [101]},
            {'mid': 2, 'reviews': [{'media_id': 11, 'score': 5}] * 2},
            {'mid': 3, 'reviews': []},
            {'mid': 4},
            {'mid': 5, 'reviews': None},
        ])
        rows = list(self.store.get_valid_author_ratings_follow_pairs())
        self.assertEqual(self.store.get_authors_count(), len(rows))
        self.assertEqual([row[0] for row in rows], [1])
        self.assertEqual(rows[0][2], [11])
        self.assertEqual(self.store.get_authors_count(is_valid=False), 5)

    def test_truncate_clears_documents_and_preserves_indexes(self):
        for name in ('animes', 'authors', 'archives'):
            self.store.db[name].insert_one({'test': True})
        self.store.truncate_all()
        for name in ('animes', 'authors', 'archives'):
            self.assertEqual(self.store.db[name].count_documents({}), 0)
        self.assertIn('mid_1', self.store.db.authors.index_information())


@unittest.skipUnless(os.environ.get('BANGUMI_TEST_REDIS_URL'), 'requires a disposable Redis server')
class RedisIntegrationTests(unittest.TestCase):
    def test_analyzer_cache_configuration_and_expiring_values(self):
        redis = Redis.from_url(os.environ['BANGUMI_TEST_REDIS_URL'])
        self.addCleanup(redis.close)
        connection = redis.connection_pool.connection_kwargs

        class TestConf(Conf):
            REDIS_HOST = connection['host']
            REDIS_PORT = connection.get('port', 6379)

        analyzer = BangumiAnalyzer(Mock(), TestConf)
        self.addCleanup(analyzer.redis.close)
        key = 'bangumi_test_' + uuid4().hex
        self.addCleanup(analyzer.redis.delete, key)
        analyzer.redis.set(key, 0.75)
        analyzer.redis.expire(key, 60)
        self.assertEqual(float(analyzer.redis.get(key)), 0.75)
        self.assertGreater(analyzer.redis.ttl(key), 0)


if __name__ == '__main__':
    unittest.main()
