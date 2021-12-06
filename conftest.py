import os
import tempfile
import pytest

from main import create_app
from db import init_testdb,add_test_data


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({'TESTING': True, 'DATABASE_URL': db_path})
 

    with app.test_client() as client:
        with app.app_context():
            init_testdb()
            add_test_data()

        yield client

    os.close(db_fd)
    os.unlink(db_path)
