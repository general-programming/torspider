#!/usr/bin/env python3

import code
import os
import re
import uuid
from urllib.parse import urljoin, urlparse

import praw
import requests

from spidercommon.model import Domain, OnionListPage, sm
from spidercommon.redis import create_redis
from spidercommon.tasks.onions import domain_cron
from spidercommon.tasks.pages import check_page, check_ports_for_all_domains, fetch_page_for_all_domains, find_onions
from spidercommon.tasks.reddit import fetch_subreddit

try:
    import IPython
except ImportError:
    IPython = None



# Connections

db = sm()
redis = create_redis()


# CLI functions

def purge_dupekeys(list_key="torspider:dupekeys:dupefilter"):
    for member_key in redis.smembers(list_key):
        if not redis.exists(member_key):
            print(f"Removing key {member_key}")
            redis.srem(list_key, member_key)


def grab_onions(url: str):
    request = requests.get(url)
    db_entry = db.query(OnionListPage).filter(OnionListPage.url == url).scalar()
    if not db_entry:
        db_entry = OnionListPage(
            url=url
        )
        db.add(db_entry)

    db_entry.content = request.text
    db.commit()
    find_onions(redis, request.text)


if __name__ == "__main__":
    if IPython:
        IPython.embed()
    else:
        code.interact(local=locals())
