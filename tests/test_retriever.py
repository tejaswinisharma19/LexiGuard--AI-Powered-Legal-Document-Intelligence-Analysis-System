import os

# Limit BLAS/OpenMP threads to reduce memory usage.
# These must be set before importing NumPy/scikit-learn.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"


from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever


# -----------------------------
# Configuration
# -----------------------------

PDF_PATH = "test_documents/legal_agreement.pdf"

QUERY = "What are the payment terms?"

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
# Run retrieval
# -----------------------------

print("\nSearching document...")
print(f"Query: {QUERY}")
print(f"Top K: {TOP_K}")
print(f"Score threshold: {SCORE_THRESHOLD}")

results = retriever.retrieve(
    QUERY,
    top_k=TOP_K,
    score_threshold=SCORE_THRESHOLD
)


# -----------------------------
# Display results
# -----------------------------

print("\n" + "=" * 60)
print("RETRIEVAL RESULTS")
print("=" * 60)

if not results:
    print("No relevant document chunks found.")
else:
    print(f"Relevant chunks found: {len(results)}")

    for number, result in enumerate(results, start=1):

        print("\n" + "-" * 60)
        print(f"Result {number}")
        print("-" * 60)

        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Page: {result['page_number']}")
        print(f"Chunk Number: {result['chunk_number']}")
        print(
            f"Similarity Score: "
            f"{result['similarity_score']:.4f}"
        )

        print("\nText:")
        print(result["text"])