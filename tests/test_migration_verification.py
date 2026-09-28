import io
import os
import sys
import unittest
from datetime import datetime, timezone

# Ensure root in sys.path
sys.path.insert(0, os.path.abspath("."))

from app import app
from extensions import local_storage_service, postgresql_service


class TestMigrationVerification(unittest.TestCase):
    """
    Verification test suite covering all 12 checks required for
    PostgreSQL and Local File Storage migration.
    """

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key-migration"
        cls.client = app.test_client()

        cls.test_email = "testmigrator@example.com"
        cls.test_pass = "SecurePass123!"
        cls.test_name = "Migrator User"

        # Clean any preexisting test user
        with postgresql_service._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s", (cls.test_email,))

    def test_01_registration(self):
        """Check 5: Registration — create user and verify in PostgreSQL"""
        res = self.client.post("/register", data={
            "full_name": self.test_name,
            "email": self.test_email,
            "password": self.test_pass,
            "confirm_password": self.test_pass
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)

        # Verify user exists in PostgreSQL
        user = postgresql_service.get_user_by_email(self.test_email)
        self.assertIsNotNone(user)
        self.assertEqual(user["email"], self.test_email)
        self.assertEqual(user["full_name"], self.test_name)
        self.assertEqual(user["role"], "user")
        self.assertEqual(user["status"], "active")
        print(" -> Check 5 PASSED: Registration verified in PostgreSQL")

    def test_02_login(self):
        """Check 6: Login — verify session and password check"""
        with self.client.session_transaction() as sess:
            sess.clear()

        res = self.client.post("/login", data={
            "email": self.test_email,
            "password": self.test_pass
        }, follow_redirects=False)

        self.assertEqual(res.status_code, 302)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user_id"), self.test_email)
            self.assertEqual(sess.get("user_name"), self.test_name)
            self.assertFalse(sess.get("is_admin"))

        print(" -> Check 6 PASSED: Login and session verified")

    def test_03_pdf_upload_and_list(self):
        """Check 7 & 8: PDF upload and Document list"""
        # Create a valid minimal PDF in memory
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 100), "LexiGuard Confidential Legal Agreement\nSection 1: General Provisions.")
        pdf_bytes = doc.tobytes()
        doc.close()

        # Login session
        with self.client.session_transaction() as sess:
            sess["user_id"] = self.test_email
            sess["user_name"] = self.test_name

        data = {
            "file": (io.BytesIO(pdf_bytes), "sample_migration_test.pdf")
        }
        res = self.client.post(
            "/api/upload",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(res.status_code, 201)
        res_json = res.get_json()
        self.assertIn("document", res_json)
        doc_meta = res_json["document"]
        doc_id = doc_meta["document_id"]
        self.__class__.created_doc_id = doc_id

        # Verify PDF exists in local storage
        storage_key = doc_meta.get("file_path") or doc_meta.get("s3_object_key")
        self.assertTrue(local_storage_service.file_exists(storage_key))

        # Verify document exists in PostgreSQL
        pg_doc = postgresql_service.get_document(doc_id)
        self.assertIsNotNone(pg_doc)
        self.assertEqual(pg_doc["filename"], "sample_migration_test.pdf")
        self.assertEqual(pg_doc["user_id"], self.test_email)
        print(" -> Check 7 PASSED: PDF upload saved to local storage and PostgreSQL")

        # Check 8: List documents API
        res_list = self.client.get("/api/documents")
        self.assertEqual(res_list.status_code, 200)
        list_json = res_list.get_json()
        doc_ids = [d["document_id"] for d in list_json.get("documents", [])]
        self.assertIn(doc_id, doc_ids)
        print(" -> Check 8 PASSED: Uploaded document appears in document list API")

    def test_04_analysis_and_history(self):
        """Check 9 & 10: Analysis workflow and history persistence"""
        doc_id = getattr(self.__class__, "created_doc_id", None)
        self.assertIsNotNone(doc_id)

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.test_email
            sess["user_name"] = self.test_name

        # Run analysis (question / summary)
        res_analyze = self.client.post("/api/analyze", json={
            "document_id": doc_id,
            "question": "Summarize this document"
        })
        self.assertEqual(res_analyze.status_code, 200)
        ana_json = res_analyze.get_json()
        self.assertIn("response", ana_json)
        print(" -> Check 9 PASSED: Analysis workflow completed successfully")

        # Check 10: History verification
        res_hist = self.client.get(f"/api/documents/{doc_id}/history")
        self.assertEqual(res_hist.status_code, 200)
        hist_json = res_hist.get_json()
        self.assertGreaterEqual(len(hist_json.get("history", [])), 1)

        # Append chat message directly to test chat history
        chat_entry = {
            "question": "Followup question?",
            "answer": "Test answer.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        postgresql_service.add_chat_message(doc_id, chat_entry)
        chat_hist = postgresql_service.get_chat_history(doc_id)
        self.assertEqual(len(chat_hist), 1)

        # Comparison history test
        comp_entry = {
            "comparison_id": "test-comp-1",
            "document_a": {"document_id": doc_id, "filename": "sample_migration_test.pdf"},
            "document_b": {"document_id": doc_id, "filename": "sample_migration_test.pdf"},
            "user_id": self.test_email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        postgresql_service.add_comparison_history(doc_id, comp_entry)
        comp_hist = postgresql_service.get_comparison_history_for_user(self.test_email)
        self.assertGreaterEqual(len(comp_hist), 1)

        print(" -> Check 10 PASSED: Analysis, chat, and comparison history verified")

    def test_05_admin_portal(self):
        """Check 12: Admin dashboard and statistics"""
        admin_email = "lexiguard662@gmail.com"

        with self.client.session_transaction() as sess:
            sess["user_id"] = admin_email
            sess["user_name"] = "Admin"
            sess["is_admin"] = True

        # Test admin stats API
        res_stats = self.client.get("/api/admin/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()
        self.assertGreaterEqual(stats["total_users"], 2)  # admin + test user
        self.assertGreaterEqual(stats["total_documents"], 1)

        # Test admin users API
        res_users = self.client.get("/api/admin/users")
        self.assertEqual(res_users.status_code, 200)
        users = res_users.get_json()
        emails = [u["email"] for u in users]
        self.assertIn(admin_email, emails)
        self.assertIn(self.test_email, emails)

        # Test admin documents API
        res_docs = self.client.get("/api/admin/documents")
        self.assertEqual(res_docs.status_code, 200)

        # Test admin activity APIs
        res_ai = self.client.get("/api/admin/ai-activity")
        self.assertEqual(res_ai.status_code, 200)

        res_comps = self.client.get("/api/admin/comparisons")
        self.assertEqual(res_comps.status_code, 200)

        print(" -> Check 12 PASSED: Admin statistics, directories, and activity verified")

    def test_06_delete_document(self):
        """Check 11: Delete document — verify PostgreSQL record AND local PDF removed"""
        doc_id = getattr(self.__class__, "created_doc_id", None)
        self.assertIsNotNone(doc_id)

        pg_doc = postgresql_service.get_document(doc_id)
        storage_key = pg_doc.get("file_path") or pg_doc.get("s3_object_key")
        self.assertTrue(local_storage_service.file_exists(storage_key))

        with self.client.session_transaction() as sess:
            sess["user_id"] = self.test_email
            sess["user_name"] = self.test_name

        res_del = self.client.delete(f"/api/documents/{doc_id}")
        self.assertEqual(res_del.status_code, 200)

        # Verify PostgreSQL record removed
        self.assertIsNone(postgresql_service.get_document(doc_id))

        # Verify local PDF removed
        self.assertFalse(local_storage_service.file_exists(storage_key))

        print(" -> Check 11 PASSED: Document record and local PDF both deleted cleanly")

    @classmethod
    def tearDownClass(cls):
        # Cleanup test user
        with postgresql_service._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = %s", (cls.test_email,))


if __name__ == "__main__":
    unittest.main()
