import argparse

from src.indexing.index_builder import (
    DEFAULT_COLLECTION,
    DEFAULT_DATA_DIR,
    DEFAULT_INDEX_DIR,
    build_or_update_index,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Costruisce l'indice locale ChromaDB per i PDF dei bandi."
    )
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA_DIR))
    parser.add_argument("--index-dir", default=str(DEFAULT_INDEX_DIR))
    parser.add_argument("--collection", default=DEFAULT_COLLECTION)
    parser.add_argument("--force", action="store_true", help="Ricrea l'indice.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_or_update_index(
        data_dir=args.data_dir,
        index_dir=args.index_dir,
        collection_name=args.collection,
        force=args.force,
    )
    print(result["message"])
    print(f"PDF trovati: {result['pdf_count']}")
    print(f"Chunk indicizzati: {result['chunks']}")
    print(f"Indice: {result['index_dir']}")
    print(f"Collection: {result['collection']}")


if __name__ == "__main__":
    main()
