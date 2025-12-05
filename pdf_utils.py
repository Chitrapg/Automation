from typing import List
import PyPDF2


def extract_pdf_text(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.

    :param pdf_path: Path to the PDF file.
    :return: Concatenated text of all pages.
    """
    reader = PyPDF2.PdfReader(pdf_path)
    text_chunks: List[str] = []

    for page in reader.pages:
        # page.extract_text() can return None, so guard with `or ""`
        text_chunks.append(page.extract_text() or "")

    return "\n".join(text_chunks)
