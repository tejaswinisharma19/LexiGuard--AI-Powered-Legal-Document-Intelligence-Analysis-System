import pytest
from knowledge_base.constitution import search_constitution, CONSTITUTION_DATA
from ai.graph import constitution_node, classify_intent

def test_constitution_exact_article_retrieval():
    res = search_constitution("What is Article 14?")
    assert res is not None
    assert res["article"] == "Article 14"
    assert "Part III" in res["part"]

def test_constitution_keyword_retrieval():
    res_speech = search_constitution("Tell me about freedom of speech")
    assert res_speech is not None
    assert "19" in res_speech["article"]

    res_liberty = search_constitution("right to life and personal liberty")
    assert res_liberty is not None
    assert res_liberty["article"] == "Article 21"

def test_constitution_fallback_non_existent():
    res = search_constitution("random non existent text xyz 12345")
    assert res is None

def test_constitution_intent_classification():
    state1 = {"user_query": "What does Article 21 of the Constitution say?"}
    intent1 = classify_intent(state1)
    assert intent1["intent"] == "constitution"

    state2 = {"user_query": "Explain fundamental rights under the Constitution"}
    intent2 = classify_intent(state2)
    assert intent2["intent"] == "constitution"

def test_constitution_node_execution():
    state_valid = {"user_query": "Article 14 equality before law"}
    res_valid = constitution_node(state_valid)
    assert "Article 14" in res_valid["response"]
    assert "Constitution of India" in res_valid["sources"][0]["document"]

    state_invalid = {"user_query": "xyz non existent query 99999"}
    res_invalid = constitution_node(state_invalid)
    assert "Not found in the constitutional knowledge base" in res_invalid["response"]
    assert len(res_invalid["sources"]) == 0
