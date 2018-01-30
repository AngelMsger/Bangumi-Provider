import json
from datetime import datetime

import requests
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
        season_id = raw_result['season_id']
        detail = json.loads(detail_response.text[19:-2])['result']
        media = detail['media']
        result = {
            '_id': season_id,
            'title': raw_result['title'],
            'alias': detail.get('alias', ''),
            'tags': [{'id': tag['tag_id'], 'name': tag['tag_name']} for tag in detail.get('tags', [])],
            'area': [{'id': area['id'], 'name': area['name']} for area in media.get('area', [])],
            'is_finish': raw_result['is_finish'],
            'favorites': raw_result['favorites'],
            'cover_url': raw_result['cover'],
            'pub_time': raw_result['pub_time'],
            'media_id': media['media_id'],
            'evaluate': detail.get('evaluate', ''),
            'episodes': len(detail['episodes'])
        }
        if 'rating' in media:
            result.update({'rating': media['rating']})
        return result

    @staticmethod
    def make_long_review(review, media_id):
        result = {
            '_id': int(review['review_id']),
            'author': review['author'],
            'title': review['title'],
            'content': review['content'],
            'ctime': datetime.fromtimestamp(int(review['ctime'])),
            'mtime': datetime.fromtimestamp(int(review['mtime'])),
            'likes': int(review['likes']),
            'score': int(review['user_rating']['score']),
            'is_origin': bool(review['is_origin']),
            'is_spoiler': bool(review['is_spoiler']),
            'media_id': int(media_id)
        }
        if 'user_season' in review:
            result.update({'last_ep_index': int(review['user_season']['last_ep_index'])})
        return result

    @staticmethod
    def make_short_review(review, media_id):
        result = {
            '_id': review['review_id'],
            'author': review['author'],
            'content': review['content'],
            'ctime': datetime.fromtimestamp(int(review['ctime'])),
            'mtime': datetime.fromtimestamp(int(review['mtime'])),
            'likes': int(review['likes']),
            'score': int(review['user_rating']['score']),
            'media_id': media_id
        }
        if 'user_season' in review:
            result.update({'last_ep_index': int(review['user_season']['last_ep_index'])})
        return result

    def get_bulk_reviews(self, media_id, long=True):
        print('[INFO] %s starting...' % media_id)
        url = 'https://bangumi.bilibili.com/review/web_api/%s/list?media_id=%s' \
              % ('long' if long else 'short', media_id)
        response = requests.get(url)
        result = json.loads(response.text)['result']
        total, reviews = result['total'], result['list']
        results, count = [], 0
        while len(results) < total and len(reviews) > 0:
            results.extend([self.make_long_review(review, media_id)
                            if long else self.make_short_review(review, media_id) for review in reviews])
            cursor = reviews[-1].get('cursor', None)
            count = len(results)
            print('[INFO] parsing %s...%s/%s.' % (media_id, count, total))
            if cursor is not None:
                reviews = json.loads(requests.get('%s&cursor=%s' % (url, cursor)).text)['result']['list']
            else:
                break
        print('[%s] %s finished.' % ('SUCCESS' if count == total else 'WARNING', media_id))
        return results

    def crawl(self, max_retry=512):
        print('[INFO] hello! this is bangumi crawler :)')

        # Get all animes
        print('[INFO] getting animes...')
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

        todo = []
        for i in range(1, pages + 1):
            print('[INFO] %s/%s...' % (i, pages))
            raw_results = json.loads(requests.get(url % i, headers=BangumiCrawler.HEADERS).text).get('result', {}) \
                .get('list', [])
            for raw_result in raw_results:
                if not self.db.is_anime_finished(int(raw_result['season_id'])):
                    todo.append(raw_result)

        # Get detail of animes
        print('[INFO] getting details...')
        url = 'https://bangumi.bilibili.com/jsonp/seasoninfo/%s.ver?callback=seasonListCallback&jsonp=jsonp'
        retry = 0
        while len(todo) > 0 and retry < max_retry:
            results = []
            for raw_result in todo:
                season_id = int(raw_result['season_id'])
                print('[INFO] starting %s...' % season_id)
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
                    print('[INFO] get %s finished.' % season_id)
                else:
                    print('[WARNING] request api failed, waiting for retry, season_id: %s' % season_id)
            self.db.persist_animes(results)
            retry += 1
            print('[INFO] %s try finished, %s solved, %s left.' % (retry, len(results), len(todo)))
        print('[%s] get detail finished, %s.' % ('SUCCESS', 'no error.')
              if len(todo) == 0 else ('WARNING', 'with %s errors.' % len(todo)))

        # Get Reviews of animes
        print('[INFO] getting reviews...')
        media_ids = self.db.get_all_media_ids()
        for media_id in media_ids:
            if not self.db.is_reviews_finished(media_id):
                long_reviews = self.get_bulk_reviews(media_id)
                short_reviews = self.get_bulk_reviews(media_id, long=False)
                self.db.persist_long_reviews(long_reviews)
                self.db.persist_short_reviews(short_reviews)

        print('[SUCCESS] all tasks finished, with %s times retry.' % retry)


if __name__ == '__main__':
    crawler = BangumiCrawler(MongoDB, conf)
    crawler.crawl()
