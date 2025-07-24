import os
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager

# Cargar variables de entorno
load_dotenv()

# --- Configuración de la Base de Datos ---
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@db:5432/{os.getenv('POSTGRES_DB')}"

# --- Función para obtener la conexión a la DB ---
# Esta función se encargará de crear y cerrar la conexión por cada petición.
# Es una práctica mucho más segura y robusta que tener una conexión global.


@contextmanager
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        yield conn
    finally:
        if conn:
            conn.close()


# --- Inicialización de la App FastAPI ---
app = FastAPI()

# --- Configuración de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Crear la tabla al iniciar (si no existe) ---


def setup_database():
    # Usamos un bucle de reintento para la configuración inicial
    retries = 5
    while retries > 0:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title TEXT NOT NULL,
                            status VARCHAR(50) DEFAULT 'pendiente',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    conn.commit()
                    print("Tabla 'tasks' verificada/creada exitosamente.")
                    return
        except psycopg2.OperationalError:
            retries -= 1
            print(
                f"No se pudo conectar a la base de datos para el setup... reintentando ({retries} intentos restantes)...")
            time.sleep(2)

# --- Modelos de Datos con Pydantic ---


class Task(BaseModel):
    id: int
    title: str
    status: str
    created_at: datetime


class CreateTask(BaseModel):
    title: str

# --- Evento de Inicio ---


@app.on_event("startup")
def on_startup():
    setup_database()

# --- Endpoints de la API ---


@app.get("/tasks", response_model=list[Task])
def get_tasks():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks ORDER BY id;")
            tasks = cur.fetchall()
    return tasks


@app.post("/tasks", response_model=Task, status_code=201)
def create_task(task: CreateTask):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tasks (title) VALUES (%s) RETURNING *;", (task.title,))
            new_task = cur.fetchone()
            if not new_task:
                raise HTTPException(
                    status_code=500, detail="No se pudo crear la tarea.")
            conn.commit()
    return new_task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task_status(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET status = 'completada' WHERE id = %s RETURNING *;", (task_id,))
            updated_task = cur.fetchone()
            if not updated_task:
                raise HTTPException(status_code=404, detail="Task not found")
            conn.commit()
    return updated_task


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail="Task not found")
            conn.commit()
    return
