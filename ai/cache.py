import hashlib

class AnswerCache:
    """
    Lightweight in-memory cache for document Q&A responses.
    Cache key is generated from: document_id + normalized_question + content_hash.
    """
    def __init__(self):
        self._cache = {}

    @staticmethod
    def generate_cache_key(document_id, question, content_hash=""):
        """
        Build a deterministic hash key for document Q&A caching.
        """
        doc_id_str = str(document_id or "").strip()
        norm_q = str(question or "").strip().lower()
        hash_str = str(content_hash or "").strip()
        raw_key = f"{doc_id_str}:{norm_q}:{hash_str}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    def get(self, document_id, question, content_hash=""):
        """
        Retrieve cached answer if present.
        """
        if not document_id or not question:
            return None
        key = self.generate_cache_key(document_id, question, content_hash)
        return self._cache.get(key)

    def set(self, document_id, question, answer_data, content_hash=""):
        """
        Store answer in cache.
        """
        if not document_id or not question or not answer_data:
            return
        key = self.generate_cache_key(document_id, question, content_hash)
        self._cache[key] = answer_data

    def clear(self):
        """
        Clear all entries from the cache (useful for testing).
        """
        self._cache.clear()

global_answer_cache = AnswerCache()
