import unittest
import json
from unittest.mock import patch
from app import app
import app as app_module

class MockSummarizerGraph:
    """
    Mock LangGraph workflow for testing Summary, Risk, Clause, and Q&A routing and persistence.
    """
    def invoke(self, state):
        query = state["user_query"].lower()
        if "summarize" in query or "summary" in query:
            return {
                "intent": "summary",
                "response": "This is a 30-day NDA agreement between Party A and Party B. Payment terms: $5,000 monthly.",
                "sources": [{"page_number": 1, "chunk_number": 1}]
            }
        elif "risk" in query:
            return {
                "intent": "risk",
                "response": "Potential Risk: Unlimited liability clause present in Section 4.",
                "sources": [{"page_number": 2, "chunk_number": 3}]
            }
        elif "clause" in query:
            return {
                "intent": "clause",
                "response": "Termination Clause: 30 days written notice required prior to termination.",
                "sources": [{"page_number": 1, "chunk_number": 2}]
            }
        else:
            return {
                "intent": "qa",
                "response": "The monthly payment amount is $5,000.",
                "sources": [{"page_number": 1, "chunk_number": 1}]
            }


class TestAnalysisHistorySummarizer(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        self.client = app.test_client()

        self.mock_docs = {
            "doc-user1": {
                "document_id": "doc-user1",
                "user_id": "user1@lexiguard.com",
                "filename": "legal_agreement.pdf",
                "s3_object_key": "documents/legal_agreement.pdf",
                "analysis_history": [],
                "chat_history": []
            },
            "doc-user2": {
                "document_id": "doc-user2",
                "user_id": "user2@lexiguard.com",
                "filename": "confidential_contract.pdf",
                "s3_object_key": "documents/confidential_contract.pdf",
                "analysis_history": [],
                "chat_history": []
            }
        }

    def login(self, user_email):
        with self.client.session_transaction() as sess:
            sess.clear()
            sess["user_id"] = user_email

    def test_summary_generation_and_history_persistence(self):
        """Verify Summarizer produces output and persists strictly 1 record to Analysis History."""
        def mock_get_document(doc_id):
            return self.mock_docs.get(doc_id)

        def mock_add_analysis_history(doc_id, entry):
            if doc_id in self.mock_docs:
                self.mock_docs[doc_id]["analysis_history"].append(entry)

        with patch.object(app_module.dynamodb_service, 'get_document', side_effect=mock_get_document), \
             patch.object(app_module.dynamodb_service, 'add_analysis_history', side_effect=mock_add_analysis_history), \
             patch.object(app_module.s3_service, 'file_exists', return_value=True), \
             patch.object(app_module.s3_service, 'download_file', return_value=None), \
             patch.object(app_module, 'extract_text_from_pdf', return_value=["Page 1 text"]), \
             patch.object(app_module, 'create_text_chunks', return_value=[{"page_number": 1, "chunk_number": 1, "text": "chunk"}]), \
             patch.object(app_module, 'lexiguard_graph', MockSummarizerGraph()):

            self.login("user1@lexiguard.com")
            res = self.client.post("/api/analyze", json={
                "document_id": "doc-user1",
                "question": "Summarize this legal document"
            })
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data["intent"], "summary")
            self.assertIn("NDA agreement", data["response"])

            doc = self.mock_docs["doc-user1"]
            self.assertEqual(len(doc["analysis_history"]), 1)
            self.assertEqual(doc["analysis_history"][0]["analysis_type"], "summary")
            self.assertEqual(len(doc["chat_history"]), 0)

    def test_qa_exclusion_from_analysis_history(self):
        """Verify Q&A persists strictly to Chat History and is excluded from Analysis History API."""
        def mock_get_document(doc_id):
            return self.mock_docs.get(doc_id)

        def mock_add_analysis_history(doc_id, entry):
            if doc_id in self.mock_docs:
                self.mock_docs[doc_id]["analysis_history"].append(entry)

        def mock_get_analysis_history(doc_id):
            doc = self.mock_docs.get(doc_id)
            return doc.get("analysis_history", []) if doc else []

        def mock_add_chat_message(doc_id, entry):
            if doc_id in self.mock_docs:
                self.mock_docs[doc_id]["chat_history"].append(entry)

        with patch.object(app_module.dynamodb_service, 'get_document', side_effect=mock_get_document), \
             patch.object(app_module.dynamodb_service, 'add_analysis_history', side_effect=mock_add_analysis_history), \
             patch.object(app_module.dynamodb_service, 'get_analysis_history', side_effect=mock_get_analysis_history), \
             patch.object(app_module.dynamodb_service, 'add_chat_message', side_effect=mock_add_chat_message), \
             patch.object(app_module.s3_service, 'file_exists', return_value=True), \
             patch.object(app_module.s3_service, 'download_file', return_value=None), \
             patch.object(app_module, 'extract_text_from_pdf', return_value=["Page 1 text"]), \
             patch.object(app_module, 'create_text_chunks', return_value=[{"page_number": 1, "chunk_number": 1, "text": "chunk"}]), \
             patch.object(app_module, 'lexiguard_graph', MockSummarizerGraph()):

            self.login("user1@lexiguard.com")

            # 1. Trigger Q&A
            res_qa = self.client.post("/api/analyze", json={
                "document_id": "doc-user1",
                "question": "What is the monthly payment amount?"
            })
            self.assertEqual(res_qa.status_code, 200)
            self.assertEqual(res_qa.get_json()["intent"], "qa")

            # 2. Trigger Summary
            res_sum = self.client.post("/api/analyze", json={
                "document_id": "doc-user1",
                "question": "Summarize this legal document"
            })
            self.assertEqual(res_sum.status_code, 200)

            # 3. Check Analysis History endpoint
            res_hist = self.client.get("/api/documents/doc-user1/history")
            self.assertEqual(res_hist.status_code, 200)
            hist_data = res_hist.get_json()
            self.assertEqual(hist_data["total_analyses"], 1)
            self.assertEqual(hist_data["history"][0]["analysis_type"], "summary")

    def test_unauthorized_analysis_history_access(self):
        """Verify user2 cannot read user1's analysis history."""
        def mock_get_document(doc_id):
            return self.mock_docs.get(doc_id)

        with patch.object(app_module.dynamodb_service, 'get_document', side_effect=mock_get_document):
            self.login("user2@lexiguard.com")
            res = self.client.get("/api/documents/doc-user1/history")
            self.assertEqual(res.status_code, 403)
