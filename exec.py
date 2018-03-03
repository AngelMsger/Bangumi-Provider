import time
from datetime import datetime

import schedule

from conf import conf, Dev, Prod
from db import MongoDB
from crawler import BangumiCrawler

if __name__ == '__main__':
    print('[INFO] Hello! This is Bangumi-Provider :)')

    crawler = BangumiCrawler(MongoDB, conf)

    if conf == Dev:
        print('[INFO] Running with Dev Enabled, Start Crawl Directly.')
        crawler.crawl()
    elif conf == Prod:
        print('[INFO] Time Now is %s, Task Schedules at %s Everyday.' % (datetime.now(), conf.CRON_AT))
        schedule.every().day.at(conf.CRON_AT).do(crawler.crawl)
        while True:
            schedule.run_pending()
            time.sleep(1)
