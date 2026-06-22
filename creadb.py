import argparse
import shutil
from pathlib import Path

from src.indexing.index_builder import (
    DEFAULT_COLLECTION,
    DEFAULT_DATA_DIR,
    DEFAULT_INDEX_DIR,
    build_or_update_index,
)

FACTS_CACHE_PATH = Path("outputs/cache/bando_facts.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Costruisce l'indice locale ChromaDB per i PDF dei bandi."
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--force", action="store_true", help="Ricrea l'indice.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Elimina prima l'intera directory dell'indice ChromaDB.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.reset:
        index_dir = Path(args.index_dir)
        if index_dir.exists():
            shutil.rmtree(index_dir)
            print(f"Indice eliminato: {index_dir}")
        if FACTS_CACHE_PATH.exists():
            FACTS_CACHE_PATH.unlink()
            print(f"Cache facts eliminata: {FACTS_CACHE_PATH}")

    result = build_or_update_index(
        data_dir=args.data_dir,
        index_dir=args.index_dir,
        collection_name=args.collection,
        force=args.force or args.reset,
    )
    if (args.force or result["status"] == "built") and FACTS_CACHE_PATH.exists():
        FACTS_CACHE_PATH.unlink()
        print(f"Cache facts eliminata: {FACTS_CACHE_PATH}")
    print(result["message"])
    print(f"PDF trovati: {result['pdf_count']}")
    print(f"Chunk indicizzati: {result['chunks']}")
    print(f"Indice: {result['index_dir']}")
    print(f"Collection: {result['collection']}")


if __name__ == "__main__":
    main()
