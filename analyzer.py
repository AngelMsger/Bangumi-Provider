import numpy as np

from scipy.stats import pearsonr

from utils import log_duration, logger


class BangumiAnalyzer:
    def __init__(self, db, conf) -> None:
        self.conf = conf
        self.db = db

    @log_duration
    def get_animes_authors_refs_matrix(self):
        authors_count = self.db.get_authors_count()
        media_ids, scores = [], []
        media_id_indexes, cur = {}, 0
        for media_id, score in self.db.get_all_anime_score_pairs():
            media_ids.append(media_id)
            scores.append(score)
            media_id_indexes[str(media_id)] = cur
            cur += 1

        mat = np.repeat(scores, authors_count).reshape(len(media_ids), authors_count).T

        mids = []
        cur = 0
        for mid, reviews, follow_media_ids in self.db.get_all_author_ratings_follow_pair():
            mids.append(mid)

            for review in reviews:
                index = str(review['media_id'])
                if index in media_id_indexes:
                    mat[cur, media_id_indexes[index]] = review['score']
            for media_id in follow_media_ids:
                index = str(media_id)
                if index in media_id_indexes:
                    mat[cur, media_id_indexes[index]] *= 1.05

            cur += 1

        return mat, media_ids, mids

    @staticmethod
    def calc_similarity(lhs, rhs):
        return pearsonr(lhs, rhs)[0]

    @staticmethod
    @log_duration
    def get_similarity_matrix(refs_matrix):
        _, cols_count = refs_matrix.shape
        mat = np.zeros((cols_count, cols_count))
        for i in range(0, cols_count):
            for j in range(i + 1, cols_count):
                mat[i, j] = BangumiAnalyzer.calc_similarity(refs_matrix[:, i], refs_matrix[:, j])
        mat += mat.T
        np.fill_diagonal(mat, -2)
        return mat

    @log_duration
    def process_animes_top_matches(self, ref_mat, media_ids) -> None:
        logger.info('Calculating Animes Similarity Matrix...')
        animes_sim_mat = self.get_similarity_matrix(ref_mat)
        logger.info('Animes Similarity Matrix %s Calculated.' % str(animes_sim_mat.shape))
        animes_sim_indexes_mat = animes_sim_mat.argsort()[:, 0 - self.conf.ANALYZE_ANIME_TOP_MATCHES_SIZE:]
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
        logger.info('Calculating Authors Similarity Matrix...')
        authors_sim_mat = self.get_similarity_matrix(ref_mat.T)
        logger.info('Authors Similarity Matrix %s Calculated.' % str(authors_sim_mat.shape))
        authors_sim_indexes_mat = authors_sim_mat.argsort()[:, 0 - self.conf.ANALYZE_AUTHOR_TOP_MATCHES_SIZE:]
        logger.info('Authors Sim-Indexes %s Get Finished.' % str(authors_sim_indexes_mat.shape))

        cur = 0
        for author_sim_indexes in authors_sim_indexes_mat:
            top_matches = []
            total_scores_with_weight, total_weight = 0, 0
            for index in author_sim_indexes:
                similarity = authors_sim_mat[cur, index]
                top_matches.append({'mid': mids[index], 'similarity': similarity})
                total_scores_with_weight += (similarity * ref_mat[index]).sum()
                total_weight += similarity
            top_matches.reverse()
            recommend_indexes = (total_scores_with_weight / total_weight).argsort()[
                                0 - self.conf.ANALYZE_ANIME_TOP_MATCHES_SIZE:]
            recommend_indexes_sorted = np.flip(recommend_indexes, axis=0)
            recommendation = [media_ids[index] for index in recommend_indexes_sorted]

            self.db.update_author_recommendation(mids[cur], top_matches, recommendation)
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
