# Stato del prototipo



## 1. Scopo del documento

Questo documento descrive lo stato attuale del prototipo realizzato durante il tirocinio.

L'obiettivo è presentare in modo sintetico e comprensibile cosa il sistema dimostra oggi, quale problema affronta, quali risultati sono stati raggiunti e quali limiti restano aperti.

Il documento non entra nel dettaglio implementativo dei singoli file o moduli. La finalità è fornire una visione funzionale del prototipo, utile per discuterne il valore, il perimetro e le possibili evoluzioni.

## 2. Obiettivo del prototipo

Il prototipo nasce per supportare la fase preliminare di analisi di un bando pubblico.

La partecipazione a un bando richiede normalmente di leggere documenti lunghi, individuare requisiti, scadenze, allegati, soggetti ammessi, vincoli tecnici e informazioni mancanti.

Il sistema sviluppato non prova a sostituire questa valutazione, né a generare automaticamente una candidatura completa. Il suo obiettivo è più circoscritto:

- aiutare l'utente a comprendere rapidamente il contenuto principale del bando;
- organizzare le informazioni più rilevanti;
- produrre una checklist operativa revisionabile;
- rispondere a domande puntuali mantenendo un collegamento con le fonti;
- distinguere tra informazioni presenti nel bando e dati che devono essere verificati dall'utente.

In questo senso il prototipo è uno strumento di supporto alla comprensione e alla preparazione, non uno strumento decisionale automatico.

## 3. Stato generale

Il prototipo è attualmente funzionante come MVP dimostrativo.

È possibile caricare un bando, analizzarlo, interrogare il contenuto e generare output utili alla revisione umana.

La demo è stata costruita intorno a un caso controllato:

- un bando reale di edilizia scolastica;
- uno scenario aziendale simulato basato su MAPI Ingegneria;
- una serie di domande operative tipiche della fase iniziale di valutazione;
- una checklist finale utilizzabile come base di lavoro.

Il sistema è quindi sufficientemente maturo per mostrare il flusso completo, ma non va presentato come prodotto pronto per l'uso in contesti reali senza ulteriore validazione.

Il perimetro operativo è un bando alla volta. Più PDF possono essere usati solo se appartengono allo stesso avviso o procedimento, ad esempio avviso principale, allegati e disciplinare. Bandi diversi caricati insieme non sono supportati, perché facts, riassunto e checklist potrebbero mescolare informazioni provenienti da avvisi differenti.

## 4. Idea di fondo

La scelta progettuale principale è non trattare il sistema come un semplice chatbot sul PDF.

Il bando viene prima trasformato in una base informativa più ordinata, composta da fatti rilevanti come soggetti ammessi, requisiti, scadenze, documenti richiesti e modalità di presentazione.

Questa base strutturata viene poi usata per generare risposte, riassunti e checklist.

Il recupero dal documento resta importante, ma viene usato come supporto e come fallback, non come unica logica del sistema. In questo modo il prototipo risulta più controllabile e più facile da spiegare.

## 5. Scenario dimostrativo

Lo scenario MAPI serve a rendere il caso d'uso più realistico.

MAPI Ingegneria S.r.l. è considerata come una società tecnica simulata che opera nell'ambito dell'ingegneria civile e della progettazione.

Nel caso analizzato, MAPI non è il soggetto che può presentare direttamente domanda al bando. Il bando ammette infatti enti locali proprietari di edifici pubblici scolastici.

MAPI può però avere un ruolo operativo plausibile: supportare un ente locale ammesso nella lettura del bando, nella verifica dei requisiti, nella raccolta della documentazione e nella preparazione tecnica della candidatura.

Questo scenario permette di dimostrare una capacità importante del prototipo: collegare il contenuto del bando a un contesto operativo, distinguendo tra soggetto proponente, soggetto di supporto e requisiti dell'edificio.

## 6. Funzionamento ad alto livello

Il flusso funzionale del prototipo può essere descritto in questo modo:

