from ai.graph import lexiguard_graph


test_queries = [
    "What are the payment terms?",
    "Give me a summary of this document.",
    "What are the potential risks in this agreement?",
]


for query in test_queries:

    initial_state = {
        "user_query": query,
        "intent": "",
        "response": "",
    }

    result = lexiguard_graph.invoke(initial_state)

    print("\n" + "=" * 50)
    print(f"Query: {query}")
    print(f"Intent: {result['intent']}")
    print(f"Response: {result['response']}")