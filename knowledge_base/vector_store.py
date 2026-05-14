"""Vector store — LanceDB primary, SimpleVectorStore fallback.

LanceDB: pure Python, no system deps, built-in ANN (IVF_PQ).
Works on Python 3.14+ where ChromaDB (pydantic v1) is broken.
"""

import uuid
import json
from pathlib import Path
from config.settings import settings

_lancedb = None


def _get_lancedb():
    global _lancedb
    if _lancedb is None:
        try:
            import lancedb
            _lancedb = lancedb
        except Exception:
            _lancedb = False
    return _lancedb if _lancedb is not False else None


class SimpleVectorStore:
    """In-memory fallback — cosine similarity brute force. OK for small KB."""

    def __init__(self):
        self._collections: dict[str, list[dict]] = {}

    def _col(self, project_id: str) -> list[dict]:
        name = f"kb_{project_id}"
        if name not in self._collections:
            self._collections[name] = []
        return self._collections[name]

    async def add(self, project_id: str, chunks: list[str],
                  embeddings: list[list[float]], file_id: str,
                  metadata: dict | None = None):
        col = self._col(project_id)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            m = {"file_id": file_id, "chunk_index": i, **(metadata or {})}
            col.append({"id": str(uuid.uuid4()), "content": chunk, "embedding": emb, "metadata": m})

    async def search(self, project_id: str, query_embedding: list[float],
                     top_k: int = 5, file_type_filter: str | None = None) -> list[dict]:
        col = self._col(project_id)

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
            scored.append((_cosine(query_embedding, item["embedding"]), item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"id": s[1]["id"], "content": s[1]["content"],
                 "metadata": s[1]["metadata"], "score": s[0]} for s in scored[:top_k]]

    async def delete_by_file(self, project_id: str, file_id: str):
        key = f"kb_{project_id}"
        if key in self._collections:
            self._collections[key] = [
                i for i in self._collections[key]
                if i.get("metadata", {}).get("file_id") != file_id
            ]

    async def list_files(self, project_id: str) -> list[dict]:
        seen = {}
        for item in self._col(project_id):
            fid = item.get("metadata", {}).get("file_id")
            if fid and fid not in seen:
                seen[fid] = {"file_id": fid, "filename": item.get("metadata", {}).get("filename", fid)}
        return list(seen.values())


class LanceDBStore:
    """LanceDB-backed vector store — persistent, ANN-indexed, production-ready."""

    def __init__(self):
        lancedb = _get_lancedb()
        if not lancedb:
            raise RuntimeError("LanceDB not available")
        db_path = Path(settings.chroma_persist_dir) / "lancedb"
        db_path.mkdir(parents=True, exist_ok=True)
        self.db = lancedb.connect(str(db_path))

    def _table_name(self, project_id: str) -> str:
        return f"kb_{project_id}"

    def _ensure_table(self, project_id: str):
        import pyarrow as pa
        name = self._table_name(project_id)
        try:
            return self.db.open_table(name)
        except Exception:
            schema = pa.schema([
                pa.field("id", pa.string()),
                pa.field("content", pa.string()),
                pa.field("embedding", pa.list_(pa.float32(), 1536)),
                pa.field("file_id", pa.string()),
                pa.field("chunk_index", pa.int32()),
                pa.field("filename", pa.string()),
                pa.field("file_type", pa.string()),
            ])
            return self.db.create_table(name, schema=schema)

    async def add(self, project_id: str, chunks: list[str],
                  embeddings: list[list[float]], file_id: str,
                  metadata: dict | None = None):
        import pyarrow as pa
        table = self._ensure_table(project_id)
        data = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            data.append({
                "id": str(uuid.uuid4()),
                "content": chunk,
                "embedding": [float(x) for x in emb],
                "file_id": file_id,
                "chunk_index": i,
                "filename": (metadata or {}).get("filename", ""),
                "file_type": (metadata or {}).get("file_type", "unknown"),
            })
        table.add(data)

    async def search(self, project_id: str, query_embedding: list[float],
                     top_k: int = 5, file_type_filter: str | None = None) -> list[dict]:
        table = self._ensure_table(project_id)
        query_vec = [float(x) for x in query_embedding]

        query = table.search(query_vec).limit(top_k)
        if file_type_filter and file_type_filter != "all":
            query = query.where(f"file_type = '{file_type_filter}'")

        try:
            results = query.to_list()
        except Exception:
            return []

        return [{
            "id": r.get("id", ""),
            "content": r.get("content", ""),
            "metadata": {
                "file_id": r.get("file_id", ""),
                "chunk_index": r.get("chunk_index", 0),
                "filename": r.get("filename", ""),
                "file_type": r.get("file_type", ""),
            },
            "score": r.get("_distance", 1.0),
        } for r in results]

    async def delete_by_file(self, project_id: str, file_id: str):
        table = self._ensure_table(project_id)
        try:
            table.delete(f"file_id = '{file_id}'")
        except Exception:
            pass

    async def list_files(self, project_id: str) -> list[dict]:
        try:
            table = self._ensure_table(project_id)
            # LanceDB doesn't have SELECT DISTINCT — use to_pandas
            df = table.to_pandas()
            if df.empty:
                return []
            seen = {}
            for _, row in df.iterrows():
                fid = row.get("file_id", "")
                if fid and fid not in seen:
                    seen[fid] = {"file_id": fid, "filename": row.get("filename", fid)}
            return list(seen.values())
        except Exception:
            return []


def create_vector_store():
    if _get_lancedb():
        try:
            return LanceDBStore()
        except Exception:
            pass
    return SimpleVectorStore()
