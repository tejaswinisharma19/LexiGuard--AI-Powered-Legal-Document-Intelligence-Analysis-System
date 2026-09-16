from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_text_chunks(pages):
    """
    Split extracted PDF text into smaller chunks.

    Each chunk keeps its original page information.
    """

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )

    chunks = []

    for page in pages:
        page_chunks = text_splitter.split_text(
            page["text"]
        )

        for chunk_number, chunk_text in enumerate(
            page_chunks,
            start=1
        ):
            chunks.append({
                "chunk_id": (
                    f"page_{page['page_number']}"
                    f"_chunk_{chunk_number}"
                ),
                "page_number": page["page_number"],
                "chunk_number": chunk_number,
                "text": chunk_text
            })

    return chunks