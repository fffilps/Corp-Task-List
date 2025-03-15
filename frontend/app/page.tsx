"use client";

import { useState, useEffect } from "react";
import { fetchTasks, createTask, updateTask, deleteTask } from "@/services/api";
import useWebSocket from '@/hooks/useWebSocket'

interface Task {
  id: string;
  taskTitle: string;
  completed: boolean;
  created_at: string;
  updated_at: string;
}

interface WebSocketMessage {
  action: 'create' | 'update' | 'delete';
  task: Task;
}

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTask, setNewTask] = useState({ taskTitle: "", completed: false });
  const [editedTask, setEditedTask] = useState<Task | null>(null);

  // Add WebSocket connection
  useWebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://127.0.0.1:8000/ws', {
    onMessage: (data: string) => {
      try {
        console.log('Received WebSocket message:', data);
        const message = JSON.parse(data);
        // Ignore ping messages
        if (message.type === 'ping') {
          return;
        }
        
        // Handle task updates
        const taskMessage = message as WebSocketMessage;
        console.log('Processing task message:', taskMessage);
        if (taskMessage.action === 'create') {
          console.log('Adding new task:', taskMessage.task);
          setTasks(prevTasks => {
            // Check if task already exists to prevent duplicates
            const taskExists = prevTasks.some(task => task.id === taskMessage.task.id);
            console.log('Task exists?', taskExists);
            return taskExists ? prevTasks : [...prevTasks, taskMessage.task];
          });
        } else if (taskMessage.action === 'update') {
          setTasks(prevTasks => prevTasks.map(task => 
            task.id === taskMessage.task.id ? taskMessage.task : task
          ));
        } else if (taskMessage.action === 'delete') {
          setTasks(prevTasks => prevTasks.filter(task => task.id !== taskMessage.task.id));
        }
      } catch (err) {
        console.error('Error processing WebSocket message:', err);
      }
    },
    onError: (error: Error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error. Real-time updates may not work.');
    },
    onOpen: () => {
      console.log('WebSocket connected successfully');
      setError(null);
    },
    onClose: () => {
      console.log('WebSocket connection closed');
      setError('WebSocket connection closed. Real-time updates may not work.');
    }
  });

  useEffect(() => {
    const loadTasks = async () => {
      try {
        setLoading(true);
        const data = await fetchTasks();
        setTasks(data);
        setError(null);
      } catch (err) {
        setError("Failed to laod tasks. Please try again later.");
        console.log(err);
      } finally {
        setLoading(false);
      }
    };

    loadTasks();
  }, []);

  // Operations
  const handleCreateTask = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!newTask.taskTitle.trim()) {
      return;
    }

    try {
      setLoading(true);
      // changed how sending WebSocket will handle the state update
      const createdTask = await createTask(newTask);
      console.log('Task created successfully:', createdTask);
      // Immediately update the tasks list with the new task
      setTasks(prevTasks => [...prevTasks, createdTask]);
      setNewTask({ taskTitle: "", completed: false });
      setError(null);
    } catch (err) {
      setError("Failed to create task. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTask = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!editedTask || !editedTask.taskTitle.trim()) {
      return;
    }

    try {
      setLoading(true);
      const updatedTask = await updateTask(editedTask.id, {
        taskTitle: editedTask.taskTitle,
        completed: editedTask.completed,
      });

      setTasks(
        tasks.map((task) => (task.id === updatedTask.id ? updatedTask : task))
      );

      setEditedTask(null);
      setError(null);
    } catch (err) {
      setError("Failed to update task. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTask = async (id: string) => {
    try {
      setLoading(true);
      await deleteTask(id);
      setTasks(tasks.filter((task) => task.id !== id));
      setError(null);
    } catch (err) {
      setError("Failed to delete task. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleComplete = async (task: Task) => {
    try {
      setLoading(true);
      const updatedTask = await updateTask(task.id, {
        ...task,
        completed: !task.completed,
      });

      setTasks(tasks.map((t) => (t.id === updatedTask.id ? updatedTask : t)));

      setError(null);
    } catch (err) {
      setError("Failed to update task. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-purple-200 p-8 font-mono">
      {error && (
        <div className="mb-8 bg-red-200 border-4 border-red-900 p-4 font-bold text-red-900">
          {error}
        </div>
      )}

      {/* Task Form */}
      <form onSubmit={handleCreateTask} className="mb-12 bg-cyan-100 border-4 border-cyan-900 p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
        <h2 className="text-3xl font-bold mb-6 uppercase tracking-tight text-cyan-900">Add New Task</h2>
        <div className="mb-4">
          <label htmlFor="title" className="block text-lg mb-2 font-bold text-cyan-900">Title*:</label>
          <input
            type="text"
            id="title"
            value={newTask.taskTitle}
            onChange={(e) => setNewTask({ ...newTask, taskTitle: e.target.value })}
            placeholder="Enter task title"
            required
            className="w-full p-3 border-4 border-cyan-900 focus:outline-none focus:ring-4 focus:ring-pink-400 transition-all bg-white text-cyan-900"
          />
        </div>
        <div className="mb-6">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              id="completed"
              checked={newTask.completed}
              onChange={(e) => setNewTask({ ...newTask, completed: e.target.checked })}
              className="w-6 h-6 border-4 border-cyan-900 checked:bg-pink-500"
            />
            <span className="font-bold text-cyan-900">Completed</span>
          </label>
        </div>

        <button type="submit" className="w-full bg-cyan-900 text-white py-3 px-6 text-lg font-bold hover:bg-pink-500 hover:text-white transition-all border-4 border-cyan-900">
          Add Task
        </button>
      </form>

      {/* Edit Task Section */}
      {editedTask && (
        <form onSubmit={handleUpdateTask} className="mb-12 bg-orange-100 border-4 border-orange-900 p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
          <h2 className="text-3xl font-bold mb-6 uppercase tracking-tight text-orange-900">Edit Task</h2>
          <div className="mb-4">
            <label htmlFor="editTitle" className="block text-lg mb-2 font-bold text-orange-900">Title*:</label>
            <input
              type="text"
              id="editTitle"
              value={editedTask.taskTitle}
              onChange={(e) => setEditedTask({...editedTask, taskTitle: e.target.value})}
              placeholder="Enter task title"
              required
              className="w-full p-3 border-4 border-orange-900 focus:outline-none focus:ring-4 focus:ring-pink-400 transition-all bg-white text-cyan-900"
            />
          </div>

          <div className="mb-6">
            <label className="flex items-center space-x-3 cursor-pointer">
              <input
                type="checkbox"
                id="editCompleted"
                checked={editedTask.completed}
                onChange={(e) => setEditedTask({...editedTask, completed: e.target.checked})}
                className="w-6 h-6 border-4 border-orange-900 checked:bg-pink-500"
              />
              <span className="font-bold text-orange-900">Completed</span>
            </label>
          </div>

          <div className="flex space-x-4">
            <button type="submit" className="flex-1 bg-orange-900 text-white py-3 px-6 text-lg font-bold hover:bg-pink-500 hover:text-white transition-all border-4 border-orange-900">
              Update Task
            </button>
            <button
              type="button"
              onClick={() => setEditedTask(null)}
              className="flex-1 bg-white border-4 border-orange-900 py-3 px-6 text-lg font-bold hover:bg-red-500 hover:text-white hover:border-red-500 transition-all text-orange-900"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Task List */}
      {loading && !tasks.length ? (
        <div className="text-2xl font-bold text-center py-12 text-purple-900">Loading tasks...</div>
      ) : (
        <div>
          {!tasks.length ? (
            <div className="text-2xl font-bold text-center py-12 bg-purple-100 border-4 border-purple-900 text-purple-900 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
              No tasks yet. Add one above!
            </div>
          ) : (
            <ul className="space-y-4">
              {tasks.map((task) => (
                <li key={task.id} className={`bg-teal-100 border-4 ${task.completed ? 'border-pink-600' : 'border-teal-900'} p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <input
                        checked={task.completed}
                        onChange={() => handleToggleComplete(task)}
                        className="w-6 h-6 border-4 border-teal-900 checked:bg-pink-500"
                        type="checkbox"
                      />
                      <h3 className={`text-xl font-bold ${task.completed ? 'line-through text-teal-600' : 'text-teal-900'}`}>
                        {task.taskTitle}
                      </h3>
                    </div>
                    <div className="flex space-x-3">
                      <button
                        onClick={() => setEditedTask(task)}
                        className="px-4 py-2 bg-pink-500 border-2 border-teal-900 font-bold hover:bg-pink-600 transition-all text-white"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteTask(task.id)}
                        className="px-4 py-2 bg-white border-2 border-teal-900 font-bold hover:bg-red-500 hover:text-white hover:border-red-500 transition-all text-teal-900"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
