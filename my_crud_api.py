import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel

OPENAPI_PATH = "openapi.json"

def openapi_schema(path: str = OPENAPI_PATH) -> None:
    try:
        schema = app.openapi()
        with open(path, "w") as f:
            json.dump(schema, f)
    except FileNotFoundError:
        return None

@asynccontextmanager
async def lifespan(app: FastAPI):
    openapi_schema()
    yield

app = FastAPI(title="My CRUD API", version="1.0.0", lifespan=lifespan)

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

# In-memory storage for tasks
tasks: dict[int, Task] = {
    1: Task(id=1, title="Buy Milk", done=False),
    2: Task(id=2, title="walk the dogs", done=False),
    3: Task(id=3, title="Read a book", done=False),
    4: Task(id=4, title="Write a blog post", done=False),
}
_next_id = max(tasks.keys()) + 1 if tasks else 1

# Check the health of the API
@app.get("/health")
async def check_health():
    return {"status": "ok",
            "tasks_count": len(tasks),
            "tasks": list(tasks.values()),
            }

@app.get("/tasks", response_model=list[Task])
async def list_tasks():
    return list(tasks.values())

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_create: TaskCreate):
    global _next_id
    task = Task(id=_next_id, title=task_create.title, done=task_create.done)
    tasks[task.id] = task
    _next_id += 1
    return task

@app.put("/tasks/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
def update_task(task_id: int, task_update: TaskUpdate):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    updated_task = task.model_copy(update=task_update.model_dump(exclude_unset=True))
    tasks[task_id] = updated_task
    return updated_task

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del tasks[task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)