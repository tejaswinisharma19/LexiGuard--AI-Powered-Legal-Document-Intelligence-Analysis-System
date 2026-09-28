import unittest
import os
import io
import sys
from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever
from ai.rag import LexiGuardRAG
from ai.llm import LexiGuardLLM
from ai.cache import global_answer_cache


class TestRAGCacheAndNegativeRetrieval(unittest.TestCase):
    def setUp(self):
        os.environ["LLM_PROVIDER"] = "mock"
        global_answer_cache.clear()

        # Sample test document chunks
        self.chunks = [
            {
                "page_number": 1,
                "chunk_number": 1,
                "text": "This Services Agreement is entered into by Party A and Party B. Payment terms require payment within 30 calendar days of invoice date."
            },
            {
                "page_number": 1,
                "chunk_number": 2,
                "text": "Termination clause: Either party may terminate this agreement by providing 30 days prior written notice."
            }
        ]

        self.embedding_model = LexiGuardEmbeddings()
        self.retriever = LexiGuardRetriever(self.embedding_model)
        self.retriever.add_chunks(self.chunks)
        self.llm = LexiGuardLLM()
        self.rag = LexiGuardRAG(self.retriever, self.llm)

    def test_negative_retrieval_no_llm_call(self):
        """Verify queries with no matching context return 'Not found in the document.' with llm_called=false."""
        captured_output = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured_output
            res = self.rag.ask("What is the CEO's annual salary?", document_id="doc-101", content_hash="hash-101")
        finally:
            sys.stdout = old_stdout

        log = captured_output.getvalue()
        self.assertEqual(res["answer"], "Not found in the document.")
        self.assertEqual(len(res["sources"]), 0)
        self.assertIn("cache=false", log)
        self.assertIn("llm_called=false", log)

    def test_positive_retrieval_and_answer_caching(self):
        """Verify positive query calls LLM once, and subsequent identical query returns cached answer."""
        # 1. First invocation: LLM called
        captured_1 = io.StringIO()
        old_stdout = sys.stdout
        try:
            sys.stdout = captured_1
            res_1 = self.rag.ask("What is the termination notice period?", document_id="doc-101", content_hash="hash-101")
        finally:
            sys.stdout = old_stdout

        log_1 = captured_1.getvalue()
        self.assertNotEqual(res_1["answer"], "Not found in the document.")
        self.assertIn("llm_called=true", log_1)

        # 2. Second invocation with identical query & document: Cache hit, llm_called=false
        captured_2 = io.StringIO()
        try:
            sys.stdout = captured_2
            res_2 = self.rag.ask("What is the termination notice period?", document_id="doc-101", content_hash="hash-101")
        finally:
            sys.stdout = old_stdout

        log_2 = captured_2.getvalue()
        self.assertEqual(res_1["answer"], res_2["answer"])
        self.assertIn("cache=true", log_2)
        self.assertIn("llm_called=false", log_2)


if __name__ == "__main__":
    unittest.main()
