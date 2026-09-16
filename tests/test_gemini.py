from ai.llm import LexiGuardLLM


llm = LexiGuardLLM()


response = llm.generate(
    "Explain a contract termination clause in simple language."
)


print("LLM RESPONSE:")
print(response)