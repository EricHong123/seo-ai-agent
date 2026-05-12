from fastapi import APIRouter, HTTPException

from interfaces.api.schemas import KBFileUpload, KBFileResponse, KBListResponse, KBDeleteRequest
from knowledge_base.kb_manager import KnowledgeBase

router = APIRouter(prefix="/kb", tags=["knowledge-base"])


@router.post("/ingest", response_model=KBFileResponse)
async def kb_ingest(body: KBFileUpload):
    kb = KnowledgeBase()
    result = await kb.ingest_file(body.path, project_id=body.project_id)
    if result.get("status") == "duplicate":
        raise HTTPException(status_code=409, detail="File already exists in KB")
    return KBFileResponse(
        file_id=result.get("file_id", ""),
        filename=result.get("filename", ""),
        status=result.get("status", "error"),
        chunk_count=result.get("chunk_count", 0),
        tags=result.get("tags", []),
    )


@router.get("/files", response_model=KBListResponse)
async def kb_list_files(project_id: str = "default"):
    kb = KnowledgeBase()
    files = await kb.list_files(project_id)
    return KBListResponse(files=files)


@router.get("/search")
async def kb_search(query: str, project_id: str = "default", top_k: int = 5):
    kb = KnowledgeBase()
    return await kb.search(query, project_id=project_id, top_k=top_k)


@router.delete("/files")
async def kb_delete_file(body: KBDeleteRequest):
    kb = KnowledgeBase()
    records = await kb.list_files(body.project_id)
    match = None
    for r in records:
        if body.filename.lower() in r["filename"].lower():
            match = r
            break
    if not match:
        raise HTTPException(status_code=404, detail="File not found in KB")
    await kb.delete_file(match["id"], body.project_id)
    return {"status": "deleted", "filename": match["filename"]}
