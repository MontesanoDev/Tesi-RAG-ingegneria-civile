# Limiti e sviluppi futuri

Aggiornato al 08/07/2026.

## 1. Scopo del documento

Questo documento raccoglie i principali limiti del prototipo e le possibili evoluzioni future.

L'obiettivo non è indebolire il lavoro svolto, ma chiarirne correttamente il perimetro. Un prototipo efficace deve mostrare cosa funziona, ma anche cosa resta fuori dalla soluzione attuale e quali sviluppi sarebbero necessari per avvicinarsi a un utilizzo più ampio.

I limiti descritti sono quindi parte della valutazione del progetto: aiutano a distinguere tra MVP dimostrativo, sistema sperimentale e prodotto completo.

## 2. Natura del prototipo

Il sistema realizzato è un MVP locale orientato alla dimostrazione di un flusso funzionale.

Il prototipo mostra come un bando pubblico possa essere caricato, analizzato, interrogato e trasformato in una checklist operativa revisionabile.

Non è invece progettato per sostituire una valutazione tecnica, amministrativa o legale. La candidatura a un bando resta un processo che richiede controllo umano, verifica delle fonti, conoscenza del contesto e validazione finale da parte di soggetti competenti.

Questo limite è intenzionale: il prototipo supporta la fase preliminare, non automatizza l'intero processo di candidatura.

## 3. Limiti sul perimetro applicativo

Il primo limite riguarda il perimetro del caso d'uso.

Il sistema è stato costruito e validato su un caso controllato: un bando reale di edilizia scolastica e uno scenario aziendale simulato basato su MAPI Ingegneria.

Questo permette una demo coerente, ma non dimostra automaticamente che il sistema funzioni allo stesso modo su qualsiasi bando pubblico.

In particolare, il prototipo attuale:

- lavora principalmente su un bando alla volta;
- supporta più PDF solo se fanno parte dello stesso avviso o procedimento;
- non gestisce automaticamente bandi molto diversi tra loro;
- non confronta più avvisi in parallelo;
- non segue l'intero ciclo di candidatura;
- non produce una domanda finale pronta all'invio.

Il valore del prototipo sta quindi nella dimostrazione del metodo, non nella copertura completa di tutti i possibili scenari amministrativi.

## 4. Limiti sui documenti

Il sistema parte da documenti caricati manualmente.

Non cerca bandi online, non scarica automaticamente allegati da portali istituzionali e non mantiene aggiornato un archivio di avvisi pubblici.

Inoltre, la qualità dell'analisi dipende dalla qualità del documento caricato. Un PDF ben strutturato e testuale è più semplice da analizzare rispetto a un documento scannerizzato, impaginato in modo complesso o ricco di tabelle difficili da interpretare.

I principali limiti documentali sono:

- assenza di ricerca automatica online;
- assenza di scraping di portali istituzionali;
- assenza di OCR avanzato per scansioni complesse;
- gestione limitata di allegati multipli;
- assenza di selezione automatica del bando attivo quando sono presenti avvisi diversi;
- possibile difficoltà con tabelle, moduli o layout irregolari;
- necessità di controllo manuale sul documento originale.

## 5. Limiti dell'estrazione informativa

Il prototipo organizza alcune informazioni principali del bando in una struttura più controllabile.

Questa scelta migliora la qualità delle risposte, ma non garantisce l'estrazione perfetta o completa di ogni informazione rilevante.

Alcuni dati possono essere distribuiti in più sezioni, espressi in modo ambiguo o dipendere da allegati non presenti nel documento analizzato.

Di conseguenza:

- i fatti estratti devono essere verificati;
- le fonti devono essere controllate dall'utente;
- alcune informazioni possono risultare mancanti;
- alcune sezioni del bando possono richiedere lettura manuale;
- il sistema non deve inventare dati quando il contenuto non è disponibile.

Il comportamento corretto, in questi casi, non è produrre comunque una risposta completa, ma segnalare l'incertezza o la necessità di verifica.

## 6. Limiti del linguaggio naturale

