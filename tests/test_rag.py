from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever


PDF_PATH = "test_documents/legal_agreement.pdf"


# Step 1: Extract PDF text
pages = extract_text_from_pdf(PDF_PATH)

print(f"Total pages: {len(pages)}")


# Step 2: Create text chunks
chunks = create_text_chunks(pages)

print(f"Total chunks: {len(chunks)}")


# Step 3: Create embedding model
embedding_model = LexiGuardEmbeddings()


# Step 4: Create retriever
retriever = LexiGuardRetriever(
    embedding_model
)


# Step 5: Add document chunks
retriever.add_chunks(chunks)


# Step 6: Retrieve relevant context
query = "What are the payment terms?"

results = retriever.retrieve(
    query,
    top_k=3,
    score_threshold=0.15
)


print("\nQUESTION:")
print(query)


print("\nRETRIEVED SOURCES:")
print(len(results))


for result in results:
    print("\n--- Source ---")
    print(f"Page: {result['page_number']}")
    print(f"Chunk: {result['chunk_number']}")
    print(f"Score: {result['similarity_score']:.4f}")
    print(f"Text: {result['text'][:300]}")