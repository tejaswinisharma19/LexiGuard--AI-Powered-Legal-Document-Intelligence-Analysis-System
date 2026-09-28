import pytest
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client

def test_user_stats_api_unauthenticated(client):
    response = client.get("/api/user/stats")
    assert response.status_code == 401
    json_data = response.get_json()
    assert "error" in json_data

def test_user_stats_api_authenticated(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_test_123"
        sess["email"] = "user@example.com"
        sess["is_admin"] = False

    mock_stats = {
        "total_documents": 5,
        "total_analyses": 8,
        "total_comparisons": 2,
        "total_chats": 12
    }

    with patch("app.dynamodb_service.get_user_stats", return_value=mock_stats):
        response = client.get("/api/user/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_documents"] == 5
        assert data["total_analyses"] == 8
        assert data["total_comparisons"] == 2
        assert data["total_chats"] == 12

def test_admin_stats_api_authenticated(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "lexiguard662@gmail.com"
        sess["email"] = "lexiguard662@gmail.com"
        sess["is_admin"] = True

    mock_sys_stats = {
        "total_users": 10,
        "total_documents": 25,
        "total_analyses": 40,
        "total_comparisons": 15
    }

    with patch("app.dynamodb_service.get_system_stats", return_value=mock_sys_stats), \
         patch("app.dynamodb_service.get_user_by_email", return_value={"user_id": "lexiguard662@gmail.com", "role": "admin"}):
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert data["total_users"] == 10
        assert data["total_documents"] == 25
