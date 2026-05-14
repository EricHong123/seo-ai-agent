import hashlib

from config.settings import settings
from config.cache import embedding_cache, cache_key

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
        # Check cache first
        results = []
        uncached_indices = []
        for i, t in enumerate(texts):
            key = cache_key("embed", t)
            hit = embedding_cache.get(key)
            if hit is not None:
                results.append((i, hit))
            else:
                uncached_indices.append(i)

        # Fetch uncached embeddings
        if uncached_indices:
            uncached_texts = [texts[i] for i in uncached_indices]
            if await self._ensure_client():
                response = await self._client.embeddings.create(
                    model=self.model, input=uncached_texts,
                )
                new_embeddings = [d.embedding for d in response.data]
            else:
                new_embeddings = [_fallback_embedding(t, self.dim) for t in uncached_texts]

            for idx, emb in zip(uncached_indices, new_embeddings):
                key = cache_key("embed", texts[idx])
                embedding_cache.set(key, emb)
                results.append((idx, emb))

        # Sort back to original order
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    async def embed_query(self, text: str) -> list[float]:
        key = cache_key("embed", text)
        hit = embedding_cache.get(key)
        if hit is not None:
            return hit
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
