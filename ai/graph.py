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
)


class LexiGuardState(TypedDict):
    """
    State information that moves through the LexiGuard graph.
    """

    user_query: str
    intent: str
    chunks: list
    response: str
    sources: list


def classify_intent(state: LexiGuardState):
    """
    Identify the type of user request.

    This is a temporary keyword-based classifier.
    It will be replaced with an LLM-based classifier later.
    """

    query = state["user_query"].lower()

    if "summary" in query or "summarize" in query:
        intent = "summary"

    elif "clause" in query or "clauses" in query:
        intent = "clause"

    elif "risk" in query or "risks" in query:
        intent = "risk"

    else:
        intent = "qa"

    return {
        "intent": intent
    }


def qa_node(state: LexiGuardState):
    """
    Answer the user's question using the existing RAG pipeline.
    """

    embedding_model = LexiGuardEmbeddings()

    retriever = LexiGuardRetriever(
        embedding_model
    )

    retriever.add_chunks(
        state["chunks"]
    )

    llm = LexiGuardLLM()

    rag = LexiGuardRAG(
        retriever=retriever,
        llm=llm
    )

    result = rag.ask(
        state["user_query"],
        top_k=3,
        score_threshold=0.15
    )

    return {
        "response": result["answer"],
        "sources": result["sources"]
    }


def summary_node(state: LexiGuardState):
    """
    Generate a structured summary using the complete document.
    """

    context_parts = []

    for chunk in state["chunks"]:
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = build_summary_prompt(
        context
    )

    llm = LexiGuardLLM()

    summary = llm.generate(
        prompt
    )

    return {
        "response": summary,
        "sources": state["chunks"]
    }


def clause_node(state: LexiGuardState):
    """
    Extract important legal clauses using the complete document.
    """

    context_parts = []

    for chunk in state["chunks"]:
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = build_clause_extraction_prompt(
        context
    )

    llm = LexiGuardLLM()

    clause_analysis = llm.generate(
        prompt
    )

    return {
        "response": clause_analysis,
        "sources": state["chunks"]
    }


def risk_node(state: LexiGuardState):
    """
    Identify potential risks using the complete document.
    """

    context_parts = []

    for chunk in state["chunks"]:
        context_parts.append(
            f"--- Source: Page {chunk['page_number']} "
            f"| Chunk: {chunk['chunk_number']} ---\n"
            f"{chunk['text']}"
        )

    context = "\n\n".join(context_parts)

    prompt = build_risk_analysis_prompt(
        context
    )

    llm = LexiGuardLLM()

    risk_analysis = llm.generate(
        prompt
    )

    return {
        "response": risk_analysis,
        "sources": state["chunks"]
    }


def route_request(state: LexiGuardState):
    """
    Decide which workflow should handle the request.
    """

    return state["intent"]


# --------------------------------------------------
# BUILD LEXIGUARD GRAPH
# --------------------------------------------------

graph_builder = StateGraph(
    LexiGuardState
)


# Add nodes
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


# START → Intent Classification
graph_builder.add_edge(
    START,
    "classify_intent"
)


# Intent Classification → Conditional Route
graph_builder.add_conditional_edges(
    "classify_intent",
    route_request,
    {
        "qa": "qa",
        "summary": "summary",
        "clause": "clause",
        "risk": "risk",
    },
)


# Workflows → END
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


# Compile the graph
lexiguard_graph = graph_builder.compile()