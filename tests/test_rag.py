from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks
from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever
from ai.rag import LexiGuardRAG


PDF_PATH = "test_documents/legal_agreement.pdf"


# Extract PDF text
pages = extract_text_from_pdf(PDF_PATH)


# Create chunks
chunks = create_text_chunks(pages)


# Create embedding model
embedding_model = LexiGuardEmbeddings()


# Create retriever
retriever = LexiGuardRetriever(
    embedding_model
)


# Add document chunks
retriever.add_chunks(chunks)


# Create RAG system
rag = LexiGuardRAG(
    retriever
)


# Ask a question
query = "How can I start an AI Agent workflow?"


# Retrieve context
result = rag.retrieve_context(
    query,
    top_k=3
)


print("QUESTION:")
print(result["query"])

print("\nRETRIEVED CONTEXT:")
print(result["context"])

print("\nNUMBER OF SOURCES:")
print(len(result["sources"]))