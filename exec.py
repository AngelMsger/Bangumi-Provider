import time

import schedule

from analyzer import BangumiAnalyzer
from conf import conf
from crawler import BangumiCrawler
from db import MongoDB
from utils import logger

if __name__ == '__main__':
    logger.info('Hello! This is Bangumi-Provider :)')

    client = MongoDB(conf)

    crawler = BangumiCrawler(client, conf)
    analyzer = BangumiAnalyzer(client, conf)

    def jobs():
        crawler.crawl()
        analyzer.analyze()

    if conf.SCHEDULE_ENABLE:
        logger.info('Running with Schedule Enabled, Tasks Schedule Every Week.')
        schedule.every().week.do(jobs)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        logger.info('Running with Schedule Disabled, Start Tasks Directly.')
        jobs()
