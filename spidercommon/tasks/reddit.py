import os

import praw

from spidercommon.tasks import WorkerTask, celery
from spidercommon.tasks.pages import find_onions

reddit = praw.Reddit(
    user_agent="/u/nepeat tor onion scraper",
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ.get("REDDIT_USERNAME", None),
    password=os.environ.get("REDDIT_PASSWORD", None)
)


@celery.task(base=WorkerTask)
def fetch_subreddit(subreddit, top=True, limit=None):
    redis = fetch_subreddit.redis

    sub = reddit.subreddit(subreddit)
    getter_funcs = [sub.hot(limit=limit)]

    if top:
        getter_funcs.extend([
            sub.top("all", limit=limit),
            sub.top("year", limit=limit),
            sub.top("month", limit=limit),
            sub.top("week", limit=limit),
            sub.top("day", limit=limit),
        ])

    for func in getter_funcs:
        for post in func:
            find_onions(redis, post.url)
            find_onions(redis, post.selftext)
