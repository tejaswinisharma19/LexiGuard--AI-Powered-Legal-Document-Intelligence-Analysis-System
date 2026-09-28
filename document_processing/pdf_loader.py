import os
import re

import pymupdf


def normalize_extracted_text(text):
    """
    Normalize common PDF extraction issues without
    changing the actual document meaning.
    """

    # Some PDFs incorrectly extract the Indian Rupee
    # symbol as the letter "I".
    #
    # Example:
    #     I75,000 -> ₹75,000
    #
    # Only apply this when "I" appears immediately
    # before a numeric monetary value.
    text = re.sub(
        r"\bI(?=\d[\d,]*(?:\.\d+)?)",
        "₹",
        text
    )

    return text


def extract_text_from_pdf(pdf_path):
    """
    Extract text and page information from a PDF.
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
        pdf_document = pymupdf.open(
            pdf_path
        )

        pages = []

        for page_number, page in enumerate(
            pdf_document,
            start=1
        ):
            text = page.get_text().strip()

            text = normalize_extracted_text(
                text
            )

            pages.append({
                "page_number": page_number,
                "text": text
            })

        pdf_document.close()

    except Exception as error:
        raise RuntimeError(
            f"Unable to process PDF: {error}"
        ) from error

    has_text = any(
        page["text"]
        for page in pages
    )

    if not has_text:
        raise ValueError(
            "No extractable text was found in the PDF."
        )

    return pages