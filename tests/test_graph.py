from ai.graph import lexiguard_graph

def test_graph_standalone_queries():
    test_queries = [
        "What are the payment terms?",
        "Give me a summary of this document.",
        "What are the potential risks in this agreement?",
    ]

    sample_chunks = [{
        "page_number": 1,
        "chunk_number": 1,
        "text": "This agreement sets out payment terms, termination conditions, liability limitations, and confidentiality requirements."
    }]

    for query in test_queries:
        initial_state = {
            "user_query": query,
            "intent": "",
            "response": "",
            "chunks": sample_chunks
        }

        result = lexiguard_graph.invoke(initial_state)
        assert result["intent"] in ["qa", "summary", "risk"]