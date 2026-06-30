import json


def test_get_tags_empty(client):
    rv = client.get('/api/tags')
    assert rv.status_code == 200
    assert rv.get_json() == []


def test_tags_created_implicitly(client):
    client.post('/api/tasks', json={'title': 'T', 'status': 'todo', 'tags': ['deploy']})
    rv = client.get('/api/tags')
    tags = rv.get_json()
    assert len(tags) == 1
    assert tags[0]['name'] == 'deploy'
    assert tags[0]['usage_count'] == 1


def test_tags_shared_across_tasks_and_notes(client):
    client.post('/api/tasks', json={'title': 'T', 'status': 'todo', 'tags': ['infra']})
    client.post('/api/notes', json={'body': 'N', 'tags': ['infra']})

    rv = client.get('/api/tags')
    tags = rv.get_json()
    assert len(tags) == 1
    assert tags[0]['usage_count'] == 2


def test_tag_color_assigned(client):
    client.post('/api/tasks', json={'title': 'T', 'status': 'todo', 'tags': ['alpha']})
    rv = client.get('/api/tags')
    tags = rv.get_json()
    assert tags[0]['color'].startswith('#')


def test_orphan_tag_pruned_on_task_delete(client):
    client.post('/api/tasks', json={'title': 'T', 'status': 'todo', 'tags': ['orphan']})
    # Tag exists
    assert len(client.get('/api/tags').get_json()) == 1
    # Delete task
    client.delete('/api/tasks/1')
    # Tag is pruned
    assert len(client.get('/api/tags').get_json()) == 0


def test_orphan_tag_pruned_on_note_delete(client):
    client.post('/api/notes', json={'body': 'N', 'tags': ['orphan']})
    assert len(client.get('/api/tags').get_json()) == 1
    client.delete('/api/notes/1')
    assert len(client.get('/api/tags').get_json()) == 0


def test_tag_not_pruned_if_still_used(client):
    client.post('/api/tasks', json={'title': 'T', 'status': 'todo', 'tags': ['shared']})
    client.post('/api/notes', json={'body': 'N', 'tags': ['shared']})
    # Delete just the task
    client.delete('/api/tasks/1')
    # Tag still has a note reference
    tags = client.get('/api/tags').get_json()
    assert len(tags) == 1
    assert tags[0]['usage_count'] == 1


def test_tag_color_palette_variety(client):
    """Tags should get different colors from the palette."""
    for i in range(5):
        client.post('/api/tasks', json={'title': f'T{i}', 'status': 'todo', 'tags': [f'tag{i}']})

    tags = client.get('/api/tags').get_json()
    colors = [t['color'] for t in tags]
    # At least some variety (not all the same)
    assert len(set(colors)) > 1
