import os

# Keep resource usage low.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever
from ai.prompts import build_qa_prompt


PDF_PATH = "test_documents/legal_agreement.pdf"


class MockLLM:
    """
    Fake LLM used for testing.

    This prevents the test from calling Gemini.
    """

    def __init__(self):
        self.last_prompt = None

    def generate(self, prompt):
        self.last_prompt = prompt

        return "MOCK ANSWER"


def build_rag_components():
    """
    Build the document retrieval components.
    """

    pages = extract_text_from_pdf(
        PDF_PATH
    )

    chunks = create_text_chunks(
        pages
    )

    embedding_model = LexiGuardEmbeddings()

    retriever = LexiGuardRetriever(
        embedding_model
    )

    retriever.add_chunks(
        chunks
    )

    return retriever


def test_payment_context():
    """
    Verify that payment-related context is retrieved
    and contains the expected information.
    """

    retriever = build_rag_components()

    results = retriever.retrieve(
        "What are the payment terms?",
        top_k=3,
        score_threshold=0.08
    )

    assert len(results) > 0

    context = "\n\n".join(
        result["text"]
        for result in results
    )

    prompt = build_qa_prompt(
        context,
        "What are the payment terms?"
    )

    print("\nPayment RAG Context:")
    print(context)

    print("\nGenerated QA Prompt:")
    print(prompt)

    assert "Payment Terms" in context
    assert "30 calendar days" in context

    assert "What are the payment terms?" in prompt

    print("\nPASS: Payment context is correctly passed to the QA prompt.")


def test_termination_context():
    """
    Verify that termination-related context is retrieved.
    """

    retriever = build_rag_components()

    results = retriever.retrieve(
        "What is the termination notice period?",
        top_k=3,
        score_threshold=0.15
    )

    assert len(results) > 0

    context = "\n\n".join(
        result["text"]
        for result in results
    )

    print("\nTermination RAG Context:")
    print(context)

    assert "Termination" in context
    assert "30 days" in context

    print("\nPASS: Termination context retrieved correctly.")


def test_unrelated_question():
    """
    Verify that an unrelated question does not
    produce usable RAG context.
    """

    retriever = build_rag_components()

    results = retriever.retrieve(
        "What is the CEO's salary?",
        top_k=3,
        score_threshold=0.15
    )

    print("\nUnrelated Question Results:")

    if not results:
        print("No relevant chunks found.")

    assert len(results) == 0

    print("\nPASS: Unrelated question produced no RAG context.")


def test_mock_llm():
    """
    Verify that our RAG prompt can be passed to an LLM
    without making a real API request.
    """

    mock_llm = MockLLM()

    prompt = build_qa_prompt(
        "Section 4 states that payment must be made within 30 calendar days.",
        "What is the payment period?"
    )

    response = mock_llm.generate(
        prompt
    )

    assert response == "MOCK ANSWER"
    assert mock_llm.last_prompt == prompt

    print("\nPASS: Mock LLM test completed without calling Gemini.")


if __name__ == "__main__":
    test_payment_context()
    test_termination_context()
    test_unrelated_question()
    test_mock_llm()

    print("\n" + "=" * 70)
    print("ALL RAG GROUNDING TESTS PASSED")
    print("=" * 70)