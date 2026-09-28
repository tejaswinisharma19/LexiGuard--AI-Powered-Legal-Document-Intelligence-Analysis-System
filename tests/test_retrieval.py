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


PDF_PATH = "test_documents/legal_agreement.pdf"


def build_retriever():
    pages = extract_text_from_pdf(PDF_PATH)
    chunks = create_text_chunks(pages)

    embedding_model = LexiGuardEmbeddings()

    retriever = LexiGuardRetriever(
        embedding_model
    )

    retriever.add_chunks(chunks)

    return retriever


def run_test(test_name, query):
    print("\n" + "=" * 70)
    print(test_name)
    print("=" * 70)

    retriever = build_retriever()

    results = retriever.retrieve(
        query,
        top_k=3,
        score_threshold=0.15
    )

    if not results:
        print("No relevant chunks found.")
        return results

    for result in results:
        print(
            f"\nPage: {result['page_number']}"
            f" | Chunk: {result['chunk_number']}"
            f" | Score: {result['similarity_score']:.4f}"
        )

        print(result["text"])
        print("-" * 70)

    return results


def main():
    # Test 1: Payment terms
    payment_results = run_test(
        "TEST 1 — PAYMENT TERMS",
        "What are the payment terms?"
    )

    assert len(payment_results) > 0

    payment_text = " ".join(
        result["text"].lower()
        for result in payment_results
    )

    assert (
        "payment" in payment_text
        or "invoice" in payment_text
    )

    print("\nPASS: Payment retrieval")


    # Test 2: Termination
    termination_results = run_test(
        "TEST 2 — TERMINATION",
        "What is the termination notice period?"
    )

    assert len(termination_results) > 0

    termination_text = " ".join(
        result["text"].lower()
        for result in termination_results
    )

    assert (
        "termination" in termination_text
        or "terminate" in termination_text
    )

    print("\nPASS: Termination retrieval")


    # Test 3: Unrelated question
    unrelated_results = run_test(
        "TEST 3 — UNRELATED QUESTION",
        "What is the CEO's salary?"
    )

    for result in unrelated_results:
        assert result["similarity_score"] < 0.50

    print("\nPASS: Unrelated question did not produce a strong match.")

    print("\n" + "=" * 70)
    print("ALL RETRIEVAL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    main()