# Work Tracker — Implementation Plan

A local, offline-first Flask application for kanban-style task tracking and a timestamped daily notes log, with a shared tagging system and plaintext export. Built entirely within the existing frozen Anaconda environment — no new packages, no version changes.

---

## 1. Guiding constraints

These are hard requirements, not preferences. Every decision below is checked against them.

- **Frozen stack.** Only libraries already installed (see `installed_libraries.txt`). No `pip install`, no version bumps.
- **Offline-first.** No CDNs, no external fonts loaded at runtime. Any JS library (e.g. a drag-drop helper) is vendored into the project as a local file.
- **Single user, single machine.** Runs on `127.0.0.1`, bound to localhost only. No auth, no network exposure.
- **Deliberate aesthetic.** A calm "logbook / desk-instrument" look — sage-grey paper background, pine-green accent (`#2F5D50`), serif + monospace type. No Bootstrap, no default component-library look.
- **Durable data.** Notes and tasks are the user's record of their work; the store must survive restarts and be trivially backed up (a single file).

---

## 2. Technology choices (mapped to installed versions)

| Layer | Choice | Installed version | Notes |
|---|---|---|---|
| Web framework | Flask | 1.1.2 | App-factory pattern; blueprints for `board`, `notes`, `api`. |
| WSGI / routing | Werkzeug | 2.0.2 | See risk note §10 — this pairing works but avoid imports deprecated in Werkzeug 2.x. |
| Templating | Jinja2 | 2.11.3 | Server-rendered shell; dynamic regions hydrated by JS. |
| Escaping | MarkupSafe | 1.1.1 | Compatible with Jinja2 2.11.3. |
| Sessions/signing | itsdangerous | 2.0.1 | Only needed if we use flash messages / CSRF token in session. |
| Storage | `sqlite3` | stdlib | Single-file DB. No ORM — thin hand-written data layer. |
| Drag & drop | SortableJS (vendored) | 1.15.7 (local file) | Not a Python package; dropped into `static/vendor/`. Pure JS, no build step. |
| Frontend | Vanilla JS (ES modules) | — | No framework. `fetch()` against a small JSON API. |
| Tests | pytest + Flask test client | pytest 6.2.4 | API regression. DOM tests discussed in §9. |

**Why no ORM / no SQLAlchemy-heavy layer:** SQLAlchemy 1.4.22 *is* installed, so it's available if preferred. But for a schema this small, the stdlib `sqlite3` module with a thin query module keeps dependencies minimal and the data layer fully transparent. This is the default unless you'd rather use SQLAlchemy (Q5).

---

## 3. Architecture overview

```
work-tracker/
├── run.bat                     # double-click launcher (Anaconda auto-detect + browser open)
├── app/
│   ├── __init__.py             # create_app() factory
│   ├── db.py                   # connection helper, schema init, migrations
│   ├── schema.sql              # table definitions
│   ├── models/
│   │   ├── tasks.py            # task + column queries
│   │   ├── notes.py            # note queries
│   │   └── tags.py            # tag CRUD, color assignment, orphan pruning
│   ├── blueprints/
│   │   ├── views.py            # GET / (renders the shell)
│   │   └── api.py              # JSON endpoints (tasks, notes, tags, export)
│   ├── templates/
│   │   ├── base.html
│   │   └── index.html
│   └── static/
│       ├── css/app.css
│       ├── js/
│       │   ├── board.js
│       │   ├── notes.js
│       │   ├── tags.js
│       │   └── api.js          # fetch wrappers
│       └── vendor/
│           └── sortable.min.js
├── data/
│   └── tracker.db              # created on first run
└── tests/
    ├── test_api_tasks.py
    ├── test_api_notes.py
    ├── test_api_tags.py
    └── test_export.py
```

**Request model.** The server renders one HTML shell. All mutations and reads after load go through a small JSON API and are applied to the DOM by vanilla JS. This keeps the UI responsive (no full-page reloads on every drag or tag toggle) while staying entirely server-authoritative for data.

---

## 4. Data model

### Tables

**Columns are fixed:** `To Do`, `In Progress`, `Done`. No `columns` table — status is a constrained value on the task itself, which keeps the board logic simple and the schema flat.

**`tasks`**
- `id` INTEGER PK
- `title` TEXT NOT NULL
- `description` TEXT
- `status` TEXT NOT NULL CHECK(status IN ('todo','doing','done')) — the fixed column
- `position` INTEGER — order within its column
- `created_at` TEXT (ISO 8601)
- `updated_at` TEXT
- `due_date` TEXT NULL *(optional — see Q4)*

**`notes`**
- `id` INTEGER PK
- `body` TEXT NOT NULL
- `created_at` TEXT (ISO 8601 timestamp — this drives the daily grouping)
- `updated_at` TEXT

**`tags`**
- `id` INTEGER PK
- `name` TEXT UNIQUE (case-folded for matching)
- `color` TEXT — assigned from the 12-color palette at creation

**`task_tags`** / **`note_tags`** — junction tables `(task_id, tag_id)` / `(note_id, tag_id)`, both with `ON DELETE CASCADE`.

