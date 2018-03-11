# Bangumi-Provider
[![Build Status](https://travis-ci.org/AngelMsger/Bangumi-Provider.svg?branch=master)](https://travis-ci.org/AngelMsger/Bangumi-Provider)

![Bangumi-Crawler](https://s1.hdslb.com/bfs/static/jinkela/home/images/bgm-nodata.png)

## Overview
Bangumi-Provider is a content provider for [Bangumi-Player](https://github.com/AngelMsger/Bangumi-Player). It crawl, analyze the data from [Bilibili](https://www.bilibili.com), and persist the result to database. It run with single thread and no framework was used.

## Features
* Incremental
* Containerized

## Usage

### With Docker-Compose
`docker-compose up`

### With Docker
`docker run -itd --name=provider --net=host --restart=always -e DB_PASSWORD=$DB_PASSWORD angelmsger/bangumi-provider`

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

## Quote
1. Use [Kaaass](kaaass.net)'s API when auth after v1.3.x.
