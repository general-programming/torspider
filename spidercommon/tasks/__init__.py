# coding=utf-8
import os

import raven
from celery import Celery, Task
from classtools import reify
from raven.contrib.celery import register_logger_signal, register_signal
from redis import StrictRedis

from spidercommon.redis import redis_pool

celery = Celery("spidercommon", include=[
    "spidercommon.tasks.pages",
    "spidercommon.tasks.reddit",
    "spidercommon.tasks.onions",
    "spidercommon.tasks.elasticsearch",
])

# Sentry exception logging if there is a sentry object.
if "SENTRY_DSN" in os.environ or ("SENTRY_TOR_DSN" in os.environ and "HTTPS_PROXY" in os.environ):
    if "HTTPS_PROXY" in os.environ:
        dsn_url = os.environ["SENTRY_TOR_DSN"]
    else:
        dsn_url = os.environ["SENTRY_DSN"]

    sentry = raven.Client(
        dsn=dsn_url,
        include_paths=["spidercommon"],
    )
    register_logger_signal(sentry)
    register_signal(sentry)

celery.config_from_object('spidercommon.tasks.config')


class WorkerTask(Task):
    abstract = True

    @reify
    def redis(self):
        return StrictRedis(connection_pool=redis_pool)
