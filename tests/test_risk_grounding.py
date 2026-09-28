import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.prompts import build_risk_analysis_prompt


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
        return "MOCK RISK ANALYSIS"


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


def test_risk_context():
    """
    Verify that the document context and risk-analysis
    instructions are correctly constructed.
    """

    context = build_document_context()

    prompt = build_risk_analysis_prompt(
        context
    )

    print("\n" + "=" * 70)
    print("RISK ANALYSIS CONTEXT TEST")
    print("=" * 70)

    print("\nDocument Context:")
    print(context)

    print("\nRisk Analysis Prompt:")
    print(prompt)

    prompt_lower = prompt.lower()

    # Verify important clauses are available.
    assert "termination" in prompt_lower
    assert "payment terms" in prompt_lower
    assert "automatic renewal" in prompt_lower
    assert "confidentiality" in prompt_lower
    assert "intellectual property" in prompt_lower
    assert "liability" in prompt_lower
    assert "data protection" in prompt_lower
    assert "dispute resolution" in prompt_lower
    assert "governing law" in prompt_lower
    assert "important obligations" in prompt_lower

    # Verify risk-analysis concepts.
    assert "potential risk" in prompt_lower
    assert "potential concern" in prompt_lower
    assert "clause requiring review" in prompt_lower
    assert "severity" in prompt_lower
    assert "why it may require review" in prompt_lower

    # Verify source references.
    assert "section" in prompt_lower
    assert "page" in prompt_lower

    # Verify cautious/legal language.
    assert "legally invalid" in prompt_lower
    assert "enforceable" in prompt_lower
    assert "unenforceable" in prompt_lower
    assert (
        "not a substitute for professional legal advice"
        in prompt_lower
    )

    # Verify the missing-information rule.
    assert (
    "no potential risks identified from the provided document context."
    in prompt_lower
)

    print(
        "\nPASS: Risk context and instructions "
        "are correctly constructed."
    )


def test_mock_risk_generation():
    """
    Verify that the risk-analysis prompt can be passed
    to an LLM without making a real API request.
    """

    context = build_document_context()

    prompt = build_risk_analysis_prompt(
        context
    )

    mock_llm = MockLLM()

    response = mock_llm.generate(
        prompt
    )

    assert response == "MOCK RISK ANALYSIS"
    assert mock_llm.last_prompt == prompt

    print(
        "\nPASS: Mock risk analysis completed "
        "without calling Gemini."
    )


if __name__ == "__main__":
    test_risk_context()
    test_mock_risk_generation()

    print("\n" + "=" * 70)
    print("ALL RISK GROUNDING TESTS PASSED")
    print("=" * 70)