1. l'utente fornisce il bando da analizzare;
2. il sistema estrae il contenuto testuale disponibile;
3. le informazioni principali vengono organizzate in una forma più strutturata;
4. l'utente può fare domande in linguaggio naturale;
5. il sistema decide se la domanda può essere risolta usando i fatti già estratti;
6. se necessario, vengono recuperati passaggi rilevanti dal documento;
7. la risposta viene presentata con fonti e in forma operativa;
8. l'utente può generare una checklist finale da revisionare.

Il punto centrale è che la revisione umana resta parte del processo. Il sistema prepara e organizza il lavoro, ma non elimina il controllo dell'utente.

## 7. Capacità già dimostrate

Il prototipo oggi dimostra le seguenti capacità:

- analizzare un bando caricato manualmente;
- individuare informazioni rilevanti per la partecipazione;
- produrre un riassunto operativo;
- produrre una checklist revisionabile;
- rispondere a domande su scadenze, documenti, soggetti ammessi e requisiti;
- distinguere tra una richiesta solo su PEC/modalità di invio e una domanda combinata su scadenza più PEC;
- riconoscere un riferimento a fonte o pagina incollato senza domanda, evitando risposte casuali;
- gestire domande legate allo scenario MAPI;
- chiarire se il problema riguarda l'azienda, l'ente proponente o l'edificio;
- combinare più aspetti nella stessa risposta quando la domanda lo richiede;
- mostrare le fonti utilizzate;
- indicare quando un'informazione deve essere verificata.

Esempi di domande gestite correttamente:

- `MAPI può presentare domanda direttamente?`
- `Quali sono i soggetti ammessi?`
- `Quando scade?`
- `Cosa devo mandare e entro quando?`
- `Mi dai anche l'email o la PEC?`
- `È questa l'email? servizio.lavoripubblici@pec.rupar.puglia.it`
- `Quando scade e dammi l'email per contattare`
- `Avviso Edilizia Scolastica Puglia 2025, pag. 23`
- `Il problema è l'azienda o l'edificio?`
- `Come partecipo al bando?`

## 8. Output principali

Gli output principali del prototipo sono tre.

Il primo è il riassunto operativo del bando. Serve a ottenere rapidamente una panoramica su oggetto, finalità, requisiti, scadenze, documentazione e obblighi principali.

Il secondo è la checklist operativa. È l'output più vicino all'obiettivo del tirocinio, perché traduce il bando in una lista di verifiche e attività da completare prima di procedere con una candidatura. La checklist può essere esportata come file Markdown scaricabile dal browser, così resta utilizzabile anche quando la demo viene eseguita su un server remoto.

Il terzo è la risposta conversazionale facts-first. In questo caso il sistema risponde a domande puntuali partendo prima dalle informazioni già estratte e usando il recupero dal documento solo quando necessario.

## 9. Ruolo del routing

Durante lo sviluppo è emerso che il linguaggio naturale introduce molte ambiguità.

Per questo motivo è stato introdotto un livello di routing: prima di rispondere, il sistema prova a capire che tipo di richiesta sta facendo l'utente.

Questo permette di distinguere, ad esempio, tra:

- una richiesta di riassunto;
- una domanda sui soggetti ammessi;
- una domanda sulla scadenza;
- una domanda solo sulla PEC o sulla modalità di invio;
- una domanda combinata su scadenza e PEC;
- un riferimento a una fonte o pagina senza richiesta esplicita;
- una richiesta di checklist;
- una domanda sul profilo MAPI;
- una domanda sull'eleggibilità di MAPI nello scenario;
- una domanda più generica da gestire con recupero dal documento.

Il routing non è pensato come soluzione definitiva a tutto il linguaggio naturale. È però sufficiente per rendere la demo più robusta e per evitare che domande importanti vengano trattate come semplici query generiche.

## 10. Ruolo del RAG

Il RAG è presente, ma non viene presentato come l'intero sistema.

Nel prototipo ha due ruoli principali:

- recuperare parti rilevanti del bando quando serve;
- fornire grounding documentale alle risposte.

Quando una domanda è coperta da informazioni già estratte, il sistema preferisce usare quelle. Quando invece la domanda è più aperta o non rientra nei casi strutturati, il RAG viene usato come fallback.

