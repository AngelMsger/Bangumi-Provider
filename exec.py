import time
from datetime import datetime

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
        logger.info('Running with Schedule Enabled, Tasks Schedule Every Day. Now: %s, Next Schedule: %s.' %
                    (datetime.now(), conf.SCHEDULE_CRON_AT))
        schedule.every().day.at(conf.SCHEDULE_CRON_AT).do(jobs)
        while True:
            schedule.run_pending()
            time.sleep(1)
    else:
        logger.info('Running with Schedule Disabled, Start Tasks Directly.')
        jobs()
