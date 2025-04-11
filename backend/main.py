from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import List, Optional, Dict
import redis
import json
import asyncio
from task_expiry import router as expiry_router
from redis_config import get_redis, TASK_KEY_PREFIX, TASK_LIST_KEY, TASK_CHANNEL

# Declaring Data Models
class TaskBase(BaseModel):
    taskTitle: str
    completed: bool = False
    expires_at: Optional[str] = None

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
        print(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            print("No active connections to broadcast to")
            return
            
        print(f"Broadcasting message to {len(self.active_connections)} connections: {message}")
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting message: {str(e)}")
                # Connection might be closed or in error state
                pass
    
    async def start_redis_listener(self):
        print("Starting Redis listener")
        # Connect to Redis
        self.redis_client = redis.Redis(
            host="redis",
            port=6379,
            db=0,
            decode_responses=True
        )

        # Initialize PubSub
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe(TASK_CHANNEL)
        print(f"Subscribed to Redis channel: {TASK_CHANNEL}")

        # Start listening for messages in a background task
        asyncio.create_task(self.listen_for_messages())

    async def listen_for_messages(self):
        print("Started listening for Redis messages")
        try:
            while True:
                message = await asyncio.to_thread(self.pubsub.get_message)
                if message and message["type"] == "message":
                    data = message["data"]
                    print(f"Received Redis message: {data}")
                    await self.broadcast(data)
                await asyncio.sleep(0.1)  # Prevent CPU hogging
        except Exception as e:
            print(f"Error in Redis listener: {str(e)}")

# Create an instance
manager = ConnectionManager()

# Init App
app = FastAPI(title="Real-Time Task List API")

# Include the expiry router
app.include_router(expiry_router)

# CORS middleware to control access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# # In-memory until Redis
# tasks_db = {}

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("New WebSocket connection request")
    await manager.connect(websocket)
    try:
        # Start Redis listener if not already started
        if manager.pubsub is None:
            await manager.start_redis_listener()
        
        # Keep the connection alive with periodic pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                print(f"Received WebSocket message: {data}")
            except asyncio.TimeoutError:
                try:
                    # Send a ping to keep the connection alive
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
            except Exception:
                break
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        manager.disconnect(websocket)

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

    # Convert the task dict and ensure boolean is converted to string
    task_dict = task.dict()
    task_dict['completed'] = str(task_dict['completed']).lower()
    
    # Handle expires_at field - convert None to empty string for Redis
    if task_dict.get('expires_at') is None:
        task_dict['expires_at'] = ''
    
    task_data = {
        **task_dict,
        "id": task_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    try:
        # Store in Redis
        task_key = f"{TASK_KEY_PREFIX}{task_id}"
        redis_client.hset(task_key, mapping=task_data)

        # Adding to library set of tasks
        redis_client.sadd(TASK_LIST_KEY, task_id)

        # Convert back to boolean for the response and WebSocket
        task_data['completed'] = task_data['completed'] == 'true'
        # Convert empty string back to None for the response
        if task_data['expires_at'] == '':
            task_data['expires_at'] = None

        # Create the message once
        message = json.dumps({"action": "create", "task": task_data})

        # Publish to Redis for other server instances
        redis_client.publish(TASK_CHANNEL, message)

        # Directly broadcast to WebSocket connections
        print("Broadcasting new task to all connections")
        await manager.broadcast(message)

        return Task(**task_data)
    except Exception as e:
        print(f"Error creating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create task")

# Get all Task as a List
@app.get("/tasks", response_model=List[Task])
async def get_tasks(redis_client: redis.Redis = Depends(get_redis)):
    # get all task IDs
    task_ids = redis_client.smembers(TASK_LIST_KEY)
    tasks = []

    for task_id in task_ids:
        task_key = f"{TASK_KEY_PREFIX}{task_id}"
        task_data = redis_client.hgetall(task_key)
        if task_data:
            # Convert completed back to boolean
            task_data['completed'] = task_data['completed'] == 'true'
            # Convert empty string to None for expires_at
            if task_data.get('expires_at') == '':
                task_data['expires_at'] = None
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
@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task: TaskCreate, redis_client: redis.Redis = Depends(get_redis)):
    task_key = f"{TASK_KEY_PREFIX}{task_id}"

    # Check if task exists
    if not redis_client.exists(task_key):
        raise HTTPException(status_code=404, detail="Task not found")

    # Get existing task data
    existing_task = redis_client.hgetall(task_key)
    
    # Convert task to dict and handle boolean
    task_dict = task.dict()
    task_dict['completed'] = str(task_dict['completed']).lower()
    
    # Handle expires_at field - convert None to empty string for Redis
    if task_dict.get('expires_at') is None:
        task_dict['expires_at'] = ''
    
    # Updates task data with passed in task, and updates the updated_at
    updated_task = {
        **existing_task, 
        **task_dict,
        "id": task_id,
        "created_at": existing_task.get("created_at", datetime.now().isoformat()),
        "updated_at": datetime.now().isoformat()
    }

    try:
        # Stores updated task
        redis_client.hset(task_key, mapping=updated_task)

        # Convert completed back to boolean for response and websocket
        updated_task['completed'] = updated_task['completed'] == 'true'
        # Convert empty string back to None for the response
        if updated_task['expires_at'] == '':
            updated_task['expires_at'] = None

        # Create the message once
        message = json.dumps({"action": "update", "task": updated_task})

        # Publish to Redis for other server instances
        redis_client.publish(TASK_CHANNEL, message)

        # Directly broadcast to WebSocket connections
        await manager.broadcast(message)

        return Task(**updated_task)
    except Exception as e:
        print(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update task")

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

    # Create the message once
    message = json.dumps({"action": "delete", "task": {"id": task_id}})

    # Publish to Redis for other server instances
    redis_client.publish(TASK_CHANNEL, message)

    # Directly broadcast to WebSocket connections
    await manager.broadcast(message)

    return {"message": "Task deleted successfully"}
# except Exception as e:
#     print(f"Error deleting task: {str(e)}")
#     raise HTTPException(status_code=500, detail="Failed to delete task")

