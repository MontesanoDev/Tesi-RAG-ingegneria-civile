import shutil
import chromadb
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext, Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 1. Embedding model
Settings.embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

# 2. Chunking più preciso
Settings.node_parser = SentenceSplitter(
    chunk_size=256,
    chunk_overlap=30,
)

# 3. Carica i documenti
print("Lettura dei documenti aziendali in corso...")
documents = SimpleDirectoryReader("./dati_azienda").load_data()

for doc in documents:
    print(f"{doc.metadata.get('file_name', '?')} - {len(doc.text)} chars")

# 4. Cancella il vecchio database e ricrea da zero
shutil.rmtree("./chroma_db", ignore_errors=True)

print("Creazione del Vector Database (ChromaDB)")
db = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = db.get_or_create_collection("tesi_rag")

# 5. Collega LlamaIndex a ChromaDB
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# 6. Ingestione: chunking + embedding + salvataggio su disco
index = VectorStoreIndex.from_documents(
    documents, storage_context=storage_context
)

print(f"Ingestione completa! Salvati {len(chroma_collection.get()['ids'])} chunk nel database.")