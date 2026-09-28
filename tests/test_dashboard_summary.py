import pytest
from unittest.mock import patch
from app import app
import app as app_module
import routes.api as api_module

class MockSummaryGraph:
    def invoke(self, state):
        assert state["user_query"] == "Summarize this legal document."
        assert len(state["chunks"]) > 0
        return {
            "intent": "summary",
            "response": (
                "Document Type: Service Agreement\n"
                "Parties: Northstar Technologies Pvt. Ltd. and BluePeak Solutions\n"
                "Effective Date: 1 October 2026\n"
                "Duration: 12 months\n"
                "Payment Terms: ₹75,000 per month, payable within 30 calendar days.\n"
                "Termination: 30 days' notice for convenience.\n"
                "Renewal: Automatic 6-month renewal unless either party provides 30 days' notice.\n"
                "Confidentiality: Confidentiality obligations apply to both parties.\n"
                "Liability: Liability is subject to the contractual cap.\n"
                "Jurisdiction: Pune, India.\n"
                "Important Obligations: Both parties must comply with their contractual obligations."
            ),
            "sources": [
                {"page_number": 1, "chunk_number": 1},
                {"page_number": 1, "chunk_number": 2}
            ]
        }

def test_dashboard_summary_api():
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

    with patch.object(app_module, 'lexiguard_graph', MockSummaryGraph()), \
         patch.object(api_module, 'lexiguard_graph', MockSummaryGraph()), \
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
                "question": "Summarize this legal document."
            }
        )

        assert response.status_code == 200
        result = response.get_json()
        assert result["document_id"] == "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
        assert result["filename"] == "legal_agreement.pdf"
        assert result["intent"] == "summary"
        assert "Service Agreement" in result["response"]
        assert len(result["sources"]) > 0