import json
from pathlib import Path

import faiss
import numpy as np


class FaissRetriever:
    def __init__(self, dimension):
        if not isinstance(dimension, int) or dimension <= 0:
            raise ValueError("Dimension must be a positive integer.")

        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.documents = []

    def add_documents(self, vectors, documents):
        vectors = np.asarray(vectors, dtype=np.float32)

        if vectors.ndim != 2:
            raise ValueError("Vectors must be a 2D array.")

        if vectors.shape[1] != self.dimension:
            raise ValueError("Vector dimension does not match.")

        if len(vectors) != len(documents):
            raise ValueError("Vectors and documents must have equal lengths.")

        if not np.isfinite(vectors).all():
            raise ValueError("Vectors must contain finite values.")

        if np.any(np.linalg.norm(vectors, axis=1) == 0):
            raise ValueError("Vectors must not be zero vectors.")

        vectors = vectors.copy()
        faiss.normalize_L2(vectors)

        self.index.add(vectors)
        self.documents.extend(documents)

    def search(self, query_vector, top_k=5):
        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        if self.index.ntotal != len(self.documents):
            raise RuntimeError("Index and document count do not match.")

        if self.index.ntotal == 0:
            return []

        query_vector = np.asarray(query_vector, dtype=np.float32)

        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        if query_vector.ndim != 2 or query_vector.shape[0] != 1:
            raise ValueError("Query must contain exactly one vector.")

        if query_vector.shape[1] != self.dimension:
            raise ValueError("Query dimension does not match.")

        if not np.isfinite(query_vector).all():
            raise ValueError("Query must contain finite values.")

        if np.linalg.norm(query_vector) == 0:
            raise ValueError("Query must not be a zero vector.")

        query_vector = query_vector.copy()
        faiss.normalize_L2(query_vector)

        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, k)

        results = []

        for score, index in zip(scores[0], indices[0]):
            if index >= 0:
                results.append(
                    {
                        "document": self.documents[index],
                        "score": float(score),
                    }
                )

        return results

    def get_document_count(self):
        return len(self.documents)

    def save(self, path):
        if self.index.ntotal != len(self.documents):
            raise RuntimeError("Index and document count do not match.")

        path = Path(path)
        faiss.write_index(self.index, str(path))

        metadata_path = Path(str(path) + ".meta.json")

        with metadata_path.open("w", encoding="utf-8") as file:
            json.dump(self.documents, file, ensure_ascii=False)

    @classmethod
    def load(cls, path):
        path = Path(path)
        index = faiss.read_index(str(path))

        if not isinstance(index, faiss.IndexFlatIP):
            raise ValueError("Unsupported FAISS index type.")

        if index.d <= 0:
            raise ValueError("Invalid index dimension.")

        metadata_path = Path(str(path) + ".meta.json")

        with metadata_path.open("r", encoding="utf-8") as file:
            documents = json.load(file)

        if not isinstance(documents, list):
            raise ValueError("Metadata must be a list.")

        if index.ntotal != len(documents):
            raise ValueError("Index and metadata count do not match.")

        retriever = cls(index.d)
        retriever.index = index
        retriever.documents = documents

        return retriever