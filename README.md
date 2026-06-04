# Sistema RAG per Bandi di Ingegneria Civile

Prototipo sviluppato per la tesi triennale in Informatica L-31 presso l'Università degli Studi di Bari Aldo Moro.

Il progetto implementa una pipeline di **Retrieval-Augmented Generation (RAG)** per interrogare documenti amministrativi italiani, con particolare attenzione a bandi regionali relativi a opere pubbliche, infrastrutture e ambiti affini all'ingegneria civile.

Il sistema indicizza documenti in formato PDF all'interno di un database vettoriale locale e mette a disposizione un'interfaccia conversazionale tramite Chainlit.

## Funzionalità principali

- Ingestione di documenti PDF da una cartella locale
- Estrazione e suddivisione del testo in chunk
- Generazione di embeddings multilingua tramite `sentence-transformers`
- Salvataggio dei vettori in locale con ChromaDB
- Orchestrazione della pipeline RAG tramite LlamaIndex
- Generazione delle risposte tramite modello LLM configurabile
- Supporto a endpoint compatibili con API in stile OpenAI
- Possibilità di utilizzare provider esterni o server universitari/aziendali
- Interfaccia chat realizzata con Chainlit
- Visualizzazione dei documenti sorgente utilizzati per la risposta
- Output di debug con chunk recuperati e relativi score di similarità

## Struttura del progetto

```text
.
├── app.py                         # Applicazione Chainlit per interrogare il sistema RAG
├── ingest.py                      # Script Python per indicizzare i documenti in ChromaDB
├── dati_azienda/                  # Cartella contenente i PDF/documenti da indicizzare
├── chroma_db/                     # Database vettoriale locale generato dopo l'ingestione
├── scripts/                       # Script per installazione, ingestion e avvio
│   ├── setup_unix.sh              # Setup ambiente e dipendenze su Linux/macOS
│   ├── setup_windows.ps1          # Setup ambiente e dipendenze su Windows PowerShell
│   ├── ingest_chroma_unix.sh      # Indicizzazione documenti su Linux/macOS
│   ├── ingest_chroma_windows.ps1  # Indicizzazione documenti su Windows PowerShell
│   ├── run_chainlit_unix.sh       # Avvio Chainlit su Linux/macOS
│   └── run_chainlit_windows.ps1   # Avvio Chainlit su Windows PowerShell
├── .env                           # Variabili d'ambiente, da non caricare su GitHub
├── .env.example                   # Esempio di configurazione
├── requirements.txt               # Dipendenze Python
└── README.md
```

## Componenti principali

### `createdb.py`

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
3. configura il modello LLM tramite variabili d'ambiente;
4. crea un query engine con:
   - streaming della risposta;
   - `similarity_top_k=8`;
   - prompt personalizzato in italiano per documenti amministrativi;
5. invia le domande dell'utente alla pipeline RAG;
6. genera la risposta tramite il modello LLM configurato;
7. mostra i documenti sorgente utilizzati nella risposta.

## Requisiti

- Python 3.10 o superiore
- Una API key per il provider LLM scelto, oppure credenziali/endpoint di un server universitario o aziendale
- Documenti PDF da indicizzare, inseriti nella cartella `./dati_azienda`

## Installazione

> [!WARNING]
> La prima installazione può richiedere parecchio tempo, anche **oltre 20 minuti**, a seconda della macchina e della connessione.
>
> Durante l'installazione alcune dipendenze possono sembrare ferme o bloccate, soprattutto durante il download o l'installazione di librerie legate a embeddings, modelli NLP, ChromaDB, Chainlit e componenti di LlamaIndex.
>
> Se il terminale non restituisce errori espliciti, **non interrompere subito il processo**: molto probabilmente non è bloccato, sta solo installando pacchetti pesanti.

### Installazione tramite script

La repository include script dedicati per preparare l'ambiente e installare le dipendenze.

Su Linux/macOS:

```bash
chmod +x scripts/setup_unix.sh
./scripts/setup_unix.sh
```

Su Windows PowerShell:

```powershell
.\scripts\setup_windows.ps1
```

Gli script di setup creano o utilizzano l'ambiente virtuale del progetto e installano le dipendenze presenti in `requirements.txt`.

### Installazione manuale

