import logging
from ai.prompts import build_qa_prompt
from ai.cache import global_answer_cache

logger = logging.getLogger("lexiguard")


class LexiGuardRAG:
    """
    Retrieval-Augmented Generation pipeline for LexiGuard.

    Retrieves relevant document chunks and sends only
    sufficiently relevant context to the language model.
    """

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def ask(
        self,
        question,
        top_k=3,
        score_threshold=0.08,
        minimum_confidence=0.08,
        document_id="",
        content_hash=""
    ):
        """
        Answer a question using RAG-first architecture and answer caching.

        Flow:
        1. Check answer cache -> If hit, return cached answer (0 LLM calls).
        2. TF-IDF retrieval & similarity check.
        3. If no relevant chunks or best_score < minimum_confidence:
           Return "Not found in the document." directly (0 LLM calls).
        4. Generate answer via LLM (1 LLM call max), cache result, and return.
        """
        provider = getattr(self.llm, "get_provider", lambda: "unknown")()

        # 1. Check Answer Cache
        if document_id and question:
            cached_result = global_answer_cache.get(document_id, question, content_hash)
            if cached_result:
                print(f"QA | document={document_id} | provider={provider} | cache=true | llm_called=false")
                return cached_result

        # 2. Retrieve document chunks
        retrieval_result = self.retriever.retrieve(
            question,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # 3. Negative retrieval: No chunks retrieved
        if not retrieval_result:
            print(f"QA | document={document_id} | provider={provider} | cache=false | llm_called=false")
            res = {
                "question": question,
                "answer": "Not found in the document.",
                "sources": []
            }
            if document_id and question:
                global_answer_cache.set(document_id, question, res, content_hash)
            return res

        # Check strongest retrieved match
        best_score = max(
            result["similarity_score"]
            for result in retrieval_result
        )

        # Reject weak retrieval results
        if best_score < minimum_confidence:
            print(f"QA | document={document_id} | provider={provider} | cache=false | llm_called=false")
            res = {
                "question": question,
                "answer": "Not found in the document.",
                "sources": []
            }
            if document_id and question:
                global_answer_cache.set(document_id, question, res, content_hash)
            return res

        # 4. Sufficient evidence: Build grounded context & call LLM once
        context_parts = []
        for result in retrieval_result:
            context_parts.append(
                f"--- Source: Page {result['page_number']} ---\n"
                f"{result['text']}"
            )

        context = "\n\n".join(context_parts)
        prompt = build_qa_prompt(context, question)

        print(f"QA | document={document_id} | provider={provider} | cache=false | llm_called=true")

        answer = self.llm.generate(prompt, max_words=50)

        result_payload = {
            "question": question,
            "answer": answer,
            "sources": retrieval_result
        }

        if document_id and question:
            global_answer_cache.set(document_id, question, result_payload, content_hash)

        return result_payload