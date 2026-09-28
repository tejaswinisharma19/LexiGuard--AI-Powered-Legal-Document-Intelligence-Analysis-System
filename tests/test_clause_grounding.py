import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.prompts import build_clause_extraction_prompt


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
        return "MOCK CLAUSE ANALYSIS"


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


def test_clause_context():
    """
    Verify that the document clauses are correctly
    passed to the clause extraction prompt.
    """

    context = build_document_context()

    prompt = build_clause_extraction_prompt(
        context
    )

    print("\n" + "=" * 70)
    print("CLAUSE EXTRACTION CONTEXT TEST")
    print("=" * 70)

    print("\nDocument Context:")
    print(context)

    print("\nClause Extraction Prompt:")
    print(prompt)

    prompt_lower = prompt.lower()

    # Verify actual clauses exist in the context.
    assert "payment terms" in prompt_lower
    assert "termination" in prompt_lower
    assert "automatic renewal" in prompt_lower
    assert "confidentiality" in prompt_lower
    assert "intellectual property" in prompt_lower
    assert "liability" in prompt_lower
    assert "data protection" in prompt_lower
    assert "dispute resolution" in prompt_lower
    assert "governing law" in prompt_lower
    assert "important obligations" in prompt_lower

    # Verify requested clause categories exist
    # in the prompt.
    assert "payment" in prompt_lower
    assert "termination" in prompt_lower
    assert "confidentiality" in prompt_lower
    assert "liability" in prompt_lower
    assert "intellectual property" in prompt_lower
    assert "renewal" in prompt_lower
    assert "jurisdiction" in prompt_lower
    assert "dispute resolution" in prompt_lower
    assert "penalties" in prompt_lower

    # Verify the missing-information rule.
    assert "not found in the document." in prompt_lower

    # Verify source references are required.
    assert "page" in prompt_lower
    assert "section" in prompt_lower

    # Verify legal disclaimer.
    assert (
        "not professional legal advice" in " ".join(prompt.lower().split())
    )

    print(
        "\nPASS: Clause context and instructions "
        "are correctly constructed."
    )


def test_mock_clause_generation():
    """
    Verify that the clause extraction prompt can be
    passed to an LLM without making a real API request.
    """

    context = build_document_context()

    prompt = build_clause_extraction_prompt(
        context
    )

    mock_llm = MockLLM()

    response = mock_llm.generate(
        prompt
    )

    assert response == "MOCK CLAUSE ANALYSIS"
    assert mock_llm.last_prompt == prompt

    print(
        "\nPASS: Mock clause extraction completed "
        "without calling Gemini."
    )


if __name__ == "__main__":
    test_clause_context()
    test_mock_clause_generation()

    print("\n" + "=" * 70)
    print("ALL CLAUSE GROUNDING TESTS PASSED")
    print("=" * 70)