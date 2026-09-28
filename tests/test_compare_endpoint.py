from app import app
import app as app_module
from unittest.mock import patch, MagicMock

DOCUMENT_A_ID = "e28d55ce-c219-4cb2-93bf-255f7bb666d7"
DOCUMENT_B_ID = "2253444b-4e61-41ab-8c18-9874d10dbcff"

class MockComparisonGraph:
    """Mock LangGraph workflow for testing the comparison API without calling Gemini."""
    def invoke(self, state):
        assert "Northstar" in state["document_a_context"]
        assert len(state["document_a_chunks"]) > 0
        assert "BluePeak" in state["document_b_context"]
        assert len(state["document_b_chunks"]) > 0

        return {
            "intent": "comparison",
            "response": {
                "comparison": [
                    {
                        "category": "Payment Terms",
                        "document_a": "₹75,000 per month, payable within 30 calendar days.",
                        "document_b": "₹90,000 per month, payable within 45 calendar days.",
                        "difference": "The monthly fee and payment period differ.",
                        "source": "Document A Page 1; Document B Page 1"
                    },
                    {
                        "category": "Termination",
                        "document_a": "30 days' notice.",
                        "document_b": "60 days' notice.",
                        "difference": "The notice periods differ.",
                        "source": "Document A Page 1; Document B Page 1"
                    },
                    {
                        "category": "Duration",
                        "document_a": "12 months.",
                        "document_b": "18 months.",
                        "difference": "The contract durations differ.",
                        "source": "Document A Page 1; Document B Page 1"
                    }
                ],
                "overall_differences": "The documents differ in payment, termination, and duration terms.",
                "disclaimer": "LexiGuard provides AI-assisted document analysis and is not a substitute for professional legal advice."
            },
            "sources": [
                {"document": "A", "page_number": 1, "chunk_number": 2},
                {"document": "B", "page_number": 1, "chunk_number": 2}
            ]
        }


def test_compare_endpoint():
    mock_graph = MockComparisonGraph()
    
    def mock_get_document(doc_id):
        return {
            "document_id": doc_id,
            "filename": "legal_agreement.pdf" if doc_id == DOCUMENT_A_ID else "legal_agreement_b.pdf",
            "s3_object_key": f"documents/{doc_id}.pdf"
        }

    def mock_download(key, path):
        import os
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open("test_documents/downloaded_legal_agreement.pdf", "rb") as src:
            data = src.read()
        with open(path, "wb") as dst:
            dst.write(data)

    with patch.object(app_module, "lexiguard_graph", mock_graph), \
         patch("routes.api.dynamodb_service.get_document", side_effect=mock_get_document), \
         patch("routes.api.dynamodb_service.add_comparison_history"), \
         patch.object(app_module.s3_service, "file_exists", return_value=True), \
         patch.object(app_module.s3_service, "download_file", side_effect=mock_download):

        app.config["SECRET_KEY"] = "test-secret-key"
        client = app.test_client()
        client.get("/login")
        with client.session_transaction() as sess:
            sess["user_id"] = "test@example.com"

        response = client.post(
            "/api/compare",
            json={
                "document_a_id": DOCUMENT_A_ID,
                "document_b_id": DOCUMENT_B_ID
            }
        )

        assert response.status_code == 200
        result = response.get_json()

        assert result["document_a"]["document_id"] == DOCUMENT_A_ID
        assert result["document_a"]["filename"] == "legal_agreement.pdf"
        assert result["document_b"]["document_id"] == DOCUMENT_B_ID
        assert result["document_b"]["filename"] == "legal_agreement_b.pdf"
        assert result["intent"] == "comparison"

        comparison = result["response"]
        assert isinstance(comparison, dict)
        assert "comparison" in comparison
        assert isinstance(comparison["comparison"], list)

        categories = [item["category"] for item in comparison["comparison"]]
        assert "Payment Terms" in categories
        assert "Termination" in categories
        assert "Duration" in categories

        payment_comparison = next(item for item in comparison["comparison"] if item["category"] == "Payment Terms")
        assert "₹75,000" in payment_comparison["document_a"]
        assert "₹90,000" in payment_comparison["document_b"]

        sources = result["sources"]
        assert len(sources) > 0
        document_a_sources = [s for s in sources if s["document"] == "A"]
        document_b_sources = [s for s in sources if s["document"] == "B"]
        assert len(document_a_sources) > 0
        assert len(document_b_sources) > 0

        for source in sources:
            assert "page_number" in source
            assert "chunk_number" in source