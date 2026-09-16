import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.graph import lexiguard_graph


PDF_PATH = "test_documents/legal_agreement.pdf"

QUESTION = "What are the payment terms?"


# Step 1: Extract PDF text
pages = extract_text_from_pdf(PDF_PATH)

print(f"Total pages: {len(pages)}")


# Step 2: Create chunks
chunks = create_text_chunks(pages)

print(f"Total chunks: {len(chunks)}")


# Step 3: Prepare initial graph state
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
print("LANGGRAPH Q&A RESULT")
print("=" * 60)

print(f"\nQuestion:")
print(result["user_query"])

print(f"\nIntent:")
print(result["intent"])

print(f"\nAnswer:")
print(result["response"])

print("\nSources:")

for source in result["sources"]:
    print(
        f"- Page {source['page_number']} "
        f"| Score: {source['similarity_score']:.4f}"
    )