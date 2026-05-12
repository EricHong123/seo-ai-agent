from knowledge_base.embeddings import EmbeddingService
from knowledge_base.vector_store import create_vector_store
from knowledge_base.file_registry import (
    init_db, is_duplicate, add_record, touch_record,
    delete_record, list_records, get_by_filename, get_by_id,
)
from knowledge_base.ingestion.parser import parse_file, parse_text
from knowledge_base.ingestion.chunker import chunk_text, count_tokens
from knowledge_base.auto_tag import auto_tag


class KnowledgeBase:
    def __init__(self, embed_service: EmbeddingService | None = None):
        self.embed = embed_service or EmbeddingService()
        self.vector = create_vector_store()
        init_db()

    async def ingest_file(
        self,
        path: str,
        project_id: str = "default",
        source: str = "user_upload",
        llm_client=None,
    ) -> dict:
        doc = await parse_file(path, source)
        if is_duplicate(doc.file_hash):
            existing = get_by_filename(doc.filename, project_id)
            return {"status": "duplicate", "file_id": existing["id"] if existing else None}

        return await self._index_document(doc, project_id, llm_client)

    async def ingest_text(
        self,
        text: str,
        project_id: str = "default",
        source: str = "tool_output",
        filename: str = "inline",
        metadata: dict | None = None,
        llm_client=None,
    ) -> dict:
        doc = await parse_text(text, filename, source)
        if is_duplicate(doc.file_hash):
            return {"status": "duplicate", "file_hash": doc.file_hash}
        return await self._index_document(doc, project_id, llm_client, metadata)

    async def _index_document(
        self,
        doc,
        project_id: str,
        llm_client=None,
        extra_metadata: dict | None = None,
    ) -> dict:
        chunks = chunk_text(doc.text)
        if not chunks:
            return {"status": "empty", "file_hash": doc.file_hash}

        tags = await auto_tag(doc.text, llm_client)
        embeddings = await self.embed.embed(chunks)
        token_count = count_tokens(doc.text)

        file_id = add_record(
            filename=doc.filename,
            file_hash=doc.file_hash,
            file_type=doc.file_type.value,
            source=doc.source,
            chunk_count=len(chunks),
            project_id=project_id,
            tags=tags,
        )

        await self.vector.add(
            project_id=project_id,
            chunks=chunks,
            embeddings=embeddings,
            file_id=file_id,
            metadata={
                "filename": doc.filename,
                "file_type": doc.file_type.value,
                "tags": ",".join(tags),
                **(extra_metadata or {}),
            },
        )

        return {
            "status": "ok",
            "file_id": file_id,
            "filename": doc.filename,
            "chunk_count": len(chunks),
            "token_count": token_count,
            "tags": tags,
        }

    async def search(
        self,
        query: str,
        project_id: str = "default",
        top_k: int = 5,
        file_type_filter: str | None = None,
    ) -> list[dict]:
        embedding = await self.embed.embed_query(query)
        results = await self.vector.search(project_id, embedding, top_k, file_type_filter)

        # Touch file records for LRU tracking
        seen: set[str] = set()
        for r in results:
            fid = r.get("metadata", {}).get("file_id", "")
            if fid and fid not in seen:
                touch_record(fid)
                seen.add(fid)

        return results

    async def delete_file(self, file_id: str, project_id: str = "default"):
        await self.vector.delete_by_file(project_id, file_id)
        delete_record(file_id)

    async def list_files(self, project_id: str = "default") -> list[dict]:
        return list_records(project_id)
