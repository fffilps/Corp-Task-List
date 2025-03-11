from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Init App
app = FastAPI(title="Real-Time Task List API")

# CORS middleware to control access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/hello")
def hello():
    return {"message": "Hello from FastAPI"}