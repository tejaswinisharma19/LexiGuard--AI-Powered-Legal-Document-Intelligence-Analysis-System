import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.graph import lexiguard_graph


PDF_PATH = "test_documents/legal_agreement.pdf"

QUESTION = "Give me a complete summary of this legal agreement."


# Step 1: Extract PDF text
pages = extract_text_from_pdf(PDF_PATH)

print(f"Total pages: {len(pages)}")


# Step 2: Create chunks
chunks = create_text_chunks(pages)

print(f"Total chunks: {len(chunks)}")


# Step 3: Prepare graph state
initial_state = {
    "user_query": QUESTION,
    "intent": "",
    "chunks": chunks,
    "response": "",
    "sources": [],
}


# Step 4: Run LangGraph
result = lexiguard_graph.invoke(
    initial_state
)


# Step 5: Display result
print("\n" + "=" * 60)
print("LANGGRAPH SUMMARY RESULT")
print("=" * 60)

print(f"\nIntent:")
print(result["intent"])

print("\nSummary:")
print(result["response"])