import re
from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader

from src.source_display import display_name_for_file, format_display_source


SECTION_RE = re.compile(r"^\s*(\d+(?:\.\d+)*\.?)\s+(.{4,120})$")


def _detect_section(text: str) -> str | None:
    for line in text.splitlines()[:12]:
        match = SECTION_RE.match(line.strip())
        if match:
            title = re.sub(r"\s+", " ", match.group(2)).strip()
            return f"{match.group(1).rstrip('.')} {title}"
    return None


def extract_pdf_documents(pdf_path: str | Path) -> list[Document]:
    """Extract one LlamaIndex document per PDF page, preserving page metadata."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF non trovato: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Il file non e' un PDF: {path}")

    reader = PdfReader(str(path))
    documents: list[Document] = []
    display_name = display_name_for_file(path.name)

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue

        section_title = _detect_section(text)
        metadata = {
            "file_name": path.name,
            "original_filename": path.name,
            "display_name": display_name,
            "file_path": str(path),
            "page": page_index,
            "section": section_title,
            "section_title": section_title,
        }
        metadata["source"] = format_display_source(metadata)

        documents.append(
            Document(
                text=text,
                metadata=metadata,
            )
        )

    if not documents:
        raise ValueError(
            "Il PDF non contiene testo estraibile. "
            "Potrebbe essere una scansione e richiedere OCR."
        )

    return documents


def load_pdf_documents(directory: str | Path) -> list[Document]:
    directory_path = Path(directory)
    if not directory_path.exists():
        raise FileNotFoundError(f"Cartella PDF non trovata: {directory_path}")

    documents: list[Document] = []
    pdf_paths = sorted(directory_path.rglob("*.pdf"))
    if not pdf_paths:
        raise FileNotFoundError(f"Nessun PDF trovato in: {directory_path}")

    for pdf_path in pdf_paths:
        documents.extend(extract_pdf_documents(pdf_path))

    return documents
