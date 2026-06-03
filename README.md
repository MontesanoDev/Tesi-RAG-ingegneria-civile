# Sistema RAG per Bandi di ingegneria civie

Prototipo sviluppato per una tesi triennale in Informatica L-31 Università degli studi di Bari Aldo Moro

Il progetto implementa una pipeline di **Retrieval-Augmented Generation (RAG)** per interrogare documenti amministrativi italiani, con particolare attenzione a bandi regionali relativi a opere pubbliche, infrastrutture e ambiti affini all'ingegneria civile.

Il sistema indicizza documenti in formato PDF all'interno di un database vettoriale locale e mette a disposizione un'interfaccia conversazionale tramite Chainlit.

## Funzionalità principali

- Ingestione di documenti PDF da una cartella locale
- Estrazione e suddivisione del testo in chunk
- Generazione di embeddings multilingua tramite `sentence-transformers`
- Salvataggio dei vettori in locale con ChromaDB
- Orchestrazione della pipeline RAG tramite LlamaIndex
- Generazione delle risposte tramite API compatibile OpenAI, nel prototipo DeepSeek
- Interfaccia chat realizzata con Chainlit
- Visualizzazione dei documenti sorgente utilizzati per la risposta
- Output di debug con chunk recuperati e relativi score di similarità

## Struttura del progetto

```text
.
├── app.py              # Applicazione Chainlit per interrogare il sistema RAG
├── ingest.py           # Script per indicizzare i documenti in ChromaDB
├── dati_azienda/       # Cartella contenente i PDF/documenti da indicizzare
├── chroma_db/          # Database vettoriale locale generato dopo l'ingestione
├── .env                # Variabili d'ambiente, da non caricare su GitHub
├── requirements.txt    # Dipendenze Python
└── README.md
```

## Componenti principali

### `ingest.py`

Questo script prepara la base documentale del sistema.

Esegue le seguenti operazioni:

1. carica i documenti presenti nella cartella `./dati_azienda`;
2. divide il testo in frammenti più piccoli tramite `SentenceSplitter`;
3. genera gli embeddings usando il modello `paraphrase-multilingual-MiniLM-L12-v2`;
4. salva i vettori ottenuti all'interno di un database ChromaDB persistente;
5. ricrea il database vettoriale da zero a ogni esecuzione.

Questo script deve essere eseguito ogni volta che vengono aggiunti, rimossi o modificati i documenti da indicizzare.

### `app.py`

Questo script avvia l'interfaccia conversazionale con Chainlit.

Esegue le seguenti operazioni:

1. carica il database ChromaDB esistente da `./chroma_db`;
2. ricostruisce un indice LlamaIndex a partire dal vector store;
3. crea un query engine con:
   - streaming della risposta;
   - `similarity_top_k=8`;
   - prompt personalizzato in italiano per documenti amministrativi;
4. invia le domande dell'utente alla pipeline RAG;
5. genera la risposta tramite il modello LLM;
6. mostra i documenti sorgente utilizzati nella risposta.

## Requisiti

- Python 3.10 o superiore
- Una API key (es OpenAi/Antrophic)
- Documenti PDF da indicizzare, inseriti nella cartella `./dati_azienda`

## Installazione

Creare un ambiente virtuale:

```bash
python -m venv .venv
```

Attivare l'ambiente virtuale.

Su Linux/macOS:

```bash
source .venv/bin/activate
```

Su Windows:

```bash
.venv\Scripts\activate
```

Installare le dipendenze:

```bash
pip install -r requirements.txt
```

Esempio di file `requirements.txt`:

```txt
chainlit
chromadb
python-dotenv
llama-index
llama-index-vector-stores-chroma
llama-index-llms-openai-like
llama-index-embeddings-huggingface
sentence-transformers
pypdf
pymupdf
```

## Variabili d'ambiente

Creare un file `.env` nella root del progetto:

```env
DEEPSEEK_API_KEY=your_api_key_here
```

Nel prototipo, DeepSeek viene utilizzato tramite l'interfaccia OpenAI-compatible di LlamaIndex:

```python
OpenAILike(
    model="deepseek-chat",
    api_base="https://api.deepseek.com",
)
```

