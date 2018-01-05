import requests
from typing import List, Optional
from urllib.parse import urljoin
from spidercommon.util.hashing import md5
from sqlalchemy.dialects.postgresql import insert

from redis import StrictRedis

from spidercommon.model import Page, Domain, OnionBlacklist, session_scope
from spidercommon.regexes import onion_regex
from spidercommon.tasks import WorkerTask, celery


def fetch_ahmia_blacklist():
    return [x.strip() for x in requests.get("https://ahmia.fi/blacklist/banned/").text.split("<br>\n\n") if x]

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
                page.content = "<h1>Nope.</h1>"
            db.commit()
