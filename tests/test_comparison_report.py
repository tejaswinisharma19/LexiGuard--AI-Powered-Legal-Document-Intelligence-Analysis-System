import pytest
import uuid
from app import app, dynamodb_service
from reports.comparison_report import generate_comparison_pdf


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_generate_comparison_pdf():
    """Verify that generate_comparison_pdf builds a non-empty PDF stream."""
    comparison_data = {
        "comparison_id": "COMP_123",
        "document_a": {"document_id": "DOC_A", "filename": "Agreement_A.pdf"},
        "document_b": {"document_id": "DOC_B", "filename": "Agreement_B.pdf"},
        "response": "Document A has 30 days notice. Document B has 60 days notice.",
        "sources": [{"document": "Document A", "page_number": 2, "text": "Notice clause"}],
        "timestamp": "2026-09-22T11:00:00Z"
    }
    pdf_buffer = generate_comparison_pdf(comparison_data)
    pdf_bytes = pdf_buffer.read()
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


def test_download_comparison_report_endpoint_success(client):
    """Test authenticated user downloading comparison PDF report."""
    comp_id = f"COMP_TEST_{uuid.uuid4().hex[:8]}"
    doc_id = f"DOC_COMP_{uuid.uuid4().hex[:8]}"
    
    comp_entry = {
        "comparison_id": comp_id,
        "user_id": "testuser@lexiguard.com",
        "document_a": {"document_id": doc_id, "filename": "DocA.pdf"},
        "document_b": {"document_id": "DOC_B", "filename": "DocB.pdf"},
        "response": "Payment terms differ.",
        "sources": [],
        "timestamp": "2026-09-22T11:00:00Z"
    }

    doc_item = {
        "document_id": doc_id,
        "filename": "DocA.pdf",
        "user_id": "testuser@lexiguard.com",
        "comparison_history": [comp_entry]
    }
    dynamodb_service.save_document(doc_item)

    with client.session_transaction() as sess:
        sess["user_id"] = "testuser@lexiguard.com"

    response = client.get(f"/api/reports/comparison/{comp_id}")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert b"%PDF" in response.data

    # Cleanup
    dynamodb_service.delete_document(doc_id)


def test_download_comparison_report_forbidden(client):
    """Test that unauthorized user cannot download another user's comparison report."""
    comp_id = f"COMP_PRIV_{uuid.uuid4().hex[:8]}"
    doc_id = f"DOC_PRIV_{uuid.uuid4().hex[:8]}"

    comp_entry = {
        "comparison_id": comp_id,
        "user_id": "owner@lexiguard.com",
        "document_a": {"document_id": doc_id, "filename": "OwnerA.pdf"},
        "document_b": {"document_id": "DOC_B", "filename": "OwnerB.pdf"},
        "response": "Private comparison result.",
        "timestamp": "2026-09-22T11:00:00Z"
    }

    doc_item = {
        "document_id": doc_id,
        "filename": "OwnerA.pdf",
        "user_id": "owner@lexiguard.com",
        "comparison_history": [comp_entry]
    }
    dynamodb_service.save_document(doc_item)

    with client.session_transaction() as sess:
        sess["user_id"] = "attacker@lexiguard.com"

    response = client.get(f"/api/reports/comparison/{comp_id}")
    assert response.status_code == 403
    assert b"Forbidden" in response.data

    # Cleanup
    dynamodb_service.delete_document(doc_id)


def test_download_comparison_report_not_found(client):
    """Test 404 response when comparison record does not exist."""
    with client.session_transaction() as sess:
        sess["user_id"] = "testuser@lexiguard.com"

    response = client.get("/api/reports/comparison/NON_EXISTENT_ID")
    assert response.status_code == 404
    assert b"Comparison record not found" in response.data
