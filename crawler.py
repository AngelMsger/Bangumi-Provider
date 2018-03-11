import json
from datetime import datetime, timedelta
from json import JSONDecodeError

import requests
from requests.exceptions import RequestException

from utils import logger, log_duration


class BangumiCrawler:
    HEADERS = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Referer': 'https://bangumi.bilibili.com/anime/index',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 '
                      'Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

    def __init__(self, db, conf) -> None:
        self.conf = conf
        self.db = db
        self.auth_status = {
            'done': False,
            'last_update': datetime.now()
        }

    @staticmethod
    def make_anime(detail_response, raw_result):
        season_id = int(raw_result['season_id'])
        try:
            detail = json.loads(detail_response.text[19:-2])['result']
        except JSONDecodeError:
            logger.warning('Could Not Decode %s.' % detail_response.text)
            return None
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
    def make_review(review, media_id, is_long=True):
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
            'media_id': int(media_id),
            'is_long': is_long
        }
        if is_long:
            result.update({
                'title': review['title'],
                'is_origin': bool(review['is_origin']),
                'is_spoiler': bool(review['is_spoiler']),
            })
        if 'user_season' in review:
            result.update({'last_ep_index': review['user_season']['last_ep_index']})
        return result

    def auth(self, username=None, password=None):
        if self.auth_status['done'] and self.auth_status['last_update'] > datetime.now() - timedelta(seconds=180):
            return False
        else:
            username = username or self.conf.CRAWL_USERNAME
            password = password or self.conf.CRAWL_PASSWORD
            try:
                if ('access_key' not in self.auth_status) or \
                        (self.auth_status['last_update'] < datetime.now() - timedelta(days=7)):
                    self.auth_status['access_key'] = requests.post('https://api.kaaass.net/biliapi/user/login', data={
                        'user': username, 'passwd': password
                    }).json()['access_key']

                response = requests.get('https://api.kaaass.net/biliapi/user/sso?access_key=%s' %
                                        self.auth_status['access_key']).json()
                if response['status'] == 'OK':
                    self.HEADERS.update({'Cookie': response['cookie']})
                    return True
            except (RequestException, JSONDecodeError, KeyError):
                return False

    def get_bulk_reviews(self, media_id, cursor, is_long=True):
        reviews_type = 'long' if is_long else 'short'
        logger.info("Getting %s's %s Reviews..." % (media_id, reviews_type))
        url = 'https://bangumi.bilibili.com/review/web_api/%s/list?media_id=%s' % (reviews_type, media_id)
        response = requests.get('%s&cursor=%s' % (url, cursor) if cursor is not None else url, headers=self.HEADERS)
        result = response.json()['result']
        total, reviews = result['total'], result['list']
        results = []
        while len(reviews) > 0:
            results.extend([self.make_review(review, media_id)
                            if is_long else self.make_review(review, media_id, is_long=False) for review in reviews])
            cursor = reviews[-1]['cursor']
            logger.debug("Processing %s's Reviews at Cursor: %s..." % (media_id, cursor))
            reviews = requests.get('%s&cursor=%s' % (url, cursor), headers=self.HEADERS).json()['result']['list']

        logger.info("Getting %s's %s Reviews Finished." % (media_id, reviews_type.title()))
        return results, cursor

    def process_animes(self, todo, max_retry):
        """
        Get Detail of Animes and Persist.
        """

        logger.info('Getting Animes...')
        url = 'https://bangumi.bilibili.com/jsonp/seasoninfo/%s.ver?callback=seasonListCallback&jsonp=jsonp'
        retry = 0
        while len(todo) > 0 and retry < max_retry:
            logger.info('Start Trying %s Times, %s Animes Left.' % (retry, len(todo)))
            results = []
            for raw_result in todo:
                season_id = int(raw_result['season_id'])
                logger.debug('Processing %s...' % season_id)
                try:
                    detail_response = requests.get(url % season_id, headers={
                        'Referer': 'https://bangumi.bilibili.com/anime/%s' % season_id
                    }.update(self.HEADERS))
                except RequestException:
                    detail_response = None
                if detail_response is not None and detail_response.status_code == 200:
                    result = self.make_anime(detail_response, raw_result)
                    if result is not None:
                        results.append(result)
                        todo.remove(raw_result)
                        logger.info('%s Processed.' % season_id)
                    else:
                        logger.warning("Decode %s's Response Error, Waiting for Retry...")
                        continue
                else:
                    logger.warning("Request %s's API Failed, Waiting for Retry..." % season_id)
            self.db.persist_animes(results)
            retry += 1
            logger.info('%s Try Finished, %s Solved, %s Left.' % (retry, len(results), len(todo)))
        logger.info('Getting Detail Finished, with %s Errors.' % len(todo))
        return len(todo), retry

    def process_reviews(self, max_retry):
        """
        Get reviews of animes
        """

        logger.info('Getting Reviews...')
        retry = 0
        entrances = self.db.get_all_entrances()
        while len(entrances) > 0 and retry < max_retry:
            logger.info('Start Trying %s Times, %s Animes Left.' % (retry, len(entrances)))
            for entrance in entrances:
                is_entrance_finished = True

                try:
                    reviews, last_long_reviews_cursor = self.get_bulk_reviews(entrance['media_id'],
                                                                              entrance['last_long_reviews_cursor'])
                    self.db.persist_reviews(entrance['media_id'], reviews, last_long_reviews_cursor)
                    entrance['last_long_reviews_cursor'] = last_long_reviews_cursor
                except (KeyError, RequestException):
                    is_entrance_finished = False
                    logger.warning("Get %s's Long Reviews Failed, Waiting for Retry..." % entrance['media_id'])
                try:
                    reviews, last_short_reviews_cursor = \
                        self.get_bulk_reviews(entrance['media_id'], entrance['last_short_reviews_cursor'],
                                              is_long=False)
                    self.db.persist_reviews(entrance['media_id'], reviews, last_short_reviews_cursor, is_long=False)
                    entrance['last_short_reviews_cursor'] = last_short_reviews_cursor
                except (KeyError, RequestException):
                    is_entrance_finished = False
                    logger.warning("Get %s's Reviews Failed, Waiting for Retry..." % entrance['media_id'])
                if is_entrance_finished:
                    entrances.remove(entrance)
                    logger.info("Get %s's Reviews Finished." % entrance['media_id'])
            retry += 1
        return len(entrances), retry

    def get_author_follow(self, mid, page_index, max_retry, retry=1):
        if retry >= max_retry:
            logger.error("Cannot Get %s's Information After Try %s Times." % (mid, retry))
            return 0, []

        url = 'https://space.bilibili.com/ajax/Bangumi/getList?mid=%s' % \
              (mid if page_index is None else '%s&page=%s' % (mid, page_index))
        response = requests.get(url, headers=self.HEADERS).json()
        if not response['status']:
            if response['data'] == '获取登录数据失败':
                logger.warning("%s's API Request Failed, Try to Auth..." % mid)
                if self.auth():
                    logger.info('Auth Success.')
                    return self.get_author_follow(mid, page_index, max_retry, retry=retry + 1)
                else:
                    raise RuntimeError('Auth Failed.')
            elif response['data'] == '用户隐私设置未公开':
                return 0, []
        return int(response['data']['pages']), response['data']['result']

    def process_authors(self, max_retry):
        logger.info('Getting Authors...')
        tasks = [i['mid'] for i in self.db.get_author_tasks()]

        retry = 0
        while len(tasks) > 0 and retry < max_retry:
            logger.info('Start Trying %s Times, %s Authors Left.' % (retry, len(tasks)))
            for mid in tasks:
                try:
                    season_ids = []
                    pages, result = self.get_author_follow(mid, page_index=None, max_retry=max_retry)
                    season_ids.extend([int(i['season_id']) for i in result])
                    for page_index in range(2, pages):
                        _, result = self.get_author_follow(mid, page_index=page_index, max_retry=max_retry)
                        season_ids.extend([int(i['season_id']) for i in result])
                    self.db.push_to_follow(mid, season_ids)
                    tasks.remove(mid)
                    logger.info("Get %s's Follow Finished." % mid)
                except (RequestException, RuntimeError) as e:
                    logger.warning("Get %s's Follow Failed, Waiting for Retry...(%s)" % (mid, e))
                    continue
            retry += 1
        return len(tasks), retry

    @log_duration
    def crawl(self, full_crawl=False, max_retry=None) -> None:
        logger.info('New Crawl Beginning...')

        # Get all animes
        logger.info('Getting Animes List...')
        url = "https://bangumi.bilibili.com/web_api/season/index_global?version=%s&area=%s&is_finish=%s&start_year=%s" \
              "&quarter=%s&tag_id=%s" % (
                  self.conf.CRAWL_VERSION,
                  self.conf.CRAWL_AREA,
                  1 if self.conf.CRAWL_IS_FINISH else 0,
                  self.conf.CRAWL_START_YEAR,
                  self.conf.CRAWL_QUARTER,
                  '' if self.conf.CRAWL_TAG_ID == 0 else self.conf.ANIMES_TAG_ID
              )
        response = requests.get(url, headers=self.HEADERS).json()
        pages = int(response.get("result", {}).get("pages", 0))
        url += '&page=%s'

        if full_crawl:
            self.db.truncate_all()

        todo = []
        for i in range(1, pages + 1):
            logger.info('Preparing %s/%s...' % (i, pages))
            while True:
                try:
                    raw_results = requests.get(url % i, headers=self.HEADERS).json().get('result', {}).get('list', [])
                    break
                except RequestException:
                    logger.warning('Get %s Todo Failed, Waiting for Retry...' % i)
            for raw_result in raw_results:
                todo.append(raw_result)

        max_retry = max_retry or self.conf.CRAWL_MAX_RETRY
        todo_left, detail_retry = self.process_animes(todo, max_retry)
        reviews_left, reviews_retry = self.process_reviews(max_retry)

        if self.conf.CRAWL_AUTHOR_FOLLOW:
            authors_left, authors_retry = self.process_authors(max_retry)
        else:
            authors_left = authors_retry = 0

        logger.info('Archiving...')
        self.db.archive()
        logger.info('Archive Finished.')

        logger.info('Crawling Tasks Finished, (%s, %s, %s) Left, with (%s, %s, %s) Times Retry.'
                    % (todo_left, reviews_left, authors_left, detail_retry, reviews_retry, authors_retry))
