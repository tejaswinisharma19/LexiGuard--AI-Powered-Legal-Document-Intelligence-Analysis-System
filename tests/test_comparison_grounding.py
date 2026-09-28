import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.prompts import build_comparison_prompt


PDF_A_PATH = "test_documents/legal_agreement.pdf"
PDF_B_PATH = "test_documents/legal_agreement_b.pdf"


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

        return (
            "MOCK DOCUMENT COMPARISON"
        )


def build_document_context(pdf_path, document_name):
    """
    Extract text from a PDF and build a page-aware
    context for comparison.
    """

    pages = extract_text_from_pdf(
        pdf_path
    )

    chunks = create_text_chunks(
        pages
    )

    context_parts = []

    for chunk in chunks:
        context_parts.append(
            f"--- {document_name} | "
            f"Page {chunk['page_number']} | "
            f"Chunk {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    return "\n\n".join(
        context_parts
    )


def test_comparison_context():
    """
    Verify that both documents and comparison
    instructions are correctly constructed.
    """

    document_a_context = build_document_context(
        PDF_A_PATH,
        "DOCUMENT A"
    )

    document_b_context = build_document_context(
        PDF_B_PATH,
        "DOCUMENT B"
    )

    combined_context = (
        "DOCUMENT A:\n\n"
        + document_a_context
        + "\n\n"
        + "DOCUMENT B:\n\n"
        + document_b_context
    )

    prompt = build_comparison_prompt(
    document_a_context,
    document_b_context
)

    prompt_lower = prompt.lower()

    print("\n" + "=" * 70)
    print("DOCUMENT COMPARISON CONTEXT TEST")
    print("=" * 70)

    print("\nComparison Prompt:")
    print(prompt)

    # -------------------------------------------------
    # Verify Document A content.
    # -------------------------------------------------

    assert "document a" in prompt_lower

    assert "₹75,000" in prompt
    assert "30 calendar days" in prompt
    assert "30 days" in prompt
    assert "6 months" in prompt

    # -------------------------------------------------
    # Verify Document B content.
    # -------------------------------------------------

    assert "document b" in prompt_lower

    assert "₹90,000" in prompt
    assert "45 days" in prompt
    assert "18 months" in prompt
    assert "12 months" in prompt

    # -------------------------------------------------
    # Verify important comparison categories.
    # -------------------------------------------------

    assert "payment" in prompt_lower
    assert "termination" in prompt_lower
    assert "duration" in prompt_lower
    assert "renewal" in prompt_lower
    assert "liability" in prompt_lower
    assert "confidentiality" in prompt_lower
    assert "obligations" in prompt_lower

    # -------------------------------------------------
    # Verify factual comparison instructions.
    # -------------------------------------------------

    assert "difference" in prompt_lower
    assert "document a" in prompt_lower
    assert "document b" in prompt_lower

    # -------------------------------------------------
    # Verify source references.
    # -------------------------------------------------

    assert "page" in prompt_lower
    assert "section" in prompt_lower

    # -------------------------------------------------
    # Verify that the model is not asked to rank
    # or provide definitive legal conclusions.
    # -------------------------------------------------

    assert "better" in prompt_lower
    assert "worse" in prompt_lower

    assert (
        "legal advice"
        in prompt_lower
    )

    print(
        "\nPASS: Both document contexts are available."
    )

    print(
        "PASS: Required comparison categories are present."
    )

    print(
        "PASS: Source and page references are present."
    )

    print(
        "PASS: Comparison instructions are present."
    )


def test_mock_comparison_generation():
    """
    Verify that the comparison prompt can be passed
    to an LLM without making a real API request.
    """

    document_a_context = build_document_context(
        PDF_A_PATH,
        "DOCUMENT A"
    )

    document_b_context = build_document_context(
        PDF_B_PATH,
        "DOCUMENT B"
    )

    combined_context = (
        "DOCUMENT A:\n\n"
        + document_a_context
        + "\n\n"
        + "DOCUMENT B:\n\n"
        + document_b_context
    )

    prompt = build_comparison_prompt(
    document_a_context,
    document_b_context
)
    mock_llm = MockLLM()

    response = mock_llm.generate(
        prompt
    )

    assert response == (
        "MOCK DOCUMENT COMPARISON"
    )

    assert mock_llm.last_prompt == prompt

    print(
        "\nPASS: Mock comparison generation completed "
        "without calling Gemini."
    )


if __name__ == "__main__":
    test_comparison_context()
    test_mock_comparison_generation()

    print("\n" + "=" * 70)
    print("ALL DOCUMENT COMPARISON GROUNDING TESTS PASSED")
    print("=" * 70)