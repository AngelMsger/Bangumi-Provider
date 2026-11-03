# Bangumi-Provider
[![Build Status](https://travis-ci.org/AngelMsger/Bangumi-Provider.svg?branch=master)](https://travis-ci.org/AngelMsger/Bangumi-Provider)

![Bangumi-Crawler](https://s1.hdslb.com/bfs/static/jinkela/home/images/bgm-nodata.png)

## Overview
Bangumi-Provider is a content provider for [Bangumi-Visualizer](https://github.com/AngelMsger/Bangumi-Visualizer). It crawl, analyze the data from [Bilibili](https://www.bilibili.com), and persist the result to database, using [Collaborative Filtering](https://www.wikiwand.com/en/Collaborative_filtering) algorithm when analyzing data. It run with single thread and no framework was used.

## Features
* Incremental Crawl & Analyze
* Multi Storage Backend Support
* Containerized

## Usage

### With Docker-Compose
`docker-compose up`

### With Docker
`docker run -itd --name=provider --net=host -e DB_PASSWORD=$DB_PASSWORD angelmsger/bangumi-provider`

### Manually
Use Python 3.12, MongoDB 8.0 and Redis 7.4 (the versions exercised by CI).
The pinned NumPy/SciPy stack requires Python 3.12 or newer; the Docker image uses 3.12.
MongoDB 8.0 currently requires a Linux kernel older than 6.19
([SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912)); CI uses Ubuntu 22.04.

`python3.12 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && python exec.py`

When database authentication is enabled, `DB_USERNAME` must be a user in
`DB_DATABASE`, with access to that database. Credentials are passed to PyMongo's
client using that database as `authSource`.

### Tests

```sh
python -m pip check
python -m unittest discover -s tests -v
```

The MongoDB and Redis integration tests are optional locally. To run them, set
`BANGUMI_TEST_MONGO_URI` to an admin URI on a **disposable local MongoDB instance**
and `BANGUMI_TEST_REDIS_URL` to a **disposable local Redis instance**. The tests
create and remove uniquely named MongoDB databases/users, and configure Redis
cache limits. CI runs both integrations, including database authentication.
Tests use local fixtures and do not validate the availability of Bilibili's APIs.

## Todo
1. MySQL support
2. Concurrent feature

## Quote
1. Use [Kaaass](kaaass.net)'s API when auth after v1.3.x.
