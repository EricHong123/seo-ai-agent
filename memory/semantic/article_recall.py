"""Semantic article memory — 'have I written about something similar?'

Uses the same vector store backend as KB (LanceDB primary, in-memory fallback).
"""

import uuid
from config.settings import settings
from knowledge_base.embeddings import EmbeddingService
from knowledge_base.vector_store import create_vector_store


class ArticleMemory:
    def __init__(self, embed_service: EmbeddingService | None = None):
        self.embed = embed_service or EmbeddingService()
        self.store = create_vector_store()

    async def remember_article(self, project_id: str, article_id: str,
                               title: str, content: str,
                               primary_keyword: str) -> str:
        embedding = await self.embed.embed_query(f"{title}\n{content[:2000]}")
        doc_id = str(uuid.uuid4())

        await self.store.add(
            project_id=f"articles_{project_id}",
            chunks=[f"{title}\n{primary_keyword}"],
            embeddings=[embedding],
            file_id=article_id,
            metadata={"title": title, "primary_keyword": primary_keyword},
        )
        return doc_id

    async def find_similar_articles(self, project_id: str, topic: str,
                                    top_k: int = 5) -> list[dict]:
        embedding = await self.embed.embed_query(topic)
        results = await self.store.search(
            project_id=f"articles_{project_id}",
            query_embedding=embedding,
            top_k=top_k,
        )
        return [{
            "id": r["id"],
            "document": r["content"],
            "metadata": r["metadata"],
            "similarity": r["score"],
        } for r in results]
