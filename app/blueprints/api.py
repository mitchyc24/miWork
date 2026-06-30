from datetime import datetime

from flask import Blueprint, request, jsonify

from ..models import tasks, notes
from ..models.tags import get_all_tags
from ..db import get_db

bp = Blueprint('api', __name__, url_prefix='/api')


# --- Board / Tasks ---

@bp.route('/board', methods=['GET'])
def get_board():
    board = tasks.get_board()
    return jsonify(board)


@bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data or not data.get('title'):
        return jsonify({'error': 'Title is required'}), 400

    status = data.get('status', 'todo')
    if status not in ('todo', 'doing', 'done'):
        return jsonify({'error': 'Invalid status'}), 400

    task = tasks.create_task(
        title=data['title'],
        description=data.get('description'),
        status=status,
        tag_names=data.get('tags')
    )
    return jsonify(task), 201


@bp.route('/tasks/<int:task_id>', methods=['PATCH'])
def update_task(task_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    task = tasks.update_task(task_id, **data)
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(task)


@bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    if tasks.delete_task(task_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Task not found'}), 404


@bp.route('/tasks/reorder', methods=['POST'])
def reorder_tasks():
    data = request.get_json()
    if not data or 'status' not in data or 'ordered_ids' not in data:
        return jsonify({'error': 'status and ordered_ids are required'}), 400

    status = data['status']
    if status not in ('todo', 'doing', 'done'):
        return jsonify({'error': 'Invalid status'}), 400

    tasks.reorder_tasks(status, data['ordered_ids'])
    return jsonify({'success': True})


# --- Notes ---

@bp.route('/notes', methods=['GET'])
def get_notes():
    result = notes.get_notes(
        tags=request.args.get('tags'),
        from_date=request.args.get('from'),
        to_date=request.args.get('to'),
        q=request.args.get('q')
    )
    return jsonify(result)


@bp.route('/notes', methods=['POST'])
def create_note():
    data = request.get_json()
    if not data or not data.get('body'):
        return jsonify({'error': 'Body is required'}), 400

    note = notes.create_note(
        body=data['body'],
        tag_names=data.get('tags')
    )
    return jsonify(note), 201


@bp.route('/notes/<int:note_id>', methods=['PATCH'])
def update_note(note_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    note = notes.update_note(note_id, **data)
    if note is None:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(note)


@bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    if notes.delete_note(note_id):
        return jsonify({'success': True})
    return jsonify({'error': 'Note not found'}), 404


# --- Tags ---

@bp.route('/tags', methods=['GET'])
def get_tags():
    db = get_db()
    return jsonify(get_all_tags(db))


# --- Export ---

@bp.route('/notes/export', methods=['GET'])
def export_notes():
    tag_filter = request.args.get('tags')
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    q = request.args.get('q')

    days = notes.get_notes(tags=tag_filter, from_date=from_date, to_date=to_date, q=q)

    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    lines = [f"WORK NOTES — exported {now}"]

    # Build filter line
    filters = []
    if tag_filter:
        filters.append(f"tags=[{tag_filter}]")
    if from_date or to_date:
        range_str = f"{from_date or ''}..{to_date or ''}"
        filters.append(f"range={range_str}")
    if q:
        filters.append(f'search="{q}"')

    if filters:
        lines.append(f"Filter: {'  '.join(filters)}")

    lines.append("=" * 72)
    lines.append("")

    for day_group in days:
        lines.append(f"# {day_group['date']}")
        lines.append("-" * 72)
        for note in day_group['notes']:
            time_str = note['created_at'][11:16]
            tag_str = ""
            if note['tags']:
                tag_str = "  " + " ".join(f"#{t['name']}" for t in note['tags'])
            lines.append(f"[{time_str}]{tag_str}")
            lines.append(note['body'])
            lines.append("")
        lines.append("")

    content = "\n".join(lines)
    today = datetime.utcnow().strftime('%Y%m%d')

    from flask import make_response
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="notes-{today}.txt"'
    return response
