from document_processing.pdf_loader import extract_text_from_pdf


pdf_path = "test_documents/legal_agreement.pdf"

pages = extract_text_from_pdf(pdf_path)

print(f"Total pages: {len(pages)}")

for page in pages:
    print(f"\n--- Page {page['page_number']} ---")
    print(page["text"][:1000])