### Design notes
- **Timestamps as ISO 8601 text** sort lexically and are SQLite-friendly without extra parsing.
- **Ordering** uses an integer `position`. On reorder, the affected column/list is renumbered in one transaction — simple and robust for single-user scale.
- **Daily grouping for notes** is derived from `date(created_at)` at query time; we don't store a separate "day" record. This keeps notes a pure timestamped stream that we *group* for display.
- **Shared tagging.** One `tags` table serves both tasks and notes via the two junction tables, so a tag like `#deploy` means the same thing and carries the same color whether it's on a card or a note. Usage counts sum across both.
- **Tag colors** are assigned once, at tag creation, by walking the 12-color palette and picking the least-used color (so the board stays visually varied). Color is stored so it's stable forever.
- **Orphan pruning:** when a note or task loses its last reference to a tag, a pass removes any tag with zero references. Runs after delete/untag operations.

---

## 5. API surface

All endpoints return JSON; mutations use proper verbs. Errors return `{ "error": "..." }` with a 4xx/5xx status and a plain, fix-oriented message.

**Tasks**
- `GET  /api/board` → the three fixed columns (`todo` / `doing` / `done`) with nested tasks (+ tags), ready to render
- `POST /api/tasks` → create `{title, description?, status, tags?}`
- `PATCH /api/tasks/<id>` → edit any field (including `status` for column moves)
- `POST /api/tasks/reorder` → `{status, ordered_ids[]}` (also handles cross-column moves by updating `status` + `position`)
- `DELETE /api/tasks/<id>`

**Notes**
- `GET  /api/notes?tags=&from=&to=&q=` → filtered, newest-first, grouped by day
- `POST /api/notes` → `{body, tags?}` (server stamps `created_at`)
- `PATCH /api/notes/<id>`
- `DELETE /api/notes/<id>`

**Tags**
- `GET  /api/tags` → all tags with usage counts (for the filter bar)
- *(create is implicit: posting a note/task with a new tag name creates it)*

**Export**
- `GET  /api/notes/export?tags=&from=&to=&q=&format=txt`
  - Same filter params as the notes list, so "what you see is what you export."
  - Returns `text/plain` with `Content-Disposition: attachment; filename="notes-YYYYMMDD.txt"`.

---

## 6. Plaintext export format

Human-readable, greppable, stable. Draft layout:

```
WORK NOTES — exported 2026-06-30 14:12
Filter: tags=[deploy, infra]  range=2026-06-01..2026-06-30  search="rollback"
========================================================================

# 2026-06-28
------------------------------------------------------------------------
[09:14]  #standup #infra
Cleared the staging queue backlog before the deploy window.

[16:40]  #deploy #rollback
Rolled back v2.3 after the migration stalled. Notes in the ticket.

# 2026-06-27
------------------------------------------------------------------------
[11:02]  #infra
...
```

- Header records the active filter so an exported file is self-documenting.
- Entries grouped by day, newest day first (or oldest-first — **Q6**), timestamped, tags inline.
- Pure ASCII rules so it opens cleanly in any editor and diffs/greps well.

---

## 7. UI / visual design

The brief asks for modern, aesthetic, and responsive. The direction is a **logbook / desk instrument**: something that feels like a well-made paper ledger rendered in software — quiet, legible, deliberate. The boldness is spent in one place (the type + the tag chips); everything else stays disciplined.

### Design tokens

**Color**
- `--paper` `#E8E9E3` — sage-grey background (the "page")
- `--ink` `#1F2421` — near-black text
- `--pine` `#2F5D50` — primary accent (active states, primary actions)
- `--pine-soft` `#3E7766` — hover
- `--rule` `#C9CBC2` — hairline dividers
- 12-color **tag palette** (muted, equal-weight) assigned per tag

**Type**
- Display / headings: **Georgia** (installed-OS serif; loaded as a system font, no web fetch)
- Body: same serif at text sizes for a cohesive ledger feel
- Data / timestamps / tags: a **monospace** system stack (`ui-monospace, "Cascadia Mono", "Consolas", monospace`)
- A deliberate type scale (e.g. 13 / 15 / 18 / 24 / 32) with generous line-height on body copy.

**Signature element**
- The **timestamp gutter** in the notes log: a left-hand monospace rail of `[HH:MM]` stamps with a hairline rule, like the margin of a lab notebook. It's the one memorable, subject-true detail and it earns its place because the log *is* a chronological record.

