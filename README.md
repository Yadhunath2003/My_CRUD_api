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

Moreover, I had also propmted Github Copilot to Create a own CRUD api different from mine and it also does the work prefectly. Here is the Prompt that I used.

```
Please create a simple crud app using fastapi where you create 4 hardcoded tasks that contains and id (int), the task_name (str), and whether the task has been completed or not (bool). From these 4 tasks, you should be ablw to do the following tasks.

1. Return a json string describing the api, and Check the Health of the api along with its status.
2. able to list all the tasks, and a specific task.
3. Create a new task.
4. Update and Delete a task.
5. And finally store all the api responses to .json file.

Please make sure to isolate this api from the existing my_crud_api.py file (by creating a new file named crub_by_ai.py) and also import the responses to a different .json file. Finally, also create a README file containing all the information on what this API does.
```