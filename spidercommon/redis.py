import os

from redis import StrictRedis, ConnectionPool

redis_pool = ConnectionPool(
    host=os.environ.get("REDIS_HOST", "localhost"),
    port=os.environ.get("REDIS_PORT", 6379)
)


def create_redis() -> StrictRedis:
    return StrictRedis(
        connection_pool=redis_pool
    )
