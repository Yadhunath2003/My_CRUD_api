import json
import sqlite3 as sqlite
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

OPENAPI_PATH = "openapi.json"
DATABASE_PATH = Path(__file__).parent / "tasks.db"

class Task(BaseModel):
    id: int
    title: str
    done: bool = False

class TaskCreate(BaseModel):
    title: str
    done: bool = False

class TaskUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None

# # In-memory storage for tasks
# tasks: dict[int, Task] = {
#     1: Task(id=1, title="Buy Milk", done=False),
#     2: Task(id=2, title="walk the dogs", done=False),
#     3: Task(id=3, title="Read a book", done=False),
#     4: Task(id=4, title="Write a blog post", done=False),
# }
# _next_id = max(tasks.keys()) + 1 if tasks else 1

#Instead of using in-memory storage, we will use SQLite for persistent storage.
def get_connection() -> sqlite.Connection:
    conn = sqlite.connect(DATABASE_PATH)
    conn.row_factory = sqlite.Row
    return conn

'''
Initiating the Database:
- Creating the Table for all the fields on the Task model.
- If the Data is already present, it will not insert the data again. 
- If the table is empty, it will insert some initial data.
'''
def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done BOOLEAN NOT NULL DEFAULT 0
            )
            """
        )
        (count,) = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()
        if count == 0:
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)",
                [
                    ("Buy Milk", False),
                    ("Walk the dogs", False),
                    ("Read a book", False),
                    ("Write a blog post", False),
                ],
            )
        conn.commit()

# Helper function to convert a database row to a Task object
def row_task(row: sqlite.Row) -> Task:
    return Task(id=row["id"], title=row["title"], done=bool(row["done"]))

'''
This is the function to select all the tasks from the database 
and return them as a list of Task objects.
'''
def db_list_tasks() -> list[Task]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT id, title, done FROM tasks").fetchall()
        return [row_task(row) for row in rows]
    finally:
        conn.close()

'''This Function would select a task by its ID from the database and
 return it as a Task object.'''
def db_get_task(task_id: int) -> Task | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        return row_task(row)
    finally:
        conn.close()

'''This function would insert a new task into the database and 
return it as a Task object.'''
def db_create_task(task_create: TaskCreate) -> Task:
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (task_create.title, task_create.done),
        )
        task_id = cursor.lastrowid
        conn.commit()
        return Task(id=task_id, title=task_create.title, done=task_create.done)
    finally:
        conn.close()

'''
This function would update an existing task in the database and
return it as a Task object.
'''
def db_update_task(task_id: int, task_update: TaskUpdate) -> Task | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            return None
        new_title = task_update.title if task_update.title is not None else row["title"]
        new_done = task_update.done if task_update.done is not None else bool(row["done"])
        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        conn.commit()
        return Task(id=task_id, title=new_title, done=new_done)
    finally:
        conn.close()

'''This function would delete a task from the database and 
return a boolean indicating success.'''
def db_delete_task(task_id: int) -> bool:
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

########################################3

def openapi_schema(path: str = OPENAPI_PATH) -> None:
    try:
        schema = app.openapi()
        with open(path, "w") as f:
            json.dump(schema, f)
    except FileNotFoundError:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db() #Initialize the database when the application starts
    openapi_schema()
    yield

app = FastAPI(title="My CRUD API", version="1.0.0", lifespan=lifespan)

#-----------------------------------------------

'''These are the same functions from the initial CRUD API implementation, 
but now they interact with the SQLite database instead of in-memory storage.'''
# Check the health of the API
@app.get("/health")
async def check_health():
    current_tasks = db_list_tasks()
    return {"status": "ok",
            "tasks_count": len(current_tasks),
            "tasks": current_tasks,
            }

@app.get("/tasks", response_model=list[Task])
async def list_tasks():
    return db_list_tasks()

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = db_get_task(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_create: TaskCreate):
    return db_create_task(task_create)

@app.put("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(task_id: int, task_update: TaskUpdate):
    updated_task = db_update_task(task_id, task_update)
    if updated_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return updated_task
    

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    deleted = db_delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)