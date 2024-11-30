import pytest
from app import app

@pytest.fixture
def client():
    app.testing = True
    return app.test_client()

def test_home(client):
    response = client.get('/hello')
    assert response.status_code == 200
    assert response.json == {'message': 'Hello, World!'}

def test_add(client):
    response = client.post('/add', json={'a': 1, 'b': 2})
    assert response.status_code == 200
    assert response.json == {'result': 3}
