"""Shared SentenceTransformer embeddings for Chroma index and query."""

from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL


def get_embedding_device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL, device=get_embedding_device())


def encode_texts(texts: List[str], batch_size: int = 256, show_progress_bar: bool = False) -> List[List[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, batch_size=batch_size, show_progress_bar=show_progress_bar, convert_to_numpy=True)
    return vectors.tolist()


def encode_query(query: str) -> List[float]:
    return encode_texts([query])[0]
