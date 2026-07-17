# Scenario MAPI

## 1. Scopo dello scenario

Lo scenario MAPI è stato introdotto per contestualizzare il prototipo all’interno di un caso d’uso realistico ma controllato.

L’obiettivo non è simulare in modo completo un’azienda reale, ma fornire al sistema un profilo aziendale minimo da confrontare con le informazioni estratte dal bando.

In questo modo il prototipo può dimostrare non solo la capacità di interrogare un documento, ma anche di distinguere tra:

- informazioni contenute nel bando;

- informazioni relative al soggetto che intende partecipare;

- dati mancanti o da verificare;

- ruolo del soggetto proponente;

- ruolo di eventuali soggetti di supporto tecnico.

## 2. Profilo sintetico di MAPI Ingegneria

MAPI Ingegneria S.r.l. è una società simulata utilizzata come riferimento nello scenario dimostrativo.

| Campo                       | Valore                                                    |
| --------------------------- | --------------------------------------------------------- |
| Nome                        | MAPI Ingegneria S.r.l.                                    |
| Settore                     | Ingegneria civile, infrastrutture e progettazione tecnica |
| Sede                        | Puglia                                                    |
| Dimensione                  | PMI                                                       |
| Ruolo nello scenario        | Supporto tecnico a un ente locale                         |
| Soggetto proponente diretto | No                                                        |

## 3. Attività principali

Nel contesto dello scenario, MAPI Ingegneria opera come società tecnica a supporto di enti pubblici o privati.

Le attività considerate sono:

- progettazione di opere pubbliche;

- direzione lavori;

- consulenza tecnica;

- gestione di pratiche autorizzative;

- supporto tecnico ad enti pubblici e privati;

- analisi documentale preliminare;

- supporto alla preparazione della documentazione tecnica.

## 4. Ruolo rispetto al bando

Nel caso studio considerato, MAPI Ingegneria non è il soggetto proponente diretto della candidatura.

Il bando analizzato ammette come soggetti proponenti enti locali pugliesi, quali Comuni, Città Metropolitana di Bari o Province proprietari di edifici pubblici scolastici.

Di conseguenza, nello scenario dimostrativo, MAPI assume il ruolo di supporto tecnico a un ente locale ammesso dal bando.

Il suo compito può consistere in:

- analisi preliminare del bando;

- individuazione dei requisiti rilevanti;

- verifica della documentazione richiesta;

- supporto alla predisposizione degli allegati tecnici;

- supporto alla progettazione o alla raccolta dei dati tecnici dell’edificio;

- produzione di una checklist operativa da sottoporre a revisione umana.

## 5. Motivazione della scelta dello scenario

Lo scenario è stato scelto perché consente di verificare un aspetto importante del sistema: la capacità di non limitarsi a rispondere a domande generiche sul bando, ma di collegare le informazioni del documento a un contesto operativo.

In particolare, lo scenario permette di testare se il sistema riesce a:

- distinguere tra soggetto proponente e soggetto di supporto;

- riconoscere che MAPI non può presentare direttamente domanda come ente proponente;

- individuare i requisiti che riguardano l’edificio;

- segnalare dati mancanti, come codice edificio/SNAES, quadro economico e livello progettuale;

- evitare di inventare dati aziendali non disponibili.

## 6. Dati disponibili nello scenario

Nel prototipo sono disponibili solo informazioni sintetiche e controllate.

| Categoria              | Informazioni disponibili                                      |
| ---------------------- | ------------------------------------------------------------- |
| Identità aziendale     | Nome, settore, sede, dimensione                               |
| Ruolo operativo        | Supporto tecnico a ente locale                                |
| Ambito tecnico         | Ingegneria civile, infrastrutture, progettazione              |
| Attività               | Progettazione, consulenza, direzione lavori, supporto tecnico |
| Relazione con il bando | Non proponente diretto; supporto a ente locale                |

## 7. Dati mancanti o da verificare

Alcune informazioni non vengono simulate in modo completo, ma vengono volutamente lasciate come dati mancanti o da verificare.

Questa scelta è utile perché consente di testare il comportamento del sistema quando non dispone di tutte le informazioni necessarie.

Dati da verificare:

- fatturato;

- numero di dipendenti;

- certificazioni effettive;

- referenze documentabili;

- curriculum tecnico;

- codice edificio / SNAES;

- quadro economico dell’intervento;

- livello progettuale disponibile;

- dati tecnici dell’edificio;

- documenti tecnici già disponibili.

## 8. Ruolo nella valutazione del prototipo

Lo scenario MAPI è utile per valutare il prototipo perché introduce un livello ulteriore rispetto alla semplice interrogazione del PDF.

Il sistema deve infatti dimostrare di saper:

- recuperare informazioni dal bando;

- utilizzare dati di scenario;

- combinare fonti diverse;

- rispondere a domande operative;

- segnalare quando un dato non è disponibile;

- produrre output revisionabili e verificabili.

## 9. Limiti dello scenario

Lo scenario è volutamente semplificato.

Non rappresenta una verifica reale di ammissibilità aziendale e non sostituisce il controllo di un esperto o dell’ente proponente.

Inoltre, alcune informazioni aziendali sono fittizie o non disponibili. Il sistema deve quindi trattarle come dati mancanti o da verificare, evitando di presentarle come informazioni certe.

## 10. Sintesi

MAPI Ingegneria S.r.l. viene utilizzata come soggetto simulato per testare il comportamento del sistema in un contesto operativo.

Nel caso studio, MAPI non presenta direttamente domanda, ma supporta un ente locale ammesso dal bando.

Lo scenario consente di dimostrare che il prototipo non si limita a interrogare un PDF, ma può collegare le informazioni del bando a un contesto di candidatura, producendo risposte e checklist utili alla revisione umana.
