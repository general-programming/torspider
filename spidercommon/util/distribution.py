# coding=utf-8
import json
import pickle
import random
import time
import uuid

from scrapy import Request
from scrapy.utils.reqser import request_to_dict


def lock_single(redis, lock_name: str, lock_expire: int=5) -> bool:
    """
        Half assed lock that ensures a single spider does a single task.
        Use this for things that are not special.
    """
    lock_key = f"lock:{lock_name}"

    # Wait 0.1 - 1 seconnds if the lock exists already.
    if redis.exists(lock_key):
        time.sleep(random.uniform(0.1, 1))
        return False

    # Set the lock if there is no lock.
    nonce = str(uuid.uuid4())
    key_result = redis.set(
        name=lock_key,
        ex=lock_expire,
        nx=True,
        value=nonce
    )

    # We're set if we got the key set.
    if key_result:
        return True

    # If it's not set, check again!
    if str(redis.get(lock_key)) == nonce:
        return True

    # We didn't get the lock. :(
    time.sleep(random.uniform(0.1, 1))
    return False


def queue_url(redis, priority: int=0, spider: str="tordirectory", *urls: str):
    queue_key = f"zqueue:{spider}"
    for url in urls:
        payload = pickle.dumps(request_to_dict(Request(
            url,
            dont_filter=True,
            priority=priority
        )))

        redis.execute_command('ZADD', queue_key, -priority, payload)
