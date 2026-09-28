import os
import re

# Keep resource usage low on the 8 GB RAM system.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def simple_stem(word):
    word = word.lower()
    for suffix in ["ated", "ation", "ating", "ates", "ments", "ment", "ing", "ed", "es", "s"]:
        if len(word) > len(suffix) + 3 and word.endswith(suffix):
            return word[:-len(suffix)]
    return word


def stemmed_analyzer(doc):
    tokens = re.findall(r'\b\w+\b', doc.lower())
    stop_words = {"what", "is", "the", "where", "will", "be", "for", "a", "in", "of", "and", "or", "to", "this", "under", "with", "all", "out", "how", "many", "does"}
    return [simple_stem(t) for t in tokens if t not in stop_words and len(t) > 1]


class LexiGuardEmbeddings:
    """
    Lightweight local text representation using TF-IDF with stemming.

    This is a zero-cost retrieval baseline and does not
    require an external embedding API.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer=stemmed_analyzer
        )

        self.document_vectors = None

    def create_embeddings(self, texts):
        """
        Create TF-IDF vectors for document chunks.
        """

        self.document_vectors = (
            self.vectorizer.fit_transform(texts)
        )

        return self.document_vectors

    def embed_query(self, query):
        """
        Convert a user query into the same TF-IDF
        vector space as the document chunks.
        """

        return self.vectorizer.transform(
            [query]
        )

    def calculate_similarity(self, query_vector):
        """
        Calculate cosine similarity between the query
        and all document chunks.
        """

        similarities = cosine_similarity(
            query_vector,
            self.document_vectors
        )

        return similarities[0]