from document_processing.pdf_loader import (
    normalize_extracted_text
)


def main():
    test_text = """
    The monthly service fee is I75,000.
    Another amount is I1,25,000.
    This is a normal sentence.
    """

    normalized_text = normalize_extracted_text(
        test_text
    )

    print("\nOriginal text:")
    print(test_text)

    print("\nNormalized text:")
    print(normalized_text)

    assert "₹75,000" in normalized_text
    assert "₹1,25,000" in normalized_text
    assert "This is a normal sentence." in normalized_text

    print("\nPASS: PDF text normalization works correctly.")


if __name__ == "__main__":
    main()