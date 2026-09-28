from ai.prompts import build_comparison_prompt


document_a_context = """
Document A:
Page 1
Payment Terms:
Monthly service fee is ₹75,000.
Payment is due within 30 calendar days.

Termination:
Either party may terminate with 30 days' notice.
"""

document_b_context = """
Document B:
Page 1
Payment Terms:
Monthly service fee is ₹90,000.
Payment is due within 45 calendar days.

Termination:
Either party may terminate with 60 days' notice.
"""


prompt = build_comparison_prompt(
    document_a_context,
    document_b_context
)


# ==========================================
# Context Checks
# ==========================================

assert document_a_context in prompt

print(
    "PASS: Document A context included"
)


assert document_b_context in prompt

print(
    "PASS: Document B context included"
)


# ==========================================
# Comparison Category Checks
# ==========================================

comparison_categories = [
    "Payment Terms",
    "Termination",
    "Duration",
    "Renewal",
    "Liability",
    "Confidentiality",
    "Obligations"
]


for category in comparison_categories:

    assert category in prompt


print(
    "PASS: All comparison categories included"
)


# ==========================================
# Structured JSON Field Checks
# ==========================================

structured_fields = [
    '"comparison"',
    '"category"',
    '"document_a"',
    '"document_b"',
    '"difference"',
    '"source"',
    '"overall_differences"',
    '"disclaimer"'
]


for field in structured_fields:

    assert field in prompt


print(
    "PASS: Structured JSON fields included"
)


# ==========================================
# Grounding Instructions
# ==========================================

assert (
    "ONLY the information provided"
    in prompt
)

assert (
    "Do not invent missing information"
    in prompt
)

assert (
    "Not found in the document."
    in prompt
)


print(
    "PASS: Grounding instructions included"
)


# ==========================================
# Neutral Analysis Checks
# ==========================================

assert (
    "Do not describe either document as better"
    in prompt
)

assert (
    "worse"
    in prompt
)

assert (
    "safer"
    in prompt
)

assert (
    "riskier"
    in prompt
)

assert (
    "more favorable"
    in prompt
)


print(
    "PASS: Neutral legal-analysis instructions included"
)


# ==========================================
# JSON-Only Response Checks
# ==========================================

assert (
    "Return ONLY valid JSON."
    in prompt
)

assert (
    "Do not include Markdown code fences."
    in prompt
)

assert (
    "Do not include explanatory text before or after the JSON."
    in prompt
)


print(
    "PASS: JSON-only response instructions included"
)


# ==========================================
# Document Data Reached Prompt
# ==========================================

assert "₹75,000" in prompt
assert "₹90,000" in prompt
assert "30 calendar days" in prompt
assert "45 calendar days" in prompt
assert "30 days" in prompt
assert "60 days" in prompt


print(
    "PASS: Comparison document data reached prompt"
)


print(
    "PASS: Structured comparison prompt test completed"
)