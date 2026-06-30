# miWork

A local, offline-first Flask application for kanban-style task tracking and a timestamped daily notes log, with a shared tagging system and plaintext export.

## Features

- **Kanban Board** — Three fixed columns (To Do / In Progress / Done) with drag-and-drop reordering via SortableJS
- **Daily Notes Log** — Timestamped notes grouped by day with a characteristic timestamp gutter
- **Shared Tagging** — Tags work across both tasks and notes with auto-assigned colors from a 12-color palette
- **Filter & Search** — Filter by tags, date range, or free-text search
- **Plaintext Export** — Export filtered notes as a self-documenting text file
- **Responsive Layout** — Side-by-side on wide screens, tabbed on narrow, with a manual toggle
- **Offline-First** — No CDNs, no external fonts, no network calls at runtime

## Quick Start

### Windows (double-click)
```
run.bat
```

### Manual
```bash
export FLASK_APP=app
flask run --host=127.0.0.1 --port=5000
```

Then open http://127.0.0.1:5000 in your browser.

## Running Tests

```bash
python -m pytest tests/ -v
```

## Architecture

```
├── app/
│   ├── __init__.py             # create_app() factory
│   ├── db.py                   # SQLite connection helper, schema init
│   ├── schema.sql              # Table definitions
│   ├── models/
│   │   ├── tasks.py            # Task + column queries
│   │   ├── notes.py            # Note queries
│   │   └── tags.py             # Tag CRUD, color assignment, orphan pruning
│   ├── blueprints/
│   │   ├── views.py            # GET / (renders the shell)
│   │   └── api.py              # JSON endpoints (tasks, notes, tags, export)
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       ├── css/app.css
│       ├── js/                 # Vanilla JS (board, notes, tags, api)
│       └── vendor/sortable.min.js
├── data/                       # tracker.db created on first run
├── tests/                      # pytest API regression tests
└── run.bat                     # Windows launcher with Anaconda auto-detection
```

## Technology

- **Flask** — Web framework (app-factory pattern)
- **SQLite** — Single-file database via stdlib `sqlite3`
- **SortableJS** — Vendored drag-and-drop library
- **Vanilla JS** — No framework, ES modules, `fetch()` API
- **pytest** — API regression tests

## Design

The UI follows a "logbook / desk-instrument" aesthetic: sage-grey paper background, pine-green accent, serif + monospace type. The signature element is the timestamp gutter in the notes log — a left-hand monospace rail of `[HH:MM]` stamps like the margin of a lab notebook.