Questa impostazione rende il progetto più difendibile: non tutto dipende dalla generazione libera del modello, e le informazioni principali restano più controllabili.

## 11. Livello di maturità

Il prototipo può essere considerato completo rispetto all'obiettivo dimostrativo iniziale.

È in grado di mostrare un flusso coerente:

- acquisizione del bando;
- analisi preliminare;
- organizzazione delle informazioni;
- interazione conversazionale;
- uso dello scenario MAPI;
- produzione di checklist;
- revisione umana finale.

Non è invece completo rispetto a un utilizzo produttivo. Mancano validazioni più ampie, gestione di casi eterogenei, integrazioni esterne e controllo amministrativo specialistico.

## 12. Limiti dichiarati

I principali limiti attuali sono:

- il sistema è stato validato su un caso dimostrativo controllato;
- lavora principalmente su un bando alla volta;
- più PDF sono ammessi solo come documenti collegati allo stesso bando;
- la qualità dell'analisi dipende dalla qualità del PDF caricato;
- non sostituisce un esperto amministrativo o tecnico;
- non verifica dati aziendali reali;
- non compila automaticamente gli allegati;
- non produce una candidatura finale pronta all'invio;
- alcune formulazioni dell'utente possono richiedere ulteriori miglioramenti del routing;
- le fonti recuperate devono comunque essere controllate dall'utente.

Questi limiti sono coerenti con la natura del lavoro: il prototipo supporta la fase preliminare, non automatizza l'intero processo di candidatura.

## 13. Risultato raggiunto

Il risultato raggiunto è un prototipo che dimostra come un sistema RAG possa essere inserito in una pipeline più ampia di supporto alla candidatura.

Il valore non sta solo nella capacità di rispondere a domande sul documento, ma nella combinazione di:

- estrazione delle informazioni principali;
- organizzazione dei dati rilevanti;
- contestualizzazione nello scenario MAPI;
- generazione di output revisionabili;
- mantenimento delle fonti;
- consapevolezza dei dati mancanti.

Il sistema aiuta quindi l'utente a passare da un bando lungo e poco immediato a una base operativa più leggibile e controllabile.

## 14. Possibili sviluppi successivi

Il prototipo può essere considerato chiuso rispetto all'obiettivo dimostrativo, ma lascia aperte alcune direzioni di sviluppo coerenti con il lavoro svolto.

Una prima direzione riguarda la validazione su casi diversi. Il sistema potrebbe essere provato su altri bandi, possibilmente con struttura e ambiti differenti, per capire quali parti della pipeline restano generalizzabili e quali richiedono adattamenti.

Una seconda direzione riguarda l'arricchimento del modello informativo. I fatti estratti dal bando potrebbero essere estesi con nuovi campi, una gestione più articolata degli allegati e una distinzione più precisa tra requisiti amministrativi, tecnici ed economici.

Una terza direzione riguarda il confronto con dati esterni al bando. Il profilo aziendale e lo scenario potrebbero diventare più completi, permettendo controlli più avanzati tra requisiti richiesti e informazioni disponibili sul soggetto che supporta o prepara la candidatura.

Infine, il prototipo potrebbe essere validato con utenti reali o revisori, migliorando la checklist, la qualità delle fonti mostrate e i formati di esportazione degli output.

Queste evoluzioni non sono necessarie per dimostrare il valore dell'MVP, ma indicano come il lavoro potrebbe proseguire verso uno strumento più generale di supporto alla lettura e alla preparazione di candidature.

## 15. Sintesi conclusiva

Il prototipo ha raggiunto l'obiettivo previsto: mostrare un sistema locale capace di supportare l'analisi preliminare di un bando pubblico e la costruzione di una checklist operativa revisionabile.

Il sistema non automatizza la candidatura, ma assiste l'utente nella comprensione del bando, nella raccolta delle informazioni principali e nella distinzione tra ciò che è noto, ciò che è richiesto e ciò che resta da verificare.

La soluzione è quindi coerente con un contesto di tirocinio e tesi: è circoscritta, dimostrabile, tecnicamente fondata e centrata su un problema reale.
