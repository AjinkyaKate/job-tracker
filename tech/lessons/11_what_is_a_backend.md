# Lesson 11 — What is a backend? (FastAPI + request-response)

> Triggered by: Ship 6 Phase A (first web page). Time to read: ~10 min.

## In one sentence

A **backend** is a long-running program that **listens on a port**, waits for HTTP requests from browsers (or other clients), runs some code to figure out a response, and sends it back.

## A real-world analogy — the restaurant kitchen

A restaurant has a front (menu, tables, waiters) and a back (kitchen, pantry, chef). The **front-of-house** is what customers see — menus, plates, the waiter taking orders. The **back-of-house** is invisible to customers — the kitchen turns the order into a meal, the pantry holds ingredients.

The web has the same shape:

| Restaurant | Web app |
|---|---|
| Customers + tables | Users + browsers |
| Menu, plates | HTML, CSS, JS (frontend) |
| Waiter | HTTP — carries orders one way, food the other |
| Kitchen + chef | Backend (Python, FastAPI) |
| Pantry | Database (SQLite, Postgres) |

When a user clicks "Submit" or opens a page, the browser sends a request through the network (the waiter walks to the kitchen). Your backend receives it, does work (chef cooks), and sends a response back (waiter brings food to the table). That round-trip is the **request-response cycle**.

## Where this shows up in our project

Ship 6 introduces `webapp.py` — a FastAPI program that:

- Starts up and keeps running (a server process)
- Listens on `localhost:8000`
- Has **routes** like `GET /` (homepage), `GET /jobs/{id}` (one job), `POST /jobs` (add a job)
- For each route, runs a Python function that reads from `tracker.db` and returns HTML to the browser
- Uses Jinja2 templates to build the HTML from data + a template file (separation of data and presentation)

You open `http://localhost:8000` in Cursor's preview or a real browser → that's a `GET /` request → FastAPI runs the homepage function → returns rendered HTML → browser displays.

## The minimum you need to know

### 1. What a "server" is

Not a special machine. A **server is just a long-running program** that keeps a TCP port open, accepts incoming connections, and reads/writes bytes over those connections. Your laptop running `uvicorn webapp:app` *is* a server. The same code on Railway is also a server — just running on someone else's machine with a public address.

A process can be a server (`uvicorn`) or a client (`curl`, your browser). It's a role, not a hardware thing.

### 2. HTTP — the language of the web, in one paragraph

HTTP is a text-based protocol. The client sends:

```
GET /jobs/1 HTTP/1.1
Host: localhost:8000
```

The server responds:

```
HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: 1234

<html>...the actual page...</html>
```

That's the whole protocol, simplified. You'll mostly care about:

- **Method**: `GET` (read), `POST` (create), `PATCH` (update), `DELETE` (remove)
- **Path**: `/jobs/1`, `/extract`, `/` — what resource is being asked for
- **Status code**: `200 OK`, `404 Not Found`, `500 Internal Server Error`, `302 Found` (redirect)
- **Body**: optional payload (form data, JSON, HTML)

### 3. FastAPI in one diagram

```
   Browser                           FastAPI app
   ┌───────┐    GET /jobs/1         ┌─────────────────────────┐
   │       │ ─────────────────────► │  @app.get("/jobs/{id}") │
   │       │                        │  def show(id: int):     │
   │       │                        │      job = db.query(id) │
   │       │                        │      return HTML(...)   │
   │       │ ◄───────────────────── │                         │
   └───────┘    HTML response       └─────────────────────────┘
```

The `@app.get("/jobs/{id}")` line is a **decorator** — it tells FastAPI "this function handles GET requests at this path." The `{id}` is a path parameter; FastAPI parses it and passes it to your function as `id`.

### 4. Routes you'll see in our Ship 6 webapp

| Method | Path | What it does |
|---|---|---|
| `GET` | `/` | Homepage: today view + all jobs |
| `GET` | `/jobs/{id}` | Detail page for one job (later phase) |
| `POST` | `/jobs` | Create a new job (later phase) |
| `POST` | `/jobs/{id}/status` | Change a job's status (later phase) |

For Phase A we only build the homepage. Each subsequent phase adds routes.

### 5. Templates — separating data from HTML

Hardcoding HTML into Python strings gets ugly fast. **Jinja2** is a template engine: you write HTML files with placeholders like `{{ job.title }}` and `{% for job in jobs %}...{% endfor %}`, then your Python code says *"render `index.html` with `jobs=[...]`"* and Jinja2 fills in the blanks.

