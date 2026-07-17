# Caso studio: bando edilizia scolastica

## 1. Scopo del documento

Questo documento descrive il bando utilizzato come caso studio per validare il prototipo.

La funzione del caso studio è collegare l'architettura generale del sistema a un esempio concreto. Il bando scelto permette infatti di mostrare come il prototipo affronta un documento reale, estrae informazioni rilevanti e produce un supporto operativo per una possibile candidatura.

Il documento non ha lo scopo di sostituire il bando originale né di fornire una valutazione amministrativa definitiva. Serve invece a spiegare perché questo bando è adatto alla demo e quali aspetti vengono usati per testare il sistema.

## 2. Bando analizzato

Il caso studio utilizza l'Avviso Edilizia Scolastica Puglia 2025.

Il bando riguarda la selezione di proposte progettuali relative a infrastrutture per istruzione primaria, secondaria e infanzia.

L'obiettivo generale è sostenere interventi su infrastrutture scolastiche e formative nel territorio regionale.

Nel prototipo il bando viene trattato come documento reale di partenza: l'utente lo carica manualmente, il sistema ne estrae il contenuto e costruisce una base informativa da cui generare risposte, riassunti e checklist.

## 3. Perché questo bando è adatto al prototipo

Il bando è adatto come caso studio perché contiene molti degli elementi tipici che rendono complessa la lettura di un avviso pubblico.

In particolare, include:

- soggetti ammessi;
- requisiti sugli edifici;
- scadenze precise;
- modalità di trasmissione della domanda;
- documenti e allegati da presentare;
- criteri di valutazione;
- obblighi successivi all'eventuale concessione;
- informazioni che devono essere verificate nel caso concreto.

Questi aspetti permettono di testare il prototipo su un flusso realistico: non basta rispondere a una singola domanda sul PDF, ma bisogna organizzare informazioni distribuite nel documento e trasformarle in una base operativa.

## 4. Informazioni principali del bando

Le informazioni principali estratte e utilizzate nella demo sono le seguenti.

| Tema                        | Informazione rilevante                                                                                                                     |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Oggetto                     | Selezione di proposte progettuali relative a infrastrutture per istruzione primaria, secondaria e infanzia.                                |
| Finalità                    | Sostenere interventi su infrastrutture scolastiche e formative nel territorio regionale.                                                   |
| Dotazione finanziaria       | 56.000.000 euro.                                                                                                                           |
| Costo minimo della proposta | Costo totale non inferiore a 500.000 euro.                                                                                                 |
| Soggetti ammessi            | Enti locali pugliesi: Comuni, Città metropolitana di Bari o Province proprietari di edifici pubblici scolastici.                           |
| Requisiti dell'edificio     | Edificio pubblico adibito a scuola o struttura educativa, censito nell'Anagrafe Regionale di Edilizia Scolastica con SNAES validato.       |
| Scadenza                    | Presentazione entro le ore 12:00 del 15/09/2025.                                                                                           |
| Modalità di invio           | Presentazione tramite PEC all'indirizzo `servizio.lavoripubblici@pec.rupar.puglia.it`.                                                     |
| Documentazione              | Istanza di finanziamento, scheda tecnica, verifica climatica, valutazione DNSH ed eventuale ulteriore documentazione prevista dall'avviso. |
| Valutazione                 | Valutazione tecnica con criteri e punteggi; soglia minima prevista.                                                                        |
| Obblighi successivi         | Avvio delle procedure previste, monitoraggio, rendicontazione e possibili revoche del contributo.                                          |

Questa sintesi non sostituisce il documento originale, ma rappresenta il livello informativo su cui il prototipo lavora durante la demo.

## 5. Aspetti rilevanti per la candidatura

Dal punto di vista operativo, il bando obbliga l'utente a verificare almeno tre livelli.

Il primo livello riguarda il soggetto proponente. Non qualunque azienda può presentare direttamente domanda: il bando ammette enti locali pugliesi proprietari di edifici pubblici scolastici.

Il secondo livello riguarda l'edificio. L'intervento deve riferirsi a un edificio coerente con i requisiti del bando, in particolare rispetto alla destinazione scolastica e al censimento nell'Anagrafe Regionale di Edilizia Scolastica con SNAES validato.

Il terzo livello riguarda la documentazione. Prima di procedere occorre predisporre allegati, schede e verifiche richieste, oltre a rispettare modalità e scadenza di trasmissione.

Questa struttura rende il bando adatto a dimostrare che il sistema deve ragionare su più piani: chi presenta, su quale edificio, con quali documenti e entro quale termine.

## 6. Collegamento con lo scenario MAPI

Il bando è stato collegato allo scenario MAPI per rendere la demo più concreta.

