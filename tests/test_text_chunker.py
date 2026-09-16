from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks


pdf_path = "test_documents/legal_agreement.pdf"

pages = extract_text_from_pdf(pdf_path)

chunks = create_text_chunks(pages)

print(f"Total pages: {len(pages)}")
print(f"Total chunks: {len(chunks)}")

for chunk in chunks[:5]:
    print("\n--- Chunk ---")
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Page: {chunk['page_number']}")
    print(f"Chunk number: {chunk['chunk_number']}")
    print(f"Text: {chunk['text'][:300]}")