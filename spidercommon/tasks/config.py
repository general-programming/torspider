# coding=utf-8
import datetime
import os

from kombu import Exchange, Queue

# Debug
if "DEBUG" in os.environ:
    CELERY_REDIRECT_STDOUTS_LEVEL = "DEBUG"

# Broker and Result backends
BROKER_URL = os.environ.get("CELERY_BROKER", "redis://localhost/1")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT", "redis://localhost/1")

BROKER_TRANSPORT_OPTIONS = {
    "fanout_prefix": True,
    "fanout_patterns": True
}

# Time
CELERY_TIMEZONE = "UTC"
CELERY_ENABLE_UTC = True
CELERY_TASK_RESULT_EXPIRES = 60 * 10  # 10 minutes

# Logging
CELERY_IGNORE_RESULT = True
CELERY_STORE_ERRORS_EVEN_IF_IGNORED = True

# Serialization
CELERY_TASK_SERIALIZER = "msgpack"
CELERY_RESULT_SERIALIZER = "msgpack"
CELERY_ACCEPT_CONTENT = ["json", "msgpack", "yaml"]

# Performance
CELERY_DISABLE_RATE_LIMITS = True

# Queue config
CELERY_DEFAULT_QUEUE = "default"
CELERY_QUEUES = (
    # Default queue
    Queue("default", Exchange("default"), routing_key="default"),

    # Misc worker queue
    Queue("worker", Exchange("worker"), routing_key="worker", delivery_mode=1),
)

# Beats config
CELERYBEAT_SCHEDULE = {
    "update_blacklist": {
        "task": "spidercommon.tasks.onions.update_blacklist",
        "schedule": datetime.timedelta(days=1),
    },
    "wipe_blacklisted": {
        "task": "spidercommon.tasks.onions.wipe_blacklisted",
        "schedule": datetime.timedelta(days=1, hours=6),
    },
    "alive_check": {
        "task": "spidercommon.tasks.onions.queue_alivecheck",
        "schedule": datetime.timedelta(hours=3),
    },
}
