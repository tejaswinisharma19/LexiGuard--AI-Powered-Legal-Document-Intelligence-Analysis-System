import pytest
from app import app
from unittest.mock import patch

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client

def test_comparison_report_pdf_unauthenticated(client):
    response = client.get("/api/reports/comparison/comp_123")
    assert response.status_code == 401
    assert "error" in response.get_json()

def test_comparison_report_pdf_not_found(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_test_123"
        sess["email"] = "user@example.com"

    with patch("app.dynamodb_service.get_comparison_by_id", return_value=None):
        response = client.get("/api/reports/comparison/non_existent_comp")
        assert response.status_code == 404
        assert "error" in response.get_json()

def test_comparison_report_pdf_success(client):
    import io
    with client.session_transaction() as sess:
        sess["user_id"] = "user_test_123"
        sess["email"] = "user@example.com"

    mock_comp = {
        "comparison_id": "comp_123",
        "user_id": "user_test_123",
        "document_a": {"filename": "DocA.pdf"},
        "document_b": {"filename": "DocB.pdf"},
        "response": {"comparison": [{"category": "Term", "document_a": "1 yr", "document_b": "2 yrs", "difference": "Different duration"}]},
        "timestamp": "2026-09-22T10:00:00Z"
    }

    mock_pdf_buffer = io.BytesIO(b"%PDF-1.4 Mock PDF Content")

    with patch("app.dynamodb_service.get_comparison_by_id", return_value=mock_comp), \
         patch("app.dynamodb_service.get_user_by_email", return_value=None), \
         patch("app.generate_comparison_pdf", return_value=mock_pdf_buffer):
        response = client.get("/api/reports/comparison/comp_123")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/pdf"
        assert b"%PDF-1.4" in response.data
