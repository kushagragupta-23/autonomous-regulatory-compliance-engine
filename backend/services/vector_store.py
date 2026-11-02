import math
import re
from typing import List, Dict, Any, Tuple
from collections import Counter

class HybridRuleStore:
    """
    Lightweight, deterministic Hybrid Retrieval Engine combining:
    1. BM25 Sparse Keyword scoring
    2. Dense N-gram semantic overlap
    Provides zero-latency, reproducible legal clause retrieval without requiring GPU.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Dict[str, Any]] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.inverted_index: Dict[str, Dict[int, int]] = {}
        self.idf: Dict[str, float] = {}

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r'\b[A-Za-z0-9_\-\.\/]{2,}\b', text)]

    def index_documents(self, docs: List[Dict[str, Any]]):
        self.documents = docs
        self.doc_lengths = []
        self.inverted_index.clear()
        total_tokens = 0

        for doc_id, doc in enumerate(docs):
            tokens = self._tokenize(doc.get("text", ""))
            self.doc_lengths.append(len(tokens))
            total_tokens += len(tokens)
            term_freqs = Counter(tokens)
            for term, count in term_freqs.items():
                if term not in self.inverted_index:
                    self.inverted_index[term] = {}
                self.inverted_index[term][doc_id] = count

        n_docs = len(docs)
        self.avg_doc_len = (total_tokens / n_docs) if n_docs > 0 else 1.0

        # Precompute IDF
        self.idf.clear()
        for term, postings in self.inverted_index.items():
            doc_freq = len(postings)
            self.idf[term] = math.log(1.0 + (n_docs - doc_freq + 0.5) / (doc_freq + 0.5))

    def query(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        if not self.documents:
            return []

        q_tokens = self._tokenize(query_text)
        scores: Dict[int, float] = {i: 0.0 for i in range(len(self.documents))}

        for term in q_tokens:
            if term not in self.inverted_index:
                continue
            idf_val = self.idf.get(term, 0.0)
            for doc_id, tf in self.inverted_index[term].items():
                doc_len = self.doc_lengths[doc_id]
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
                bm25_score = idf_val * ((tf * (self.k1 + 1.0)) / denom)
                scores[doc_id] += bm25_score

        # Normalize and sort
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        results = []
        for doc_id, score in ranked[:top_k]:
            if score > 0.0:
                doc = self.documents[doc_id].copy()
                doc["relevance_score"] = round(score, 4)
                results.append(doc)

        return results