### Layout
- Two views — **Board** and **Log** — with a layout that adapts to width:
  - **Narrow screens:** a single view at a time, switched by a quiet top tab-bar (Board ↔ Log).
  - **Wide screens:** Board and Log shown **side-by-side** by default.
  - A small **layout toggle** lets you manually override either way (force tabs on a wide screen, or split when there's room), with the choice remembered between sessions.
- **Board:** three fixed columns (To Do / In Progress / Done), draggable cards, an inline "+ add" affordance per column.
- **Log:** a single-column reverse-chronological stream; a sticky filter/search bar at top; an "Export" button that respects the active filter.
- **Tags:** colored monospace chips shared across cards and notes. The filter bar is a row of toggleable chips with live usage counts.

The breakpoint between stacked-tabs and side-by-side sits around ~960px; below it the split is too cramped to be useful, so tabs take over. The manual toggle is stored client-side (a single preference) so it doesn't need a server round-trip.

### Responsiveness & quality floor
- Below ~960px the layout collapses from side-by-side to tabbed automatically; the manual toggle still works in both ranges. Board columns scroll horizontally on narrow screens; the log is single-column everywhere and reflows naturally.
- Visible keyboard focus rings, `prefers-reduced-motion` respected (drag animations and reveals soften to none), adequate hit targets on touch.
- Copy is plain and active-voice: buttons say what they do (**Add note**, **Export**, **Delete**), empty states invite action ("No notes yet — write the first one.").

### Motion (restrained)
- Card drag uses SortableJS's ghost/animation only; no decorative motion elsewhere. A subtle fade when a note is added is the single ambient touch.

---

## 8. Build phases & milestones

Each phase ends in something runnable and testable.

1. **Scaffold + storage.** App factory, `schema.sql`, `db.py`, first-run DB creation, base template renders an empty shell. *Test: app boots, DB initializes.*
2. **Tasks + board.** Task model, board API, columns, card rendering, drag-and-drop with reordering and cross-column moves (SortableJS vendored). *Test: create/move/delete via API.*
3. **Notes + log.** Note model, create/list/edit/delete, timestamped stream, day grouping, the timestamp-gutter UI. *Test: create/list/delete; correct day grouping.*
4. **Tagging.** Shared tag model, implicit tag creation, palette color assignment, chips on cards and notes, orphan pruning. *Test: tag lifecycle + pruning.*
5. **Filter & search.** Tag-chip filtering, free-text search over note bodies, date-range filter, all combinable. *Test: each filter and combinations.*
6. **Export.** Plaintext export honoring the active filter, with the self-documenting header and attachment download. *Test: export content + filename + filter echo.*
7. **Aesthetic pass.** Final type scale, spacing, palette, focus states, reduced-motion, mobile reflow. Critique-and-cut pass.
8. **Launcher + offline check.** `run.bat` with Anaconda auto-detection and auto browser-open; verify zero network calls at runtime (no CDN, fonts are system).
9. **Test hardening.** Fill out API regression; add DOM/interaction tests (§9); document how to run them.

---

## 9. Testing strategy

- **API regression (pytest + Flask test client):** every endpoint, happy path + the obvious error paths (missing fields, bad ids, empty reorder). This is the primary safety net and runs purely inside the installed Python stack.
- **Data-layer tests:** ordering renumber, tag color assignment determinism, orphan pruning.
- **Export tests:** byte-level checks on header, grouping, and filename.
- **DOM / interaction tests:** these run under Node/jsdom, which is *outside* the Python environment. **Q3:** confirm Node + jsdom are available on the machine; if not, we substitute lightweight in-browser smoke checks or skip this tier rather than add a dependency.

---

## 10. Risks & mitigations

- **Flask 1.1.2 ↔ Werkzeug 2.0.2.** This is a known-fragile pairing; some Werkzeug 2.x changes broke older Flask in certain imports. Mitigation: stick to documented Flask 1.1 APIs, avoid importing Werkzeug internals directly, and pin behavior with a boot smoke-test in Phase 1. If a break surfaces, we adapt within installed versions (e.g. shim the specific import) rather than upgrading.
- **No build step for JS.** We use plain ES modules served statically — no bundler, no transpile. Keeps things installable-free and debuggable.
- **SQLite concurrency.** Single-user/localhost makes this a non-issue; we still wrap multi-statement mutations (reorder, prune) in transactions.
- **Data safety.** The DB is one file under `data/`; the launcher can optionally copy a timestamped backup on start. *(Q7 — worth it?)*

---

## 11. Open questions

The three structural decisions are now settled:

- **Q1 — Columns:** ✅ Fixed (To Do / In Progress / Done).
- **Q2 — Tag scope:** ✅ Shared across tasks *and* notes.
- **Q3 — Layout:** ✅ Side-by-side on wide screens, tabbed on narrow, with a manual toggle that's remembered.

Still open — lower stakes, settled with defaults below unless you say otherwise:

- **Q4 — Task fields:** beyond title + description, do you want due dates and/or priority on cards? *(Default: none, to keep cards clean; due-date is scaffolded in the schema but hidden.)*
- **Q5 — Data layer:** thin `sqlite3` *(default)* vs. SQLAlchemy (also installed).
- **Q6 — Export order:** newest-day-first *(default)* or oldest-first within the file?
- **Q7 — Auto-backup:** copy a timestamped DB backup on each launch? *(Default: yes — it's cheap insurance for a single-file store.)*
- **Q8 — Note editing:** append-only log vs. freely editable after posting? *(Default: editable, with `updated_at` tracked; a true append-only mode is a one-line change if you prefer the integrity.)*

---

*This is a living document — we'll fold your answers back in and refine before any code is written.*
