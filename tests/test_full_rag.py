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
from ai.rag import LexiGuardRAG
from ai.llm import LexiGuardLLM


# -----------------------------
# Configuration
# -----------------------------

PDF_PATH = "test_documents/legal_agreement.pdf"


QUESTION = "What are the payment terms?"
TOP_K = 3
SCORE_THRESHOLD = 0.15


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
# Create LLM
# -----------------------------

print("Creating LLM...")

llm = LexiGuardLLM()


# -----------------------------
# Create RAG system
# -----------------------------

print("Creating RAG system...")

rag = LexiGuardRAG(
    retriever=retriever,
    llm=llm
)


# -----------------------------
# Ask question
# -----------------------------

print("\nAsking question...")
print(f"Question: {QUESTION}")

result = rag.ask(
    QUESTION,
    top_k=TOP_K,
    score_threshold=SCORE_THRESHOLD
)


# -----------------------------
# Display result
# -----------------------------

print("\n" + "=" * 60)
print("RAG RESULT")
print("=" * 60)

print("\nQUESTION:")
print(result["question"])

print("\nANSWER:")
print(result["answer"])


# -----------------------------
# Display sources
# -----------------------------

print("\nSOURCES:")

if not result["sources"]:
    print("No relevant sources found.")
else:
    for source in result["sources"]:
        print(
            f"Page {source['page_number']} | "
            f"Similarity: "
            f"{source['similarity_score']:.4f}"
        )