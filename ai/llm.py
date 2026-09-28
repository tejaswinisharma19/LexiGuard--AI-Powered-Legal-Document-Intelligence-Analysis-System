import os
import requests

from config import Config


class LexiGuardLLM:
    """
    Language model interface for LexiGuard supporting Gemini 3.5 Flash-Lite and local Mock mode.
    """

    def __init__(self, api_key=None, model=None):
        self.provider = (
            os.getenv("LLM_PROVIDER")
            or getattr(Config, "LLM_PROVIDER", "gemini")
        ).lower().strip()

        self.api_key = (
            api_key
            or getattr(Config, "GEMINI_API_KEY", None)
            or os.getenv("GEMINI_API_KEY")
        )
        self.model = (
            model
            or getattr(Config, "GEMINI_MODEL", "gemini-3.5-flash-lite")
            or os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        )

    def get_provider(self):
        """
        Get the active LLM provider (e.g. 'gemini' or 'mock').
        """
        return (
            os.getenv("LLM_PROVIDER")
            or getattr(Config, "LLM_PROVIDER", "gemini")
        ).lower().strip()

    @staticmethod
    def truncate_to_word_limit(text, max_words=50):
        """
        Safely truncate text to a maximum word count.
        """
        if not text or not isinstance(text, str):
            return text
        words = text.strip().split()
        if len(words) <= max_words:
            return text.strip()
        return " ".join(words[:max_words]).rstrip(".,;:") + "..."

    def _generate_mock(self, prompt, max_words=None):
        """
        Generate a deterministic local mock response without calling Gemini or external APIs.
        """
        prompt_lower = prompt.lower() if prompt else ""

        # 1. Comparison prompt check
        if "compare" in prompt_lower or ("document a" in prompt_lower and "document b" in prompt_lower) or "overall_differences" in prompt_lower:
            import json
            mock_comparison = {
                "comparison": [
                    {
                        "category": "Payment Terms",
                        "document_a": "Payment due within 30 days of invoice.",
                        "document_b": "Payment due within 15 days of invoice.",
                        "difference": "Document B has a shorter 15-day payment window.",
                        "source": "Doc A Page 1 · Doc B Page 1"
                    },
                    {
                        "category": "Termination",
                        "document_a": "30 days prior written notice required.",
                        "document_b": "60 days prior written notice required.",
                        "difference": "Document B requires double the notice period.",
                        "source": "Doc A Page 1 · Doc B Page 2"
                    },
                    {
                        "category": "Duration",
                        "document_a": "12-month initial term.",
                        "document_b": "24-month initial term.",
                        "difference": "Document B has a longer initial term.",
                        "source": "Doc A Page 1 · Doc B Page 1"
                    },
                    {
                        "category": "Renewal",
                        "document_a": "Automatic annual renewal.",
                        "document_b": "Manual written renewal required.",
                        "difference": "Document A auto-renews; Document B requires manual opt-in.",
                        "source": "Doc A Page 2 · Doc B Page 2"
                    },
                    {
                        "category": "Liability",
                        "document_a": "Liability capped at total fees paid.",
                        "document_b": "Unlimited liability for breach.",
                        "difference": "Document B exposes parties to unlimited liability.",
                        "source": "Doc A Page 2 · Doc B Page 3"
                    },
                    {
                        "category": "Confidentiality",
                        "document_a": "2-year post-termination obligation.",
                        "document_b": "5-year post-termination obligation.",
                        "difference": "Document B extends confidentiality to 5 years.",
                        "source": "Doc A Page 2 · Doc B Page 2"
                    },
                    {
                        "category": "Obligations",
                        "document_a": "Standard performance obligations.",
                        "document_b": "Enhanced audit compliance obligations.",
                        "difference": "Document B includes additional audit compliance duties.",
                        "source": "Doc A Page 1 · Doc B Page 3"
                    }
                ],
                "overall_differences": "Document B enforces stricter payment terms, longer termination notice, and unlimited liability.",
                "disclaimer": "LexiGuard provides AI-assisted document analysis for informational purposes only."
            }
            return json.dumps(mock_comparison)

        # 2. Summary prompt check
        if "summary" in prompt_lower or "summarize" in prompt_lower or "document type" in prompt_lower:
            text = (
                "Document Summary: 30-day Services Agreement between Party A and Party B. "
                "Effective Date: Jan 2026. Payment: $5,000 monthly within 30 days of invoice. "
                "Termination: 30 days written notice required. Confidentiality: Mutual 2-year obligation. "
                "Liability: Capped at total fees paid. Jurisdiction: Delaware."
            )

        # 3. Risk Analysis prompt check
        elif "risk" in prompt_lower or "concerns" in prompt_lower or "severity" in prompt_lower:
            text = (
                "Potential Risks: 1. High Risk: Section 4 contains an unlimited liability clause for breach. "
                "2. Medium Risk: Auto-renewal occurs unless canceled 60 days prior. "
                "3. Low Risk: Governing law is set to Delaware jurisdiction."
            )

        # 4. Clause Extraction prompt check
        elif "clause extraction" in prompt_lower or "extract" in prompt_lower or ("clause" in prompt_lower and "user question:" not in prompt_lower):
            text = (
                "Clause Extraction: 1. Termination: Section 8 requires 30 days written notice. "
                "2. Payment: Section 3 mandates payment within 30 days of invoice. "
                "3. Confidentiality: Section 6 protects proprietary data for 2 years post-termination."
            )

        # 5. Standard Q&A prompt
        else:
            user_q = prompt_lower
            if "user question:" in prompt_lower:
                user_q = prompt_lower.split("user question:")[1].split("=")[0].strip()

            if "cure" in user_q or "material breach" in user_q:
                text = "Failure to cure a material breach within 15 calendar days allows immediate termination."
            elif "arbitrat" in user_q or "dispute" in user_q or "pune" in user_q:
                text = "Any dispute shall be referred to arbitration in Pune under Indian law."
            elif "monthly" in user_q or "payment" in user_q or "fee" in user_q:
                text = "Payment is due within 30 calendar days of invoice. The monthly service fee is ₹75,000."
            elif "notice" in user_q or "termination" in user_q:
                text = "Termination requires 30 days prior written notice."
            else:
                text = (
                    "Based on the document context: Payment is due within 30 calendar days of invoice. "
                    "Termination requires 30 days prior written notice to the other party."
                )

        if max_words:
            text = self.truncate_to_word_limit(text, max_words)
        return text

    def _generate_gemini(self, prompt, max_words=None):
        """
        Generate content using Gemini 3.5 Flash-Lite via google.genai SDK.
        """
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in your .env file or set LLM_PROVIDER=mock for local testing."
            )

        print(f"GEMINI REQUEST START | model={self.model} | prompt_length={len(prompt or '')}")

        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            result_text = (response.text or "").strip()
            if not result_text:
                raise RuntimeError("Gemini 3.5 Flash-Lite returned an empty response.")
            if max_words:
                result_text = self.truncate_to_word_limit(result_text, max_words)
            return result_text
        except Exception as error:
            error_str = str(error)
            print(f"GEMINI REQUEST FAILED | exception_type={type(error).__name__} | exception_message={error_str}")
            if "429" in error_str or "quota" in error_str.lower() or "resource_exhausted" in error_str.lower():
                raise RuntimeError(
                    "Gemini API free-tier quota is currently exhausted. Switch to mock mode for local testing (set LLM_PROVIDER=mock in .env) or wait for the quota to reset."
                ) from error
            raise RuntimeError(
                f"Error calling Gemini 3.5 Flash-Lite ({self.model}): {error}"
            ) from error

    def generate(self, prompt, max_words=None):
        """
        Generate a response using the active provider (Gemini 3.5 Flash-Lite or local MockLLM).
        """
        provider = self.get_provider()
        if provider == "mock":
            return self._generate_mock(prompt, max_words=max_words)
        else:
            return self._generate_gemini(prompt, max_words=max_words)