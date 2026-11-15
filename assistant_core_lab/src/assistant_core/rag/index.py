"""Keyword retrieval indexes for the Lab 06 knowledge base."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Protocol

from assistant_core.rag.chunker import Chunk

STOP = frozenset(
    "a an and are at be by can do for from how i in is it my of on or the to what when where who with".split()
)


def tokenize(text: str) -> list[str]:
    """Return lowercase word tokens with common English stop words removed."""
    return [token for token in re.findall(r"\w+", text.lower()) if token not in STOP]


@dataclass(frozen=True)
class Hit:
    """A retrieved chunk and its relevance score."""

    chunk: Chunk
    score: float


class Index(Protocol):
    """Common interface used by the RAG answerer."""

    def search(self, query: str, k: int = 3) -> list[Hit]: ...


class BM25Index:
    """Rank chunks with Okapi BM25."""

    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.docs = [tokenize(f"{chunk.title} {chunk.text}") for chunk in chunks]
        self.avgdl = sum(map(len, self.docs)) / max(len(self.docs), 1)
        document_frequency = Counter(token for document in self.docs for token in set(document))
        document_count = len(self.docs)
        self.idf = {
            token: math.log(1 + (document_count - frequency + 0.5) / (frequency + 0.5))
            for token, frequency in document_frequency.items()
        }
        self.tf = [Counter(document) for document in self.docs]

    def search(self, query: str, k: int = 3) -> list[Hit]:
        if k <= 0 or not self.chunks:
            return []

        query_tokens = tokenize(query)
        scores: list[float] = []
        for index, term_frequency in enumerate(self.tf):
            document_length = len(self.docs[index])
            score = sum(
                self.idf.get(token, 0)
                * term_frequency[token]
                * (self.k1 + 1)
                / (
                    term_frequency[token]
                    + self.k1 * (1 - self.b + self.b * document_length / self.avgdl)
                )
                for token in query_tokens
                if token in term_frequency
            )
            scores.append(score)

        ranked = sorted(range(len(scores)), key=lambda index: (-scores[index], self.chunks[index].id))[:k]
        return [Hit(self.chunks[index], round(scores[index], 3)) for index in ranked if scores[index] > 0]


class TfidfIndex:
    """Rank chunks with cosine similarity over TF-IDF vectors."""

    def __init__(self, chunks: list[Chunk]):
        self.chunks = chunks
        documents = [tokenize(f"{chunk.title} {chunk.text}") for chunk in chunks]
        document_frequency = Counter(token for document in documents for token in set(document))
        document_count = len(documents)
        self.idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }
        self.vecs = [self._vector(document) for document in documents]

    def _vector(self, tokens: list[str]) -> dict[str, float]:
        term_frequency = Counter(tokens)
        vector = {token: count * self.idf.get(token, 0) for token, count in term_frequency.items()}
        norm = math.sqrt(sum(weight * weight for weight in vector.values())) or 1.0
        return {token: weight / norm for token, weight in vector.items()}

    def search(self, query: str, k: int = 3) -> list[Hit]:
        if k <= 0:
            return []

        query_vector = self._vector(tokenize(query))
        similarities = [
            sum(weight * vector.get(token, 0) for token, weight in query_vector.items())
            for vector in self.vecs
        ]
        ranked = sorted(
            range(len(similarities)),
            key=lambda index: (-similarities[index], self.chunks[index].id),
        )[:k]
        return [
            Hit(self.chunks[index], round(similarities[index], 3))
            for index in ranked
            if similarities[index] > 0
        ]


class HybridIndex:
    """Combine BM25 and TF-IDF rankings with reciprocal-rank fusion."""

    def __init__(self, chunks: list[Chunk]):
        self.bm25 = BM25Index(chunks)
        self.tfidf = TfidfIndex(chunks)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        if k <= 0:
            return []

        fused: dict[str, float] = {}
        best: dict[str, Hit] = {}
        for hits in (self.bm25.search(query, 10), self.tfidf.search(query, 10)):
            for rank, hit in enumerate(hits):
                fused[hit.chunk.id] = fused.get(hit.chunk.id, 0) + 1 / (60 + rank)
                best.setdefault(hit.chunk.id, hit)

        top = sorted(fused, key=lambda chunk_id: (-fused[chunk_id], chunk_id))[:k]
        return [Hit(best[chunk_id].chunk, best[chunk_id].score) for chunk_id in top]


def make_index(kind: str, chunks: list[Chunk]) -> Index:
    """Construct the configured retrieval index."""
    indexes = {"bm25": BM25Index, "tfidf": TfidfIndex, "hybrid": HybridIndex}
    return indexes[kind](chunks)
