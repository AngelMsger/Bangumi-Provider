import json
import time
import time
from datetime import datetime

import requests
import schedule
from requests.exceptions import RequestException

from conf import conf
from db import MongoDB


class BangumiCrawler:
    HEADERS = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://bangumi.bilibili.com/anime/index',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.119 '
                      'Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    def __init__(self, db_class, configurations) -> None:
        self.db = db_class(configurations)
        self.conf = configurations

    @staticmethod
    def make_anime(detail_response, raw_result):
        season_id = int(raw_result['season_id'])
        detail = json.loads(detail_response.text[19:-2])['result']
        media = detail['media']
        result = {
            'season_id': season_id,
            'title': raw_result['title'],
            'alias': detail.get('alias', ''),
            'tags': [{'id': int(tag['tag_id']), 'name': tag['tag_name']} for tag in detail.get('tags', [])],
            'area': [{'id': int(area['id']), 'name': area['name']} for area in media.get('area', [])],
            'is_finish': bool(raw_result['is_finish']),
            'favorites': int(raw_result['favorites']),
            'danmaku_count': int(detail['danmaku_count']),
            'cover_url': raw_result['cover'],
            'pub_time': datetime.fromtimestamp(raw_result['pub_time']),
            'media_id': media['media_id'],
            'evaluate': detail.get('evaluate', ''),
            'episodes': len(detail['episodes'])
        }
        if 'rating' in media:
            result.update({
                'rating': {
                    'count': int(media['rating']['count']),
                    'score': float(media['rating']['score'])
                }
            })
        return result

    @staticmethod
    def make_review(review, media_id, long=True):
        author = review['author']
        result = {
            'review_id': int(review['review_id']),
            'author': {
                'mid': int(author['mid']),
                'avatar_url': author['avatar'],
                'uname': author['uname']
            },

            'content': review['content'],
            'ctime': datetime.fromtimestamp(int(review['ctime'])),
            'mtime': datetime.fromtimestamp(int(review['mtime'])),
            'likes': int(review['likes']),
            'score': float(review['user_rating']['score']),
            'media_id': int(media_id)
        }
        if long:
            result.update({
                'title': review['title'],
                'is_origin': bool(review['is_origin']),
                'is_spoiler': bool(review['is_spoiler']),
            })
        if 'user_season' in review:
            result.update({'last_ep_index': review['user_season']['last_ep_index']})
        return result

    def get_bulk_reviews(self, media_id, cursor, long=True):
        reviews_type = 'long' if long else 'short'
        print("[INFO] Getting %s's %s Reviews..." % (media_id, reviews_type))
        url = 'https://bangumi.bilibili.com/review/web_api/%s/list?media_id=%s' % (reviews_type, media_id)
        response = requests.get('%s&cursor=%s' % (url, cursor) if cursor is not None else url)
        result = json.loads(response.text)['result']
        total, reviews = result['total'], result['list']
        results = []
        while len(reviews) > 0:
            results.extend([self.make_review(review, media_id)
                            if long else self.make_review(review, media_id, long=False) for review in reviews])
            cursor = reviews[-1]['cursor']
            print("[DEBUG] Processing %s's Reviews at Cursor: %s..." % (media_id, cursor))
            reviews = json.loads(requests.get('%s&cursor=%s' % (url, cursor)).text)['result']['list']
        print('[%s] %s Finished.' %
              ('SUCCESS' if self.db.get_reviews_count(media_id, long=long) == total else 'WARNING', media_id))
        return results, cursor

    def crawl(self, full_crawl=False, max_retry=16):
        print('[INFO] New Crawl Beginning...')

        # Get all animes
        print('[INFO] Getting Animes List...')
        url = "https://bangumi.bilibili.com/web_api/season/index_global?version=%s&area=%s&is_finish=%s&start_year=%s" \
              "&quarter=%s&tag_id=%s" % (
                  self.conf.ANIMES_VERSION,
                  self.conf.ANIMES_AREA,
                  1 if self.conf.ANIMES_IS_FINISH else 0,
                  self.conf.ANIMES_START_YEAR,
                  self.conf.ANIMES_QUARTER,
                  '' if self.conf.ANIMES_TAG_ID == 0 else self.conf.ANIMES_TAG_ID
              )
        response = json.loads(requests.get(url, headers=BangumiCrawler.HEADERS).text)
        pages = int(response.get("result", {}).get("pages", 0))
        url += '&page=%s'

        if full_crawl:
            self.db.truncate_all()
        else:
            self.db.archive()

        todo = []
        for i in range(1, pages + 1):
            print('[INFO] Preparing %s/%s...' % (i, pages))
            raw_results = json.loads(requests.get(url % i, headers=BangumiCrawler.HEADERS).text).get('result', {}) \
                .get('list', [])
            for raw_result in raw_results:
                todo.append(raw_result)

        # Get detail of animes
        url = 'https://bangumi.bilibili.com/jsonp/seasoninfo/%s.ver?callback=seasonListCallback&jsonp=jsonp'
        detail_retry = 0
        while len(todo) > 0 and detail_retry < max_retry:
            print('[INFO] Start Trying %s Times, %s Animes Left.' % (detail_retry, len(todo)))
            results = []
            for raw_result in todo:
                season_id = int(raw_result['season_id'])
                print('[INFO] Processing %s...' % season_id)
                try:
                    detail_response = requests.get(url % season_id, headers={
                        'Referer': 'https://bangumi.bilibili.com/anime/%s' % season_id
                    }.update(BangumiCrawler.HEADERS))
                except RequestException:
                    detail_response = None
                if detail_response is not None and detail_response.status_code == 200:
                    result = self.make_anime(detail_response, raw_result)
                    results.append(result)
                    todo.remove(raw_result)
                    print('[INFO] %s Processed.' % season_id)
                else:
                    print('[WARNING] Request API Failed, Waiting for Retry, season_id: %s.' % season_id)
            self.db.persist_animes(results)
            detail_retry += 1
            print('[INFO] %s Try Finished, %s Solved, %s Left.' % (detail_retry, len(results), len(todo)))
        print('[%s] Getting Detail Finished, %s.' % ('SUCCESS', 'no error.')
              if len(todo) == 0 else ('WARNING', 'with %s errors.' % len(todo)))

        # Get reviews of animes
        print('[INFO] Getting Reviews...')
        reviews_retry = 0
        entrances = self.db.get_all_entrances()
        while len(entrances) > 0 and reviews_retry < max_retry:
            print('[INFO] Start Trying %s Times, %s Animes Left.' % (reviews_retry, len(entrances)))
            for entrance in entrances:
                media_id, last_long_reviews_cursor, last_short_reviews_cursor = entrance
                long_reviews, last_long_reviews_cursor = self.get_bulk_reviews(media_id, last_long_reviews_cursor)
                short_reviews, last_short_reviews_cursor = self.get_bulk_reviews(media_id, last_short_reviews_cursor,
                                                                                 long=False)
                self.db.persist_reviews(media_id, long_reviews, last_long_reviews_cursor)
                self.db.persist_reviews(media_id, short_reviews, last_short_reviews_cursor, long=False)
                entrances.remove(entrance)
                print("[INFO] Get %s's Reviews Finished." % media_id)
            reviews_retry += 1

        print('[SUCCESS] Tasks Finished, %s Left, with (%s, %s) Times Retry.'
              % (len(entrances), detail_retry, reviews_retry))


if __name__ == '__main__':
    print('[INFO] Hello! This is Bangumi-Crawler :)')

    crawler = BangumiCrawler(MongoDB, conf)
    schedule.every().day.at(conf.CRON_AT).do(crawler.crawl)

    while True:
        schedule.run_pending()
        time.sleep(1)
