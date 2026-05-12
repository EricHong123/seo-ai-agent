import fitz  # PyMuPDF


async def parse_pdf(file_path: str) -> str:
    doc = fitz.open(file_path)
    text_parts: list[str] = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)
