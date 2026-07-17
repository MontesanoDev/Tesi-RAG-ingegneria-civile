# Stack tecnico

Aggiornato al 08/07/2026.

## 1. Scopo del documento

Questo documento descrive lo stack tecnico utilizzato nel prototipo.

L'obiettivo non è elencare ogni dettaglio implementativo, ma spiegare quali tecnologie sono state scelte, quale ruolo hanno nel sistema e perché sono coerenti con l'obiettivo del progetto.

Il prototipo è pensato come applicazione locale per analisi preliminare di bandi, interrogazione documentale e generazione di checklist revisionabili.

## 2. Visione generale dello stack

Il sistema è costruito come applicazione Python locale con interfaccia conversazionale.

Lo stack combina:

- parsing di documenti PDF;
- indicizzazione vettoriale locale;
- retrieval semantico;
- generazione tramite modello LLM configurabile;
- estrazione di fatti strutturati dal bando;
- routing delle domande utente;
- interfaccia chat per la demo;
- salvataggio di output Markdown.

Il RAG è quindi una parte dello stack, ma non coincide con l'intera architettura. Attorno al retrieval sono stati aggiunti livelli applicativi per rendere il comportamento più controllabile.

## 3. Linguaggio e ambiente

Il linguaggio principale è Python.

Python è stato scelto perché dispone di un ecosistema maturo per:

- elaborazione di documenti;
- integrazione con modelli linguistici;
- costruzione di pipeline RAG;
- prototipazione rapida;
- sviluppo di interfacce dimostrative.

Non è presente un framework backend complesso: la scelta è stata mantenere il prototipo 'leggero' e locale, concentrandosi sul flusso documentale e sulla demo.

## 4. Interfaccia utente

L'interfaccia è realizzata con Chainlit.

Chainlit è stato scelto perché consente di costruire rapidamente una chat dimostrativa per applicazioni LLM/RAG.

Nel prototipo l'interfaccia permette di:

- caricare o selezionare un PDF;
- avviare l'indicizzazione;
- fare domande in linguaggio naturale;
- generare un riassunto operativo;
- generare una checklist;
- visualizzare le fonti recuperate;
- salvare l'output prodotto.

I comandi dell'interfaccia sono pensati come azioni esplicite. Non usano testo aggiuntivo, salvo il comando di caricamento manuale del PDF, che riceve il percorso del file. Le domande libere vengono invece inviate senza selezionare un comando.

La UI non contiene la logica principale del sistema. Il suo ruolo è orchestrare le funzioni applicative e rendere il prototipo utilizzabile durante la demo.

## 5. Parsing dei documenti

Per la lettura dei PDF viene usato `pypdf`.

Il parser estrae il testo disponibile dal documento e mantiene informazioni di base sulla provenienza, in particolare la pagina.

Questa scelta è adeguata per il caso studio perché il bando utilizzato è trattabile come PDF testuale.

Il prototipo non include OCR avanzato. Di conseguenza, documenti scannerizzati o con layout particolarmente complessi potrebbero richiedere strumenti aggiuntivi.

## 6. Chunking e indicizzazione

Dopo l'estrazione, il testo viene suddiviso in parti più piccole.

Questa fase serve a rendere il documento interrogabile: invece di passare al modello l'intero PDF, il sistema recupera solo i passaggi più pertinenti rispetto alla domanda.

L'indicizzazione è locale e usa ChromaDB come database vettoriale.

I vettori vengono salvati in una directory locale, in modo da poter riutilizzare l'indice senza ricostruirlo a ogni avvio.

Il progetto mantiene anche un manifest dell'indice, utile per capire se i PDF sono cambiati e se l'indice deve essere aggiornato.

Nel prototipo attuale l'indice è pensato per rappresentare il bando in analisi. Può contenere più PDF quando questi sono documenti dello stesso procedimento, ma non isola automaticamente bandi diversi. La gestione di più bandi separati richiederebbe un meccanismo di selezione del bando attivo o indici/cache distinti.

