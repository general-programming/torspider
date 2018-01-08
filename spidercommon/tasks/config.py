# coding=utf-8
import os

from celery.schedules import crontab
from kombu import Exchange, Queue

# Debug
if "DEBUG" in os.environ:
    worker_redirect_stdouts_level = "DEBUG"

# Broker and Result backends
broker_url = os.environ.get("CELERY_BROKER", "redis://localhost/1")
result_backend = os.environ.get("CELERY_RESULT", "redis://localhost/1")

broker_transport_options = {
    "fanout_prefix": True,
    "fanout_patterns": True
}

# Time
timezone = "UTC"
enable_utc = True
result_expires = 60 * 10  # 10 minutes

# Logging
task_ignore_result = True
task_store_errors_even_if_ignored = True

# Serialization
task_serializer = "msgpack"
result_serializer = "msgpack"
accept_content = ["json", "msgpack", "yaml"]

# Performance
worker_disable_rate_limits = True

# Queue config
task_default_queue = "default"
task_queues = (
    # Default queue
    Queue("default", Exchange("default"), routing_key="default"),

    # Misc worker queue
    Queue("worker", Exchange("worker"), routing_key="worker", delivery_mode=1),
)

# Beats config
beat_schedule = {
    "update_blacklist": {
        "task": "spidercommon.tasks.onions.update_blacklist",
        "schedule": crontab(minute=0, hour=0),
    },
    "wipe_blacklisted": {
        "task": "spidercommon.tasks.onions.wipe_blacklisted",
        "schedule": crontab(minute=0, hour="*/6"),
    },
    "alive_check": {
        "task": "spidercommon.tasks.onions.queue_alivecheck",
        "schedule": crontab(minute=0, hour="*/3"),
    },
}
