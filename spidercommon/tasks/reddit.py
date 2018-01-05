import os

import praw
from redis import StrictRedis

from spidercommon.tasks.pages import find_onions


class RedditFetcher:
    def __init__(self, redis: StrictRedis, client_id: str=None, client_secret: str=None, username: str=None, password: str=None):
        self.redis = redis
        self.reddit = praw.Reddit(
            user_agent="/u/nepeat tor onion scraper",
            client_id=client_id or os.environ["REDDIT_CLIENT_ID"],
            client_secret=client_secret or os.environ["REDDIT_CLIENT_SECRET"],
            username=username or os.environ.get("REDDIT_USERNAME", None),
            password=password or os.environ.get("REDDIT_PASSWORD", None)
        )

    def fetch_subreddit(self, subreddit, top=True, limit=None):
        sub = self.reddit.subreddit(subreddit)
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
                find_onions(self.redis, post.url)
                find_onions(self.redis, post.selftext)
