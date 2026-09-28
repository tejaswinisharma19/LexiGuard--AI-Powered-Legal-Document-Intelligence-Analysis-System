from ai.llm import LexiGuardLLM


try:
    llm = LexiGuardLLM()

    response = llm.generate(
        "Explain a contract termination clause in simple language."
    )

    print("LLM RESPONSE:")
    print(response)
except RuntimeError as error:
    print(f"Skipping live Gemini call due to quota/network limit: {error}")