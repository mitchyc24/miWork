def test_export_empty(client):
    rv = client.get('/api/notes/export')
    assert rv.status_code == 200
    assert rv.content_type.startswith('text/plain')
    assert 'WORK NOTES' in rv.data.decode()


def test_export_with_notes(client):
    client.post('/api/notes', json={'body': 'Deploy v2', 'tags': ['deploy']})
    client.post('/api/notes', json={'body': 'Fix bug'})

    rv = client.get('/api/notes/export')
    text = rv.data.decode()
    assert 'WORK NOTES' in text
    assert 'Deploy v2' in text
    assert 'Fix bug' in text
    assert '#deploy' in text


def test_export_content_disposition(client):
    client.post('/api/notes', json={'body': 'Test'})
    rv = client.get('/api/notes/export')
    assert 'attachment' in rv.headers.get('Content-Disposition', '')
    assert 'notes-' in rv.headers.get('Content-Disposition', '')
    assert '.txt' in rv.headers.get('Content-Disposition', '')


def test_export_with_filter(client):
    client.post('/api/notes', json={'body': 'Note A', 'tags': ['infra']})
    client.post('/api/notes', json={'body': 'Note B', 'tags': ['deploy']})

    rv = client.get('/api/notes/export?tags=infra')
    text = rv.data.decode()
    assert 'Note A' in text
    assert 'Note B' not in text
    assert 'tags=[infra]' in text


def test_export_with_search_filter(client):
    client.post('/api/notes', json={'body': 'Rollback happened'})
    client.post('/api/notes', json={'body': 'All good'})

    rv = client.get('/api/notes/export?q=rollback')
    text = rv.data.decode()
    assert 'Rollback happened' in text
    assert 'All good' not in text
    assert 'search="rollback"' in text


def test_export_header_format(client):
    rv = client.get('/api/notes/export')
    text = rv.data.decode()
    lines = text.split('\n')
    assert lines[0].startswith('WORK NOTES')
    assert '=' * 72 in text
