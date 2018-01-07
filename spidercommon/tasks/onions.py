import datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from redis import StrictRedis
from sqlalchemy.dialects.postgresql import insert

from spidercommon.model import Domain, OnionBlacklist, Page, session_scope
from spidercommon.regexes import onion_regex
from spidercommon.tasks import WorkerTask, celery
from spidercommon.util.compat import random
from spidercommon.util.distribution import queue_url
from spidercommon.util.hashing import md5


def fetch_ahmia_blacklist():
    return [x.strip() for x in requests.get("https://ahmia.fi/blacklist/banned/").text.split("<br>\n\n") if x]

BLACKLISTED_BLANK = "<h1>Nope.</h1>"


@celery.task(base=WorkerTask)
def update_blacklist():
    redis = update_blacklist.redis

    blacklist_md5_sources = {
        "ahmia": fetch_ahmia_blacklist()
    }
    blacklist_md5 = [*blacklist_md5_sources["ahmia"]]

    with session_scope() as db:
        for source, hashlist in blacklist_md5_sources.items():
            for onionhash in hashlist:
                statement = insert(OnionBlacklist).values(
                    hexhash=onionhash,
                    hashmethod="md5",
                    source=source
                ).on_conflict_do_nothing(index_elements=["hexhash"])
                db.execute(statement)

    with session_scope() as db:
        for domain in db.query(Domain).yield_per(500):
            if md5(domain.host) in blacklist_md5:
                domain.blacklisted = True


@celery.task(base=WorkerTask)
def wipe_blacklisted():
    with session_scope() as db:
        for domain in db.query(Domain).filter(Domain.blacklisted == True).yield_per(250):
            for page in db.query(Page).filter(Page.domain_id == domain.id).yield_per(250):
                if page.content != BLACKLISTED_BLANK:
                    page.content = BLACKLISTED_BLANK
            db.commit()


@celery.task(base=WorkerTask)
def queue_alivecheck():
    redis = queue_alivecheck.redis

    with session_scope() as db:
        for domain in db.query(Domain).filter(Domain.blacklisted == False).yield_per(500):
            time_delta = datetime.datetime.utcnow() - domain.last_crawl
            time_hours = (time_delta.total_seconds() / 60) / 24

            # Dirty exponential that guarantees that the function runs by the time last crawl reaches 4 days, 20 hours.
            probablity = (10 ** (1/58)) ** time_hours
            if probablity > random.randint(0, 100):
                if domain.port == 80:
                    queue_url(redis, domain.priority, "singleurls", f"http://{domain.host}")
                else:
                    queue_url(redis, domain.priority, "singleurls", f"http://{domain.host}:{domain.port}")
