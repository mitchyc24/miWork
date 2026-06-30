from datetime import datetime

from ..db import get_db
from .tags import get_or_create_tags, prune_orphan_tags


def get_notes(tags=None, from_date=None, to_date=None, q=None):
    """Get notes filtered and grouped by day, newest first."""
    db = get_db()
    conditions = []
    params = []

    if tags:
        tag_list = [t.strip().lower() for t in tags.split(',') if t.strip()]
        if tag_list:
            placeholders = ','.join('?' * len(tag_list))
            conditions.append(f"""n.id IN (
                SELECT nt.note_id FROM note_tags nt
                JOIN tags t ON t.id = nt.tag_id
                WHERE t.name IN ({placeholders})
            )""")
            params.extend(tag_list)

    if from_date:
        conditions.append("date(n.created_at) >= ?")
        params.append(from_date)

    if to_date:
        conditions.append("date(n.created_at) <= ?")
        params.append(to_date)

    if q:
        conditions.append("n.body LIKE ?")
        params.append(f"%{q}%")

    where = ""
    if conditions:
        where = "WHERE " + " AND ".join(conditions)

    rows = db.execute(f"""
        SELECT n.id, n.body, n.created_at, n.updated_at
        FROM notes n
        {where}
        ORDER BY n.created_at DESC
    """, params).fetchall()

    notes = []
    for row in rows:
        note = dict(row)
        note['tags'] = _get_note_tags(db, note['id'])
        notes.append(note)

    # Group by day
    days = {}
    for note in notes:
        day = note['created_at'][:10]
        if day not in days:
            days[day] = []
        days[day].append(note)

    result = [{'date': day, 'notes': day_notes} for day, day_notes in days.items()]
    return result


def create_note(body, tag_names=None):
    db = get_db()
    now = datetime.utcnow().isoformat() + 'Z'

    cur = db.execute(
        "INSERT INTO notes (body, created_at) VALUES (?, ?)",
        (body, now)
    )
    note_id = cur.lastrowid

    if tag_names:
        tag_ids = get_or_create_tags(db, tag_names)
        for tid in tag_ids:
            db.execute("INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tid))

    db.commit()
    return get_note(note_id)


def get_note(note_id):
    db = get_db()
    row = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if row is None:
        return None
    note = dict(row)
    note['tags'] = _get_note_tags(db, note_id)
    return note


def update_note(note_id, **kwargs):
    db = get_db()
    note = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        return None

    now = datetime.utcnow().isoformat() + 'Z'

    if 'body' in kwargs:
        db.execute(
            "UPDATE notes SET body = ?, updated_at = ? WHERE id = ?",
            (kwargs['body'], now, note_id)
        )

    if 'tags' in kwargs:
        db.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
        if kwargs['tags']:
            tag_ids = get_or_create_tags(db, kwargs['tags'])
            for tid in tag_ids:
                db.execute("INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tid))
        prune_orphan_tags(db)

    db.commit()
    return get_note(note_id)


def delete_note(note_id):
    db = get_db()
    note = db.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
    if note is None:
        return False
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    prune_orphan_tags(db)
    db.commit()
    return True


def _get_note_tags(db, note_id):
    rows = db.execute("""
        SELECT t.id, t.name, t.color
        FROM tags t JOIN note_tags nt ON t.id = nt.tag_id
        WHERE nt.note_id = ?
        ORDER BY t.name
    """, (note_id,)).fetchall()
    return [dict(r) for r in rows]