Nel caso studio, MAPI Ingegneria S.r.l. non può essere considerata soggetto proponente diretto, perché il bando ammette enti locali pugliesi proprietari di edifici pubblici scolastici.

MAPI può però assumere un ruolo coerente con il suo profilo simulato: supportare tecnicamente un ente locale nella fase di analisi, verifica dei requisiti, raccolta documentale e preparazione della candidatura.

Questo collegamento permette di testare domande più realistiche rispetto a una semplice interrogazione del PDF, ad esempio:

- `MAPI può presentare domanda direttamente?`
- `Serve per forza un ente locale?`
- `Il problema è l'azienda o l'edificio?`
- `Se abbiamo il progetto ma non il codice SNAES, siamo a posto?`

In questi casi il sistema deve combinare informazioni del bando e dati dello scenario, evitando di dare una risposta generica o fuorviante.

## 7. Domande guida usate nella demo

Il caso studio è stato usato per verificare il comportamento del prototipo su domande operative ricorrenti.

Esempi:

- chi può presentare domanda;
- se MAPI può partecipare direttamente;
- quali requisiti deve avere l'edificio;
- quale documentazione deve essere trasmessa;
- qual è la scadenza;
- quale PEC o modalità di invio usare;
- se un indirizzo PEC indicato dall'utente coincide con quello del bando;
- come rispondere quando l'utente chiede insieme scadenza e PEC;
- quali informazioni mancano per valutare davvero la candidatura;
- quali sono i primi passi da verificare;
- come trasformare il bando in una checklist.

Queste domande rappresentano il tipo di interazione che un utente potrebbe avere nella fase iniziale di analisi del bando.

## 8. Output generati dal caso studio

Sul bando analizzato il prototipo produce tre output principali.

Il primo è un riassunto operativo, utile per ottenere rapidamente una panoramica del bando.

Il secondo è una checklist di candidatura, che organizza requisiti, documenti, scadenze e informazioni da verificare.

Il terzo è una serie di risposte puntuali in chat, basate prima sulle informazioni strutturate estratte dal bando e poi, quando necessario, sul recupero dal documento.

Il valore del caso studio sta nel mostrare che questi output derivano dallo stesso documento, ma rispondono a esigenze diverse:

- comprendere;
- verificare;
- preparare;
- revisionare.

## 9. Informazioni mancanti o da verificare

Il bando contiene requisiti che non possono essere risolti dal solo documento generale.

Per valutare una candidatura concreta servono dati specifici sull'ente, sull'edificio e sul progetto.

Nel caso studio vengono evidenziati come dati da verificare:

- codice edificio / SNAES;
- quadro economico;
- livello progettuale disponibile;
- dati tecnici dell'edificio;
- documenti tecnici già disponibili;
- ruolo effettivo dell'ente locale proponente;
- eventuali requisiti amministrativi non simulati nello scenario.

Questa parte è importante perché mostra un comportamento corretto del prototipo: quando un dato non è disponibile, il sistema deve segnalarlo invece di inventarlo.

## 10. Valore del caso studio

Il caso studio consente di dimostrare il valore del prototipo su un problema concreto.

Il sistema non si limita a cercare parole nel PDF, ma prova a trasformare il bando in una struttura utilizzabile per la fase preliminare di candidatura.

In particolare, il caso mostra che il prototipo può:

- estrarre informazioni rilevanti da un bando reale;
- distinguere tra requisiti del bando e dati dello scenario;
- riconoscere il ruolo non diretto di MAPI;
- individuare requisiti legati all'edificio;
- produrre una checklist utile alla revisione umana;
- mantenere il collegamento con le fonti;
- segnalare dati mancanti.

Il caso studio rende quindi visibile la differenza tra una semplice chat sul documento e una pipeline orientata al supporto operativo.

## 11. Limiti del caso studio

Il caso studio resta controllato.

Il bando è reale, ma lo scenario aziendale è simulato e semplificato. Inoltre, il prototipo non esegue una verifica legale o amministrativa definitiva.

Alcune informazioni possono richiedere controllo manuale sul documento completo o su allegati non presenti nella demo.

Di conseguenza, il caso studio va presentato come validazione funzionale del prototipo, non come simulazione completa di una candidatura reale.

## 12. Sintesi

Il bando di edilizia scolastica è stato scelto perché contiene requisiti, vincoli e informazioni operative sufficientemente ricchi da mettere alla prova il prototipo.

Attraverso questo caso, il sistema dimostra di poter supportare la lettura di un bando reale, collegarlo a uno scenario aziendale simulato e produrre risposte e checklist utili alla revisione umana.

Il caso studio conferma quindi il perimetro del progetto: supporto alla fase preliminare di analisi e preparazione, non automazione completa della candidatura.
