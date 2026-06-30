import os
import tempfile
import pytest

from app import create_app


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    application = create_app({
        'TESTING': True,
        'DATABASE': db_path,
    })
    yield application
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
