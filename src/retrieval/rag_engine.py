import os
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

QA_PROMPT_TMPL = (
    "Sei un assistente esperto di documentazione amministrativa italiana.\n"
    "Rispondi basandoti esclusivamente sul contesto fornito.\n"
    "Regole:\n"
    "- Non inventare nomi, date, importi, requisiti o allegati non presenti nel contesto.\n"
    "- Se il contesto contiene informazioni parziali, indica chiaramente cosa e' da verificare.\n"
    "- Se il contesto non contiene informazioni rilevanti, rispondi: "
    "'Informazione non trovata nei documenti caricati.'\n"
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
    source = metadata.get("source")
    if source:
        return str(source)

    file_name = metadata.get("file_name", "Documento sconosciuto")
    page = metadata.get("page")
    return f"{file_name}, pagina {page}" if page else str(file_name)


def _node_metadata(node: Any) -> dict[str, Any]:
    metadata = getattr(node, "metadata", None)
    if metadata is not None:
        return metadata
    inner_node = getattr(node, "node", None)
    return getattr(inner_node, "metadata", {}) or {}


def format_sources(source_nodes: list[Any]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()

    for node in source_nodes:
        metadata = _node_metadata(node)
        key = (metadata.get("file_name", ""), metadata.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "source": _format_source(metadata),
                "file_name": metadata.get("file_name"),
                "page": metadata.get("page"),
                "score": node.score,
            }
        )

    return sources


class RagEngine:
    def __init__(
        self,
        index_dir: str | Path = DEFAULT_INDEX_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        similarity_top_k: int = 8,
        streaming: bool = True,
    ) -> None:
        self.index_dir = Path(index_dir)
        self.collection_name = collection_name
        self.similarity_top_k = similarity_top_k
        self.streaming = streaming
        self.query_engine = self._load_query_engine()

    def _load_query_engine(self):
        configure_llm()
        configure_embedding_model()

        db = chromadb.PersistentClient(path=str(self.index_dir))
        collection = db.get_or_create_collection(self.collection_name)
        if collection.count() == 0:
            raise FileNotFoundError(
                "Indice non presente o vuoto. Costruisci prima l'indice del bando."
            )

        vector_store = ChromaVectorStore(chroma_collection=collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        return index.as_query_engine(
            streaming=self.streaming,
            similarity_top_k=self.similarity_top_k,
            text_qa_template=PromptTemplate(QA_PROMPT_TMPL),
        )

    def query(self, question: str):
        if not question or not question.strip():
            raise ValueError("Query vuota.")
        response = self.query_engine.query(question.strip())
        return {
            "response": response,
            "answer": "" if self.streaming else str(response),
            "sources": format_sources(response.source_nodes),
        }


def query_bando(question: str, **kwargs) -> dict[str, Any]:
    return RagEngine(**kwargs).query(question)
