import gc

import numpy as np
from redis import Redis
from scipy.stats import pearsonr
import h5py
from datetime import datetime, timedelta

from utils import log_duration, logger


class BangumiAnalyzer:
    def __init__(self, db, conf) -> None:
        self.conf = conf
        self.db = db
        self.redis = Redis(self.conf.REDIS_HOST, self.conf.REDIS_PORT, db=self.conf.REDIS_DATABASE,
                           password=self.conf.REDIS_PASSWORD)
        self.redis.config_set('maxmemory', self.conf.REDIS_MAX_MEMORY)
        self.redis.config_set('maxmemory-policy', 'allkeys-lru')

    @log_duration
    def get_animes_authors_refs_matrix(self):
        mat, media_ids, mids = None, None, None
        try:
            with h5py.File(self.conf.HDF5_FILENAME, "r") as f:
                last_update = datetime.strptime(f.attrs['last_update'], '%Y-%m-%d %H:%M:%S.%f')
                if last_update > datetime.now() - timedelta(hours=self.conf.HDF5_DATA_SET_TTL):
                    mat = np.array(f['animes_authors_refs_matrix'])
                    media_ids = np.array(f['media_ids'])
                    mids = np.array(f['mids'])
                else:
                    raise ValueError('Data Set Expired.')
        except (OSError, KeyError, ValueError) as e:
            logger.warning('Data Set in HDF5 File Will Not be Used for Ref Matrix Because %s.' % e)

        if mat is None or media_ids is None or mids is None:
            media_ids, media_id_indexes, cur = [], {}, 0
            for entrance in self.db.get_all_entrances():
                media_ids.append(entrance['media_id'])
                media_id_indexes[str(entrance['media_id'])] = cur
                cur += 1

            authors_count = self.db.get_authors_count()
            mat = np.zeros((authors_count, len(media_ids)), dtype='int8')

            mids = []
            cur = 0
            for mid, reviews, _ in self.db.get_valid_author_ratings_follow_pairs():
                mids.append(mid)
                for review in reviews:
                    index = str(review['media_id'])
                    mat[cur, media_id_indexes[index]] = review['score']
                cur += 1

            with h5py.File(self.conf.HDF5_FILENAME, "w") as f:
                f.create_dataset('animes_authors_refs_matrix', data=mat)
                f.create_dataset('media_ids', data=media_ids)
                f.create_dataset('mids', data=mids)
        return mat, media_ids, mids

    @staticmethod
    def calc_similarity(lhs, rhs):
        index = np.logical_and(lhs > 0, rhs > 0)
        lhs_shared, rhs_shared = lhs[index], rhs[index]
        return pearsonr(lhs, rhs)[0] if len(lhs_shared) > 1 else 0

    @log_duration
    def get_similarity_matrix(self, refs_matrix):
        mat = None
        try:
            with h5py.File(self.conf.HDF5_FILENAME, "r") as f:
                mat = np.array(f['animes_similarity_matrix'])
        except (OSError, KeyError) as e:
            logger.warning('Data Set in HDF5 File Will Not be Used for Similarity Matrix Because %s.' % e)

        if mat is None:
            _, cols_count = refs_matrix.shape
            mat = np.zeros((cols_count, cols_count))
            for i in range(0, cols_count):
                logger.info('Calculating Similarities %s/%s...' % (i, cols_count))
                for j in range(i + 1, cols_count):
                    mat[i, j] = BangumiAnalyzer.calc_similarity(refs_matrix[:, i], refs_matrix[:, j])
            mat += mat.T
            np.fill_diagonal(mat, -1)

            with h5py.File(self.conf.HDF5_FILENAME, "r+") as f:
                f.create_dataset('animes_similarity_matrix', data=mat)
                f.attrs['last_update'] = str(datetime.now())
        return mat

    @log_duration
    def process_animes_top_matches(self, ref_mat, media_ids) -> None:
        logger.info('Calculating Animes Similarity Matrix...')
        animes_sim_mat = self.get_similarity_matrix(ref_mat)
        logger.info('Animes Similarity Matrix %s Calculated.' % str(animes_sim_mat.shape))
        animes_sim_indexes_mat = np.flip(animes_sim_mat.argsort()[:,
                                         0 - self.conf.ANALYZE_ANIME_TOP_MATCHES_SIZE:], axis=1)
        logger.info('Animes Sim-Indexes %s Get Finished.' % str(animes_sim_indexes_mat.shape))

        cur = 0
        for anime_sim_indexes in animes_sim_indexes_mat:
            self.db.update_anime_top_matches(media_ids[cur], [{
                'media_id': media_ids[index],
                'similarity': animes_sim_mat[cur, index]
            } for index in anime_sim_indexes])
            cur += 1
        logger.info('Animes Top-Matches Persisted.')

    @log_duration
    def process_authors_recommendation(self, ref_mat, media_ids, mids) -> None:
        for i in range(0, len(mids)):
            if self.db.is_need_re_calculate(mids[i]):
                logger.info("[%s/%s] Calculating %s's Top-Matches and Recommendation..." % (i, len(mids), mids[i]))
                similarities = np.empty((len(mids),))
                similarities[i] = -1
                for j in range(0, len(mids)):
                    if i != j:
                        index_pair = '%s:%s' % (mids[min(i, j)], mids[max(i, j)])
                        similarity = self.redis.get(index_pair)
                        if similarity is None:
                            similarity = self.calc_similarity(ref_mat[i], ref_mat[j])
                            self.redis.set(index_pair, similarity)
                            self.redis.expire(index_pair, self.conf.REDIS_SIMILARITY_TTL)
                        similarities[j] = similarity
                sorted_indexes = np.flip(similarities.argsort(), axis=0)[0 - self.conf.ANALYZE_AUTHOR_TOP_MATCHES_SIZE:]

                top_matches, recommendation = [], []
                total_scores_with_weight, total_weight = 0, 0
                for index in sorted_indexes:
                    similarity = similarities[index]
                    top_matches.append({'mid': mids[index], 'similarity': similarity})
                    total_scores_with_weight += similarity * ref_mat[index]
                    total_weight += similarity
                recommend_indexes_sorted = np.flip((total_scores_with_weight / total_weight).argsort(), axis=0)
                author_watched_media_ids = self.db.get_author_watched_media_ids(mids[i])
                for index in recommend_indexes_sorted:
                    if len(recommendation) == self.conf.ANALYZE_AUTHOR_RECOMMENDATION_SIZE:
                        break
                    if media_ids[index] not in author_watched_media_ids:
                        recommendation.append(media_ids[index])

                self.db.update_author_recommendation(mids[i], top_matches, recommendation)
            else:
                logger.info('[%s/%s] Skip Calculating %s.' % (i, len(mids), mids[i]))
        logger.info('Authors Top-Matches Persisted.')

    def analyze(self) -> None:
        logger.info('New Analyze Beginning...')

        logger.info('Getting Ref Matrix...')
        ref_mat, media_ids, mids = self.get_animes_authors_refs_matrix()
        logger.info('Ref Matrix %s Got, with %s Medias and %s Authors.'
                    % (ref_mat.shape, len(media_ids), len(mids)))

        self.process_animes_top_matches(ref_mat, media_ids)
        self.process_authors_recommendation(ref_mat, media_ids, mids)

        logger.info('Analyzing Tasks Finished.')
        gc.collect()
