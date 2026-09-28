import json
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

from ai.embeddings import LexiGuardEmbeddings
from ai.retriever import LexiGuardRetriever
from ai.rag import LexiGuardRAG
from ai.llm import LexiGuardLLM

from ai.prompts import (
    build_summary_prompt,
    build_clause_extraction_prompt,
    build_risk_analysis_prompt,
    build_comparison_prompt,
)


class LexiGuardState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    user_query: str
    intent: str
    chunks: list

    # Single-document analysis
    document_a_context: str
    document_b_context: str

    # Comparison-specific chunks
    document_a_chunks: list
    document_b_chunks: list

    response: str
    sources: list


def classify_intent(state):
    """
    Identify what the user wants to do with the document.
    """

    query = state["user_query"].lower()

    if (
        "compare" in query
        or "comparison" in query
        or "difference" in query
        or "differences" in query
    ):
        intent = "comparison"

    elif (
        "constitution" in query
        or "constitutional" in query
        or "article 1" in query
        or "article 2" in query
        or "article 3" in query
        or "article 4" in query
        or "article 5" in query
        or "article 14" in query
        or "article 15" in query
        or "article 16" in query
        or "article 19" in query
        or "article 20" in query
        or "article 21" in query
        or "article 22" in query
        or "article 23" in query
        or "article 25" in query
        or "article 32" in query
        or "article 44" in query
        or "article 51" in query
        or "article 368" in query
        or "fundamental right" in query
        or "fundamental duty" in query
        or "directive principle" in query
        or "uniform civil code" in query
    ):
        intent = "constitution"

    elif (
        "summary" in query
        or "summarize" in query
    ):
        intent = "summary"

    elif (
        "clause" in query
        or "clauses" in query
    ):
        intent = "clause"

    elif (
        "risk" in query
        or "risks" in query
    ):
        intent = "risk"

    else:
        intent = "qa"

    return {
        "intent": intent
    }


def qa_node(state):
    """
    Answer a question using RAG over a single document.
    """

    embedding_model = LexiGuardEmbeddings()

    retriever = LexiGuardRetriever(
        embedding_model
    )

    retriever.add_chunks(
        state.get("chunks", [])
    )

    llm = LexiGuardLLM()

    rag = LexiGuardRAG(
        retriever=retriever,
        llm=llm
    )

    document_id = state.get("document_id", "")
    content_hash = state.get("content_hash", "")

    result = rag.ask(
        state["user_query"],
        top_k=3,
        score_threshold=0.08,
        minimum_confidence=0.08,
        document_id=document_id,
        content_hash=content_hash
    )

    return {
        "response": result["answer"],
        "sources": result["sources"]
    }


def summary_node(state):
    """
    Generate a structured summary of the document.
    """

    context_parts = []

    for chunk in state.get("chunks", []):
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = build_summary_prompt(
        context
    )

    llm = LexiGuardLLM()

    summary = llm.generate(
        prompt,
        max_words=50
    )

    return {
        "response": summary,
        "sources": state.get("chunks", [])
    }


def clause_node(state):
    """
    Extract important legal clauses from the document.
    """

    context_parts = []

    for chunk in state.get("chunks", []):
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = build_clause_extraction_prompt(
        context
    )

    llm = LexiGuardLLM()

    clause_analysis = llm.generate(
        prompt,
        max_words=50
    )

    return {
        "response": clause_analysis,
        "sources": state.get("chunks", [])
    }


def risk_node(state, llm=None):
    """
    Analyze document chunks for potential risks.

    An optional LLM can be provided for testing.
    If no LLM is provided, LexiGuard uses Gemini.
    """

    context_parts = []

    for chunk in state.get("chunks", []):
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(
        context_parts
    )

    prompt = build_risk_analysis_prompt(
        context
    )

    if llm is None:
        llm = LexiGuardLLM()

    risk_analysis = llm.generate(
        prompt,
        max_words=50
    )

    return {
        "response": risk_analysis,
        "sources": state["chunks"]
    }


