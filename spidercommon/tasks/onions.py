# coding=utf-8
import datetime
from typing import List, Optional
from urllib.parse import urljoin

import requests
from celery.utils.log import get_task_logger
from redis import StrictRedis
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert

from spidercommon.constants import BLACKLISTED_BLANK
from spidercommon.model import (Domain, File, OnionBlacklist, Page,
                                session_scope)
from spidercommon.regexes import onion_regex
from spidercommon.tasks import WorkerTask, celery
from spidercommon.tasks.pages import check_page
from spidercommon.util.compat import random
from spidercommon.util.distribution import queue_url
from spidercommon.util.hashing import md5, sha256
from spidercommon.util.storage import HashedFile

logger = get_task_logger(__name__)


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
        for domain in db.query(Domain).filter(Domain.blacklisted == False).yield_per(500):
            if md5(domain.host) in blacklist_md5:
                domain.blacklisted = True


@celery.task(base=WorkerTask)
def wipe_blacklisted():
    with session_scope() as db:
        for domain in db.query(Domain).filter(Domain.blacklisted == True).yield_per(250):
            for file_obj in db.query(File).filter(and_(File.domain_id == domain.id, File.file_hash != sha256(BLACKLISTED_BLANK))).yield_per(250):
                file_store = HashedFile.from_hash(file_obj.file_hash)
                file_store.write(BLACKLISTED_BLANK)
                file_obj.content = BLACKLISTED_BLANK


@celery.task(base=WorkerTask)
def domain_cron():
    redis = domain_cron.redis

    with session_scope() as db:
        for domain in db.query(Domain).filter(Domain.blacklisted == False).yield_per(500):
            time_delta = datetime.datetime.utcnow() - domain.last_crawl
            time_hours = (time_delta.total_seconds() / 60) / 24

            # Mark the domain as dead if there has been no crawls for a week.
            if domain.is_alive and time_hours > (24 * 7):
                logger.debug(f"{domain.host} has not been crawled for {time_hours} hours. Marked as dead.")
                domain.is_alive = False

            # Dirty exponential that guarantees that the function runs by the time last crawl reaches 4 days, 20 hours if the domain is alive.
            # The time is bumped to about a month if the domain is dead.
            if domain.is_alive:
                probablity = (10 ** (1 / 58)) ** time_hours
            else:
                probablity = (10 ** (1 / 420)) ** time_hours

            if probablity > random.randint(0, 100):
                check_page(redis, domain.host, domain.port, single=True, priority=domain.priority)
