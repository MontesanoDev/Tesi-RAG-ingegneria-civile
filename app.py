import os

import chainlit as cl
import chromadb
from dotenv import load_dotenv
from llama_index.core import PromptTemplate, Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai_like import OpenAILike
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

# --- CONFIGURAZIONE LLM ---
llm_model = os.getenv("LLM_MODEL")
llm_api_key = os.getenv("LLM_API_KEY")
llm_api_base = os.getenv("LLM_API_BASE")
llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))

if not llm_model or not llm_api_key or not llm_api_base:
    raise ValueError(
        "Configurazione LLM mancante. "
        "Imposta LLM_MODEL, LLM_API_KEY e LLM_API_BASE nel file .env."
    )

Settings.llm = OpenAILike(
    model=llm_model,
    api_key=llm_api_key,
    api_base=llm_api_base,
    temperature=llm_temperature,
    is_chat_model=True,
)

# --- CONFIGURAZIONE EMBEDDING ---
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# --- PROMPT PERSONALIZZATO ---
QA_PROMPT_TMPL = (
    "Sei un assistente esperto di documentazione amministrativa italiana.\n"
    "Rispondi basandoti PRINCIPALMENTE sul contesto fornito.\n"
    "Regole:\n"
    "- Usa le informazioni nel contesto per costruire una risposta completa e utile.\n"
    "- Se il contesto contiene informazioni parziali, usa quelle che trovi.\n"
    "- Se il contesto non contiene NESSUNA informazione rilevante, "
    "rispondi: 'Non ho trovato questa informazione nei documenti disponibili.'\n"
    "- Non inventare nomi, date, importi o dati specifici non presenti nel contesto.\n"
    "- Rispondi in italiano in modo chiaro e completo.\n\n"
    "Contesto:\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n\n"
    "Domanda: {query_str}\n"
    "Risposta: "
)
qa_prompt = PromptTemplate(QA_PROMPT_TMPL)


@cl.on_chat_start
async def start():
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection("tesi_rag")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_vector_store(vector_store)

    query_engine = index.as_query_engine(
        streaming=True,
        similarity_top_k=8,
        text_qa_template=qa_prompt,
    )
    cl.user_session.set("query_engine", query_engine)


@cl.on_message
async def main(message: cl.Message):
    query_engine = cl.user_session.get("query_engine")
    msg = cl.Message(content="", author="Lexis AI")
    response = await cl.make_async(query_engine.query)(message.content)

    # DEBUG: mostra nel terminale i chunk recuperati.
    for i, node in enumerate(response.source_nodes):
        print(f"\n=== CHUNK {i + 1} (score: {node.score:.4f}) ===")
        print(f"File: {node.metadata.get('file_name', '?')}")
        print(node.text[:300])
        print("=" * 50)

    for token in response.response_gen:
        await msg.stream_token(token)
    await msg.send()

    source_nodes = response.source_nodes
    if source_nodes:
        seen_sources = {}
        for node in source_nodes:
            file_name = node.metadata.get("file_name", "Documento sconosciuto")
            score = node.score or 0
            if file_name not in seen_sources or score > seen_sources[file_name]:
                seen_sources[file_name] = score

        sources_text = "\n\n---\n**Fonti aziendali consultate:**\n"
        for file_name, score in seen_sources.items():
            sources_text += f"- *{file_name}* (rilevanza: {score * 100:.1f}%)\n"
        await cl.Message(content=sources_text).send()