Layout:
```
job-tracker/
├── webapp.py              # Python code (logic, DB calls)
└── templates/
    └── index.html         # HTML (presentation)
```

Same separation as the kitchen / dining-room. The chef (Python) doesn't care about plating; the waiter (template) doesn't care about how the food was cooked.

### 6. Running it (Ship 6 Phase A worked example)

```
.venv/bin/uvicorn webapp:app --reload --port 8000
```

- `uvicorn` is an ASGI server (the program that actually listens on the port and runs your FastAPI app)
- `webapp:app` means "in the `webapp.py` file, find the variable named `app`"
- `--reload` watches your files and restarts when you save (dev only — never in production)
- `--port 8000` is the TCP port; pick anything > 1024

Open `http://localhost:8000` in a browser. That's it.

To stop: Ctrl-C in the terminal.

### 7. FastAPI's free `/docs`

Visit `http://localhost:8000/docs` and FastAPI auto-generates an interactive API documentation page from your routes. You can poke endpoints right there. This is one of FastAPI's best features for learning — it makes the API tangible.

## A worked example — `webapp.py`'s homepage handler

Reading the actual Ship 6 code (sketch):

```python
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
TEMPLATES = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
def homepage(request: Request):
    # 1. Query the DB (same as cmd_today + list_jobs in tracker.py)
    today = "2026-05-24"
    due = [...]      # SELECT * FROM jobs WHERE next_action_at <= today...
    jobs = [...]     # SELECT * FROM jobs ORDER BY ...
    contacts = [...] # SELECT * FROM contacts ...

    # 2. Hand the data + template to Jinja2 to render
    return TEMPLATES.TemplateResponse("index.html", {
        "request": request,
        "today": today,
        "due": due,
        "jobs": jobs,
    })
```

Reading top to bottom:
- `app = FastAPI()` — create the app instance
- `@app.get("/")` — register this function as the handler for `GET /`
- `request: Request` — required argument when using templates (Jinja2 needs the request context)
- `response_class=HTMLResponse` — tells FastAPI we're returning HTML (not JSON, the default)
- The function body fetches data and returns a template render call

The template file (`templates/index.html`) is plain HTML with Jinja2 placeholders:

```html
<h1>Job Tracker — {{ today }}</h1>
{% for job in jobs %}
  <div>{{ job.title }} @ {{ job.company }}</div>
{% endfor %}
```

`{{ ... }}` interpolates a value. `{% ... %}` runs a control statement (for, if).

## Check yourself

- What's the difference between a "client" and a "server" in HTTP?
- What does the `@app.get("/")` decorator actually do?
- Why is the template file separate from `webapp.py` instead of building HTML strings in Python?
- What does `--reload` give you, and why should you NOT use it in production?
- If you visit `localhost:8000/jobs/1` and there's no route registered for `/jobs/{id}` yet, what status code do you get back?

## Interview-ready 60-second answer

*"A backend is a long-running program that listens on a port and handles HTTP requests. The request-response cycle is the fundamental unit: client sends a request with a method (GET/POST/etc.), path, and optional body; server runs the matching handler and sends back a status code + body. Python's two dominant backend frameworks are Django (batteries-included) and FastAPI (modern, async-first, ASGI). FastAPI uses Python type hints to auto-generate API docs and request validation. For rendering HTML, you'd use a template engine like Jinja2 to separate data from presentation. In production, you'd run the app behind an ASGI server like uvicorn or gunicorn, often with a reverse proxy like nginx."*

## Open threads

- **ASGI vs WSGI** — older Python web frameworks (Flask, Django pre-3.0) are WSGI (synchronous); FastAPI is ASGI (async-capable). Not blocking for us; relevant if we hit scaling concerns.
- **Async functions in FastAPI** — `async def` handlers let one process serve many concurrent requests; we're using sync handlers for now (simpler, fine for personal use).
- **Form handling / file uploads** — needs `python-multipart`; we'll add when we build the add-job form.
- **CORS** — only matters when frontend is served from a different domain than the backend; we serve from the same FastAPI app, so skip.
- **Authentication** — none in dev; for deploy we'll add HTTP basic auth so the URL isn't world-readable.
- **HTMX** — for interactivity without a JS framework; Lesson 12 when we add it in Ship 6 Phase C.
