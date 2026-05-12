import tempfile
import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from interfaces.api.schemas import KBFileUpload, KBFileResponse, KBListResponse, KBDeleteRequest
from knowledge_base.kb_manager import KnowledgeBase

router = APIRouter(prefix="/kb", tags=["knowledge-base"])

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def kb_upload(file: UploadFile = File(...), project_id: str = Form("default")):
    """Upload a file directly to the knowledge base."""
    kb = KnowledgeBase()

    # Save uploaded file to temp location
    safe_name = Path(file.filename or "upload").name
    dest = UPLOAD_DIR / f"{project_id}_{safe_name}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        result = await kb.ingest_file(str(dest), project_id=project_id)
        if result.get("status") == "duplicate":
            dest.unlink(missing_ok=True)
            return {"status": "duplicate", "filename": safe_name}
        dest.unlink(missing_ok=True)
        return {
            "status": "ok",
            "file_id": result.get("file_id", ""),
            "filename": safe_name,
            "chunk_count": result.get("chunk_count", 0),
            "token_count": result.get("token_count", 0),
            "tags": result.get("tags", []),
            "file_type": result.get("file_type", "unknown"),
        }
    except Exception as e:
        dest.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(e))


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
