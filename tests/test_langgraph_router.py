import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.graph import lexiguard_graph


PDF_PATH = "test_documents/legal_agreement.pdf"


pages = extract_text_from_pdf(
    PDF_PATH
)

chunks = create_text_chunks(
    pages
)


test_queries = [
    "What are the payment terms?",
    "Give me a summary of this agreement.",
    "Extract the important clauses from this agreement.",
    "Identify the potential risks in this agreement.",
]


for query in test_queries:

    initial_state = {
        "user_query": query,
        "intent": "",
        "chunks": chunks,
        "response": "",
        "sources": [],
    }

    result = lexiguard_graph.invoke(
        initial_state
    )

    print("\n" + "=" * 60)
    print("LANGGRAPH ROUTER TEST")
    print("=" * 60)

    print(f"\nQuery:")
    print(query)

    print(f"\nDetected Intent:")
    print(result["intent"])

    print("\nResponse Preview:")

    response = result["response"]

    print(response[:500])

    print("\n" + "-" * 60)