from docx import Document


async def parse_docx(file_path: str) -> str:
    doc = Document(file_path)
    text_parts: list[str] = []
    for para in doc.paragraphs:
        if para.text.strip():
            text_parts.append(para.text)
    return "\n\n".join(text_parts)
