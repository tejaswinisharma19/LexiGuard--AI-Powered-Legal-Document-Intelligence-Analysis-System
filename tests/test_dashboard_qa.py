import pytest
from unittest.mock import patch, MagicMock
from app import app
import routes.api as api_module

class MockQAGraph:
    def invoke(self, state):
        assert state["user_query"] == "What are the payment terms?"
        assert len(state["chunks"]) > 0
        return {
            "intent": "qa",
            "response": "The monthly payment is ₹75,000 and payment is due within 30 calendar days.",
            "sources": [{"page_number": 1, "chunk_number": 2}]
        }

def test_dashboard_qa_api():
    def mock_get_document(doc_id):
        return {
            "document_id": doc_id,
            "filename": "legal_agreement.pdf",
            "s3_object_key": f"documents/{doc_id}.pdf"
        }

    def mock_download(key, path):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open("test_documents/downloaded_legal_agreement.pdf", "rb") as src:
            data = src.read()
        with open(path, "wb") as dst:
            dst.write(data)

    app.config["SECRET_KEY"] = "test-secret-key"
    client = app.test_client()

    with patch.object(api_module, 'lexiguard_graph', MockQAGraph()), \
         patch.object(api_module.dynamodb_service, 'get_document', side_effect=mock_get_document), \
         patch.object(api_module.dynamodb_service, 'add_analysis_history', return_value=True), \
         patch.object(api_module.dynamodb_service, 'add_chat_message', return_value=True), \
         patch.object(api_module.s3_service, 'file_exists', return_value=True), \
         patch.object(api_module.s3_service, 'download_file', side_effect=mock_download):

        with client.session_transaction() as sess:
            sess["user_id"] = "test@example.com"

        response = client.post(
            "/api/analyze",
            json={
                "document_id": "e28d55ce-c219-4cb2-93bf-255f7bb666d7",
                "question": "What are the payment terms?"
            }
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result["document_id"] == "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
        assert result["filename"] == "legal_agreement.pdf"
        assert result["intent"] == "qa"
        assert "₹75,000" in result["response"]
        assert len(result["sources"]) > 0