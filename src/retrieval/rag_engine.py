import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from llama_index.core import PromptTemplate, Settings, VectorStoreIndex
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.indexing.index_builder import (
    DEFAULT_COLLECTION,
    DEFAULT_INDEX_DIR,
    configure_embedding_model,
)
from src.source_display import format_display_source

QA_PROMPT_TMPL = (
    "Sei un assistente esperto di documentazione amministrativa italiana.\n"
    "Rispondi basandoti esclusivamente sul contesto fornito.\n"
    "Regole:\n"
    "- Non inventare nomi, date, importi, requisiti o allegati non presenti nel contesto.\n"
    "- Se il contesto contiene informazioni parziali, indica chiaramente cosa e' da verificare.\n"
    "- Se il contesto non contiene informazioni rilevanti, rispondi che l'informazione "
    "non e' recuperata nel contesto disponibile e suggerisci di verificare il documento completo.\n"
    "- Rispondi in italiano in modo chiaro e operativo.\n\n"
    "Contesto:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n\n"
    "Domanda: {query_str}\n"
    "Risposta: "
)


def configure_llm() -> None:
    load_dotenv()
    llm_model = os.getenv("LLM_MODEL")
    llm_api_key = os.getenv("LLM_API_KEY")
    llm_api_base = os.getenv("LLM_API_BASE")
    llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    if not llm_model or not llm_api_key or not llm_api_base:
        raise ValueError(
            "Configurazione LLM mancante. Imposta LLM_MODEL, LLM_API_KEY "
            "e LLM_API_BASE nel file .env."
        )

    Settings.llm = OpenAILike(
        model=llm_model,
        api_key=llm_api_key,
        api_base=llm_api_base,
        temperature=llm_temperature,
        is_chat_model=True,
    )


def _format_source(metadata: dict[str, Any]) -> str:
    if (
        metadata.get("display_name")
        or metadata.get("original_filename")
        or metadata.get("file_name")
        or metadata.get("page")
        or metadata.get("source")
    ):
        return format_display_source(metadata)
    return "Documento sconosciuto"


def _node_metadata(node: Any) -> dict[str, Any]:
    metadata = getattr(node, "metadata", None)
    if metadata is not None:
        return metadata
    inner_node = getattr(node, "node", None)
    return getattr(inner_node, "metadata", {}) or {}


def _node_text(node: Any) -> str:
    text = getattr(node, "text", None)
    if text is not None:
        return str(text)
    inner_node = getattr(node, "node", None)
    get_content = getattr(inner_node, "get_content", None)
    if callable(get_content):
        return str(get_content())
    return str(getattr(inner_node, "text", "") or "")


def _normalize_for_search(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return without_accents.lower()


def _search_tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalize_for_search(text))
        if len(token) > 2
    }


def _source_from_metadata(
    metadata: dict[str, Any],
    score: float | None = None,
) -> dict[str, Any]:
    return {
        "source": _format_source(metadata),
        "display_name": metadata.get("display_name"),
        "file_name": metadata.get("file_name"),
        "original_filename": metadata.get("original_filename"),
        "page": metadata.get("page"),
        "section": metadata.get("section"),
        "section_title": metadata.get("section_title") or metadata.get("section"),
        "score": score,
    }


def format_sources(source_nodes: list[Any], dedupe: bool = True) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()

    for node in source_nodes:
        metadata = _node_metadata(node)
        key = (metadata.get("file_name", ""), metadata.get("page"))
        if dedupe and key in seen:
            continue
        seen.add(key)
        sources.append(_source_from_metadata(metadata, score=node.score))

    return sources


class RagEngine:
    def __init__(
        self,
        index_dir: str | Path = DEFAULT_INDEX_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        similarity_top_k: int = 8,
        streaming: bool = True,
        build_query_engine: bool = True,
    ) -> None:
        self.index_dir = Path(index_dir)
        self.collection_name = collection_name
        self.similarity_top_k = similarity_top_k
        self.streaming = streaming
        self.build_query_engine = build_query_engine
        self.collection = None
        self.index = self._load_index()
        self.query_engine = self._build_query_engine() if build_query_engine else None

    def _load_index(self):
        if self.build_query_engine:
            configure_llm()
        configure_embedding_model()

        db = chromadb.PersistentClient(path=str(self.index_dir))
        collection = db.get_or_create_collection(self.collection_name)
        if collection.count() == 0:
            raise FileNotFoundError(
                "Indice non presente o vuoto. Costruisci prima l'indice del bando."
            )
        self.collection = collection

        vector_store = ChromaVectorStore(chroma_collection=collection)
        return VectorStoreIndex.from_vector_store(vector_store)

    def _build_query_engine(self):
        return self.index.as_query_engine(
            streaming=self.streaming,
            similarity_top_k=self.similarity_top_k,
            text_qa_template=PromptTemplate(QA_PROMPT_TMPL),
        )

    def retrieve(
        self,
        question: str,
        similarity_top_k: int | None = None,
        dedupe_sources: bool = False,
    ):
        if not question or not question.strip():
            raise ValueError("Query vuota.")
        retriever = self.index.as_retriever(
            similarity_top_k=similarity_top_k or self.similarity_top_k
        )
        nodes = retriever.retrieve(question.strip())
        return {
            "nodes": nodes,
            "texts": [_node_text(node) for node in nodes],
            "sources": format_sources(nodes, dedupe=dedupe_sources),
        }

    def keyword_search(self, question: str, top_k: int = 8):
        if not question or not question.strip():
            raise ValueError("Query vuota.")
        if self.collection is None:
            raise RuntimeError("Collection Chroma non inizializzata.")

        query_tokens = _search_tokens(question)
        if not query_tokens:
            return {"texts": [], "sources": []}

        result = self.collection.get(include=["documents", "metadatas"])
        documents = result.get("documents") or []
        metadatas = result.get("metadatas") or []
        ranked: list[tuple[float, str, dict[str, Any]]] = []

        for document, metadata in zip(documents, metadatas):
            text = document or ""
            text_tokens = _search_tokens(text)
            if not text_tokens:
                continue
            overlap = query_tokens & text_tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(query_tokens), 1)
            ranked.append((score, text, metadata or {}))

        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = ranked[:top_k]
        return {
            "texts": [text for _, text, _ in selected],
            "sources": [
                _source_from_metadata(metadata, score=score)
                for score, _, metadata in selected
            ],
        }

    def query(self, question: str):
        if not question or not question.strip():
            raise ValueError("Query vuota.")
        if self.query_engine is None:
            raise RuntimeError("Query engine LLM non inizializzato.")
        response = self.query_engine.query(question.strip())
        return {
            "response": response,
            "answer": "" if self.streaming else str(response),
            "sources": format_sources(response.source_nodes),
        }


def query_bando(question: str, **kwargs) -> dict[str, Any]:
    return RagEngine(**kwargs).query(question)
