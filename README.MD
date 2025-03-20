# Task Management Application

A real-time task management application built with Next.js, FastAPI, Redis, and WebSocket for live updates. This application allows users to manage tasks with real-time synchronization across multiple clients.

## 🚀 Tech Stack

### Backend: FastAPI (Python)
### Frontend: Next.js (React)
### Database/Message Broker: Redis
### Containerization: Docker & Docker Compose

## Architecture

### Frontend
- **Next.js** - React framework for production-grade applications
- **TypeScript** - For type-safe code
- **WebSocket** - For real-time updates
- **Tailwind CSS** - For styling

### Backend
- **FastAPI** - Modern, fast web framework for building APIs with Python, used for CRUD operations on tasks
- **Redis** - For pub/sub messaging functionality and data persistence/caching
- **WebSocket** - For real-time communication and tasks updates
- **uvicorn** - ASGI server implementation

### Project Flow
1. User interacts with the Next.js frontend to create/update/delete a task
2. Frontend sends a REST request to the FastAPI backend
3. Backend processes the request and updates Redis
4. Backend publishes an update message to the Redis Pub/Sub channel
5. All connected clients receive the update via WebSocket connections
6. Frontend updates the UI in real-time without requiring a page refresh

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:
- Docker Desktop
- Node.js (for local development)
- Python 3.8+ (for local development)

## 🚀 Getting Started

### Using Docker (Recommended)

1. Clone the repository
``` git clone https://github.com/yourusername/realtime-todo-redis.git ```
2. Navigate to the project root directory
``` cd realtime-todo-redis ```
3. Run the following command:
   ```bash
   docker compose up --build
   ```
   This will start both the frontend and backend services.

### Local Development

#### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Redis Setup (Docker)
1. 
   ``` docker run --name redis -p 6379:6379 -d redis ```

#### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the development server:
   ```bash
   npm run dev
   ```

## 🏗️ Project Structure

### Frontend (/frontend)
- `app/` - Next.js pages and routing
- `components/` - Reusable React components
- `hooks/` - Custom React hooks
- `services/` - API and WebSocket services
- `public/` - Static assets

### Backend (/backend)
- `main.py` - Main FastAPI application
- `requirements.txt` - Python dependencies

## 🔧 Architecture

### WebSocket Implementation
The application uses WebSocket connections for real-time updates. When changes are made to tasks:
1. The backend publishes updates to Redis
2. Redis pub/sub system broadcasts the changes
3. Connected clients receive updates through WebSocket
4. Frontend automatically updates to reflect changes

### Redis Usage
Redis is utilized for:
- Pub/Sub functionality for real-time updates - task_updates (CRUD)
- Data persistence / In-Memory Database - JSON with ID keys
- Scalability across multiple instances
- High-performance data operations

## 🔐 Environment Variables

### Frontend (.env)
```
NEXT_PUBLIC_API_URL=your_api_url
NEXT_PUBLIC_WS_URL=your_websocket_url
```

## API Endpoints

### Task Management
- GET ("/tasks") - Retrieve all tasks
- POST ("/tasks") - Create a new task
- PUT ("/tasks/{id}") - Update an existing task
- DELETE ("/tasks/{id}") - Delete a task

### WebSocket
- GET ("/ws") - WebSocket endpoint for real-time updates

## Future Enhancements

- Task Expiry
- Rate Limiting
- Real-Time Analytics
- User Authentication
- Task Catergories
- Task priorites and sorting
- Offine support with local storage

## 🤝 Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.