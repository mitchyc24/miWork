import json


def test_get_board_empty(client):
    rv = client.get('/api/board')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data == {'todo': [], 'doing': [], 'done': []}


def test_create_task(client):
    rv = client.post('/api/tasks', json={'title': 'Test task', 'status': 'todo'})
    assert rv.status_code == 201
    data = rv.get_json()
    assert data['title'] == 'Test task'
    assert data['status'] == 'todo'
    assert data['id'] == 1


def test_create_task_missing_title(client):
    rv = client.post('/api/tasks', json={'status': 'todo'})
    assert rv.status_code == 400


def test_create_task_invalid_status(client):
    rv = client.post('/api/tasks', json={'title': 'Bad', 'status': 'invalid'})
    assert rv.status_code == 400


def test_create_task_with_tags(client):
    rv = client.post('/api/tasks', json={'title': 'Tagged', 'status': 'todo', 'tags': ['deploy', 'infra']})
    assert rv.status_code == 201
    data = rv.get_json()
    tag_names = [t['name'] for t in data['tags']]
    assert 'deploy' in tag_names
    assert 'infra' in tag_names


def test_update_task(client):
    client.post('/api/tasks', json={'title': 'Original', 'status': 'todo'})
    rv = client.patch('/api/tasks/1', json={'title': 'Updated'})
    assert rv.status_code == 200
    assert rv.get_json()['title'] == 'Updated'


def test_update_task_not_found(client):
    rv = client.patch('/api/tasks/999', json={'title': 'Nope'})
    assert rv.status_code == 404


def test_delete_task(client):
    client.post('/api/tasks', json={'title': 'Delete me', 'status': 'todo'})
    rv = client.delete('/api/tasks/1')
    assert rv.status_code == 200
    # Verify it's gone
    board = client.get('/api/board').get_json()
    assert len(board['todo']) == 0


def test_delete_task_not_found(client):
    rv = client.delete('/api/tasks/999')
    assert rv.status_code == 404


def test_reorder_tasks(client):
    client.post('/api/tasks', json={'title': 'A', 'status': 'todo'})
    client.post('/api/tasks', json={'title': 'B', 'status': 'todo'})
    client.post('/api/tasks', json={'title': 'C', 'status': 'todo'})

    # Reverse order
    rv = client.post('/api/tasks/reorder', json={'status': 'todo', 'ordered_ids': [3, 2, 1]})
    assert rv.status_code == 200

    board = client.get('/api/board').get_json()
    ids = [t['id'] for t in board['todo']]
    assert ids == [3, 2, 1]


def test_reorder_cross_column(client):
    client.post('/api/tasks', json={'title': 'Move me', 'status': 'todo'})

    # Move task 1 to 'doing'
    rv = client.post('/api/tasks/reorder', json={'status': 'doing', 'ordered_ids': [1]})
    assert rv.status_code == 200

    board = client.get('/api/board').get_json()
    assert len(board['todo']) == 0
    assert len(board['doing']) == 1
    assert board['doing'][0]['status'] == 'doing'


def test_reorder_missing_fields(client):
    rv = client.post('/api/tasks/reorder', json={'status': 'todo'})
    assert rv.status_code == 400


def test_board_ordering(client):
    client.post('/api/tasks', json={'title': 'First', 'status': 'todo'})
    client.post('/api/tasks', json={'title': 'Second', 'status': 'todo'})
    board = client.get('/api/board').get_json()
    assert board['todo'][0]['title'] == 'First'
    assert board['todo'][1]['title'] == 'Second'
