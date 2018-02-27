# Bangumi-Crawler
[![Build Status](https://travis-ci.org/AngelMsger/Bangumi-Crawler.svg?branch=master)](https://travis-ci.org/AngelMsger/Bangumi-Crawler)

![Bangumi-Crawler](https://s1.hdslb.com/bfs/static/jinkela/home/images/bgm-nodata.png)

## Overview
Bangumi-Crawler is a animes information and their comments crawler for [Bilibili](https://www.bilibili.com). It run with single thread and no framework was used.

## Features
* Incremental
* Containerized

## Usage

### With Docker-Compose
`docker-compose up`

### With Docker
`docker run -itd --name=crawler --net=host --restart=always -e DB_PASSWORD=password angelmsger/bangumi-crawler`

### Manually

#### Set up env
```
python -m venv venv
source venv/bin/activate
pip install -r requirements
```

#### Set up storage backend
Make sure your storage backend work correnctly, **ONLY** [MongoDB](https://www.mongodb.com) is supported now.

#### Configuration
Custom `conf.py`.

#### Run
`python exec.py`

## Todo
1. MySQL support
2. Concurrent feature
