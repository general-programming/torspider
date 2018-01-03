import code
import os

import praw
import requests

from spidercommon.model import Domain, OnionListPage, sm
from spidercommon.redis import create_redis
from spidercommon.regexes import onion_regex

# Connections

reddit = praw.Reddit(
    user_agent="/u/nepeat tor onion scraper",
    client_id=os.environ["REDDIT_CLIENT_ID"],
    client_secret=os.environ["REDDIT_CLIENT_SECRET"],
    username=os.environ.get("REDDIT_USERNAME", None),
    password=os.environ.get("REDDIT_PASSWORD", None)
)

db = sm()
redis = create_redis()

# CLI functions

def purge_dupekeys(list_key="torspider:dupekeys:dupefilter"):
    for member_key in redis.smembers(list_key):
        if not redis.exists(member_key):
            print(f"Removing key {member_key}")
            redis.srem(list_key, member_key)

def fetch_subreddit(subreddit, top=True, limit=None):
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
            add_onions(post.url)
            add_onions(post.selftext)

def check_ports():
    http_ports = [80, 5000, 5800, 8000, 8008, 8080]
    for domain in db.query(Domain):
        for port in http_ports:
            if port == 80:
                joined_url = f"http://{domain.host}"
            else:
                joined_url = f"http://{domain.host}:{port}"
            redis.sadd("torspider:singleurls", joined_url)

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
    add_onions(request.text)

# Helper functions

def add_onions(content):
    if not content:
        return

    try:
        content = str(content)
    except UnicodeDecodeError:
        pass

    onions = onion_regex.findall(content)
    for onion in onions:
        print(f"Adding {onion} to queue.")
        redis.sadd("torspider:urls", f"http://{onion}")

if __name__ == "__main__":
    code.interact(local=locals())
