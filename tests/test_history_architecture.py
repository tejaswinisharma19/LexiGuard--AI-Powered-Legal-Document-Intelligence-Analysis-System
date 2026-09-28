import unittest
import uuid
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash

from app import app, dynamodb_service
from config import Config


class TestHistoryArchitecture(unittest.TestCase):
    """
    Automated integration tests for LexiGuard history separation:
    - Chat History (Q&A only)
    - Analysis History (Summary, Risk, Clause Extraction only)
    - Comparison History (Structured side-by-side comparison across 7 categories)
    - User ownership & privacy isolation
    """

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.dynamodb_service = dynamodb_service

        self.user_a_email = "history.usera@example.com"
        self.user_b_email = "history.userb@example.com"
        self.password = "SecurePassword123!"

        # Create User A
        self.dynamodb_service.save_user({
            "email": self.user_a_email,
            "password_hash": generate_password_hash(self.password),
            "full_name": "History User A"
        })

        # Create User B
        self.dynamodb_service.save_user({
            "email": self.user_b_email,
            "password_hash": generate_password_hash(self.password),
            "full_name": "History User B"
        })

        # Create Document A for User A
        self.doc_a_id = f"test_doc_a_{uuid.uuid4().hex[:8]}"
        self.doc_a = {
            "document_id": self.doc_a_id,
            "user_id": self.user_a_email,
            "filename": "agreement_a.pdf",
            "file_size_bytes": 1024,
            "page_count": 2,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "s3_object_key": f"documents/{self.doc_a_id}.pdf",
            "processing_status": "processed"
        }
        self.dynamodb_service.save_document(self.doc_a)

        # Create Document B for User A
        self.doc_b_id = f"test_doc_b_{uuid.uuid4().hex[:8]}"
        self.doc_b = {
            "document_id": self.doc_b_id,
            "user_id": self.user_a_email,
            "filename": "agreement_b.pdf",
            "file_size_bytes": 2048,
            "page_count": 3,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "s3_object_key": f"documents/{self.doc_b_id}.pdf",
            "processing_status": "processed"
        }
        self.dynamodb_service.save_document(self.doc_b)

        # Create Document C for User B
        self.doc_c_id = f"test_doc_c_{uuid.uuid4().hex[:8]}"
        self.doc_c = {
            "document_id": self.doc_c_id,
            "user_id": self.user_b_email,
            "filename": "agreement_c_user_b.pdf",
            "file_size_bytes": 3072,
            "page_count": 4,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "s3_object_key": f"documents/{self.doc_c_id}.pdf",
            "processing_status": "processed"
        }
        self.dynamodb_service.save_document(self.doc_c)

    def tearDown(self):
        for doc_id in [self.doc_a_id, self.doc_b_id, self.doc_c_id]:
            try:
                self.dynamodb_service.delete_document(doc_id)
            except Exception:
                pass

        for email in [self.user_a_email, self.user_b_email]:
            try:
                self.dynamodb_service.table.delete_item(
                    Key={"document_id": f"USER#{email}"}
                )
            except Exception:
                pass

    def test_unauthenticated_history_protection(self):
        """Unauthenticated requests to history routes must return 302 or 401."""
        res_page = self.client.get("/comparison-history")
        self.assertEqual(res_page.status_code, 302)
        self.assertIn("/login", res_page.location)

        res_api = self.client.get("/api/comparison-history")
        self.assertEqual(res_api.status_code, 401)

    def test_chat_and_analysis_history_isolation(self):
        """Verify Q&A goes ONLY to chat_history and Risk/Summary goes ONLY to analysis_history."""
        # Login as User A
        self.client.post("/login", data={"email": self.user_a_email, "password": self.password})

        # Add a Q&A chat message directly or via endpoint logic
        chat_entry = {
            "message_id": str(uuid.uuid4()),
            "history_type": "chat",
            "user_message": "What is the termination notice period?",
            "assistant_response": "The notice period is 30 days.",
            "sources": [{"page_number": 1, "chunk_number": 2}],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.dynamodb_service.add_chat_message(self.doc_a_id, chat_entry)

        # Add a Risk Analysis entry
        risk_entry = {
            "analysis_id": str(uuid.uuid4()),
            "history_type": "analysis",
            "analysis_type": "risk",
            "question": "Analyze risks",
            "response": "Auto-renewal clause risk identified.",
            "sources": [{"page_number": 1, "chunk_number": 1}],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.dynamodb_service.add_analysis_history(self.doc_a_id, risk_entry)

        # 1. Check Chat History API
        res_chat = self.client.get(f"/api/documents/{self.doc_a_id}/chat-history")
        self.assertEqual(res_chat.status_code, 200)
        chat_data = res_chat.get_json().get("chat_history", [])
        self.assertTrue(any(c.get("user_message") == "What is the termination notice period?" for c in chat_data))
        # Ensure Risk analysis is NOT in chat history
        self.assertFalse(any(c.get("analysis_type") == "risk" for c in chat_data))

        # 2. Check Analysis History API
        res_analysis = self.client.get(f"/api/documents/{self.doc_a_id}/history")
        self.assertEqual(res_analysis.status_code, 200)
        analysis_data = res_analysis.get_json().get("history", [])
        self.assertTrue(any(a.get("analysis_type") == "risk" for a in analysis_data))
        # Ensure Q&A question is NOT in analysis history
        self.assertFalse(any(a.get("question") == "What is the termination notice period?" for a in analysis_data))

        print("PASS: Chat History and Analysis History strict isolation verified!")

    def test_comparison_history_persistence_and_categories(self):
        """Verify comparison history persists correctly and preserves all 7 categories."""
        self.client.post("/login", data={"email": self.user_a_email, "password": self.password})

        comp_entry = {
            "comparison_id": str(uuid.uuid4()),
            "user_id": self.user_a_email,
            "history_type": "comparison",
            "document_a": {"document_id": self.doc_a_id, "filename": "agreement_a.pdf"},
            "document_b": {"document_id": self.doc_b_id, "filename": "agreement_b.pdf"},
            "response": {
                "comparison": [
                    {"category": "Payment Terms", "document_a": "₹75,000", "document_b": "₹90,000", "difference": "₹15,000 diff"},
                    {"category": "Termination", "document_a": "30 days", "document_b": "60 days", "difference": "30 days diff"},
                    {"category": "Duration", "document_a": "12 months", "document_b": "24 months", "difference": "12 months diff"},
                    {"category": "Renewal", "document_a": "Automatic", "document_b": "Manual", "difference": "Renewal type diff"},
                    {"category": "Liability", "document_a": "6 months fees", "document_b": "12 months fees", "difference": "Cap diff"},
                    {"category": "Confidentiality", "document_a": "Standard", "document_b": "Strict", "difference": "Strictness diff"},
                    {"category": "Obligations", "document_a": "SOW based", "document_b": "Fixed deliverable", "difference": "Scope diff"}
                ]
            },
            "sources": [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        self.dynamodb_service.add_comparison_history(self.doc_a_id, comp_entry)

        # Query GET /api/comparison-history
        res_comp = self.client.get("/api/comparison-history")
        self.assertEqual(res_comp.status_code, 200)
        comp_list = res_comp.get_json().get("comparison_history", [])
        self.assertTrue(len(comp_list) > 0)
        retrieved_comp = comp_list[0]

        # Verify all 7 categories preserved
        categories = [item["category"] for item in retrieved_comp["response"]["comparison"]]
        expected_cats = ["Payment Terms", "Termination", "Duration", "Renewal", "Liability", "Confidentiality", "Obligations"]
        for cat in expected_cats:
            self.assertIn(cat, categories)

        print("PASS: Comparison History persistence and all 7 categories verified!")

    def test_user_ownership_privacy(self):
        """User B must NOT see User A's comparison or document history."""
        # 1. Add comparison for User A
        comp_entry = {
            "comparison_id": f"comp_{uuid.uuid4().hex[:8]}",
            "user_id": self.user_a_email,
            "history_type": "comparison",
            "document_a": {"document_id": self.doc_a_id, "filename": "agreement_a.pdf"},
            "document_b": {"document_id": self.doc_b_id, "filename": "agreement_b.pdf"},
            "response": {"comparison": []},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.dynamodb_service.add_comparison_history(self.doc_a_id, comp_entry)

        # 2. Login as User B
        self.client.get("/logout")
        self.client.post("/login", data={"email": self.user_b_email, "password": self.password})

        # 3. User B calls GET /api/comparison-history
        res_user_b_comp = self.client.get("/api/comparison-history")
        self.assertEqual(res_user_b_comp.status_code, 200)
        user_b_list = res_user_b_comp.get_json().get("comparison_history", [])
        self.assertFalse(any(c.get("user_id") == self.user_a_email for c in user_b_list))

        # 4. User B attempts GET /api/documents/<User_A_doc_id>/comparison-history -> 403 Forbidden
        res_forbidden = self.client.get(f"/api/documents/{self.doc_a_id}/comparison-history")
        self.assertEqual(res_forbidden.status_code, 403)

        print("PASS: User ownership and history privacy isolation verified!")


if __name__ == "__main__":
    unittest.main()
