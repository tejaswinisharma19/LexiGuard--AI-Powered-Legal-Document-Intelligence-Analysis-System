from document_processing.pdf_loader import extract_text_from_pdf
from document_processing.text_chunker import create_text_chunks

from ai.graph import (
    comparison_node,
    classify_intent
)


# ==========================================
# Mock LLM
# ==========================================

class MockLLM:
    """
    Mock language model used to test the comparison
    workflow without calling Gemini.
    """

    def generate(self, prompt):

        # Verify both documents reached the prompt
        assert "Document A" in prompt
        assert "Document B" in prompt

        # Verify important comparison categories
        assert "Payment Terms" in prompt
        assert "Termination" in prompt
        assert "Liability" in prompt

        return """
{
    "comparison": [
        {
            "category": "Payment Terms",
            "document_a": "₹75,000 per month, payable within 30 calendar days.",
            "document_b": "₹90,000 per month, payable within 45 calendar days.",
            "difference": "The monthly fee and payment period differ.",
            "source": "Document A Page 1; Document B Page 1"
        },
        {
            "category": "Termination",
            "document_a": "30 days' notice.",
            "document_b": "60 days' notice.",
            "difference": "The notice periods differ.",
            "source": "Document A Page 1; Document B Page 1"
        },
        {
            "category": "Duration",
            "document_a": "12 months.",
            "document_b": "18 months.",
            "difference": "The contract durations differ.",
            "source": "Document A Page 1; Document B Page 1"
        },
        {
            "category": "Renewal",
            "document_a": "Automatic 6-month renewal with 30 days' notice.",
            "document_b": "Automatic 12-month renewal with 60 days' notice.",
            "difference": "The renewal period and notice requirement differ.",
            "source": "Document A Page 1; Document B Page 1"
        },
        {
            "category": "Liability",
            "document_a": "Liability cap based on six months preceding the event.",
            "document_b": "Liability cap based on three months preceding the event.",
            "difference": "The liability cap calculation period differs.",
            "source": "Document A Page 2; Document B Page 2"
        },
        {
            "category": "Confidentiality",
            "document_a": "Confidentiality obligations apply.",
            "document_b": "Confidentiality obligations apply.",
            "difference": "No material difference identified.",
            "source": "Document A Page 2; Document B Page 2"
        },
        {
            "category": "Obligations",
            "document_a": "Parties must comply with contractual obligations.",
            "document_b": "Client must follow payment schedules and provider must protect data.",
            "difference": "The stated obligations differ.",
            "source": "Document A Page 2; Document B Page 2"
        }
    ],
    "overall_differences": "The documents differ in payment terms, termination notice, duration, renewal terms, liability provisions, and stated obligations.",
    "disclaimer": "LexiGuard provides AI-assisted document analysis and is not a substitute for professional legal advice."
}
"""


# ==========================================
# Load Document A
# ==========================================

document_a_pages = extract_text_from_pdf(
    "test_documents/legal_agreement.pdf"
)

document_a_chunks = create_text_chunks(
    document_a_pages
)


# ==========================================
# Load Document B
# ==========================================

document_b_pages = extract_text_from_pdf(
    "test_documents/legal_agreement_b.pdf"
)

document_b_chunks = create_text_chunks(
    document_b_pages
)


# ==========================================
# Build Document Context
# ==========================================

document_a_context_parts = []

for chunk in document_a_chunks:

    document_a_context_parts.append(
        f"--- Document A | Page {chunk['page_number']} "
        f"| Chunk {chunk['chunk_number']} ---\n"
        f"{chunk['text']}"
    )


document_a_context = "\n\n".join(
    document_a_context_parts
)


document_b_context_parts = []

for chunk in document_b_chunks:

    document_b_context_parts.append(
        f"--- Document B | Page {chunk['page_number']} "
        f"| Chunk {chunk['chunk_number']} ---\n"
        f"{chunk['text']}"
    )


document_b_context = "\n\n".join(
    document_b_context_parts
)


# ==========================================
# Test Intent Classification
# ==========================================

intent_state = {
    "user_query":
        "Compare Document A and Document B.",
    "intent": ""
}


intent_result = classify_intent(
    intent_state
)


assert intent_result["intent"] == "comparison"

print(
    "PASS: Comparison intent classification works"
)


# ==========================================
# Build Comparison State
# ==========================================

comparison_state = {

    "user_query":
        "Compare Document A and Document B.",

    "intent":
        "comparison",

    "chunks":
        [],

    "document_a_context":
        document_a_context,

    "document_b_context":
        document_b_context,

    "document_a_chunks":
        document_a_chunks,

    "document_b_chunks":
        document_b_chunks,

    "response":
        "",

    "sources":
        []
}


# ==========================================
# Execute Comparison Node
# ==========================================

result = comparison_node(
    comparison_state,
    llm=MockLLM()
)


# ==========================================
# Verify Structured Response
# ==========================================

assert isinstance(
    result["response"],
    dict
)

print(
    "PASS: Comparison node returned structured data"
)


assert "comparison" in result["response"]

assert isinstance(
    result["response"]["comparison"],
    list
)

print(
    "PASS: Structured comparison list returned"
)


# ==========================================
# Verify Categories
# ==========================================

categories = [
    item["category"]
    for item in result["response"]["comparison"]
]


for category in [
    "Payment Terms",
    "Termination",
    "Duration",
    "Renewal",
    "Liability",
    "Confidentiality",
    "Obligations"
]:

    assert category in categories


print(
    "PASS: All comparison categories returned"
)


# ==========================================
# Verify Document Data
# ==========================================

assert (
    "₹75,000"
    in result["response"]["comparison"][0]["document_a"]
)

assert (
    "₹90,000"
    in result["response"]["comparison"][0]["document_b"]
)


print(
    "PASS: Document A and B comparison data returned"
)


# ==========================================
# Verify Sources
# ==========================================

sources = result["sources"]


assert len(sources) > 0


document_a_sources = [
    source
    for source in sources
    if source["document"] == "A"
]


document_b_sources = [
    source
    for source in sources
    if source["document"] == "B"
]


assert len(document_a_sources) > 0
assert len(document_b_sources) > 0


print(
    "PASS: Document A source references returned"
)

print(
    "PASS: Document B source references returned"
)


for source in sources:

    assert "page_number" in source
    assert "chunk_number" in source


print(
    "PASS: Source references contain page and chunk information"
)


print(
    "PASS: Structured comparison graph test completed without Gemini"
)