import redis
from typing import Generator

# Redis Configuration
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
TASK_KEY_PREFIX = "task:"
TASK_LIST_KEY = "tasks"
TASK_CHANNEL = "task_updates"

def get_redis() -> Generator[redis.Redis, None, None]:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True
    )
    try:
        yield redis_client
    finally:
        redis_client.close() 