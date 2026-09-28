import pytest
from unittest.mock import patch
from app import app
import app as app_module
import routes.api as api_module

class MockRiskGraph:
    def invoke(self, state):
        assert state["user_query"] == "Analyze this document for potential risks and clauses requiring review."
        assert len(state["chunks"]) > 0
        return {
            "intent": "risk",
            "response": (
                "Potential Risk 1:\n"
                "Severity: Medium\n"
                "The agreement contains an automatic renewal clause. "
                "The parties should review the renewal period and "
                "non-renewal notice requirement.\n"
                "Source: Page 1, Chunk 2\n\n"
                "Potential Risk 2:\n"
                "Severity: Medium\n"
                "The liability provision contains a contractual "
                "liability cap. The parties should review the cap "
                "and its exclusions.\n"
                "Source: Page 2, Chunk 1\n\n"
                "Potential Risk 3:\n"
                "Severity: Low\n"
                "The termination provision requires advance notice "
                "for termination for convenience.\n"
                "Source: Page 1, Chunk 2\n\n"
                "Note: LexiGuard provides AI-assisted document "
                "analysis and is not a substitute for professional "
                "legal advice."
            ),
            "sources": [
                {"page_number": 1, "chunk_number": 2},
                {"page_number": 2, "chunk_number": 1}
            ]
        }

def test_dashboard_risk_api():
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

    with patch.object(app_module, 'lexiguard_graph', MockRiskGraph()), \
         patch.object(api_module, 'lexiguard_graph', MockRiskGraph()), \
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
                "question": "Analyze this document for potential risks and clauses requiring review."
            }
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result["document_id"] == "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
        assert result["filename"] == "legal_agreement.pdf"
        assert result["intent"] == "risk"
        assert "Potential Risk" in result["response"]
        assert len(result["sources"]) > 0