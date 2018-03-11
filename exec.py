import time
from datetime import datetime

import schedule

from conf import conf, Dev, Prod
from db import MongoDB
from crawler import BangumiCrawler
from analyzer import BangumiAnalyzer
from utils import logger

if __name__ == '__main__':
    print('[INFO] Hello! This is Bangumi-Provider :)')

    client = MongoDB(conf)

    crawler = BangumiCrawler(client, conf)
    analyzer = BangumiAnalyzer(client, conf)

    def jobs():
        crawler.crawl()
        analyzer.analyze()

    if conf == Dev:
        logger.info('Running with Dev Enabled, Start Task Directly.')
        jobs()
    elif conf == Prod:
        logger.info('Time Now is %s, Task Schedules at %s Everyday.' % (datetime.now(), conf.CRON_AT))
        schedule.every().day.at(conf.CRON_AT).do(jobs)
        while True:
            schedule.run_pending()
            time.sleep(1)
