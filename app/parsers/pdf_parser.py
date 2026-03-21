from typing import Optional
import fitz  # PyMuPDF


def parse_pdf(file_path: str, document_name: str) -> list[dict]:
    """Parse a PDF file and return a list of text chunks with metadata."""
    pages: list[dict] = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text").strip()
        if text:
            pages.append(
                {
                    "text": text,
                    "metadata": {
                        "document_name": document_name,
                        "page": page_num + 1,
                        "source_type": "pdf",
                    },
                }
            )
    doc.close()
    return pages
