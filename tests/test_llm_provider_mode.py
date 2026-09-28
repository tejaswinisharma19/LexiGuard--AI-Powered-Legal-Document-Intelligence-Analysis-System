import unittest
import os
import json
from ai.llm import LexiGuardLLM
from config import Config

class TestLLMProviderMode(unittest.TestCase):
    def setUp(self):
        self.original_provider = os.getenv("LLM_PROVIDER")

    def tearDown(self):
        if self.original_provider is not None:
            os.environ["LLM_PROVIDER"] = self.original_provider
        elif "LLM_PROVIDER" in os.environ:
            del os.environ["LLM_PROVIDER"]

    def test_mock_provider_qa(self):
        """Verify LLM_PROVIDER=mock generates deterministic Q&A responses under 50 words without API key."""
        os.environ["LLM_PROVIDER"] = "mock"
        llm = LexiGuardLLM(api_key=None)
        res = llm.generate("What is the payment notice period?", max_words=50)
        self.assertIn("Payment is due", res)
        self.assertLessEqual(len(res.split()), 50)

    def test_mock_provider_summary(self):
        """Verify LLM_PROVIDER=mock generates deterministic Summary under 50 words."""
        os.environ["LLM_PROVIDER"] = "mock"
        llm = LexiGuardLLM(api_key=None)
        res = llm.generate("Create a factual summary of the document", max_words=50)
        self.assertIn("Document Summary:", res)
        self.assertLessEqual(len(res.split()), 50)

    def test_mock_provider_risk(self):
        """Verify LLM_PROVIDER=mock generates deterministic Risk Analysis under 50 words."""
        os.environ["LLM_PROVIDER"] = "mock"
        llm = LexiGuardLLM(api_key=None)
        res = llm.generate("Identify potential risks in this document", max_words=50)
        self.assertIn("Potential Risks:", res)
        self.assertLessEqual(len(res.split()), 50)

    def test_mock_provider_clause(self):
        """Verify LLM_PROVIDER=mock generates deterministic Clause Extraction under 50 words."""
        os.environ["LLM_PROVIDER"] = "mock"
        llm = LexiGuardLLM(api_key=None)
        res = llm.generate("Extract important legal clauses", max_words=50)
        self.assertIn("Clause Extraction:", res)
        self.assertLessEqual(len(res.split()), 50)

    def test_mock_provider_comparison(self):
        """Verify LLM_PROVIDER=mock generates structured 7-category JSON for comparisons."""
        os.environ["LLM_PROVIDER"] = "mock"
        llm = LexiGuardLLM(api_key=None)
        res = llm.generate("Compare Document A and Document B overall_differences")
        data = json.loads(res)
        self.assertIn("comparison", data)
        self.assertEqual(len(data["comparison"]), 7)
        self.assertIn("overall_differences", data)


if __name__ == "__main__":
    unittest.main()
