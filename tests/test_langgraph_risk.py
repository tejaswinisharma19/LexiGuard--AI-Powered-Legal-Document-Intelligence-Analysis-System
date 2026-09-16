import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.graph import lexiguard_graph


PDF_PATH = "test_documents/legal_agreement.pdf"

QUESTION = "Identify the potential risks in this agreement."


pages = extract_text_from_pdf(
    PDF_PATH
)

print(f"Total pages: {len(pages)}")


chunks = create_text_chunks(
    pages
)

print(f"Total chunks: {len(chunks)}")


initial_state = {
    "user_query": QUESTION,
    "intent": "",
    "chunks": chunks,
    "response": "",
    "sources": [],
}


result = lexiguard_graph.invoke(
    initial_state
)


print("\n" + "=" * 60)
print("LANGGRAPH RISK ANALYSIS RESULT")
print("=" * 60)

print(f"\nIntent:")
print(result["intent"])

print("\nRisk Analysis:")
print(result["response"])