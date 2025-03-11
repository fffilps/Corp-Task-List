"use client";

import { useState, useEffect } from "react";
import { fetchTasks, createTask, updateTask, deleteTask } from "@/services/api";

export default function Home() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newTask, setNewTask] = useState({ taskTitle: "", completed: false });
  const [editedTask, setEditedTask] = useState(null);

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
  const handleCreateTask = async (e) => {
    e.preventDefault();

    if (!newTask.taskTitle.trim()) {
      return;
    }

    try {
      setLoading(true);
      const createdTask = await createTask(newTask);
      setTasks([...tasks, createdTask]);
      setNewTask({ taskTitle: "", completed: false });
      setError(null);
    } catch (err) {
      setError("Failed to create task. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateTask = async (e) => {
    e.preventDefault();

    if (!editedTask || !editedTask.title.trim()) {
      return;
    }

    try {
      setLoading(true);
      const updatedTask = await updateTask(editedTask.id, {
        title: editedTask.title,
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

  const handleDeleteTask = async (id) => {
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

  const handleToggleComplete = async (task) => {
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
    <div>
      {error && <div>{error}</div>}

      {tasks && <div className="text-3xl">{tasks.map(task => <li key={task.id}>{task.taskTitle}</li>)}</div>}

      <form onSubmit={handleCreateTask}>
        <h2>Add New Task</h2>
        <div>
          <label htmlFor="title">Title*:</label>
          <input
            type="text"
            id="title"
            value={newTask.taskTitle}
            onChange={(e) => setNewTask({ ...newTask, taskTitle: e.target.value })}
            placeholder="Enter task title"
            required
          />
        </div>
        <div>
          <input
            type="checkbox"
            id="completed"
            checked={newTask.completed}
            onChange={(e) =>
              setNewTask({ ...newTask, completed: e.target.checked })
            }
          />
          <label htmlFor="completed">Completed</label>
        </div>

        <button type="submit">Add Task</button>
      </form>
    </div>
  );
}
