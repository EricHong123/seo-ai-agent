"""Vector store with automatic fallback for environments without ChromaDB."""

import uuid

from config.settings import settings

# Lazy import ChromaDB — it may not be available on Python 3.14+
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


class SimpleVectorStore:
    """In-memory fallback vector store — uses cosine similarity of raw vectors.
    Works without ChromaDB. Good enough for MVP/testing with small KB sizes."""

    def __init__(self):
        self._collections: dict[str, list[dict]] = {}

    def _collection(self, project_id: str) -> list[dict]:
        name = f"kb_{project_id}"
        if name not in self._collections:
            self._collections[name] = []
        return self._collections[name]

    async def add(
        self, project_id: str, chunks: list[str],
        embeddings: list[list[float]], file_id: str,
        metadata: dict | None = None,
    ):
        col = self._collection(project_id)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            m = {"file_id": file_id, "chunk_index": i}
            if metadata:
                m.update(metadata)
            col.append({"id": str(uuid.uuid4()), "content": chunk, "embedding": emb, "metadata": m})

    async def search(
        self, project_id: str, query_embedding: list[float],
        top_k: int = 5, file_type_filter: str | None = None,
    ) -> list[dict]:
        col = self._collection(project_id)

        def _cosine(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            na = sum(x * x for x in a) ** 0.5
            nb = sum(x * x for x in b) ** 0.5
            return dot / (na * nb) if na and nb else 0.0

        scored = []
        for item in col:
            if file_type_filter and file_type_filter != "all":
                if item.get("metadata", {}).get("file_type") != file_type_filter:
                    continue
            score = _cosine(query_embedding, item["embedding"])
            scored.append((score, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for score, item in scored[:top_k]:
            out.append({
                "id": item["id"],
                "content": item["content"],
                "metadata": item["metadata"],
                "score": score,
            })
        return out

    async def delete_by_file(self, project_id: str, file_id: str):
        col = self._collection(project_id)
        self._collections[f"kb_{project_id}"] = [
            item for item in col if item.get("metadata", {}).get("file_id") != file_id
        ]

    async def list_files(self, project_id: str) -> list[dict]:
        col = self._collection(project_id)
        seen = {}
        for item in col:
            fid = item.get("metadata", {}).get("file_id")
            if fid and fid not in seen:
                seen[fid] = {"file_id": fid, "filename": item.get("metadata", {}).get("filename", fid)}
        return list(seen.values())


class ChromaVectorStore:
    """ChromaDB-backed vector store — full-featured, persistent."""

    def __init__(self):
        chromadb = _get_chromadb()
        if not chromadb:
            raise RuntimeError("ChromaDB not available")
        from chromadb.config import Settings as ChromaSettings
        self.client = chromadb.PersistentClient(
            path=str(settings.chroma_persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

    def _collection(self, project_id: str):
        name = f"kb_{project_id}"
        return self.client.get_or_create_collection(name=name)

    async def add(self, project_id, chunks, embeddings, file_id, metadata=None):
        col = self._collection(project_id)
        ids = [str(uuid.uuid4()) for _ in chunks]
        metas = [{"file_id": file_id, "chunk_index": i, **(metadata or {})} for i in range(len(chunks))]
        col.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metas)

    async def search(self, project_id, query_embedding, top_k=5, file_type_filter=None):
        col = self._collection(project_id)
        where = None
        if file_type_filter and file_type_filter != "all":
            where = {"file_type": file_type_filter}
        results = col.query(
            query_embeddings=[query_embedding], n_results=top_k,
            where=where, include=["documents", "metadatas", "distances"],
        )
        out = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for i in range(len(ids)):
            out.append({
                "id": ids[i], "content": docs[i],
                "metadata": metas[i] or {},
                "score": 1.0 - (dists[i] if dists else 0.0),
            })
        return out

    async def delete_by_file(self, project_id, file_id):
        col = self._collection(project_id)
        results = col.get(where={"file_id": file_id})
        if results["ids"]:
            col.delete(ids=results["ids"])

    async def list_files(self, project_id):
        col = self._collection(project_id)
        results = col.get(include=["metadatas"])
        seen = {}
        for meta in (results.get("metadatas") or []):
            fid = meta.get("file_id")
            if fid and fid not in seen:
                seen[fid] = {"file_id": fid, "filename": meta.get("filename", fid)}
        return list(seen.values())


def create_vector_store() -> SimpleVectorStore | ChromaVectorStore:
    if _get_chromadb():
        try:
            return ChromaVectorStore()
        except Exception:
            pass
    return SimpleVectorStore()
