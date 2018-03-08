import numpy as np

from scipy.stats import pearsonr


class BangumiAnalyzer:
    def __init__(self, db_class, conf) -> None:
        self.conf = conf
        self.db = db_class(self.conf)

    def get_animes_authors_refs_matrix(self):
        pass
