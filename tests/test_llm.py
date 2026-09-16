from ai.llm import LexiGuardLLM


llm = LexiGuardLLM()

response = llm.generate(
    "Explain a termination clause in simple language."
)

print(response)