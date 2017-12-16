import code
import os
import re
import uuid
from urllib.parse import urlparse

import praw
from spidercommon.redis import create_redis

# Connections

reddit = praw.Reddit(user_agent="/u/nepeat tor onion scraper")

if "REDDIT_USERNAME" in os.environ and "REDDIT_PASSWORD" in os.environ:
    reddit.login(
        os.environ["REDDIT_USERNAME"],
        os.environ["REDDIT_PASSWORD"]
    )

redis = create_redis()

# Parsers

onion_regex = re.compile(r"IMCOMPLETE", re.IGNORECASE)

# CLI functions

def fetch_subreddit(subreddit, top=True, limit=None):
    sub = reddit.get_subreddit(subreddit)

    for post in sub.get_hot(limit=limit):
        check_onions(post)

    if top:
        topfuncs = [
            sub.get_top_from_all,
            sub.get_top_from_year,
            sub.get_top_from_month,
            sub.get_top_from_week,
            sub.get_top_from_day,
        ]
        for func in topfuncs:
            for post in func(limit=limit):
                check_onions(post)

def check_onions(post):
    raise NotImplementedError()

if __name__ == "__main__":
    code.interact(local=locals())
