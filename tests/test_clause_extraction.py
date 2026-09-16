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
from ai.prompts import build_clause_extraction_prompt
from ai.llm import LexiGuardLLM


# -----------------------------
# Configuration
# -----------------------------

PDF_PATH = "test_documents/legal_agreement.pdf"


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
# Whole-document context
# -----------------------------

print("\nPreparing complete document context...")

# Clause extraction is a whole-document analysis task.
# Therefore, we provide all chunks instead of retrieving
# only the top matching chunks.

document_chunks = chunks

print(
    f"Document chunks provided: "
    f"{len(document_chunks)}"
)


# -----------------------------
# Build document context
# -----------------------------

context_parts = []

for chunk in document_chunks:

    context_parts.append(
        f"--- Source: Page {chunk['page_number']} "
        f"| Chunk: {chunk['chunk_number']} ---\n"
        f"{chunk['text']}"
    )


context = "\n\n".join(context_parts)


# -----------------------------
# Build clause extraction prompt
# -----------------------------

print("\nBuilding clause extraction prompt...")

prompt = build_clause_extraction_prompt(context)


# -----------------------------
# Create LLM
# -----------------------------

print("Creating LLM...")

llm = LexiGuardLLM()


# -----------------------------
# Generate clause analysis
# -----------------------------

print("\nExtracting legal clauses...")

clause_analysis = llm.generate(prompt)


# -----------------------------
# Display result
# -----------------------------

print("\n" + "=" * 60)
print("CLAUSE EXTRACTION RESULT")
print("=" * 60)

print("\n" + clause_analysis)