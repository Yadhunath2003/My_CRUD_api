# My CRUD API

This project contains a FastAPI CRUD application in `my_crud_api.py`. It manages tasks in memory and runs on port `8000` by default.

## How `my_crud_api.py` Works

### Data models and storage

- `Task` represents a complete task with an integer `id`, a string `title`, and a boolean `done` value.
- `TaskCreate` validates the fields needed when creating a task.
- `TaskUpdate` allows `title` and `done` to be updated independently because both fields are optional.
- Four tasks are loaded when the application starts: Buy Milk, walk the dogs, Read a book, and Write a blog post.
- Tasks are stored in the in-memory `tasks` dictionary, so changes are lost when the application stops.
- New task IDs are generated using `_next_id`, which starts one higher than the largest existing ID.

### API description and health check

FastAPI automatically provides interactive documentation at `/docs` and an OpenAPI schema at `/openapi.json`.

The `GET /health` endpoint returns the current API status, task count, and all stored tasks.

### CRUD endpoints

- `GET /tasks` returns all tasks.
- `GET /tasks/{task_id}` returns one task or a `404` error when the ID does not exist.
- `POST /tasks` creates a task, assigns its ID, and returns `201 Created`.
- `PUT /tasks/{task_id}` updates the provided task fields and returns the updated task.
- `DELETE /tasks/{task_id}` removes a task and returns `204 No Content`.

When the application starts, its lifespan function generates the OpenAPI schema and saves it to `openapi.json`.

## Run the API

Install the dependencies if needed:

```bash
pip install fastapi uvicorn
```

Start the API:

```bash
uvicorn my_crud_api:app --reload --port 8000
```

The interactive documentation is available at `http://127.0.0.1:8000/docs`.

## Example requests

Create a task:

```bash
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Learn FastAPI\",\"done\":false}"
```

Update a task:

```bash
curl -X PUT http://127.0.0.1:8000/tasks/1 -H "Content-Type: application/json" -d "{\"done\":true}"
```

Delete a task:

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```