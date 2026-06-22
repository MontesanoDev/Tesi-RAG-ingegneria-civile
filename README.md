# MVP Chainlit/RAG per supporto alla candidatura a bandi

Prototipo sviluppato per la tesi triennale in Informatica L-31 presso l'Università degli Studi di Bari Aldo Moro.

Il progetto implementa una pipeline locale per l'analisi preliminare di un bando e la generazione di una checklist operativa revisionabile. Il RAG non viene trattato come soluzione completa, ma come componente centrale di retrieval e grounding dentro una pipeline piu' ampia.

Il sistema indicizza PDF caricati manualmente in un database vettoriale locale, permette interrogazioni grounded sul documento e produce una checklist Markdown con requisiti, allegati, scadenze, vincoli, informazioni aziendali necessarie e punti da verificare.

## Funzionalità principali

- Selezione o caricamento manuale di PDF del bando
- Estrazione testo pagina per pagina con metadati di fonte
- Suddivisione del testo in chunk
- Generazione di embeddings multilingua tramite `sentence-transformers`
- Salvataggio dei vettori in locale con ChromaDB
- Orchestrazione della pipeline RAG tramite LlamaIndex
- Query libera grounded sul bando
- Generazione checklist Markdown revisionabile
- Evidenza di informazioni mancanti o da verificare
- Generazione delle risposte tramite modello LLM configurabile
- Supporto a endpoint compatibili con API in stile OpenAI
- Possibilità di utilizzare provider esterni o server universitari/aziendali
- Interfaccia chat realizzata con Chainlit
- Visualizzazione dei documenti sorgente utilizzati per la risposta
- Output di debug con chunk recuperati e relativi score di similarità

## Struttura del progetto

```text
.
├── app.py                         # Wrapper Chainlit verso src/ui/chainlit_app.py
├── creadb.py                      # Wrapper CLI per costruire/aggiornare l'indice
├── src/
│   ├── parsing/pdf_parser.py      # Estrazione testo dai PDF con metadati pagina
│   ├── indexing/index_builder.py  # Chunking e indicizzazione ChromaDB
│   ├── retrieval/rag_engine.py    # Query grounded tramite LlamaIndex
│   ├── generation/checklist_generator.py
│   └── ui/chainlit_app.py         # UI minima Chainlit
├── data/
│   ├── bandi/                     # PDF dei bandi caricati manualmente
│   └── aziende/                   # Profilo aziendale simulato, es. mapi_ingegneria.yaml
├── outputs/checklist/             # Checklist Markdown salvate dalla UI
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

### `creadb.py`

Questo script prepara l'indice locale del bando.

Esegue le seguenti operazioni:

1. carica i PDF presenti in `./data/bandi`;
2. estrae testo e metadati pagina;
3. divide il testo in frammenti tramite `SentenceSplitter`;
4. genera embeddings usando `paraphrase-multilingual-MiniLM-L12-v2`;
5. salva i vettori in ChromaDB locale;
6. evita di ricreare l'indice se i PDF non sono cambiati, salvo opzione `--force`.

Esempio:

```bash
python creadb.py --data-dir data/bandi
```

### `app.py`

Questo script avvia l'interfaccia minimale Chainlit.

Esegue le seguenti operazioni:

1. permette di caricare o selezionare un PDF;
2. lancia la costruzione indice con `/index`;
3. esegue query libere sul bando;
4. genera checklist con `/checklist`;
5. salva l'ultima checklist con `/save`;
6. mostra le fonti recuperate quando disponibili.

La logica applicativa resta nei moduli sotto `src/`; la UI orchestra soltanto i componenti.

## Requisiti

- `uv` (consigliato), oppure Python 3.10 o superiore con `pip`
- Una API key per il provider LLM scelto, oppure credenziali/endpoint di un server universitario o aziendale
- Documenti PDF da indicizzare, inseriti nella cartella `./data/bandi`
- Profilo aziendale simulato opzionale in `./data/aziende/mapi_ingegneria.yaml`

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

Gli script di setup usano `uv` quando è disponibile, con fallback automatico a `pip`.
Creano o utilizzano l'ambiente virtuale del progetto e installano le dipendenze presenti in `requirements.txt`.
Con `uv` non è necessario avere `pip`; se Python 3.12 non è disponibile, `uv` può installarlo automaticamente.
Su Linux e Windows installano prima la versione CPU-only di PyTorch, evitando il download non necessario delle librerie NVIDIA/CUDA.

### Installazione manuale

In alternativa, è possibile installare il progetto manualmente con `uv` oppure `pip`.

Con `uv`:

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python -r requirements.txt
```

