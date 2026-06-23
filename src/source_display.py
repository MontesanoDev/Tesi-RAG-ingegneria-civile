import re
from pathlib import Path
from typing import Any


DOCUMENT_DISPLAY_NAMES = {
    "509c5dd0-6b28-4166-ba2a-2b39e980cc60.pdf": "Avviso Edilizia Scolastica Puglia 2025",
    "2cec3ece-e5ae-41b9-a436-3097a27b3625.pdf": "Avviso Edilizia Scolastica Puglia 2025",
}

UUID_FILENAME_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.pdf$",
    re.IGNORECASE,
)
SOURCE_PAGE_RE = re.compile(
    r"(?P<file>[^,/\\]+\.pdf).*?(?:pag(?:ina)?\.?\s*)(?P<page>\d+)",
    re.IGNORECASE,
)
VISIBLE_PDF_RE = re.compile(
    r"(?P<file>[A-Za-z0-9_.-]+\.pdf)(?:,\s*(?:pag(?:ina)?\.?\s*)(?P<page>\d+))?",
    re.IGNORECASE,
)


def display_name_for_file(file_name: str | None) -> str:
    if not file_name:
        return "Documento sconosciuto"

    name = Path(file_name).name
    mapped_name = DOCUMENT_DISPLAY_NAMES.get(name)
    if mapped_name:
        return mapped_name

    stem = Path(name).stem
    if UUID_FILENAME_RE.match(name):
        return "Avviso Edilizia Scolastica Puglia 2025"

    normalized = re.sub(r"[_-]+", " ", stem).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.title() if normalized else name


def format_display_source(metadata: dict[str, Any]) -> str:
    source = str(metadata.get("source") or "")
    source_match = SOURCE_PAGE_RE.search(source)
    fallback_file_name = source_match.group("file") if source_match else None
    fallback_page = int(source_match.group("page")) if source_match else None

    metadata_display_name = metadata.get("display_name")
    file_display_name = display_name_for_file(
        metadata.get("original_filename") or metadata.get("file_name") or fallback_file_name
    )
    display_name = (
        metadata_display_name
        if metadata_display_name and metadata_display_name != "Bando caricato"
        else file_display_name
    )
    page = metadata.get("page")

    parts = [str(display_name)]
    if page or fallback_page:
        parts.append(f"pag. {page or fallback_page}")

    return ", ".join(parts)


def normalize_visible_sources(text: str) -> str:
    def replace(match: re.Match) -> str:
        file_name = match.group("file")
        page = match.group("page")
        display_name = display_name_for_file(file_name)
        return f"{display_name}, pag. {page}" if page else display_name

    return VISIBLE_PDF_RE.sub(replace, text)
