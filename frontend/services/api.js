const API_BASE_URL = 'http://localhost:8000'

// Fetch all tasks
export const fetchTasks = async () => {
    const response = await fetch(`${API_BASE_URL}/tasks`)

    if (!response.ok) {
        throw new Error(`Failed to fetch tasks: ${response.status}`)
    }

    return response.json()
}

// Create a new task
export const createTask = async (taskData) => {
    const response = await fetch(`${API_BASE_URL}/tasks`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData),
        message: "Posting a task",
        type: "text"
    })

    if (!response.ok) {
        throw new Error(`Failed to create task: $(response.status)`)
    }

    return response.json()
}

// Update a task
export const updateTask = async (taskId, taskData) => {
    const response = await fetch(`${API_BASE_URL}/tasks/${taskId}`, {
        method: "PUT",
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(taskData)
    })

    if (!response.ok) {
        throw new Error(`Failed to update task: $(response.status)`)
    }

    return response.json()

}

// Delete a task
export const deleteTask = async () => {
    const response = await fetch(`${API_BASE_URL}/tasks/${tasksId}`, {
        method: 'DELETE'
    })

    if (!response.ok) {
        throw new Error(`Failed to delete tasks: ${response.status}`)
    }

    return response.json()
}