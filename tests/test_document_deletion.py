import os
import uuid
import pytest
from app import dynamodb_service
from services.local_storage_service import LocalStorageService

def test_dynamodb_delete():
    doc_id = f"test_del_{uuid.uuid4().hex[:8]}"
    test_document = {
        "document_id": doc_id,
        "filename": "test_delete.pdf",
        "file_path": f"documents/{doc_id}.pdf"
    }

    dynamodb_service.save_document(test_document)
    document = dynamodb_service.get_document(doc_id)
    assert document is not None

    dynamodb_service.delete_document(doc_id)
    deleted_document = dynamodb_service.get_document(doc_id)
    assert deleted_document is None

def test_local_storage_delete():
    storage_service = LocalStorageService()
    object_key = f"documents/test_delete_service_{uuid.uuid4().hex[:8]}.pdf"
    test_file_path = "test_delete_service.pdf"

    with open(test_file_path, "w", encoding="utf-8") as file:
        file.write("LexiGuard local storage deletion test.")

    storage_service.upload_file(test_file_path, object_key)
    assert storage_service.file_exists(object_key)

    storage_service.delete_file(object_key)
    assert not storage_service.file_exists(object_key)

    if os.path.exists(test_file_path):
        os.remove(test_file_path)