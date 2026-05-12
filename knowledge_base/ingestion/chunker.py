import tiktoken

from config.settings import settings


enc = tiktoken.get_encoding("cl100k_base")


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> list[str]:
    size = chunk_size or settings.kb_chunk_size
    overlap = overlap or settings.kb_chunk_overlap

    tokens = enc.encode(text)
    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        end = min(start + size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunks.append(enc.decode(chunk_tokens))
        if end >= len(tokens):
            break
        start = end - overlap
    return chunks


def count_tokens(text: str) -> int:
    return len(enc.encode(text))
