# Bangumi-Crawler

![Bangumi-Crawler](https://s1.hdslb.com/bfs/static/jinkela/home/images/bgm-nodata.png)

## Overview
Bangumi-Crawler is a animes information and their comments crawler for [Bilibil](https://www.bilibili.com). It run with single thread and no framework was used.

## Features
* Incremental
* Containerized

## Usage

### With Docker
`docker run angelmsger/bangumi-crawler -itd --name=crawler --restart=always -e DB_HOST=192.168.151.198 -e DB_USERNAME=dev -e DB_PASSWORD=password`

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
Custom ```conf.py```.

#### Run
```python exec.py```

## Todo
1. MySQL support
2. Concurrent feature