Su Windows sostituire `.venv/bin/python` con `.venv\Scripts\python.exe`.
Su macOS non è necessario il comando separato per PyTorch CPU-only.

Con `pip`, creare un ambiente virtuale:

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

Su Linux e Windows, installare prima PyTorch CPU-only:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

Poi installare le altre dipendenze:

```bash
pip install -r requirements.txt
```

Su macOS è sufficiente eseguire direttamente `pip install -r requirements.txt`.

Esempio di file `requirements.txt`:

```txt
chainlit
llama-index-core
llama-index-vector-stores-chroma
chromadb
llama-index-llms-openai-like
llama-index-embeddings-huggingface
pypdf
python-dotenv
```

Il progetto installa `llama-index-core` e solo le integrazioni effettivamente usate,
evitando il metapacchetto `llama-index` e le sue integrazioni starter aggiuntive.
I PDF vengono letti direttamente con `pypdf`, senza il plugin generalista
`llama-index-readers-file`.

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
data/bandi/
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

Questa operazione esegue `creadb.py`, estrae il contenuto dei PDF, genera gli embeddings e aggiorna il database vettoriale locale nella cartella `chroma_db`.

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

Inserire i PDF dei bandi nella cartella `data/bandi`:

```text
data/bandi/
├── bando_1.pdf
├── bando_2.pdf
└── bando_3.pdf
```

Il progetto è pensato per lavorare con documenti amministrativi reali, generalmente pubblicati dagli enti pubblici in formato PDF.

Il profilo aziendale simulato può essere salvato in:

```text
data/aziende/mapi_ingegneria.yaml
```

Questo file non viene indicizzato come bando: viene usato come contesto strutturato per capire quali informazioni aziendali risultano già disponibili e quali restano da verificare.

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
python creadb.py
```

Lo script:

- legge i PDF presenti in `./data/bandi`;
- li suddivide in chunk;
- genera gli embeddings;
- crea o aggiorna il database locale ChromaDB in `./chroma_db`.

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

Successivamente aprire l'interfaccia Chainlit nel browser. I comandi principali sono:

```text
/index
/checklist
/save
/bando percorso/file.pdf
```

Una domanda senza prefisso viene trattata come query libera sul bando indicizzato.

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
/checklist
```

```text
Questo bando è rilevante per un'azienda che opera nell'ambito dell'ingegneria civile?
```

## Pipeline RAG

La pipeline attuale segue questi passaggi:

1. **Ingestione dei documenti**  
   I documenti vengono caricati dalla cartella locale `data/bandi`.

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
- il profilo aziendale è simulato e va completato a mano;
- eventuali PDF scansionati potrebbero richiedere OCR prima dell'ingestione;
- le fonti dipendono dai metadati estraibili dal PDF e dalla qualita' del testo recuperato;
- la checklist e' un supporto revisionabile, non una candidatura completa.

## Possibili sviluppi futuri

- confronto tra il bando e un profilo aziendale piu' completo;
- verifica preliminare automatica dei requisiti di ammissibilita';
- estrazione strutturata di metadati dai bandi;
- esportazione dei risultati in Markdown, DOCX o PDF;
- supporto OCR per PDF scansionati;
- metriche di valutazione della qualita' del retrieval;
- confronto tra diversi modelli di embedding;
- integrazione con server LLM universitari o aziendali.

## Licenza

Il codice sorgente è rilasciato con licenza MIT.

Le dipendenze di terze parti mantengono le rispettive licenze originali.

I documenti pubblici utilizzati per i test non vengono redistribuiti, salvo dove esplicitamente consentito dalla fonte originale.
