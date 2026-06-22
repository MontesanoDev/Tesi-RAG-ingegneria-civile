# Assistente RAG per bandi pubblici

Demo Chainlit per il supporto all’analisi di bandi pubblici.

Il prototipo consente di caricare o indicizzare documenti di bando, interrogarli tramite retrieval locale e generare output operativi revisionabili, come riepiloghi e checklist per la candidatura.

Il sistema non sostituisce la valutazione umana o tecnico-amministrativa: serve a orientare l’analisi iniziale, evidenziare requisiti, allegati, scadenze, criteri di valutazione e informazioni mancanti da verificare.

## Obiettivo della demo

L’obiettivo non è realizzare un semplice chatbot su PDF, ma mostrare una pipeline di supporto alla candidatura:

1. caricamento o indicizzazione del bando;
2. estrazione e organizzazione del contenuto;
3. recupero delle informazioni rilevanti tramite RAG;
4. generazione di riepiloghi e checklist operative;
5. revisione umana dell’output prodotto.

Il caso studio principale usa un bando reale della Regione Puglia sull’edilizia scolastica, scelto come benchmark iniziale perché lungo, strutturato, rumoroso e ricco di allegati, requisiti e vincoli.

## Funzionalità principali

* Domande libere sul bando indicizzato, con risposta dai fatti estratti quando possibile.
* Riepilogo operativo del bando.
* Generazione di checklist per la candidatura.
* Estrazione riutilizzabile dei fatti principali del bando.
* Salvataggio della checklist in Markdown.
* Indicizzazione dei PDF presenti in `data/bandi/`.
* Gestione di un profilo aziendale simulato tramite file YAML.
* Fonti leggibili con riferimento alle pagine del documento.
* Routing leggero delle richieste per distinguere saluti, profilo aziendale, riepilogo, checklist e domande documentali.

## Comandi disponibili

### `/index`

Indicizza o aggiorna i PDF presenti in:

```bash
data/bandi/
```

Usare questo comando dopo aver aggiunto o modificato i documenti.

### `/checklist`

Genera una checklist operativa per la candidatura.

La checklist usa gli stessi fatti estratti del riepilogo operativo e aggrega informazioni su:

* soggetti ammessi;
* requisiti principali;
* scadenze;
* modalità di presentazione;
* documentazione da trasmettere;
* criteri di valutazione;
* informazioni mancanti;
* obblighi successivi all’eventuale concessione.

### `/facts`

Mostra in formato debug i fatti estratti dal bando:

* oggetto e finalità;
* dotazione finanziaria;
* soggetti ammessi;
* requisiti edificio;
* termini e modalità;
* documentazione;
* criteri;
* obblighi successivi;
* fonti e pagine recuperate.

### `/save`

Salva l’ultima checklist generata in formato Markdown.

Gli output vengono salvati nella cartella:

```bash
outputs/checklist/
```

### `/bando percorso/file.pdf`

Imposta o aggiunge un PDF specifico come documento di bando.

Esempio:

```bash
/bando data/bandi/avviso_edilizia_scolastica_puglia_2025.pdf
```

## Profilo aziendale simulato

Il profilo demo viene letto da:

```bash
data/aziende/mapi_ingegneria.yaml
```

Puoi fare domande come:

```text
Chi siamo?
```

oppure:

```text
Qual è il nostro ruolo?
```

Nel caso studio, MAPI Ingegneria S.r.l. rappresenta una società tecnica simulata che supporta un ente locale nell’analisi del bando e nella preparazione della candidatura. Non è necessariamente il soggetto proponente del bando.

## Query utili per la demo

```text
Riassumi il bando
```

```text
Quali soggetti possono presentare domanda?
```

```text
Qual è la scadenza per presentare l’istanza?
```

```text
Quali documenti devo trasmettere?
```

```text
Quali sono i criteri di valutazione?
```

```text
Quali informazioni mancano per capire se possiamo candidarci?
```

```text
/checklist
```

## Ricostruzione dell’indice

Quando cambiano PDF, metadata, nomi delle fonti o logica di indicizzazione, è consigliabile ricostruire l’indice da zero.

Su sistemi Unix/macOS:

```bash
./scripts/reset_db_unix.sh
```

In alternativa, eliminare manualmente la cartella del vector store locale e rieseguire:

```bash
/index
```

oppure lo script di indicizzazione previsto dal progetto.

## Flusso consigliato per la demo

1. Verificare che il PDF del bando sia presente in `data/bandi/`.
2. Ricostruire l’indice se i documenti o i metadata sono cambiati.
3. Avviare Chainlit.
4. Verificare il contesto con una domanda semplice, ad esempio:

```text
Quali soggetti possono presentare domanda?
```

5. Chiedere un riepilogo generale:

```text
Riassumi il bando
```

6. Generare la checklist operativa:

```text
/checklist
```

7. Salvare l’output:

```text
/save
```

## Limiti attuali

Il prototipo è pensato come MVP e presenta alcuni limiti intenzionali:

* non compila automaticamente una candidatura completa;
* non sostituisce la revisione di un esperto;
* non esegue OCR su documenti scansionati;
* non verifica automaticamente la validità giuridica delle informazioni;
* la qualità delle risposte dipende dalla qualità del parsing, dell’indicizzazione e del retrieval;
* eventuali informazioni mancanti devono essere controllate manualmente.

## Ruolo del RAG

Il RAG viene usato come componente di recupero e grounding.

Non rappresenta l’intero sistema, ma serve a:

* recuperare sezioni rilevanti del bando;
* ridurre risposte non fondate sul documento;
* mantenere riferimenti alle fonti;
* supportare la generazione di output revisionabili.

La logica applicativa distingue diversi tipi di richiesta: domande puntuali, riepiloghi, checklist, saluti e domande sul profilo aziendale. In questo modo il retrieval documentale viene attivato solo quando necessario.
