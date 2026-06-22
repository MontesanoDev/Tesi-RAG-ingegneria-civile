from pathlib import Path

from llama_index.core import Document
from pypdf import PdfReader


def extract_pdf_documents(pdf_path: str | Path) -> list[Document]:
    """Extract one LlamaIndex document per PDF page, preserving page metadata."""
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF non trovato: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Il file non e' un PDF: {path}")

    reader = PdfReader(str(path))
    documents: list[Document] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue

        documents.append(
            Document(
                text=text,
                metadata={
                    "file_name": path.name,
                    "file_path": str(path),
                    "page": page_index,
                    "source": f"{path.name}, pagina {page_index}",
                },
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
