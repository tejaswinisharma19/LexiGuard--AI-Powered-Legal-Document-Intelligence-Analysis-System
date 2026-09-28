import uuid
from app import app, dynamodb_service
from services.local_storage_service import LocalStorageService

def test_delete_document_api():
    doc_id = f"test_api_del_{uuid.uuid4().hex[:8]}"
    object_key = f"documents/{doc_id}.pdf"
    storage_service = LocalStorageService()
    test_file = "test_api_delete.pdf"

    with open(test_file, "w", encoding="utf-8") as file:
        file.write("LexiGuard API deletion test.")

    storage_service.upload_file(test_file, object_key)

    dynamodb_service.save_document({
        "document_id": doc_id,
        "user_id": "test@example.com",
        "filename": "test_api_delete.pdf",
        "file_size_bytes": 32,
        "page_count": 1,
        "upload_timestamp": "2026-09-18T12:00:00+05:30",
        "s3_object_key": object_key,
        "content_hash": "test-api-delete-hash",
        "processing_status": "processed"
    })

    try:
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["user_id"] = "test@example.com"

        response = client.delete(f"/api/documents/{doc_id}")
        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data["message"] == "Document deleted successfully."
        assert response_data["document_id"] == doc_id
        assert dynamodb_service.get_document(doc_id) is None
        assert not storage_service.file_exists(object_key)
    finally:
        import os
        if os.path.exists(test_file):
            os.remove(test_file)