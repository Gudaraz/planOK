import { useState, useEffect } from 'react';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  const [tasks, setTasks] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [error, setError] = useState(null);

  // Cargar las tareas iniciales desde la API cuando el componente se monta
  useEffect(() => {
    setError(null);
    fetch(`${API_URL}/tasks`)
      .then(res => {
        if (!res.ok) throw new Error("Error del servidor al cargar tareas.");
        return res.json();
      })
      .then(data => setTasks(data))
      .catch(err => {
        console.error("Error al cargar tareas:", err);
        setError("No se pudieron cargar las tareas. ¿Está el backend funcionando?");
      });
  }, []);

  // Manejar el envío del formulario para crear una nueva tarea
  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    setError(null);

    fetch(`${API_URL}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: inputValue }),
    })
    .then(async res => {
      if (!res.ok) {
        // Si hay un error, intenta leer el detalle del error del backend
        const errorData = await res.json().catch(() => ({ detail: "Error desconocido" }));
        throw new Error(errorData.detail || "Error del servidor al crear tarea.");
      }
      // Solo intenta parsear JSON si la respuesta es exitosa
      return res.json();
    })
    .then(newTask => {
      setTasks([...tasks, newTask]);
      setInputValue('');
    })
    .catch(err => {
      console.error("Error al crear tarea:", err);
      setError(err.message);
    });
  };

  // Manejar la actualización del estado de una tarea
  const handleUpdateStatus = (taskId) => {
    setError(null);
    fetch(`${API_URL}/tasks/${taskId}`, { method: 'PUT' })
      .then(res => {
        if (!res.ok) throw new Error("Error al actualizar tarea.");
        return res.json();
      })
      .then(updatedTask => {
        setTasks(tasks.map(task => 
          task.id === taskId ? updatedTask : task
        ));
      })
      .catch(err => {
        console.error("Error al actualizar tarea:", err);
        setError(err.message);
      });
  };

  // Manejar la eliminación de una tarea
  const handleDelete = (taskId) => {
    setError(null);
    fetch(`${API_URL}/tasks/${taskId}`, { method: 'DELETE' })
      .then(res => {
        if (res.ok) {
          setTasks(tasks.filter(task => task.id !== taskId));
        } else {
          throw new Error("Error al eliminar tarea.");
        }
      })
      .catch(err => {
        console.error("Error al eliminar tarea:", err);
        setError(err.message);
      });
  };

  return (
    <div className="container">
      <h1>Gestor de Tareas</h1>
      <p>Una aplicación simple con React, FastAPI y Docker.</p>
      <form onSubmit={handleSubmit} className="task-form">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="¿Qué necesitas hacer?"
          className="task-input"
        />
        <button type="submit" className="task-button">Agregar</button>
      </form>
      {error && <p className="error-message">{error}</p>}
      <ul className="task-list">
        {tasks.map(task => (
          <li key={task.id} className={`task-item ${task.status === 'completada' ? 'completed' : ''}`}>
            <div className="task-content">
              <span className="task-title">{task.title}</span>
              <span className="task-date">
                {new Date(task.created_at).toLocaleString()}
              </span>
            </div>
            <div className="task-actions">
              {task.status === 'pendiente' && (
                <button onClick={() => handleUpdateStatus(task.id)} className="action-button complete">Completar</button>
              )}
              <button onClick={() => handleDelete(task.id)} className="action-button delete">Eliminar</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
