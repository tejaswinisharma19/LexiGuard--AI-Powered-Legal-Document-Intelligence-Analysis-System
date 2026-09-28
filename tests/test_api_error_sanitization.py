import pytest
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess["user_id"] = "lexiguard662@gmail.com"
            sess["user_email"] = "lexiguard662@gmail.com"
            sess["role"] = "admin"
        yield client


def test_list_documents_error_sanitization(client):
    with patch("services.postgresql_service.PostgreSQLService.list_documents", side_effect=Exception("Internal DB Connection Timeout Secret: AWS_KEY_12345")):
        response = client.get("/api/documents")
        assert response.status_code == 500
        json_data = response.get_json()
        assert "error" in json_data
        assert "details" not in json_data
        assert "AWS_KEY_12345" not in response.get_data(as_text=True)
        assert "Internal DB Connection Timeout" not in response.get_data(as_text=True)


def test_delete_document_error_sanitization(client):
    with patch("services.postgresql_service.PostgreSQLService.get_document", side_effect=Exception("DynamoDB Internal Fault: Partition Key missing")):
        response = client.delete("/api/documents/doc-123")
        assert response.status_code == 500
        json_data = response.get_json()
        assert "error" in json_data
        assert "details" not in json_data
        assert "DynamoDB Internal Fault" not in response.get_data(as_text=True)


def test_admin_stats_error_sanitization(client):
    with patch("services.postgresql_service.PostgreSQLService.get_system_stats", side_effect=Exception("DynamoDB Access Denied: User admin not authorized")):
        response = client.get("/api/admin/stats")
        assert response.status_code == 500
        json_data = response.get_json()
        assert "error" in json_data
        assert "details" not in json_data
        assert "Access Denied" not in response.get_data(as_text=True)
