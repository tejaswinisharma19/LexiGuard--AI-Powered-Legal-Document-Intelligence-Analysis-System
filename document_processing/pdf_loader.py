import os

import pymupdf


def extract_text_from_pdf(pdf_path):
    """
    Extract text from every page of a PDF.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        list: Page-wise extracted text.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        ValueError: If the PDF contains no extractable text.
        RuntimeError: If the PDF cannot be opened or processed.
    """

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(
            f"PDF file not found: {pdf_path}"
        )

    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError(
            "Only PDF files are supported."
        )

    try:
        pdf_document = pymupdf.open(pdf_path)

        pages = []

        for page_number, page in enumerate(
            pdf_document, start=1
        ):
            text = page.get_text().strip()

            pages.append({
                "page_number": page_number,
                "text": text
            })

        pdf_document.close()

    except Exception as error:
        raise RuntimeError(
            f"Unable to process PDF: {error}"
        ) from error

    has_text = any(page["text"] for page in pages)

    if not has_text:
        raise ValueError(
            "No extractable text was found in the PDF."
        )

    return pages