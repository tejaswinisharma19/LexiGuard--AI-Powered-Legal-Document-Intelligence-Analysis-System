import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.prompts import build_summary_prompt


PDF_PATH = "test_documents/legal_agreement.pdf"


class MockLLM:
    """
    Fake LLM used for testing.

    This prevents the test from making a real
    Gemini API request.
    """

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt):
        self.last_prompt = prompt

        return "MOCK SUMMARY"


def build_document_context():
    """
    Extract and prepare the complete document context.
    """

    pages = extract_text_from_pdf(
        PDF_PATH
    )

    chunks = create_text_chunks(
        pages
    )

    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    return "\n\n".join(
        context_parts
    )


def test_summary_context():
    """
    Verify that the complete document is correctly
    passed to the summary prompt.
    """

    context = build_document_context()

    prompt = build_summary_prompt(
        context
    )

    print("\n" + "=" * 70)
    print("SUMMARY CONTEXT TEST")
    print("=" * 70)

    print("\nDocument Context:")
    print(context)

    print("\nSummary Prompt:")
    print(prompt)

    # Verify important document information exists
    # in the context.
    assert "Northstar Technologies" in context
    assert "BluePeak Solutions" in context
    assert "1 October 2026" in context
    assert "12 months" in context
    assert "₹75,000" in context
    assert "30 calendar days" in context
    assert "30 days" in context
    assert "6 months" in context
    assert "Confidentiality" in context
    assert "Liability" in context
    assert "Pune, Maharashtra" in context

    # Verify the summary instructions exist.
    prompt_lower = prompt.lower()

    assert "document type" in prompt_lower
    assert "parties" in prompt_lower
    assert "effective date" in prompt_lower
    assert "duration" in prompt_lower
    assert "payment terms" in prompt_lower
    assert "termination" in prompt_lower
    assert "renewal" in prompt_lower
    assert "confidentiality" in prompt_lower
    assert "liability" in prompt_lower
    assert "jurisdiction" in prompt_lower
    assert "important obligations" in prompt_lower

    # Verify the missing-information rule.
    assert "Not found in the document." in prompt

    # Verify the legal disclaimer.
    assert (
       "not professional legal advice" in " ".join(prompt.lower().split())
    )

    print(
        "\nPASS: Summary context and instructions "
        "are correctly constructed."
    )


def test_mock_summary_generation():
    """
    Verify that the summary prompt can be passed to
    an LLM without making a real API request.
    """

    context = build_document_context()

    prompt = build_summary_prompt(
        context
    )

    mock_llm = MockLLM()

    response = mock_llm.generate(
        prompt
    )

    assert response == "MOCK SUMMARY"
    assert mock_llm.last_prompt == prompt

    print(
        "\nPASS: Mock summary generation completed "
        "without calling Gemini."
    )


if __name__ == "__main__":
    test_summary_context()
    test_mock_summary_generation()

    print("\n" + "=" * 70)
    print("ALL SUMMARY GROUNDING TESTS PASSED")
    print("=" * 70)