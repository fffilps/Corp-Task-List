from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import datetime, timedelta
import redis
import json
from redis_config import get_redis, TASK_KEY_PREFIX, TASK_CHANNEL

router = APIRouter()

# REDIS CONFIG
REDIS_HOST = "redis"
REDIS_PORT = 6379
REDIS_DB = 0
TASK_LIST_KEY = "tasks"

# Set task expiry
@router.post("/tasks/{task_id}/expiry")
async def set_task_expiry(
    task_id: str,
    expiry_hours: int = Query(..., ge=1, le=168), # between 1 hour and 7 days
    redis_client: redis.Redis = Depends(get_redis)
):
    task_key = f"{TASK_KEY_PREFIX}{task_id}"

    # Check if task exists
    if not redis_client.exists(task_key):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Expiry to seconds
    expiry_seconds = expiry_hours * 3600

    # Setting Expiry time
    redis_client.expire(task_key, expiry_seconds)

    # Updating tsak with expiry settings
    expiry_time = datetime.now() + timedelta(hours=expiry_hours)
    redis_client.hset(task_key, "expires_at", expiry_time.isoformat())

    # GET all of the task
    task_data = redis_client.hgetall(task_key)

    # Publish task update
    redis_client.publish(
        TASK_CHANNEL,
        json.dumps({"action": "update", "task": task_data})
    )

    return {"message": f"Task will expire in {expiry_hours} hours"}