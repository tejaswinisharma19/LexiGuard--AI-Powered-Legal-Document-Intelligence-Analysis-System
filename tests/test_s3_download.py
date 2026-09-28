import os
import pytest
from services.local_storage_service import LocalStorageService


def test_storage_download_standalone():
    storage = LocalStorageService(upload_folder="uploads")
    test_src = "test_download_src.txt"
    with open(test_src, "w", encoding="utf-8") as f:
        f.write("Local storage download test content")

    storage.upload_file(test_src, "documents/test_dl.txt")
    dest = "test_download_dest.txt"
    try:
        res = storage.download_file("documents/test_dl.txt", dest)
        assert res == dest
        assert os.path.exists(dest)
    finally:
        storage.delete_file("documents/test_dl.txt")
        if os.path.exists(test_src):
            os.remove(test_src)
        if os.path.exists(dest):
            os.remove(dest)