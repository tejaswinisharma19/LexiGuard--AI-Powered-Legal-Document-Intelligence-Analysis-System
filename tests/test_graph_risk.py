import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.graph import classify_intent, risk_node


PDF_PATH = "test_documents/legal_agreement.pdf"


class MockLLM:
    """
    Fake LLM for testing.

    This prevents any real Gemini API request.
    """

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt, **kwargs):
        self.last_prompt = prompt

        return (
            "MOCK RISK ANALYSIS\n\n"
            "Potential risk identified for testing purposes."
        )


def build_chunks():
    """
    Extract the sample PDF and create chunks.
    """

    pages = extract_text_from_pdf(
        PDF_PATH
    )

    return create_text_chunks(
        pages
    )


def test_risk_intent_classification():
    """
    Verify that risk-related questions are routed
    to the risk intent.
    """

    state = {
        "user_query": "What are the potential risks in this contract?",
        "intent": "",
        "chunks": [],
        "response": "",
        "sources": []
    }

    result = classify_intent(
        state
    )

    assert result["intent"] == "risk"

    print(
        "\nPASS: Risk intent classification works."
    )


def test_risk_node():
    """
    Verify that the LangGraph risk node can process
    document chunks without calling Gemini.
    """

    chunks = build_chunks()

    state = {
        "user_query": "What are the potential risks in this contract?",
        "intent": "risk",
        "chunks": chunks,
        "response": "",
        "sources": []
    }

    mock_llm = MockLLM()

    result = risk_node(
        state,
        llm=mock_llm
    )

    assert "response" in result
    assert "sources" in result

    assert result["response"] == (
        "MOCK RISK ANALYSIS\n\n"
        "Potential risk identified for testing purposes."
    )

    assert len(result["sources"]) == len(
        chunks
    )

    assert mock_llm.last_prompt is not None

    prompt_lower = (
        mock_llm.last_prompt.lower()
    )

    # Verify the actual document context reached the LLM.
    assert "payment terms" in prompt_lower
    assert "termination" in prompt_lower
    assert "liability" in prompt_lower

    # Verify source information reached the prompt.
    assert "page 1" in prompt_lower
    assert "page 2" in prompt_lower

    print(
        "\nPASS: Risk node executed with MockLLM."
    )

    print(
        "PASS: Document context reached the risk prompt."
    )

    print(
        "PASS: Sources were returned correctly."
    )

    print(
        "PASS: Gemini was not called."
    )


if __name__ == "__main__":
    test_risk_intent_classification()
    test_risk_node()

    print("\n" + "=" * 70)
    print("ALL LANGGRAPH RISK NODE TESTS PASSED")
    print("=" * 70)