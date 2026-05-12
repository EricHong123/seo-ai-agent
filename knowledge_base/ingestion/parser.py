import hashlib
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from knowledge_base.ingestion.pdf_parser import parse_pdf
from knowledge_base.ingestion.docx_parser import parse_docx
from knowledge_base.ingestion.html_parser import parse_html
from knowledge_base.ingestion.url_fetcher import fetch_url


class FileType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    MD = "md"
    TXT = "txt"
    URL = "url"
    UNKNOWN = "unknown"


@dataclass
class ParsedDocument:
    text: str
    file_type: FileType
    file_hash: str
    filename: str
    source: str  # "user_upload" / "tool_output" / "url_fetch"


EXT_MAP = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".html": FileType.HTML,
    ".htm": FileType.HTML,
    ".md": FileType.MD,
    ".txt": FileType.TXT,
}


def detect_type(path: str) -> FileType:
    ext = Path(path).suffix.lower()
    if ext in EXT_MAP:
        return EXT_MAP[ext]
    # Try URL
    if path.startswith(("http://", "https://")):
        return FileType.URL
    return FileType.UNKNOWN


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def parse_file(path: str, source: str = "user_upload") -> ParsedDocument:
    file_type = detect_type(path)

    if file_type == FileType.URL:
        html = await fetch_url(path)
        text = await parse_html(html)
        fname = path.split("/")[-1] or path
    elif file_type == FileType.PDF:
        text = await parse_pdf(path)
        fname = Path(path).name
    elif file_type == FileType.DOCX:
        text = await parse_docx(path)
        fname = Path(path).name
    elif file_type in (FileType.HTML, FileType.MD, FileType.TXT):
        text = Path(path).read_text(encoding="utf-8")
        fname = Path(path).name
    else:
        raise ValueError(f"Unsupported file type: {file_type} ({path})")

    return ParsedDocument(
        text=text,
        file_type=file_type,
        file_hash=compute_hash(text),
        filename=fname,
        source=source,
    )


async def parse_text(text: str, filename: str = "inline", source: str = "tool_output") -> ParsedDocument:
    return ParsedDocument(
        text=text,
        file_type=FileType.TXT,
        file_hash=compute_hash(text),
        filename=filename,
        source=source,
    )
