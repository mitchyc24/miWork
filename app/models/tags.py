from datetime import datetime

from ..db import get_db


TAG_PALETTE = [
    '#8B5E3C', '#4A7C59', '#2E6B8A', '#7B4F8A',
    '#8A6B2E', '#3C6E5E', '#5E4A8B', '#8A3C5E',
    '#2E8A6B', '#6B3C8A', '#8A8A2E', '#3C5E8B',
]


def get_or_create_tags(db, tag_names):
    """Get or create tags by name. Returns list of tag ids."""
    tag_ids = []
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        row = db.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        if row:
            tag_ids.append(row['id'])
        else:
            color = _pick_color(db)
            cur = db.execute(
                "INSERT INTO tags (name, color) VALUES (?, ?)",
                (name, color)
            )
            tag_ids.append(cur.lastrowid)
    return tag_ids


def _pick_color(db):
    """Pick the least-used color from the palette."""
    rows = db.execute("SELECT color, COUNT(*) as cnt FROM tags GROUP BY color").fetchall()
    used = {r['color']: r['cnt'] for r in rows}
    min_count = float('inf')
    pick = TAG_PALETTE[0]
    for color in TAG_PALETTE:
        cnt = used.get(color, 0)
        if cnt < min_count:
            min_count = cnt
            pick = color
    return pick


def prune_orphan_tags(db):
    """Remove tags with zero references in both task_tags and note_tags."""
    db.execute("""
        DELETE FROM tags WHERE id NOT IN (
            SELECT tag_id FROM task_tags
            UNION
            SELECT tag_id FROM note_tags
        )
    """)


def get_all_tags(db):
    """Get all tags with usage counts."""
    rows = db.execute("""
        SELECT t.id, t.name, t.color,
            (SELECT COUNT(*) FROM task_tags WHERE tag_id = t.id) +
            (SELECT COUNT(*) FROM note_tags WHERE tag_id = t.id) as usage_count
        FROM tags t
        ORDER BY t.name
    """).fetchall()
    return [dict(r) for r in rows]