Durante lo sviluppo è emerso che il linguaggio naturale è uno degli aspetti più delicati.

Domande simili possono essere formulate in molti modi diversi. Una richiesta apparentemente semplice può combinare più aspetti, ad esempio scadenza e PEC, documenti e termine, soggetto proponente ed edificio. Inoltre l'utente può incollare frammenti, fonti o riferimenti di pagina che non sono vere domande e che devono essere trattati come input non informativi.

Il router introdotto nel prototipo migliora la gestione di questi casi, ma non può essere considerato una soluzione definitiva a tutte le possibili formulazioni.

I limiti principali sono:

- nuove frasi possono richiedere ulteriori test;
- alcune domande ambigue possono essere classificate in modo non ottimale;
- riferimenti a pagine o fonti senza domanda devono essere filtrati per evitare risposte non pertinenti;
- il sistema copre bene i casi dimostrativi, ma non tutte le varianti linguistiche possibili;
- la robustezza va mantenuta con esempi di regressione e verifiche progressive.

Questo limite è tipico dei sistemi conversazionali: la qualità non dipende solo dal modello, ma anche dalla progettazione del routing e dalla chiarezza dei casi d'uso.

## 7. Limiti dello scenario MAPI

Lo scenario MAPI è volutamente semplificato.

MAPI Ingegneria S.r.l. viene usata come soggetto simulato per contestualizzare la demo. Non rappresenta una verifica reale di ammissibilità aziendale.

Nel caso studio, MAPI non è soggetto proponente diretto, ma può operare come supporto tecnico a un ente locale ammesso.

Restano quindi fuori dal prototipo:

- dati aziendali reali e completi;
- verifica di certificazioni effettive;
- controllo di fatturato, referenze e requisiti economici;
- curriculum tecnico documentabile;
- integrazione con archivi aziendali;
- verifica amministrativa del ruolo contrattuale di MAPI.

Lo scenario serve a dimostrare il collegamento tra bando e contesto operativo, non a certificare l'idoneità di un'azienda reale.

## 8. Limiti sulla checklist

La checklist generata dal sistema è un output revisionabile.

Non è un documento amministrativo definitivo e non deve essere usata senza controllo umano.

La checklist aiuta a organizzare il lavoro, ma:

- non sostituisce la lettura del bando;
- non garantisce la completezza assoluta;
- non compila gli allegati;
- non produce la candidatura finale;
- non verifica automaticamente la disponibilità dei documenti;
- non controlla se l'ente proponente possiede realmente tutti i requisiti.

Il suo valore è operativo: trasformare il bando in una lista più gestibile di verifiche e attività.

## 9. Limiti del modello e del RAG

Il RAG viene usato come componente di recupero e grounding, non come soluzione completa.

Anche con fonti recuperate, una risposta generata da un modello linguistico deve essere controllata.

I limiti principali sono:

- il recupero può selezionare passaggi incompleti;
- il modello può sintetizzare in modo non perfetto;
- una fonte recuperata non implica automaticamente interpretazione corretta;
- la qualità dipende dalla configurazione del modello utilizzato;
- le risposte devono restare subordinate al documento originale.

Per ridurre questi rischi, il prototipo usa una logica facts-first quando possibile e mantiene la revisione umana come parte centrale del processo.

## 10. Limiti di valutazione

La valutazione del prototipo è stata principalmente funzionale e qualitativa.

Sono stati verificati i casi principali della demo, soprattutto quelli legati al routing e alle domande operative ricorrenti.

Mancano però:

- un benchmark su molti bandi diversi;
- una valutazione quantitativa dell'accuratezza;
- test con utenti reali;
- confronto sistematico con metodi manuali;
- misurazione dei tempi risparmiati;
- valutazione da parte di esperti amministrativi.

Per una fase successiva, questi elementi sarebbero importanti per capire quanto il sistema sia davvero utile fuori dal contesto dimostrativo.

## 11. Rischi principali

I rischi da tenere presenti sono:

