# Bangumi

## Overview
Bangumi(this repo) is a simple crawler for [Bilibil](https://www.bilibili.com) with single thread and no framework.

## Usage
1. Set up env

```
python -m venv venv
source venv/bin/activate
pip install -r requirements
```
2. Set up storage backend

 Make sure your storage backend work correnctly, **ONLY** [MongoDB](https://www.mongodb.com) is supported now.
3. Configuration

 Custom ```conf.py```.
4. Run

 ```python exec.py```

## Todo
1. MySQL support
2. Concurrent feature
3. Upsert
