from datetime import datetime

from ..db import get_db
from .tags import get_or_create_tags, prune_orphan_tags


def get_board():
    """Get all tasks grouped by status columns with their tags."""
    db = get_db()
    board = {'todo': [], 'doing': [], 'done': []}

    rows = db.execute("""
        SELECT t.id, t.title, t.description, t.status, t.position,
               t.created_at, t.updated_at, t.due_date
        FROM tasks t
        ORDER BY t.position ASC
    """).fetchall()

    for row in rows:
        task = dict(row)
        task['tags'] = _get_task_tags(db, task['id'])
        board[task['status']].append(task)

    return board


def create_task(title, description=None, status='todo', tag_names=None):
    db = get_db()
    now = datetime.utcnow().isoformat() + 'Z'

    max_pos = db.execute(
        "SELECT COALESCE(MAX(position), -1) FROM tasks WHERE status = ?",
        (status,)
    ).fetchone()[0]

    cur = db.execute(
        "INSERT INTO tasks (title, description, status, position, created_at) VALUES (?, ?, ?, ?, ?)",
        (title, description, status, max_pos + 1, now)
    )
    task_id = cur.lastrowid

    if tag_names:
        tag_ids = get_or_create_tags(db, tag_names)
        for tid in tag_ids:
            db.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tid))

    db.commit()
    return get_task(task_id)


def get_task(task_id):
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    task = dict(row)
    task['tags'] = _get_task_tags(db, task_id)
    return task


def update_task(task_id, **kwargs):
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        return None

    now = datetime.utcnow().isoformat() + 'Z'
    fields = []
    values = []

    for field in ('title', 'description', 'status', 'due_date'):
        if field in kwargs and kwargs[field] is not None:
            fields.append(f"{field} = ?")
            values.append(kwargs[field])

    if fields:
        fields.append("updated_at = ?")
        values.append(now)
        values.append(task_id)
        db.execute(
            f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?",
            values
        )

    if 'tags' in kwargs:
        db.execute("DELETE FROM task_tags WHERE task_id = ?", (task_id,))
        if kwargs['tags']:
            tag_ids = get_or_create_tags(db, kwargs['tags'])
            for tid in tag_ids:
                db.execute("INSERT OR IGNORE INTO task_tags (task_id, tag_id) VALUES (?, ?)", (task_id, tid))
        prune_orphan_tags(db)

    db.commit()
    return get_task(task_id)


def delete_task(task_id):
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        return False
    db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    prune_orphan_tags(db)
    db.commit()
    return True


def reorder_tasks(status, ordered_ids):
    """Reorder tasks within a column. Also updates status for cross-column moves."""
    db = get_db()
    for position, task_id in enumerate(ordered_ids):
        db.execute(
            "UPDATE tasks SET status = ?, position = ?, updated_at = ? WHERE id = ?",
            (status, position, datetime.utcnow().isoformat() + 'Z', task_id)
        )
    db.commit()


def _get_task_tags(db, task_id):
    rows = db.execute("""
        SELECT t.id, t.name, t.color
        FROM tags t JOIN task_tags tt ON t.id = tt.tag_id
        WHERE tt.task_id = ?
        ORDER BY t.name
    """, (task_id,)).fetchall()
    return [dict(r) for r in rows]
