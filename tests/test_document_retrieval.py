from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.embeddings import LexiGuardEmbeddings


PDF_PATH = "test_documents/legal_agreement.pdf"


# Step 1: Extract text from PDF
pages = extract_text_from_pdf(PDF_PATH)


# Step 2: Create chunks
chunks = create_text_chunks(pages)


# Step 3: Extract only the text for vectorization
chunk_texts = [
    chunk["text"]
    for chunk in chunks
]


# Step 4: Create embedding system
embedding_model = LexiGuardEmbeddings()


# Step 5: Create vectors for all chunks
embedding_model.create_embeddings(chunk_texts)


# Step 6: Ask a question
query = "How can I start an AI Agent workflow?"


# Step 7: Convert question into a vector
query_vector = embedding_model.embed_query(query)


# Step 8: Calculate similarity
similarities = embedding_model.calculate_similarity(
    query_vector
)


# Step 9: Find the most relevant chunks
top_indices = similarities.argsort()[::-1][:3]


print(f"Total chunks: {len(chunks)}")

print("\nTop 3 relevant chunks:\n")


for rank, index in enumerate(top_indices, start=1):

    chunk = chunks[index]

    print(f"--- Result {rank} ---")
    print(f"Similarity: {similarities[index]:.4f}")
    print(f"Page: {chunk['page_number']}")
    print(f"Chunk: {chunk['chunk_number']}")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Text: {chunk['text'][:500]}")
    print()