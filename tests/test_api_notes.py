import json


def test_get_notes_empty(client):
    rv = client.get('/api/notes')
    assert rv.status_code == 200
    assert rv.get_json() == []


def test_create_note(client):
    rv = client.post('/api/notes', json={'body': 'Test note'})
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['body'] == 'Test note'
    assert data['id'] == 1
    assert 'created_at' in data


def test_create_note_missing_body(client):
    rv = client.post('/api/notes', json={})
    assert rv.status_code == 400


def test_create_note_with_tags(client):
    rv = client.post('/api/notes', json={'body': 'Tagged note', 'tags': ['standup', 'deploy']})
    assert rv.status_code == 201
    data = rv.get_json()
    tag_names = [t['name'] for t in data['tags']]
    assert 'standup' in tag_names
    assert 'deploy' in tag_names


def test_update_note(client):
    client.post('/api/notes', json={'body': 'Original'})
    rv = client.patch('/api/notes/1', json={'body': 'Updated'})
    assert rv.status_code == 200
    assert rv.get_json()['body'] == 'Updated'


def test_update_note_not_found(client):
    rv = client.patch('/api/notes/999', json={'body': 'Nope'})
    assert rv.status_code == 404


def test_delete_note(client):
    client.post('/api/notes', json={'body': 'Delete me'})
    rv = client.delete('/api/notes/1')
    assert rv.status_code == 200
    notes = client.get('/api/notes').get_json()
    assert len(notes) == 0


def test_delete_note_not_found(client):
    rv = client.delete('/api/notes/999')
    assert rv.status_code == 404


def test_notes_day_grouping(client):
    client.post('/api/notes', json={'body': 'Note 1'})
    client.post('/api/notes', json={'body': 'Note 2'})
    rv = client.get('/api/notes')
    data = rv.get_json()
    # Both notes on same day
    assert len(data) == 1
    assert len(data[0]['notes']) == 2


def test_notes_search(client):
    client.post('/api/notes', json={'body': 'Deploy went well'})
    client.post('/api/notes', json={'body': 'Meeting notes'})

    rv = client.get('/api/notes?q=deploy')
    data = rv.get_json()
    assert len(data) == 1
    assert data[0]['notes'][0]['body'] == 'Deploy went well'


def test_notes_tag_filter(client):
    client.post('/api/notes', json={'body': 'Note A', 'tags': ['infra']})
    client.post('/api/notes', json={'body': 'Note B', 'tags': ['deploy']})

    rv = client.get('/api/notes?tags=infra')
    data = rv.get_json()
    total_notes = sum(len(d['notes']) for d in data)
    assert total_notes == 1
    assert data[0]['notes'][0]['body'] == 'Note A'