## Dataset

Inserire i documenti da indicizzare nella cartella `dati_azienda`:

```text
dati_azienda/
├── bando_1.pdf
├── bando_2.pdf
└── bando_3.pdf
```

Il progetto è pensato per lavorare con documenti amministrativi reali, generalmente pubblicati dagli enti pubblici in formato PDF.

I documenti pubblici utilizzati per il test non devono necessariamente essere redistribuiti direttamente nella repository. Quando opportuno, la repository può contenere solo link ufficiali alle fonti e metadati estratti.

## Utilizzo

### 1. Indicizzazione dei documenti

Eseguire lo script di ingestione:

```bash
python ingest.py
```

Lo script:

- legge i documenti presenti in `./dati_azienda`;
- li suddivide in chunk;
- genera gli embeddings;
- ricrea il database locale ChromaDB in `./chroma_db`.

Al termine dell'esecuzione viene stampato il numero di chunk salvati nel database.

### 2. Avvio dell'applicazione Chainlit

Eseguire:

```bash
chainlit run app.py
```

Successivamente aprire l'interfaccia Chainlit nel browser e porre domande sui documenti indicizzati.

## Esempi di domande

```text
Qual è la scadenza del bando?
```

```text
Chi sono i beneficiari ammessi?
```

```text
Quali interventi sono finanziabili?
```

```text
Qual è l'importo massimo del contributo?
```

```text
Quali documenti devono essere presentati?
```

## Pipeline RAG

La pipeline attuale segue questi passaggi:

1. **Ingestione dei documenti**  
   I documenti vengono caricati dalla cartella locale `dati_azienda`.

2. **Chunking**  
   Il testo viene suddiviso in frammenti più piccoli tramite:

   ```python
   SentenceSplitter(chunk_size=256, chunk_overlap=30)
   ```

3. **Embedding**  
   Ogni chunk viene convertito in un vettore numerico usando:

   ```text
   sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
   ```

   Il modello è adatto al retrieval semantico multilingua e funziona anche con testi in italiano.

4. **Archiviazione vettoriale**  
   I vettori vengono salvati localmente tramite ChromaDB.

5. **Retrieval**  
   Quando l'utente pone una domanda, il sistema recupera i chunk più rilevanti dal database vettoriale.

6. **Generazione della risposta**  
   I chunk recuperati vengono forniti come contesto al modello LLM, che genera una risposta in italiano.

7. **Visualizzazione delle fonti**  
   L'interfaccia mostra i documenti utilizzati come fonti per la risposta.

## Prompt personalizzato

L'applicazione utilizza un prompt personalizzato in italiano, pensato per documenti amministrativi.

Il modello viene istruito a:

- rispondere principalmente usando il contesto fornito;
- non inventare date, nomi, importi o requisiti non presenti nei documenti;
- indicare esplicitamente quando un'informazione non è disponibile nei documenti indicizzati;
- rispondere in modo chiaro e completo in italiano.

## Stato attuale del prototipo

Il progetto è un prototipo sperimentale e non un sistema pronto per la produzione.

Limitazioni attuali:

- i documenti vengono selezionati manualmente;
- il database vettoriale viene ricreato da zero durante l'ingestione;
- la visualizzazione delle fonti mostra il nome del documento, non ancora la citazione precisa per pagina;
- eventuali PDF scansionati potrebbero richiedere OCR prima dell'ingestione;
- il modulo di ricerca web tramite agenti non è ancora implementato.

## Possibili sviluppi futuri

- ricerca automatica di bandi regionali tramite agenti web;
- estrazione strutturata di metadati dai bandi;
- esportazione dei risultati in Excel/CSV;
- citazioni puntuali a livello di pagina;
- supporto OCR per PDF scansionati;
- metriche di valutazione della qualità del retrieval;
- confronto tra diversi modelli di embedding;
- dashboard per monitorare documenti indicizzati e campi estratti.

## Licenza

Il codice sorgente è rilasciato con licenza MIT.

Le dipendenze di terze parti mantengono le rispettive licenze originali.

I documenti pubblici utilizzati per i test non vengono redistribuiti, salvo dove esplicitamente consentito dalla fonte originale.
