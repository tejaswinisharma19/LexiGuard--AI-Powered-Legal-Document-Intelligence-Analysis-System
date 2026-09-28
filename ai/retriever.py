class LexiGuardRetriever:
    """
    Retrieves the most relevant document chunks
    for a user query.
    """

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.chunks = []

    def add_chunks(self, chunks):
        """
        Store document chunks and create their
        TF-IDF representations.
        """

        self.chunks = chunks

        chunk_texts = [
            chunk["text"]
            for chunk in chunks
        ]

        self.embedding_model.create_embeddings(
            chunk_texts
        )

    def retrieve(
        self,
        query,
        top_k=3,
        score_threshold=0.08
    ):
        """
        Retrieve relevant chunks using cosine similarity.

        Chunks below the similarity threshold are
        rejected as insufficiently relevant.
        """

        if not self.chunks:
            return []

        query_vector = (
            self.embedding_model.embed_query(query)
        )

        similarities = (
            self.embedding_model.calculate_similarity(
                query_vector
            )
        )

        top_indices = (
            similarities.argsort()[::-1][:top_k]
        )

        results = []

        for index in top_indices:
            score = float(similarities[index])

            # Reject weak matches.
            if score < score_threshold:
                continue

            chunk = self.chunks[index].copy()

            chunk["similarity_score"] = score

            results.append(chunk)

        return results