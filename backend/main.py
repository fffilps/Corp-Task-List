from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import List, Optional, Dict
import redis
import json
import asyncio

# Declaring Data Models
class TaskBase(BaseModel):
    taskTitle: str
    completed: bool = False

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str
    created_at: str
    updated_at: str

# WebSocket Init and connection
class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.pubsub = None
        self.redis_client = None
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnet(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                # Connection might be closed or in error state
                pass
    
    async def start_redis_listener(self):
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            decode_responses=True
        )

        # Initialize PubSub
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(TASK_CHANNEL)

        # Start listening for messages in a background task
        asyncio.create_task(self.listen_for_messages())

    async def listen_for_messages(self):
        # This needs to run in a seperate thread because Redis PubSub is blocking
        for message in self.pubsub.listen():
            if message["type"] == "message":
                data = message["data"]
                await self.braodcast(data)

# Create an instance
manager = ConnectionManager()

# Init App
app = FastAPI(title="Real-Time Task List API")


# CORS middleware to control access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory until Redis
tasks_db = {}

# Redis Configuration
REDIS_HOST = "redis" # Docker service name
REDIS_PORT = 6379
REDIS_DB = 0
TASK_KEY_PREFIX = "task:"
TASK_LIST_KEY = "task"
TASK_CHANNEL = "task_updates" # Channel for Pub/Sub

# Redis Dependecy init
def get_redis(): 
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True # Need in order to work with strings and not bytes
    )
    try:
        yield redis_client
    finally:
        redis_client.close()

# Helper Functions
def generate_task_id():
    return str(uuid.uuid4())

# backend test
@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}


# CRUD endpoints
# Craates Tasks
@app.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate, redis_client: redis.Redis = Depends(get_redis)):
    task_id = generate_task_id()
    timestamp = datetime.now().isoformat()

    task_data = {
        **task.dict(),
        "id": task_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # # Store to Memory
    # tasks_db[task_id] = task_data

    # Store in Redis
    task_key = f"{TASK_KEY_PREFIX}{task_id}"
    redis_client.hset(task_key, mapping=task_data)

    # Adding to library set of tasks
    redis_client.sadd(TASK_LIST_KEY, task_id)

    # Publish event for real-time updates
    redis_client.publish(
        TASK_CHANNEL,
        json.dumps({"action": "create", "task": task_data})
    )

    return Task(**task_data)

# Get all Task as a List
@app.get("/tasks", response_model=List[Task])
async def get_tasks(redis_client: redis.Redis = Depends(get_redis)):

    # get all task IDs
    task_ids = redis_client.smembers(TASK_LIST_KEY)
    tasks = []

    for task_id in task_ids:
        task_key= f"{TASK_KEY_PREFIX}{task_id}"
        task_data = redis.client.hgetall(task_key)
        if task_data:
            tasks.append(Task(**task_data))

    return tasks

    # # uses a list comprehension to get all tracks and converts each to Task object
    # return [Task(**task) for task in tasks_db.values()]

# Get specific Task using ID
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, task: TaskCreate):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return Task(**tasks_db[task_id])

# Update Task using ID
@app.put("/tasks/{tasks_id}", response_model=Task)
async def update_task(task_id: str, task: TaskCreate, redis_client: redis.Redis = Depends(get_redis)):
    task_key = f"{TASK_KEY_PREFIX}{task_id}"

    # Check if task exists
    if not redis_client.exists(task_key):
        raise HTTPException(status_code=404, detail="Task not found")

    # Get existing task data
    existing_task = redis_client.hgetall(task_key)
    
    # Updates task data with passed in task, and updates the updated_at
    updated_task = {
        **existing_task, 
        **task.dict(),
        "updated_at": datetime.now().isoformat()
    }

    # Stores updated task
    redis_client.hset(task_key, mapping=updated_task)

    # Publishes event for real-time updates
    redis_client.publish(
        TASK_CHANNEL,
        json.dumps({"action": "update", "task": updated_task})
    )

    return Task(**updated_task)

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, redis_client: redis.Redis = Depends(get_redis)):
    task_key = f"{TASK_KEY_PREFIX}{task_id}"

    # Check if task exist
    if not redis_client.exists(task_key):
        raise HTTPException(status_code=404, detail="Task not found")

    # Gets task data before deleting
    task_data = redis_client.hgetall(task_key)

    redis_client.delete(task_key)
    redis_client.srem(TASK_LIST_KEY, task_id)

    # Publish event for real-time updates
    redis_client.publish(
        TASK_CHANNEL,
        json.dumps({ "action": "delete", "task": task_data})
    )
    
    # Delete Task by ID
    del tasks_db[task_id]

    return {"message": "Task deleted successfully"}