def comparison_node(state, llm=None):
    """
    Compare two legal documents using a structured
    JSON response from the language model.
    """

    document_a_context = state["document_a_context"]
    document_b_context = state["document_b_context"]

    prompt = build_comparison_prompt(
        document_a_context,
        document_b_context
    )

    if llm is None:
        llm = LexiGuardLLM()

    raw_response = llm.generate(prompt)

    cleaned_response = raw_response.strip()
    if cleaned_response.startswith("```"):
        lines = cleaned_response.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_response = "\n".join(lines).strip()

    try:
        comparison_data = json.loads(cleaned_response)

    except json.JSONDecodeError as error:
        raise ValueError(
            "The comparison model returned an invalid JSON response."
        ) from error

    if not isinstance(comparison_data, dict):
        raise ValueError(
            "The comparison response must be a JSON object."
        )

    if "comparison" not in comparison_data:
        raise ValueError(
            "The comparison response is missing the 'comparison' field."
        )

    if not isinstance(
        comparison_data["comparison"],
        list
    ):
        raise ValueError(
            "The 'comparison' field must contain a list."
        )

    sources = []

    for chunk in state.get(
        "document_a_chunks",
        []
    ):
        sources.append({
            "document": "A",
            "page_number": chunk["page_number"],
            "chunk_number": chunk["chunk_number"]
        })

    for chunk in state.get(
        "document_b_chunks",
        []
    ):
        sources.append({
            "document": "B",
            "page_number": chunk["page_number"],
            "chunk_number": chunk["chunk_number"]
        })

    return {
        "response": comparison_data,
        "sources": sources
    }

def constitution_node(state):
    """
    Answer constitutional questions using local Constitution of India knowledge base.
    """
    from knowledge_base.constitution import search_constitution
    query = state.get("user_query", "")
    provision = search_constitution(query)

    if not provision:
        return {
            "response": "Not found in the constitutional knowledge base.",
            "sources": []
        }

    formatted_response = (
        f"**{provision['article']} — {provision['title']}**\n\n"
        f"**Part / Chapter:** {provision['part']} ({provision['chapter']})\n\n"
        f"**Provision Text:**\n\"{provision['text']}\"\n\n"
        f"*Legal Disclaimer: AI-assisted constitutional reference for informational purposes.*"
    )

    sources = [{
        "document": "Constitution of India",
        "page_number": provision["article"],
        "chunk_number": provision["part"]
    }]

    return {
        "response": formatted_response,
        "sources": sources
    }

def route_request(state):
    """
    Route the request to the correct processing node.
    """

    return state["intent"]


# ---------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------

graph_builder = StateGraph(
    LexiGuardState
)


# ---------------------------------------------------------
# Add Nodes
# ---------------------------------------------------------

graph_builder.add_node(
    "classify_intent",
    classify_intent
)

graph_builder.add_node(
    "qa",
    qa_node
)

graph_builder.add_node(
    "summary",
    summary_node
)

graph_builder.add_node(
    "clause",
    clause_node
)

graph_builder.add_node(
    "risk",
    risk_node
)

graph_builder.add_node(
    "comparison",
    comparison_node
)

graph_builder.add_node(
    "constitution",
    constitution_node
)


# ---------------------------------------------------------
# Start → Intent Classification
# ---------------------------------------------------------

graph_builder.add_edge(
    START,
    "classify_intent"
)


# ---------------------------------------------------------
# Conditional Routing
# ---------------------------------------------------------

graph_builder.add_conditional_edges(
    "classify_intent",
    route_request,
    {
        "qa": "qa",
        "summary": "summary",
        "clause": "clause",
        "risk": "risk",
        "comparison": "comparison",
        "constitution": "constitution",
    }
)


# ---------------------------------------------------------
# Processing Nodes → END
# ---------------------------------------------------------

graph_builder.add_edge(
    "qa",
    END
)

graph_builder.add_edge(
    "summary",
    END
)

graph_builder.add_edge(
    "clause",
    END
)

graph_builder.add_edge(
    "risk",
    END
)

graph_builder.add_edge(
    "comparison",
    END
)

graph_builder.add_edge(
    "constitution",
    END
)


# ---------------------------------------------------------
# Compile Graph
# ---------------------------------------------------------

lexiguard_graph = graph_builder.compile()