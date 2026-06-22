import hashlib
import json
from pathlib import Path
from typing import Any

import chromadb
from chromadb.errors import NotFoundError
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.parsing.pdf_parser import load_pdf_documents

DEFAULT_DATA_DIR = Path("data/bandi")
DEFAULT_INDEX_DIR = Path("chroma_db")
DEFAULT_COLLECTION = "bandi_mvp"
DEFAULT_MANIFEST = "index_manifest.json"


def configure_embedding_model() -> None:
    Settings.embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    Settings.node_parser = SentenceSplitter(chunk_size=256, chunk_overlap=30)


def _pdf_inventory(data_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path),
            "name": path.name,
            "size": path.stat().st_size,
            "mtime": path.stat().st_mtime,
        }
        for path in sorted(data_dir.rglob("*.pdf"))
        if path.is_file()
    ]


def _fingerprint(inventory: list[dict[str, Any]]) -> str:
    payload = json.dumps(inventory, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _manifest_path(index_dir: Path) -> Path:
    return index_dir / DEFAULT_MANIFEST


def _read_manifest(index_dir: Path) -> dict[str, Any] | None:
    path = _manifest_path(index_dir)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(index_dir: Path, manifest: dict[str, Any]) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    _manifest_path(index_dir).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _get_collection(index_dir: Path, collection_name: str):
    db = chromadb.PersistentClient(path=str(index_dir))
    return db, db.get_or_create_collection(collection_name)


def index_exists(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    index_dir: str | Path = DEFAULT_INDEX_DIR,
    collection_name: str = DEFAULT_COLLECTION,
) -> bool:
    data_path = Path(data_dir)
    index_path = Path(index_dir)
    inventory = _pdf_inventory(data_path) if data_path.exists() else []
    manifest = _read_manifest(index_path)
    if not inventory or not manifest:
        return False

    _, collection = _get_collection(index_path, collection_name)
    return (
        manifest.get("fingerprint") == _fingerprint(inventory)
        and manifest.get("collection") == collection_name
        and collection.count() > 0
    )


def build_or_update_index(
    data_dir: str | Path = DEFAULT_DATA_DIR,
    index_dir: str | Path = DEFAULT_INDEX_DIR,
    collection_name: str = DEFAULT_COLLECTION,
    force: bool = False,
) -> dict[str, Any]:
    data_path = Path(data_dir)
    index_path = Path(index_dir)
    inventory = _pdf_inventory(data_path) if data_path.exists() else []
    if not inventory:
        raise FileNotFoundError(f"Nessun PDF trovato in {data_path}.")

    current_fingerprint = _fingerprint(inventory)
    if not force and index_exists(data_path, index_path, collection_name):
        _, collection = _get_collection(index_path, collection_name)
        return {
            "status": "skipped",
            "message": "Indice gia' aggiornato.",
            "chunks": collection.count(),
            "pdf_count": len(inventory),
            "index_dir": str(index_path),
            "collection": collection_name,
        }

    configure_embedding_model()
    documents = load_pdf_documents(data_path)

    db = chromadb.PersistentClient(path=str(index_path))
    try:
        db.delete_collection(collection_name)
    except NotFoundError:
        pass
    collection = db.get_or_create_collection(collection_name)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    VectorStoreIndex.from_documents(documents, storage_context=storage_context)

    manifest = {
        "collection": collection_name,
        "fingerprint": current_fingerprint,
        "pdfs": inventory,
        "document_pages": len(documents),
        "chunks": collection.count(),
    }
    _write_manifest(index_path, manifest)

    return {
        "status": "built",
        "message": "Indice creato o aggiornato.",
        "chunks": collection.count(),
        "pdf_count": len(inventory),
        "pages": len(documents),
        "index_dir": str(index_path),
        "collection": collection_name,
    }
