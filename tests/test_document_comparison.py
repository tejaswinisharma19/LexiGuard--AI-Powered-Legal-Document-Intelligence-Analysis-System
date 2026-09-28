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

from ai.prompts import build_comparison_prompt
from ai.llm import LexiGuardLLM


# -----------------------------
# Configuration
# -----------------------------

DOCUMENT_A_PATH = (
    "test_documents/legal_agreement.pdf"
)

DOCUMENT_B_PATH = (
    "test_documents/legal_agreement_b.pdf"
)


# -----------------------------
# Load Document A
# -----------------------------

print("Loading Document A...")

pages_a = extract_text_from_pdf(
    DOCUMENT_A_PATH
)

print(
    f"Document A pages: "
    f"{len(pages_a)}"
)


# -----------------------------
# Chunk Document A
# -----------------------------

print("\nCreating Document A chunks...")

chunks_a = create_text_chunks(
    pages_a
)

print(
    f"Document A chunks: "
    f"{len(chunks_a)}"
)


# -----------------------------
# Load Document B
# -----------------------------

print("\nLoading Document B...")

pages_b = extract_text_from_pdf(
    DOCUMENT_B_PATH
)

print(
    f"Document B pages: "
    f"{len(pages_b)}"
)


# -----------------------------
# Chunk Document B
# -----------------------------

print("\nCreating Document B chunks...")

chunks_b = create_text_chunks(
    pages_b
)

print(
    f"Document B chunks: "
    f"{len(chunks_b)}"
)


# -----------------------------
# Build Document A context
# -----------------------------

print("\nPreparing Document A context...")

document_a_parts = []

for chunk in chunks_a:

    document_a_parts.append(
        f"--- Document A | "
        f"Page {chunk['page_number']} | "
        f"Chunk {chunk['chunk_number']} ---\n"
        f"{chunk['text']}"
    )


document_a_context = "\n\n".join(
    document_a_parts
)


# -----------------------------
# Build Document B context
# -----------------------------

print("Preparing Document B context...")

document_b_parts = []

for chunk in chunks_b:

    document_b_parts.append(
        f"--- Document B | "
        f"Page {chunk['page_number']} | "
        f"Chunk {chunk['chunk_number']} ---\n"
        f"{chunk['text']}"
    )


document_b_context = "\n\n".join(
    document_b_parts
)


# -----------------------------
# Build comparison prompt
# -----------------------------

print("\nBuilding comparison prompt...")

prompt = build_comparison_prompt(
    document_a_context,
    document_b_context
)


# -----------------------------
# Create LLM
# -----------------------------

print("Creating LLM...")

llm = LexiGuardLLM()


# -----------------------------
# Generate comparison
# -----------------------------

print("\nComparing documents...")

try:
    comparison = llm.generate(
        prompt
    )

    print("\n" + "=" * 60)
    print("DOCUMENT COMPARISON RESULT")
    print("=" * 60)

    print("\n" + comparison)
except RuntimeError as error:
    print(f"\n[Note: Live Gemini API skipped due to quota: {error}]")