- affidarsi troppo alla risposta generata senza controllare la fonte;
- interpretare il prototipo come sistema decisionale automatico;
- usare la checklist come documento finale invece che come base di lavoro;
- applicare lo stesso flusso a bandi molto diversi senza adattamenti;
- caricare bandi diversi nello stesso indice e interpretare i facts come se fossero riferiti a un solo avviso;
- non aggiornare il sistema quando cambiano struttura dei bandi o requisiti normativi;
- confondere il ruolo di un soggetto tecnico di supporto con quello del proponente ammesso.

Questi rischi non impediscono l'utilizzo del prototipo, ma chiariscono perché la revisione umana resta essenziale.

## 12. Sviluppi futuri a breve termine

Gli sviluppi più immediati riguardano il consolidamento dell'MVP.

Possibili interventi:

- testare il prototipo su altri bandi simili;
- aggiungere nuovi esempi di domande per migliorare il routing;
- raffinare l'estrazione delle fonti;
- migliorare la gestione di documenti con tabelle;
- arricchire la checklist con sezioni più personalizzabili;
- rendere più chiara la distinzione tra dati certi e dati da verificare;
- migliorare l'esportazione degli output per la revisione.

Questi sviluppi restano coerenti con l'obiettivo attuale: supportare la fase preliminare senza cambiare radicalmente architettura.

## 13. Sviluppi futuri a medio termine

In una fase successiva, il sistema potrebbe essere esteso per gestire scenari più complessi.

Possibili evoluzioni:

- supporto a più documenti collegati allo stesso bando;
- analisi separata di avviso, allegati, disciplinari e moduli;
- confronto più strutturato tra requisiti del bando e profilo aziendale;
- gestione di profili aziendali più completi;
- introduzione di controlli automatici su requisiti ricorrenti;
- esportazione di report più adatti alla revisione interna;
- gestione di checklist per ruoli diversi, ad esempio ente proponente e consulente tecnico.

Questa fase trasformerebbe il prototipo da demo su caso singolo a strumento più generale di supporto documentale.

## 14. Sviluppi futuri a lungo termine

Gli sviluppi più avanzati riguarderebbero l'integrazione del sistema in un vero processo organizzativo.

Possibili direzioni:

- integrazione con archivi documentali aziendali;
- gestione di più bandi e confronto tra opportunità;
- monitoraggio automatico di portali pubblici;
- aggiornamento periodico dei bandi disponibili;
- workflow collaborativo tra tecnici, amministrativi e revisori;
- storico delle checklist prodotte;
- tracciamento delle decisioni e delle verifiche svolte;
- supporto alla compilazione assistita di alcune sezioni della candidatura.

Questi sviluppi richiederebbero però un salto di complessità significativo e andrebbero progettati come evoluzione separata rispetto all'MVP.

## 15. Evoluzioni non prioritarie

Alcune funzionalità possono sembrare utili, ma non sono prioritarie per il prototipo attuale.

Ad esempio:

- automatizzare completamente la candidatura;
- generare allegati finali senza revisione;
- costruire agenti autonomi complessi;
- sostituire il controllo tecnico o amministrativo;
- coprire tutti i tipi di bando senza specializzazione.

Queste direzioni rischierebbero di allargare troppo il perimetro e rendere il sistema meno controllabile.

Per il lavoro svolto, è più difendibile mantenere un obiettivo chiaro: supporto alla lettura, organizzazione delle informazioni e preparazione di una checklist revisionabile.

## 16. Sintesi conclusiva

Il prototipo ha raggiunto il suo obiettivo principale: dimostrare un flusso locale per analizzare un bando reale, estrarre informazioni rilevanti, contestualizzarle nello scenario MAPI e produrre output revisionabili.

I limiti principali riguardano la generalizzazione, la completezza dell'estrazione, la variabilità del linguaggio naturale e l'assenza di validazione su larga scala.

Gli sviluppi futuri più realistici consistono nel testare il sistema su altri bandi, migliorare la gestione dei documenti, rafforzare il routing e rendere più ricchi gli output di revisione.

La direzione complessiva resta la stessa: non automatizzare la candidatura, ma costruire un supporto affidabile alla fase preliminare di comprensione, verifica e preparazione.
