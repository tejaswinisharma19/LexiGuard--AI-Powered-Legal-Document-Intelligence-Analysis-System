class LexiGuardRetriever:
    """
    Retrieve the most relevant document chunks
    for a user query.
    """

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.chunks = []

    def add_chunks(self, chunks):
        """
        Add document chunks and create their embeddings.
        """
        self.chunks = chunks

        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        self.embedding_model.create_embeddings(chunk_texts)

    def retrieve(self, query, top_k=3, score_threshold=0.15):
        """
        Retrieve the most relevant chunks for a query.

        Args:
            query (str): User question.
            top_k (int): Maximum number of chunks to return.
            score_threshold (float): Minimum similarity score
                required for a chunk to be considered relevant.

        Returns:
            list: Relevant document chunks with similarity scores.
        """

        query_vector = self.embedding_model.embed_query(query)

        similarities = self.embedding_model.calculate_similarity(
            query_vector
        )

        # Get the indices of the top matching chunks
        top_indices = similarities.argsort()[::-1][:top_k]

        results = []

        for index in top_indices:
            score = float(similarities[index])

            # Ignore chunks that are not relevant enough
            if score < score_threshold:
                continue

            chunk = self.chunks[index].copy()

            chunk["similarity_score"] = score

            results.append(chunk)

        return results