from typing import List, Optional
from urllib.parse import urljoin

from redis import StrictRedis

from spidercommon.model import Domain, session_scope
from spidercommon.regexes import onion_regex
from spidercommon.tasks import WorkerTask, celery


@celery.task(base=WorkerTask)
def update_blacklist():
    redis = update_blacklist.redis

    with session_scope() as db:
        # XXX do things that update the database
        pass
