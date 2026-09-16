import os

# -----------------------------
# Reduce NumPy/OpenBLAS memory usage
# -----------------------------

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever
from ai.prompts import build_summary_prompt
from ai.llm import LexiGuardLLM


# -----------------------------
# Configuration
# -----------------------------

PDF_PATH = "test_documents/legal_agreement.pdf"

QUERY = "Provide a complete summary of this legal agreement."


# -----------------------------
# Load PDF
# -----------------------------

print("Loading PDF...")

pages = extract_text_from_pdf(PDF_PATH)

print(f"Total pages: {len(pages)}")


# -----------------------------
# Create text chunks
# -----------------------------

print("\nCreating text chunks...")

chunks = create_text_chunks(pages)

print(f"Total chunks: {len(chunks)}")


# -----------------------------
# Create embedding model
# -----------------------------

print("\nCreating embedding model...")

embedding_model = LexiGuardEmbeddings()


# -----------------------------
# Create retriever
# -----------------------------

print("Creating retriever...")

retriever = LexiGuardRetriever(embedding_model)

retriever.add_chunks(chunks)


# -----------------------------
# Retrieve document context
# -----------------------------

print("\nRetrieving relevant document context...")

retrieval_results = retriever.retrieve(
    QUERY,
    top_k=5,
    score_threshold=0.10
)

print(f"Relevant chunks found: {len(retrieval_results)}")


# -----------------------------
# Check retrieval
# -----------------------------

if not retrieval_results:
    print("\nNo relevant document context found.")
    print("Cannot generate summary.")
    raise SystemExit


# -----------------------------
# Build context
# -----------------------------

context_parts = []

for result in retrieval_results:
    context_parts.append(
        f"--- Source: Page {result['page_number']} ---\n"
        f"{result['text']}"
    )

context = "\n\n".join(context_parts)


# -----------------------------
# Build summary prompt
# -----------------------------

print("\nBuilding summary prompt...")

prompt = build_summary_prompt(context)


# -----------------------------
# Create LLM
# -----------------------------

print("Creating LLM...")

llm = LexiGuardLLM()


# -----------------------------
# Generate summary
# -----------------------------

print("\nGenerating document summary...")

summary = llm.generate(prompt)


# -----------------------------
# Display summary
# -----------------------------

print("\n" + "=" * 60)
print("DOCUMENT SUMMARY")
print("=" * 60)

print("\n" + summary)