import httpx
from bs4 import BeautifulSoup


async def fetch_url(url: str) -> str:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; SEO-AI-Agent/1.0)",
        })
        response.raise_for_status()
        return response.text
