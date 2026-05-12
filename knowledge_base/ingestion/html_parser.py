from bs4 import BeautifulSoup


async def parse_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Preserve SEO-relevant structure
    out: list[str] = []
    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "title", "meta"]):
        tag_name = tag.name
        text = tag.get_text(strip=True)
        if not text:
            continue
        if tag_name.startswith("h"):
            out.append(f"\n## {text}")
        elif tag_name == "title":
            out.insert(0, f"# {text}")
        elif tag_name == "meta" and tag.get("name") == "description":
            out.insert(1, f"> {tag.get('content', '')}")
        else:
            out.append(text)

    return "\n\n".join(out)
