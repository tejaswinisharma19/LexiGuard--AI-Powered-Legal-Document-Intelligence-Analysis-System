from ai.prompts import build_qa_prompt


class LexiGuardRAG:
    """
    Handles the RAG pipeline for LexiGuard.

    The pipeline retrieves relevant document chunks,
    builds a grounded prompt, and sends it to the LLM.
    """

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def ask(self, question, top_k=3, score_threshold=0.15):
        """
        Answer a question using retrieved document context.

        Args:
            question (str): User's question.
            top_k (int): Maximum number of chunks to retrieve.
            score_threshold (float): Minimum similarity score.

        Returns:
            dict: Question, answer, and source information.
        """

        # Step 1: Retrieve relevant document chunks
        retrieval_result = self.retriever.retrieve(
            question,
            top_k=top_k,
            score_threshold=score_threshold
        )

        # Step 2: Stop if no relevant information was found
        if not retrieval_result:
            return {
                "question": question,
                "answer": "Not found in the document.",
                "sources": []
            }

        # Step 3: Build context from retrieved chunks
        context_parts = []

        for result in retrieval_result:
            context_parts.append(
                f"--- Source: Page {result['page_number']} ---\n"
                f"{result['text']}"
            )

        context = "\n\n".join(context_parts)

        # Step 4: Build grounded prompt
        prompt = build_qa_prompt(
            context,
            question
        )

        # Step 5: Generate answer using the LLM
        answer = self.llm.generate(prompt)

        # Step 6: Return answer and sources
        return {
            "question": question,
            "answer": answer,
            "sources": retrieval_result
        }