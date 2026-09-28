import pytest
from app import app
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test_secret_key"
    with app.test_client() as client:
        yield client

def test_chat_history_unauthenticated(client):
    response = client.get("/api/documents/doc_123/chat-history")
    assert response.status_code == 401
    assert "error" in response.get_json()

def test_chat_history_authenticated(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_test_123"
        sess["email"] = "user@example.com"

    mock_doc = {
        "document_id": "doc_123",
        "user_id": "user_test_123",
        "filename": "agreement.pdf",
        "chat_history": [
            {"user_message": "What is the payment term?", "assistant_response": "30 days", "timestamp": "2026-09-22T10:00:00Z"}
        ]
    }

    with patch("app.dynamodb_service.get_document", return_value=mock_doc), \
         patch("app.dynamodb_service.get_chat_history", return_value=mock_doc["chat_history"]):
        response = client.get("/api/documents/doc_123/chat-history")
        assert response.status_code == 200
        data = response.get_json()
        assert "chat_history" in data
        assert len(data["chat_history"]) == 1

def test_chat_analysis_api_structure(client):
    with client.session_transaction() as sess:
        sess["user_id"] = "user_test_123"
        sess["email"] = "user@example.com"

    mock_doc = {
        "document_id": "doc_123",
        "filename": "agreement.pdf",
        "s3_object_key": "docs/agreement.pdf",
        "user_id": "user_test_123"
    }

    mock_graph_result = {
        "intent": "qa",
        "response": "This agreement terminates in 30 days.",
        "sources": [{"page_number": 1, "chunk_number": 1, "score": 0.9}]
    }

    with patch("app.dynamodb_service.get_document", return_value=mock_doc), \
         patch("app.s3_service.file_exists", return_value=True), \
         patch("app.s3_service.download_file"), \
         patch("app.extract_text_from_pdf", return_value=[{"page_number": 1, "text": "Content"}]), \
         patch("app.create_text_chunks", return_value=[]), \
         patch("app.lexiguard_graph.invoke", return_value=mock_graph_result), \
         patch("app.dynamodb_service.add_chat_message"):
        response = client.post("/api/analyze", json={
            "document_id": "doc_123",
            "question": "When does this agreement terminate?"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "response" in data
        assert data["intent"] == "qa"
