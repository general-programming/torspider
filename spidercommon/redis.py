import os

from redis import ConnectionPool, StrictRedis

redis_pool = ConnectionPool(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=os.environ.get("REDIS_PORT", 6379)
)


def create_redis() -> StrictRedis:
    return StrictRedis(
        connection_pool=redis_pool
    )
