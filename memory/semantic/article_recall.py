import uuid
from config.settings import settings
from knowledge_base.embeddings import EmbeddingService

# Lazy ChromaDB import
_chromadb = None


def _get_chromadb():
    global _chromadb
    if _chromadb is None:
        try:
            import chromadb
            _chromadb = chromadb
        except Exception:
            _chromadb = False
    return _chromadb if _chromadb is not False else None


class ArticleMemory:
    """Semantic memory for articles: 'have I written about something similar?'"""

    def __init__(self, embed_service: EmbeddingService | None = None):
        self.embed = embed_service or EmbeddingService()
        self._client = None
        self._fallback: dict[str, list[dict]] = {}  # project_id -> list of entries

    def _get_client(self):
        if self._client is None:
            chromadb = _get_chromadb()
            if chromadb:
                try:
                    from chromadb.config import Settings as ChromaSettings
                    self._client = chromadb.PersistentClient(
                        path=str(settings.chroma_persist_dir),
                        settings=ChromaSettings(anonymized_telemetry=False),
                    )
                except Exception:
                    self._client = False
            else:
                self._client = False
        return self._client if self._client is not False else None

    def _collection(self, project_id: str):
        client = self._get_client()
        if client:
            name = f"articles_{project_id}"
            return client.get_or_create_collection(name=name)
        return None

    async def remember_article(
        self, project_id: str, article_id: str,
        title: str, content: str, primary_keyword: str,
    ) -> str:
        embedding = await self.embed.embed_query(f"{title}\n{content[:2000]}")
        doc_id = str(uuid.uuid4())

        col = self._collection(project_id)
        if col:
            col.add(
                ids=[doc_id], embeddings=[embedding],
                documents=[f"{title}\n{primary_keyword}"],
                metadatas=[{"article_id": article_id, "title": title, "primary_keyword": primary_keyword}],
            )
        else:
            # Fallback: in-memory
            key = f"articles_{project_id}"
            if key not in self._fallback:
                self._fallback[key] = []
            self._fallback[key].append({
                "id": doc_id, "embedding": embedding,
                "document": f"{title}\n{primary_keyword}",
                "metadata": {"article_id": article_id, "title": title, "primary_keyword": primary_keyword},
            })

        return doc_id

    async def find_similar_articles(
        self, project_id: str, topic: str, top_k: int = 5,
    ) -> list[dict]:
        embedding = await self.embed.embed_query(topic)

        col = self._collection(project_id)
        if col:
            if col.count() == 0:
                return []
            results = col.query(
                query_embeddings=[embedding],
                n_results=min(top_k, col.count()),
                include=["documents", "metadatas", "distances"],
            )
            out = []
            ids = results.get("ids", [[]])[0]
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]
            for i in range(len(ids)):
                out.append({
                    "id": ids[i], "document": docs[i],
                    "metadata": metas[i] or {},
                    "similarity": 1.0 - (dists[i] if dists else 0.0),
                })
            return out
        else:
            # Fallback: cosine similarity on in-memory entries
            key = f"articles_{project_id}"
            entries = self._fallback.get(key, [])

            def _cosine(a, b):
                dot = sum(x * y for x, y in zip(a, b))
                na = sum(x * x for x in a) ** 0.5
                nb = sum(x * x for x in b) ** 0.5
                return dot / (na * nb) if na and nb else 0.0

            scored = [(_cosine(embedding, e["embedding"]), e) for e in entries]
            scored.sort(key=lambda x: x[0], reverse=True)

            return [
                {"id": e["id"], "document": e["document"],
                 "metadata": e["metadata"], "similarity": score}
                for score, e in scored[:top_k]
            ]
