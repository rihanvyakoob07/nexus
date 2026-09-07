"""OpenAI embeddings + ChromaDB vector store for similarity retrieval."""
import os
from typing import List
from openai import AsyncOpenAI
from app.core.config import get_settings

settings = get_settings()
_client = AsyncOpenAI(api_key=settings.openai_api_key)

# Lazy-loaded ChromaDB collection
_chroma_client = None
_collection = None


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        _collection = _chroma_client.get_or_create_collection("nexus_skills")
    return _collection


async def embed_text(text: str) -> List[float]:
    response = await _client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def upsert_engineer_profile(engineer_id: int, profile_text: str):
    collection = _get_collection()
    embedding = await embed_text(profile_text)
    collection.upsert(
        ids=[f"eng_{engineer_id}"],
        embeddings=[embedding],
        documents=[profile_text],
        metadatas=[{"engineer_id": engineer_id}],
    )


async def search_similar_engineers(query_text: str, n_results: int = 10) -> List[dict]:
    collection = _get_collection()
    embedding = await embed_text(query_text)
    results = collection.query(query_embeddings=[embedding], n_results=n_results)
    out = []
    for i, meta in enumerate(results["metadatas"][0]):
        out.append({
            "engineer_id": meta["engineer_id"],
            "distance": results["distances"][0][i],
        })
    return out
