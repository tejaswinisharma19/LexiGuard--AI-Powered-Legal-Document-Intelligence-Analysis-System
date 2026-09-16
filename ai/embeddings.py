from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LexiGuardEmbeddings:
    """
    Lightweight text vectorization system for LexiGuard.

    This implementation uses TF-IDF as a local,
    zero-cost retrieval baseline.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.document_vectors = None

    def create_embeddings(self, texts):
        """
        Convert document chunks into numerical vectors.
        """

        self.document_vectors = self.vectorizer.fit_transform(texts)

        return self.document_vectors

    def embed_query(self, query):
        """
        Convert a user query into the same vector space
        as the document chunks.
        """

        return self.vectorizer.transform([query])

    def calculate_similarity(self, query_vector):
        """
        Calculate similarity between a query and all
        stored document vectors.
        """

        similarities = cosine_similarity(
            query_vector,
            self.document_vectors
        )

        return similarities[0]