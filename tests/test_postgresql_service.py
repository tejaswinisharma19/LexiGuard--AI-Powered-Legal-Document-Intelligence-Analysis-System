import uuid
import pytest
from services.postgresql_service import PostgreSQLService

def test_postgresql_crud_operations():
    service = PostgreSQLService()
    doc_id = f"test_pg_crud_{uuid.uuid4().hex[:8]}"
    test_document = {
        "document_id": doc_id,
        "filename": "legal_agreement.pdf",
        "file_size_bytes": 5208,
        "page_count": 2,
        "upload_timestamp": "2026-09-17T11:00:00",
        "file_path": f"documents/{doc_id}.pdf",
        "processing_status": "processed"
    }

    service.save_document(test_document)
    doc = service.get_document(doc_id)
    assert doc is not None
    assert doc["filename"] == "legal_agreement.pdf"

    service.delete_document(doc_id)
    assert service.get_document(doc_id) is None
