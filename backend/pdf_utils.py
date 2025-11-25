from pathlib import Path
from typing import Optional

import pdfplumber


def extract_text(pdf_path: Path, max_pages: int = 5) -> str:
    """
    Return concatenated text from the first `max_pages` pages of a PDF.
    """
    text_parts: list[str] = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages[:max_pages]:
            page_text = page.extract_text() or ""
            if page_text.strip():
                text_parts.append(page_text)
    return "\n\n".join(text_parts)