## 7. Embeddings

Per generare rappresentazioni vettoriali del testo viene usato un modello di embeddings multilingua tramite integrazione Hugging Face.

Nel prototipo è usato il modello `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.

La scelta di un modello multilingua è coerente con il caso d'uso, perché i documenti e le domande sono in italiano.

Gli embeddings servono per recuperare passaggi semanticamente vicini alla richiesta dell'utente, anche quando non coincidono esattamente le parole usate.

## 8. Retrieval e orchestrazione RAG

La pipeline RAG è orchestrata con LlamaIndex.

LlamaIndex viene usato per:

- collegare il database vettoriale alla logica di query;
- recuperare i chunk rilevanti;
- costruire il contesto da passare al modello;
- gestire la generazione grounded sul documento.

Nel prototipo, però, il retrieval non è l'unico meccanismo di risposta.

Quando la domanda riguarda un'informazione già rappresentata nei fatti estratti dal bando, il sistema preferisce usare quei dati strutturati. Il RAG viene usato soprattutto come fallback per domande più aperte o non coperte dai fatti.

## 9. Modello linguistico

Il modello generativo non è vincolato a un provider specifico.

La configurazione avviene tramite variabili d'ambiente:

- modello;
- API key;
- endpoint;
- temperatura.

Il prototipo usa un'interfaccia compatibile con API in stile OpenAI tramite `OpenAILike` di LlamaIndex.

Questa scelta permette di collegare il sistema a:

- provider esterni;
- endpoint universitari;
- server aziendali;
- eventuali modelli self-hosted compatibili.

In questo modo il progetto resta più flessibile e non dipende rigidamente da un singolo servizio.

## 10. Dati strutturati del bando

Uno degli elementi più importanti dello stack applicativo è la presenza dei `BandoFacts`.

I `BandoFacts` rappresentano una struttura intermedia in cui vengono raccolte le informazioni principali del bando:

- oggetto;
- finalità;
- dotazione finanziaria;
- soggetti ammessi;
- requisiti dell'edificio;
- scadenza;
- modalità di presentazione;
- documenti richiesti;
- criteri di valutazione;
- obblighi successivi;
- informazioni mancanti o da verificare.

Questa struttura riduce la dipendenza dalla generazione libera del modello.

Invece di chiedere sempre al RAG di ricostruire una risposta, il sistema può usare dati già organizzati e collegati alle fonti.

## 11. Routing delle domande

Il prototipo include un livello di routing semantico.

Il router prova a classificare la richiesta dell'utente prima di generare la risposta.

Questo permette di distinguere tra:

- saluti;
- comandi espliciti;
- richiesta di riassunto;
- richiesta di checklist;
- domande sui fatti del bando;
- domande sulla PEC o sulla modalità di invio;
- domande multi-topic, ad esempio scadenza più PEC;
- riferimenti a fonti o pagine incollati senza una domanda;
- domande sul profilo MAPI;
- domande sull'eleggibilità di MAPI nello scenario;
- domande generiche da mandare al RAG.

Il routing è importante perché evita che ogni input venga gestito nello stesso modo. Alcune domande richiedono risposte facts-first, altre richiedono una risposta scenario-aware, altre combinano più topic e altre ancora possono essere lasciate al recupero generico dal documento.

## 12. Profilo aziendale e scenario

Il profilo MAPI è salvato come file YAML locale.

Questa scelta consente di mantenere separati:

- dati del bando;
- dati dello scenario;
- logica di risposta.

Lo scenario MAPI introduce un livello ulteriore rispetto al solo PDF: il sistema può rispondere non solo a "cosa dice il bando", ma anche a "come si applica questo bando allo scenario considerato".

Nel caso studio, questo permette di chiarire che MAPI non è soggetto proponente diretto, ma può agire come supporto tecnico a un ente locale ammesso.

## 13. Output e persistenza

Il prototipo produce output testuali in Markdown.

Gli output principali sono:

- riassunto operativo;
- checklist revisionabile;
- risposte puntuali in chat;
- fonti recuperate;
- cache dei fatti estratti.

La checklist può essere salvata localmente nella cartella degli output e inviata all'interfaccia come file Markdown scaricabile dal browser.

La scelta del Markdown è coerente con il prototipo: è semplice, leggibile, modificabile e adatto alla revisione manuale.

## 14. Script e automazione locale

Il progetto include script per semplificare le operazioni principali:

- installazione dell'ambiente;
- indicizzazione dei documenti;
- reset dell'indice;
- avvio dell'interfaccia Chainlit.

## 15. Test

Il progetto include test automatici, in particolare sul routing.

I test servono a verificare che le domande principali della demo vengano classificate correttamente.

Questo è importante perché il routing è una parte delicata del sistema: piccole variazioni linguistiche possono cambiare il comportamento della risposta.

I test di regressione aiutano quindi a mantenere stabili i casi principali, ad esempio:

- eleggibilità MAPI;
- soggetti ammessi;
- scadenza;
- documenti richiesti;
- PEC o modalità di invio;
- scadenza più PEC;
- riferimenti fonte/pagina senza richiesta informativa;
- chiarimento tra azienda ed edificio.

## 16. Dipendenze principali

Le dipendenze principali sono:

| Tecnologia              | Ruolo                                                    |
| ----------------------- | -------------------------------------------------------- |
| Python                  | Linguaggio principale del prototipo.                     |
| Chainlit                | Interfaccia conversazionale per la demo.                 |
| LlamaIndex              | Orchestrazione del retrieval e integrazione LLM.         |
| ChromaDB                | Database vettoriale locale.                              |
| Hugging Face embeddings | Generazione delle rappresentazioni vettoriali del testo. |
| `pypdf`                 | Estrazione del testo dai PDF.                            |
| `python-dotenv`         | Lettura della configurazione da variabili d'ambiente.    |
| OpenAI-like API         | Interfaccia flessibile verso modelli compatibili.        |

## 17. Motivazione delle scelte

Le scelte tecniche sono state guidate da tre criteri.

Il primo è la rapidità di prototipazione. Il tirocinio richiedeva un sistema dimostrabile, non una piattaforma completa.

Il secondo è la controllabilità. Per questo il sistema non si affida solo al RAG, ma introduce dati strutturati, routing e checklist revisionabile.

Il terzo è la riproducibilità locale. L'indice, i documenti, il profilo aziendale e gli output restano nel progetto, rendendo più semplice mostrare e discutere il prototipo.

## 18. Limiti tecnici dello stack

Lo stack scelto è adeguato a un MVP, ma presenta limiti.

In particolare:

- non include OCR avanzato;
- non gestisce nativamente workflow multiutente;
- non è progettato per grandi volumi documentali;
- non isola automaticamente più bandi diversi caricati nello stesso indice;
- non implementa una pipeline di deployment produttivo;
- dipende dalla qualità del modello LLM configurato;
- richiede controllo umano sulle risposte generate.

Questi limiti sono coerenti con il perimetro del progetto e non impediscono la validazione del caso d'uso.

## 19. Sintesi

Lo stack tecnico combina strumenti leggeri e adatti alla prototipazione con componenti specifici per retrieval, embeddings, interfaccia chat e generazione LLM.

La scelta più importante non è una singola libreria, ma l'organizzazione complessiva: il sistema non usa il RAG come unico meccanismo, ma lo integra in una pipeline più controllata basata su fatti strutturati, routing e revisione umana.

Questo rende lo stack coerente con l'obiettivo del progetto: supportare l'analisi preliminare di un bando e la produzione di una checklist operativa revisionabile.
