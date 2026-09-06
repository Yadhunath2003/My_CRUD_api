import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent
RESPONSES_PATH = BASE_DIR / "crub_by_ai_responses.json"
OPENAPI_PATH = BASE_DIR / "crub_by_ai_openapi.json"


class Task(BaseModel):
    id: int
    task_name: str
    completed: bool = False


class TaskCreate(BaseModel):
    task_name: str
    completed: bool = False


class TaskUpdate(BaseModel):
    task_name: str | None = None
    completed: bool | None = None


tasks: dict[int, Task] = {
    1: Task(id=1, task_name="Buy milk", completed=False),
    2: Task(id=2, task_name="Walk the dogs", completed=False),
    3: Task(id=3, task_name="Read a book", completed=False),
    4: Task(id=4, task_name="Write a blog post", completed=False),
}
next_id = max(tasks) + 1


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def read_response_log() -> list[dict]:
    if not RESPONSES_PATH.exists():
        return []
    try:
        return json.loads(RESPONSES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def save_response_log(entry: dict) -> None:
    responses = read_response_log()
    responses.append(entry)
    write_json(RESPONSES_PATH, responses)


@asynccontextmanager
async def lifespan(_: FastAPI):
    write_json(OPENAPI_PATH, app.openapi())
    if not RESPONSES_PATH.exists():
        write_json(RESPONSES_PATH, [])
    yield


app = FastAPI(
    title="CRUD Tasks API",
    version="1.0.0",
    description="A simple in-memory CRUD API for managing tasks.",
    lifespan=lifespan,
)


@app.middleware("http")
async def store_api_response(request: Request, call_next):
    response = await call_next(request)
    body = b"".join([chunk async for chunk in response.body_iterator])
    try:
        response_body = json.loads(body) if body else None
    except json.JSONDecodeError:
        response_body = body.decode("utf-8", errors="replace")

    save_response_log(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "response": response_body,
        }
    )
    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.get("/", summary="Describe the API")
async def describe_api():
    return {
        "name": "CRUD Tasks API",
        "description": "An in-memory API for creating, reading, updating, and deleting tasks.",
        "endpoints": {
            "GET /health": "Check API health and task count",
            "GET /tasks": "List all tasks",
            "GET /tasks/{task_id}": "Get one task",
            "POST /tasks": "Create a task",
            "PUT /tasks/{task_id}": "Update a task",
            "DELETE /tasks/{task_id}": "Delete a task",
        },
    }


@app.get("/health", summary="Check API health")
async def check_health():
    return {"status": "ok", "tasks_count": len(tasks)}


@app.get("/tasks", response_model=list[Task], summary="List all tasks")
async def list_tasks():
    return list(tasks.values())


@app.get("/tasks/{task_id}", response_model=Task, summary="Get a task")
async def get_task(task_id: int):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED, summary="Create a task")
async def create_task(task_create: TaskCreate):
    global next_id
    task = Task(id=next_id, **task_create.model_dump())
    tasks[task.id] = task
    next_id += 1
    return task


@app.put("/tasks/{task_id}", response_model=Task, summary="Update a task")
async def update_task(task_id: int, task_update: TaskUpdate):
    task = tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    updated_task = task.model_copy(update=task_update.model_dump(exclude_unset=True))
    tasks[task_id] = updated_task
    return updated_task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a task")
async def delete_task(task_id: int):
    if task_id not in tasks:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    del tasks[task_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("crub_by_ai:app", host="127.0.0.1", port=8001, reload=True)