import os

from redis import StrictRedis


def create_redis(decode_responses=False) -> StrictRedis:
    return StrictRedis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=os.environ.get("REDIS_PORT", 6379),
        decode_responses=decode_responses
    )
