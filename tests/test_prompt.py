from ai.prompts import build_qa_prompt


context = """
--- Source: Page 4 ---
Either party may terminate the agreement
by providing 30 days written notice.

--- Source: Page 7 ---
Payment shall be made within 15 days
of receiving the invoice.
"""


question = "How many days notice is required to terminate the agreement?"


prompt = build_qa_prompt(
    context,
    question
)


print(prompt)