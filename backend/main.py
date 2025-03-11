from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import List, Optional, Dict

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

# Helper Functions
def generate_task_id():
    return str(uuid.uuid4())

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}


# CRUD endpoints
# Craates Tasks
@app.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    task_id = generate_task_id()
    timestamp = datetime.now().isoformat()

    task_data = {
        **task.dict(),
        "id": task_id,
        "created_at": timestamp,
        "updated_at": timestamp
    }
    
    # Store to Memory
    tasks_db[task_id] = task_data
    return Task(**task_data)

# Get all Task as a List
@app.get("/tasks", response_model=List[Task])
async def get_tasks():
    # uses a list comprehension to get all tracks and converts each to Task object
    return [Task(**task) for task in tasks_db.values()]

# Get specific Task using ID
@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str, task: TaskCreate):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return Task(**tasks_db[task_id])

# Update Task using ID
@app.put("/tasks/{tasks_id}", response_model=Task)
async def update_task(task_id: str, task: TaskCreate):
    if task_id not in task_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Updates task data with passed in task, and updates the updated_at
    tasks_db[task_id].update(
        **task.dict(),
        updated_at=datetime.now().isoformat()
    )

    return Task(**tasks_db[task_id])

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    if task_id not in tasks_db:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Delete Task by ID
    del tasks_db[task_id]

    return {"message": "Task deleted successfully"}