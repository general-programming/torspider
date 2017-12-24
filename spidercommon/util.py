import random
import time
import uuid
import hashlib

def md5(content: str):
    return hashlib.md5(content.encode("utf8")).hexdigest()

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