In alternativa, è possibile installare il progetto manualmente.

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
llama-index
llama-index-vector-stores-chroma
chromadb
llama-index-llms-openai-like
llama-index-embeddings-huggingface
llama-index-readers-file
pymupdf
pypdf
python-dotenv
```

## Configurazione del modello LLM

Il progetto NON è vincolato a uno specifico provider LLM.

La configurazione del modello generativo viene gestita tramite variabili d'ambiente, in modo da poter utilizzare:

- API esterne compatibili con il formato OpenAI;
- endpoint locali o remoti messi a disposizione dall'università;
- server aziendali o self-hosted, purché espongano un'interfaccia compatibile;
- eventuali altri adapter supportati da LlamaIndex, modificando solo il blocco di configurazione del modello.

Nel codice viene utilizzato `OpenAILike` di LlamaIndex, che permette di collegare la pipeline RAG a un endpoint compatibile con API in stile OpenAI.

Esempio di configurazione nel file `.env`:

```env
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=your_api_key_here
LLM_API_BASE=https://api.openai.com/v1
LLM_TEMPERATURE=0.1
```

Nel caso di utilizzo di un server universitario o aziendale, è sufficiente modificare le variabili:

```env
LLM_MODEL=nome-modello
LLM_API_KEY=token_o_placeholder
LLM_API_BASE=http://server-universitario:8000/v1
LLM_TEMPERATURE=0.1
```

L'importante è che l'endpoint indicato in `LLM_API_BASE` esponga un'interfaccia compatibile con il formato atteso dal client. In caso contrario, sarà necessario sostituire `OpenAILike` con l'adapter LlamaIndex più adatto al modello o al servizio utilizzato.

Esempio di configurazione lato codice:

```python
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
```

Questa impostazione consente di separare la logica applicativa dal provider effettivamente utilizzato. La pipeline RAG, il database vettoriale e l'interfaccia Chainlit rimangono invariati anche cambiando modello generativo.

## Script di utilità

Oltre agli script di installazione descritti nella sezione precedente, la repository include script per eseguire le due operazioni principali del prototipo:

- indicizzazione dei documenti in ChromaDB;
- avvio dell'interfaccia Chainlit.

### Indicizzazione dei documenti

Prima di avviare l'applicazione, inserire i PDF da analizzare nella cartella:

```text
dati_azienda/
```

Poi eseguire lo script di ingestion.

Su Linux/macOS:

```bash
chmod +x scripts/ingest_chroma_unix.sh
./scripts/ingest_chroma_unix.sh
```

Su Windows PowerShell:

```powershell
.\scripts\ingest_chroma_windows.ps1
```

Questa operazione esegue `ingest.py`, estrae il contenuto dei documenti, genera gli embeddings e ricrea il database vettoriale locale nella cartella `chroma_db`.

### Avvio dell'interfaccia Chainlit

Dopo aver indicizzato i documenti, è possibile avviare l'interfaccia conversazionale.

Su Linux/macOS:

```bash
chmod +x scripts/run_chainlit_unix.sh
./scripts/run_chainlit_unix.sh
```

Su Windows PowerShell:

```powershell
.\scripts\run_chainlit_windows.ps1
```

In alternativa, è sempre possibile avviare manualmente l'applicazione con:

```bash
chainlit run app.py
```

Gli script non modificano la logica del progetto: servono solo a rendere più semplice e ripetibile l'esecuzione delle varie fasi del prototipo.

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

Il progetto può essere eseguito sia tramite comandi manuali sia tramite gli script presenti nella cartella `scripts/`.

### 1. Indicizzazione dei documenti

Metodo consigliato tramite script.

Su Linux/macOS:

```bash
./scripts/ingest_chroma_unix.sh
```

Su Windows PowerShell:

```powershell
.\scripts\ingest_chroma_windows.ps1
```

In alternativa, eseguire manualmente:

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

Metodo consigliato tramite script.

Su Linux/macOS:

```bash
./scripts/run_chainlit_unix.sh
```

Su Windows PowerShell:

```powershell
.\scripts\run_chainlit_windows.ps1
```

In alternativa, eseguire manualmente:

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

```text
Questo bando è rilevante per un'azienda che opera nell'ambito dell'ingegneria civile?
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
   I chunk recuperati vengono forniti come contesto al modello LLM configurato, che genera una risposta in italiano.

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
- dashboard per monitorare documenti indicizzati e campi estratti;
- integrazione con server LLM universitari o aziendali.

## Licenza

Il codice sorgente è rilasciato con licenza MIT.

Le dipendenze di terze parti mantengono le rispettive licenze originali.

I documenti pubblici utilizzati per i test non vengono redistribuiti, salvo dove esplicitamente consentito dalla fonte originale.
