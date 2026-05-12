import hashlib

from config.settings import settings

# Lazy OpenAI import
_openai = None


def _get_openai():
    global _openai
    if _openai is None:
        try:
            from openai import AsyncOpenAI
            _openai = AsyncOpenAI
        except Exception:
            _openai = False
    return _openai if _openai is not False else None


class EmbeddingService:
    def __init__(self):
        self.model = settings.embedding_model
        self.dim = settings.embedding_dim
        self._client = None
        self._available = None

    async def _ensure_client(self):
        if self._available is not None:
            return self._available
        oai = _get_openai()
        if oai and settings.openai_api_key:
            try:
                self._client = oai(api_key=settings.openai_api_key)
                self._available = True
                return True
            except Exception:
                pass
        self._available = False
        return False

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if await self._ensure_client():
            response = await self._client.embeddings.create(
                model=self.model, input=texts,
            )
            return [d.embedding for d in response.data]

        # Fallback: deterministic hash-based pseudo-embeddings
        # Not semantic, but allows the system to function without OpenAI
        return [_fallback_embedding(t, self.dim) for t in texts]

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]


def _fallback_embedding(text: str, dim: int = 1536) -> list[float]:
    """Deterministic hash-based vector. Same text → same vector. Not semantic."""
    import struct
    h = hashlib.sha256(text.encode()).digest()
    vec = []
    for i in range(dim):
        # Use struct to get floats from hash bytes
        idx = i % (len(h) - 4)
        val = struct.unpack("f", h[idx:idx+4])[0]
        vec.append(max(-1.0, min(1.0, val)))
    return vec
