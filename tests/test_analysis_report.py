import pytest
import uuid
from app import app, dynamodb_service
from reports.analysis_report import generate_analysis_pdf


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_generate_analysis_pdf():
    """Verify that generate_analysis_pdf builds a non-empty PDF stream."""
    analysis_data = {
        "analysis_type": "summary",
        "question": "Summarize this document",
        "response": "This is a legal document summary containing key terms.",
        "sources": [{"page_number": 1, "chunk_number": 1, "text": "Page 1 sample context"}],
        "timestamp": "2026-09-22T10:00:00Z"
    }
    pdf_buffer = generate_analysis_pdf("test_agreement.pdf", analysis_data)
    pdf_bytes = pdf_buffer.read()
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_download_analysis_report_endpoint_success(client):
    """Test authenticated user downloading analysis PDF report."""
    doc_id = f"DOC_TEST_{uuid.uuid4().hex[:8]}"
    doc_item = {
        "document_id": doc_id,
        "filename": "Test_Doc.pdf",
        "user_id": "testuser@lexiguard.com",
        "analysis_history": [
            {
                "analysis_id": "ANALYSIS_123",
                "analysis_type": "summary",
                "question": "Summarize document",
                "response": "The agreement outlines obligations.",
                "sources": [],
                "user_id": "testuser@lexiguard.com",
                "timestamp": "2026-09-22T10:00:00Z"
            }
        ]
    }
    dynamodb_service.save_document(doc_item)

    with client.session_transaction() as sess:
        sess["user_id"] = "testuser@lexiguard.com"

    response = client.get(f"/api/reports/analysis/{doc_id}")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert b"%PDF" in response.data

    # Cleanup
    dynamodb_service.delete_document(doc_id)


def test_download_analysis_report_forbidden(client):
    """Test that a user cannot download analysis report for another user's document."""
    doc_id = f"DOC_OTHER_{uuid.uuid4().hex[:8]}"
    doc_item = {
        "document_id": doc_id,
        "filename": "Private_Doc.pdf",
        "user_id": "owner@lexiguard.com",
        "analysis_history": [
            {
                "analysis_id": "ANALYSIS_456",
                "response": "Secret details",
                "user_id": "owner@lexiguard.com"
            }
        ]
    }
    dynamodb_service.save_document(doc_item)

    with client.session_transaction() as sess:
        sess["user_id"] = "attacker@lexiguard.com"

    response = client.get(f"/api/reports/analysis/{doc_id}")
    assert response.status_code == 403
    assert b"Forbidden" in response.data

    # Cleanup
    dynamodb_service.delete_document(doc_id)


def test_download_analysis_report_not_found(client):
    """Test 404 response when analysis history does not exist."""
    doc_id = f"DOC_EMPTY_{uuid.uuid4().hex[:8]}"
    doc_item = {
        "document_id": doc_id,
        "filename": "Empty.pdf",
        "user_id": "testuser@lexiguard.com"
    }
    dynamodb_service.save_document(doc_item)

    with client.session_transaction() as sess:
        sess["user_id"] = "testuser@lexiguard.com"

    response = client.get(f"/api/reports/analysis/{doc_id}")
    assert response.status_code == 404
    assert b"No analysis history found" in response.data

    # Cleanup
    dynamodb_service.delete_document(doc_id)
