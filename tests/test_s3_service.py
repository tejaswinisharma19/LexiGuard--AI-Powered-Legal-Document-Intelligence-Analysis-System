import os
import unittest
from services.local_storage_service import LocalStorageService


class TestLocalStorageService(unittest.TestCase):
    def setUp(self):
        self.service = LocalStorageService(upload_folder="uploads")
        self.test_src = "test_local_storage_tmp.txt"
        with open(self.test_src, "w", encoding="utf-8") as f:
            f.write("Local storage test content")

    def tearDown(self):
        if os.path.exists(self.test_src):
            os.remove(self.test_src)
        self.service.delete_file("documents/test_local_file.pdf")

    def test_upload_and_exists(self):
        result = self.service.upload_file(self.test_src, "documents/test_local_file.pdf")
        self.assertEqual(result["bucket"], "local")
        self.assertEqual(result["object_key"], "documents/test_local_file.pdf")
        self.assertTrue(self.service.file_exists("documents/test_local_file.pdf"))

    def test_delete(self):
        self.service.upload_file(self.test_src, "documents/test_local_file.pdf")
        self.service.delete_file("documents/test_local_file.pdf")
        self.assertFalse(self.service.file_exists("documents/test_local_file.pdf"))


if __name__ == "__main__":
    unittest.main()
