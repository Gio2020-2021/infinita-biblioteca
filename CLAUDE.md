# Progetto Transurfing

Costruire e far crescere nel tempo una **mappa operativa del Transurfing** — pubblicata
come Artifact e mantenuta qui in locale — a partire dai libri di Klod Nagal
(Operation Moksha) e, a salire, dall'opera originale di Vadim Zeland.

Il progetto cresce: nuovi libri arrivano man mano, e ogni libro nuovo va assorbito
nella mappa esistente, non affiancato con una pagina a parte.

## L'artifact

> **Pubblicazione sospesa dal 6-9-2026 per decisione dell'utente: «deve rimanere tutto in
> locale».** L'artifact esiste e l'URL sotto resta valido, ma non si pubblica più finché
> non lo chiede lui. Per vedere il lavoro si usa `python3 strumenti/anteprima.py --apri`.
> Il sorgente continua a essere scritto **senza** `<!doctype>`, `<html>` e `<head>`, cioè
> nella forma che l'Artifact si aspetta, così la pubblicazione resta possibile in qualunque
> momento senza rimetterci mano.


**Mappa del Transurfing** — https://claude.ai/code/artifact/2575020f-c213-426a-83a4-b422fcd79ef6

Sorgente locale: `sito/mappa-transurfing.html` (è il file che si pubblica, unica copia
di verità — modificare questo, mai ripartire da capo).

Per aggiornarlo da una sessione futura: modificare `sito/mappa-transurfing.html`, poi
`Artifact` con `url` = quello sopra. **Leggerlo prima di pubblicare** se la sessione
non l'ha già pubblicato: un publish su un artifact che la conversazione non ha letto
viene rifiutato.

> **Due account, due copie — storia da tenere presente.** L'utente lavora con due account
> e la sessione può cambiarlo a metà lavoro senza preavviso (arriva solo una notifica di
> sistema, «the signed-in account changed», e l'artifact dell'altro account smette di
> essere raggiungibile: un publish su quell'URL risponde *artifact not found*).
> Esistono quindi due copie della mappa:
> `2575020f-…` (account originale, **quella buona: aggiornata al 5-9-2026 sera, dieci
> parti**) e `d2ea2b16-…` (creata sull'altro account lo stesso giorno, ferma a metà
> giornata). **Usare sempre `2575020f-…`.** Se un publish viene rifiutato, controllare con
> `Artifact action:"list"` quale delle due appartiene all'account corrente invece di
> crearne una terza: pubblicare senza `url` genera un artifact nuovo e i dati di pratica
> dell'utente (registro ✓, fine, amalgama) restano sulla vecchia, non si spostano.

Capability dichiarate: `db` (registro ✓, fine, amalgama, risvegli e **il diario** — dati
privati dell'utente), `sample` (filtro dell'anima, forgia dell'amalgama) e `downloads`
(lo scarico del diario in un file di testo).
Ripubblicando **senza** passare `capabilities` la dichiarazione resta invariata; passandole
si sostituisce l'intero insieme, quindi vanno riscritte tutte e tre.

I dati che l'utente accumula sull'artifact sono leggibili da qui con
`Artifact action:"read_db"` — collezione `registro`, documenti `pratica/fine`,
`pratica/amalgama`, `pratica/risveglio`, e la collezione **`diario`** (un documento per
giornata, id `AAAA-MM-GG`, campi `dichiarazione` · `giornata` · `constatazione` ·
`aggiornato`). Utile se chiede un parere su come sta andando. **Sono i suoi pensieri
privati**: leggerli solo se lo chiede lui, mai di iniziativa.

## Il diario (parte operativa, non dottrina)

`parte-diario` è la seconda parte operativa dopo il banco: i **due taccuini** di *Scardinare*
(dichiarazione al mattino, constatazione alla sera) più uno spazio libero per la giornata, che
nei libri non c'è ed è stato aggiunto perché è dove la giornata succede. Scelto dall'utente fra
quattro impostazioni provate in mockup (`sito/mockup-diario.html` e `sito/mockup-diario-4.html`,
tenuti come documentazione della scelta).

- Salva in doppio: `localStorage` (`tr.diario`) subito, e `db` con debounce di 800 ms. Se il db
  non c'è la pagina funziona lo stesso e lo stato dice «solo qui».
- Un giorno svuotato del tutto **cancella** il suo documento invece di lasciarne uno vuoto.
- Il fine e l'amalgama nel fianco sono **letti dal banco**, non riscritti: unica fonte di verità.
- Le parti operative (`casa`, `diario`) hanno un bottone nella barra ma **nessun nodo nel
  diagramma radiale**, che elenca solo la dottrina: `verifica.py` lo sa (insieme `OPERATIVE`).
- Vale qui più che altrove il [vincolo del banco](#vincolo-di-progettazione-del-banco-di-lavoro):
  niente serie, niente conteggi, niente rosso su un giorno vuoto.

## Struttura

```
testi/           i libri estratti in .txt, una riga per riga leggibile,
                 con marcatori "=== PAGINA n ===" per risalire al PDF
pdf-sorgenti/    i PDF dei libri
sorgente/        LA COPIA DI VERITÀ — si modifica QUI, mai in sito/
                 telaio/         identico per ogni mappa della biblioteca
                   corpo/        apertura, barra (modello), pannelli, chiusura
                   stile/        11 fogli generici
                   script/       6 moduli generici
                 mappe/
                   transurfing/  mappa.json · titolo.txt · testata.html · piede.html
                                 rituale.html · parti/ · stile/ (banco, diario)
                                 script/ (rituale, banco, diario)
sito/            mappa-transurfing.html   GENERATO da costruisci.py — non modificarlo
                 anteprima-locale.html    generata, usa-e-getta, mai modificarla
                 mockup-biblioteca.html   il mockup della biblioteca (documentazione)
note/            appunti di lavorazione, sintesi, materiale non ancora assorbito
strumenti/       costruisci.py sorgente/ → sito/mappa-transurfing.html
                 estrai.py    PDF → testo
                 anteprima.py anteprima locale fedele all'involucro dell'Artifact
                 verifica.py  controlli di coerenza — eseguirlo SEMPRE prima di pubblicare
                 rinumera.py  rinumera i sommari in progressione continua (01→N)
                 cita.py      verifica ogni citazione sui testi e ne trova la pagina
                 assembla.py  ricomposizione della pagina nelle parti (usa-e-getta,
                              già eseguito il 5-9-2026; non rieseguirlo, il file è a posto)
```

### Il file è generato: si modifica `sorgente/`

Il progetto è cresciuto oltre i 13.000 righe in un file solo, ed è stato spezzato il
6-9-2026. **Da allora `sito/mappa-transurfing.html` è un artefatto**: si modificano i pezzi
in `sorgente/` e si ricostruisce.

```bash
python3 strumenti/anteprima.py --apri       # COSTRUISCE TUTTO E APRE IL PORTALE
python3 strumenti/costruisci.py             # ricostruisce le mappe e il portale
python3 strumenti/costruisci.py transurfing # solo una mappa
python3 strumenti/costruisci.py --controlla # dice se sono allineate ai pezzi
```

**Per avviare il sito basta il primo comando.** Costruisce, avvolge ogni pagina nel guscio
che l'Artifact aggiunge in pubblicazione, la scrive in `sito/locale/` (usa-e-getta, ignorata
da git) e apre `sito/locale/index.html`, il portale della biblioteca. I nomi dei file
restano gli stessi in `sito/` e in `sito/locale/`, così i **rimandi fra mappe** funzionano
identici nei due posti.

**I rimandi fra mappe** si scrivono `href="vesica:il-perno"` e diventano
`href="vesica.html#il-perno"`. Vengono **verificati in costruzione**: se la mappa non esiste
o l'ancora non c'è, la costruzione si ferma e lo dice. Serve perché *Rapporto Vesica* fa da
perno e punta ovunque — senza controllo il primo spostamento di una sezione romperebbe i
rimandi in silenzio.

**`mappa.json` è la carta d'identità di una mappa** e genera i quattro elenchi paralleli.
`stile` e `script` sono elenchi **ordinati**: ogni nome si cerca prima in `mappe/<id>/`,
poi in `telaio/`, così un foglio proprio (il banco, il diario) può stare in mezzo a quelli
generici. Una mappa che non vuole il diario lo toglie da quell'elenco e basta.
`parti` è la sola fonte per barra, ordine fisico, `PARTI` e `BRANCHES`; una parte con
`"operativa": true` compare nella barra ma non nel diagramma.

`--controlla` esiste per una ragione precisa: se qualcuno (o una sessione futura) modifica
il file generato, la modifica sparisce alla ricostruzione successiva. Il controllo se ne
accorge e dice **a quale riga** i due divergono, invece di sovrascrivere in silenzio.
Lanciarlo prima di mettere le mani sul progetto.

Lo spezzettamento è stato fatto **senza toccare una virgola**: la ricomposizione era
identica byte per byte all'originale. Se un giorno serve rifarlo, il criterio è quello —
un refactor che cambia anche solo uno spazio non è un refactor.

`rinumera.py --scrivi` sa di questo: scrive nei pezzi di `sorgente/`, non nel file
generato, e poi richiama `costruisci.py` da sé. Uno strumento nuovo che *modifichi* il
sito deve fare altrettanto; quelli che si limitano a *leggere* (`verifica`, `cita`,
`anteprima`) continuano a lavorare sul file costruito, che è la vista completa.

Prima di ogni pubblicazione:

```bash
python3 strumenti/costruisci.py    # per primo: il resto legge il file costruito
python3 strumenti/verifica.py      # id duplicati, link morti, tag, i quattro elenchi paralleli
python3 strumenti/rinumera.py      # numerazione del sommario (--scrivi per applicare)
python3 strumenti/cita.py          # citazioni letterali e attribuite al libro giusto (~30 s)
python3 strumenti/anteprima.py --apri
```

Aggiungere un libro:

```bash
python3 strumenti/estrai.py            # estrae i PDF nuovi, salta quelli già fatti
python3 strumenti/estrai.py --tutti    # ri-estrae tutto
```

Vedere la pagina in locale prima di pubblicare:

```bash
python3 strumenti/anteprima.py --apri
```

### Trappola già incontrata: `hidden` e l'involucro

Il sorgente non ha `<!doctype>`, `<html>` né `<head>`: li aggiunge l'Artifact al momento
della pubblicazione, e quell'involucro porta con sé un reset che include
`[hidden]{display:none!important}`. Una regola d'autore come `.veil{display:flex}` batte
l'attributo `hidden` del browser, quindi **fuori da quell'involucro un pannello nascosto
con `el.hidden = true` resta visibile** — è già successo col pannello del rituale, che
in locale non si chiudeva.

Il file ora dichiara `[hidden]{display:none!important}` per conto suo: non toglierla.
Stessa cautela per qualsiasi elemento nuovo che si nasconda con `hidden` e abbia un
`display` esplicito. E usare `anteprima.py` per provare, non aprire il sorgente nudo.

### Trappola già incontrata: l'editor riformatta il file, `verifica.py` si rompe

Il file viene aperto in VS Code, che a ogni salvataggio lo riformatta (indentazione,
spazi dentro le graffe CSS, `id:"x"` → `id: "x"` nel JS). I controlli scritti come
stringa letterale con spazi fissi smettono di trovare quello che cercano — è già
successo sia alla regola `[hidden]{display:none!important}` sia al pattern che isolava
il contenuto di ogni `<div class="part">` per il controllo "ogni sezione sta in una
parte sola". **Scrivere i controlli per struttura (regex tollerante agli spazi, o
posizione fra un marcatore e il successivo), mai per stringa esatta con spaziatura
fissa.** Se `verifica.py` comincia a segnalare falsi problemi dopo che il file è stato
aperto in editor, è quasi certamente questo — non un guasto nel sito.

## Cosa è già stato letto e assorbito nella mappa

Letti **integralmente** e mappati:

1. `1-…-lo-spazio-delle-varianti-…txt` — **Zeland vol. I**. La spina dorsale teorica:
   modello delle varianti · pendoli · onda della fortuna · equilibrio · passaggio indotto ·
   corrente delle varianti.
2. `2-…-fruscio-delle-stelle-del-mattino-…txt` — **Zeland vol. II** (209 pp). L'apparato
   pratico: intenzione interna/esterna e sua depurazione · diapositive e sfera del benessere ·
   visualizzazione del processo e catene di transfer · anima e ragione, la freile, la finestra
   e il «frame» · fini e porte, proprie e altrui · l'ispirazione.
3. `3-…-avanti-nel-passato-…txt` — **Zeland vol. III** (120 pp, ricostruito via OCR).
   Energia · Freiling · coordinazione dell'importanza e dell'intenzione · le mele cadono in
   cielo · transazione e sfumature delle decorazioni · lettere ai lettori · inversione della realtà.
4. `reality-transurfing-le-regole-dello-specchio-…txt` — **Zeland vol. IV + vol. V** in un
   solo file (336 pp). Il PDF italiano è un *doppio ebook*: alle righe 54-3441 sta *La Gestione
   della Realtà* (vol. IV — cap. I *Le danze con le ombre*, cap. II *Il sogno degli dei*), alle
   righe 3950-7367 *Le Mele Cadono in Cielo* (vol. V — cap. I *Il mondo speculare*, cap. II
   *Il portiere dell'Eternità*). **I due indici sono scambiati rispetto ai rispettivi libri**:
   fidarsi dei frontespizi (righe 26 e 3920), non della posizione dell'indice. Ha strato di
   testo pulito, niente OCR e niente pagine doppie.
5-7. Trilogia di Klod Nagal: `transurfing-hackerare` · `surfare-nell-ologramma` ·
   `cosa-ci-ha-detto-tafti`.
8. `tafti-la-sacerdotessa-camminando-dal-vivo-in-un-film-vadim-zeland.txt` — **Zeland**, primo
   libro del ciclo Tafti (177 pp, 2017). Non un compendio del Transurfing: è la fonte diretta da
   cui Nagal aveva già tratto la treccina, i due schermi, l'illusione dell'azione scenica —
   qui però nella voce originale di Tafti, in prima persona e con un registro ironico-dispotico
   dichiarato tale dall'autore stesso in appendice (intervista 2017). Materiale genuinamente
   nuovo: il principio del beneficio/permesso/seguire e i comandi della Forza, l'impostazione
   dell'immagine e del riflesso (le due tecniche speculari, con le persone e con la realtà), il
   nuovo manichino (Scintilla del Creatore, forme-pensiero vs marker-pensiero, sincronizzazione
   del progetto), e *Lada* — lo stato di armonia da generare apposta, che è la stessa idea del
   registro ✓ del banco. 45 capitoli brevi, indice completo alle righe 51-98 e 7213-7272.
9. `cosa-non-ha-detto-tafti-vadim-zeland.txt` — **Zeland**, seguito diretto del precedente (223
   pp, 2019/2020). Formato diverso: non la voce di Tafti in prima persona, ma **domande di
   lettori con risposte di Zeland** — utile perché mostra il metodo applicato a casi concreti e
   ne chiarisce i limiti con più precisione della teoria. Letto per intero (23 capitoli, indice
   riga 8); molti capitoli (Treccina 1-2-3, Gli schermi, L'attenzione, Realizzazione 1-2, Il
   manichino, Le lucciole) **rinforzano** materiale già assorbito con Tafti la Sacerdotessa e non
   hanno prodotto sezioni nuove. Tre capitoli erano invece territorio scoperto e sono diventati
   sezioni: **I figli** (l'unica eccezione dichiarata alla regola «non si possono impostare le
   persone»: la salute dei figli piccoli, finché condividono lo strato di mondo dei genitori),
   **I soldi** (il denaro non è mai il fine da illuminare, è sempre conseguenza della missione),
   **Le relazioni** (impostare l'atteggiamento verso una persona, mai la persona; include «Il
   regalo di Tafti», il rituale per trovare un partner). Il capitolo *La sociofobia* cita **due
   passaggi da Scardinare il Sistema Tecnogeno** (nota 23-24, pag. 411 e 416: la formula
   molletta/consapevolezza/flusso e l'esempio di James Bond per l'intenzione dell'Arbitro) — da
   verificare e ri-citare con contesto pieno quando si leggerà quel libro. Il capitolo
   *L'alimentazione* è stato deliberatamente **lasciato fuori dalla mappa**: consigli dietetici e
   di salute alternativa che esulano dal metodo operativo che la mappa documenta.
10. `reality-transurfing-5-0-scardinare-il-sistema-tecnogeno-vadim-zeland.txt` — **Zeland**,
    ciclo Matrix (454 pp, 2012). Primo libro del progetto a ricevere una **parte a sé stante**
    (Parte VIII, «La tecnosfera», 5 sezioni) invece di essere assorbito in quelle esistenti: la
    scala del discorso è quella della civiltà, non della persona, ed è materiale che i primi
    cinque volumi non coprivano. Letto per intero. Parte I (visualizzazione, forma-pensiero,
    «bio-televisore», file di configurazione) è **rinforzo** di materiale già mappato, salvo
    un aneddoto (l'autista abusivo, sez. *L'idrodinamica dell'intenzione* — diventato una storia
    in Parte IX). Parte II (la tecnosfera, cattura dell'attenzione, coscienza tecnogena,
    l'artefatto d'intenzione) e Parte IV (la società, l'involuzione della coscienza, lo
    scardinamento e l'unificazione della personalità, anatomia dell'importanza, le mollette
    mentali, i ricevitori e i trasmettitori, i due taccuini, la trasmissione dell'intenzione, la
    liberazione della Forza) sono il nucleo nuovo, diventato le cinque sezioni della Parte VIII.
    **Parte III (la biosfera, 20 capitoli) è quasi interamente crudismo/vegetarianismo militante
    ed è stata lasciata fuori** per lo stesso motivo del capitolo *L'alimentazione* di Cosa non
    ha detto Tafti — un solo aneddoto vagliato e scartato perché non separabile dalla tesi
    dietetica (la legge di attrazione della Forza). Restano fuori anche, dentro Parte II e IV,
    i capitoli puramente medici (Aprire lo sportello, Le mollette somatiche, Il controllo del
    supporto vitale) salvo le metafore che ne sopravvivono citate a parte (l'«ingranaggio»,
    il «joystick»). I due passaggi già citati in *Cosa non ha detto Tafti* (nota 23-24) sono
    ora citati per esteso e in contesto nella sezione **Le mollette mentali**.

11. `transurfing-vivo-vadim-zeland.txt` — **Zeland**, ciclo Matrix (432 pp, 2013 in italiano;
    originale *Živoj Transerfing*). È il **4.0**, cioè il libro che precede *Scardinare* (5.0): stesso
    ciclo, stesso argomento, formato a domande e risposte. Per questo **non ha avuto una parte a sé**
    ma ha allargato la Parte VIII con una sezione sola, *La seconda civiltà*. Il suo glossario non
    introduce **nessun** termine nuovo — tutti già mappati — e dei 23 capitoli **dieci sono di
    salute/alimentazione** (XI, XII, XIII, XV, XVII, XIX, XX, XXI, XXIII e gli Allegati 1-2-5) e
    restano fuori per il criterio di sempre. Il nuovo vero: i pendoli come **forma di vita che nasce
    e muore** («il pendolo si estingue quando finisce nell'oblio ciò che l'ha generato»), la
    **seconda civiltà** che governa la prima, l'assenza di piani («chi gestisce la giungla?
    Nessuno»), «la ragione non ha una volontà libera», il **credo dell'Arbitro** (→ innestato in
    `#arbitro`), **brama contro risolutezza** (→ `#intenzione`) e la **mosca nella ragnatela**,
    l'immagine con cui giustifica perché le pratiche antiche non bastano più.

12. `la-sacerdotessa-itfat-vadim-zeland.txt` — **Zeland**, ciclo Tafti (375 pp, italiano 2021; originale 2018).
    **L'unico romanzo di Zeland**, scritto nello stesso settembre 2017 di *Tafti la Sacerdotessa* e mandato alla
    traduttrice insieme a quello (la sua *Nota della traduttrice*, in coda, racconta che stava per rinunciare per noia
    e che l'ha salvata il filone comico di Adja il Verde). 52 capitoli brevi, indice a riga 28.
    **Nessuna parte nuova**: la dottrina è quella di Tafti, già mappata, e le parti codificano dottrina — a differenza
    di *Scardinare*, qui non cambia la scala del discorso. È però tutt'altro che ridondante: dovendo far spiegare il
    metodo a una sacerdotessa amnesica e a una diva che non ne sa nulla, Zeland è costretto a **spiegare ciò che
    altrove aveva solo asserito**. Ne è venuta **una sezione nuova, `#testimone` («Il Testimone»)**, nell'Officina
    subito dopo `#treccina` perché nel libro il Testimone è il *prerequisito* della treccina: l'attenzione
    sull'attenzione, l'«abitudine inversa» allenabile («è come lavarsi i denti»), la scala
    spettatore/personaggio/osservatore, i raggi blu, e la tecnica nuova **scardinare la sceneggiatura** (quando il
    copione è già partito, fare qualcosa fuori dalla logica degli eventi).
    Innesti: `#treccina` (rudimento arcaico · «non è una treccia del desiderio ma una treccia dell'intenzione» ·
    perché si è atrofizzata · «possedere non significa avere ma essere in grado di gestire»), `#intenzione`
    (**il retropensiero**: «non un desiderio, non un comando, né una richiesta, ma piuttosto un permesso» — parola che
    non compare in nessun altro libro), `#tecnosfera` (**il coperchio del mondo**, la tecnosfera raccontata come farsa).
    Tre storie in Parte IX: *La zuppa di latte* · *Il convegno degli scienziati* · *«Conoscete voi stessi?»*.
    **Dato notevole per `#divergenze`:** in 375 pagine le parole *pendolo*, *diapositiva* e *matrix* non compaiono
    **nemmeno una volta**; resta la sola treccina (12). Quando Zeland smette di argomentare e racconta, il vocabolario
    che gli resta addosso è quello del 2017.

13. `surfare-nell-ologramma.txt` — **Klod Nagal**, Operation Moksha (~80 pp, 22 capitoli).
    Già letto nel 2026 e mappato, **riletto per intero il 6-9-2026** su richiesta dell'utente,
    ed è la rilettura che ha prodotto la Parte XI. Scoperte:
    **(a)** Nagal dichiara lui stesso di non esporre Zeland (la citazione sta nella regola qui
    sopra) e liquida i pendoli come «argomento noiosissimo», rimandando ai libri di Zeland;
    **(b)** sette capitoli su ventidue non sono Transurfing (decreti anti-arconti, perdono
    karmico, trasmutazione alchemica del dolore, protezioni con sale ed erbe più uovo e cotone
    divinatori, ricapitolazione tolteca da Castaneda, mindfulness, I Ching);
    **(c)** c'è uno **strato commerciale dichiarato** — libri su WhatsApp a 10 euro, lezioni
    personalizzate richiamate una decina di volte, rimandi a specialisti a pagamento — che la
    mappa ora riporta come fatto, in `#nagal`, perché cambia come si pesa un'affermazione.
    Il Transurfing vero che contiene è in tre punti **migliore di Zeland** e sta in `#nagal`:
    la regola del silenzio («NON DITELO A NESSUNO, NEMMENO A ME!», la formulazione più netta
    del corpus e la ragione per cui banco e diario sono privati), l'immagine del supermercato
    per la nonchalance, e il consiglio di transizione («non licenziatevi prima di averlo
    ottenuto» · «mantenete i piedi in due scarpe»), che in Zeland non c'è. Il capitolo finale
    di controindicazioni è onesto: «ne ho manifestate il 90%».

Ogni capitolo di Zeland si chiude con un **Riepilogo** scritto dall'autore: sono la sintesi
più densa disponibile, da leggere per primi quando si torna sui testi.

**Le tre promesse del vol. I sono state mantenute e sono nella mappa:**

| Promessa | Dove è stata sciolta |
|---|---|
| L'Enigma del Guardiano | vol. III — «Otterrete la libertà quando cesserete la vostra battaglia» (sez. 23) |
| «Le mele cadono in cielo» | vol. III — la coordinazione dell'intenzione · e il vol. V, che porta quel titolo, la porta a compimento nei sette principi dello specchio |
| Cosa sia davvero la scelta | vol. II — l'intenzione come risolutezza ad avere (sez. 10) |

**Copertura verificata:** gli indici dei **cinque** volumi Zeland del corso base (102 sezioni per
i primi tre, 26 per il quarto e il quinto) sono stati confrontati uno per uno con il testo del
sito. Nessuna sezione manca. Il confronto si rifà con lo script di audit riportato in fondo a
questo file — rifarlo dopo ogni libro nuovo. Per *Scardinare il Sistema Tecnogeno* l'audit è
stato fatto per capitolo (non per volume, essendo un solo libro di 34 capitoli): tutti i capitoli
di Parte I, II e IV superano la sonda tranne quelli deliberatamente esclusi (dietetici/medici,
vedi voce 10 sopra); Parte III (biosfera) non è stata sondata perché esclusa in blocco.

Estratti ma **non ancora letti** (12 libri, ~2.650 pp): bardo-arconte, codice-moksha,
gnosi-e-rigpa, la-quinta-via, la-quinta-via-ii, ritorno-all-origine, stranieri-sulla-terra,
ufo-alieni-libro, arconti-e-gnosticismo, dark-cupido, legge-di-attrazione, trappola-tunnel-di-luce.
Sono la cornice metafisica (Matrix, arconti, gnosticismo, trappola della reincarnazione) a cui i
libri sul Transurfing rimandano senza svilupparla.

## Prossimo passo concordato

L'utente fornisce i libri di **Vadim Zeland** in ordine, uno alla volta, mettendoli in
`pdf-sorgenti/`. I cinque volumi del corso base sono arrivati e sono stati assorbiti. Restano:

| Ciclo | Titoli |
|---|---|
| Corso base (2004-05) | ~~Lo Spazio delle Varianti~~ ✓ · ~~Il Fruscio delle Stelle del Mattino~~ ✓ · ~~Avanti nel Passato~~ ✓ · ~~La Gestione della Realtà~~ ✓ · ~~Le Mele Cadono in Cielo~~ ✓ |
| Espansione | **Il Proiettore della Realtà Separata** ← non ancora arrivato |
| Matrix | ~~Scardinare il Sistema Tecnogeno~~ ✓ · ~~Transurfing Vivo~~ ✓ |
| Pratici | Tarocchi dello Spazio delle Varianti |
| Tafti (2018-21) | ~~Tafti la Sacerdotessa~~ ✓ · ~~Cosa non ha detto Tafti~~ ✓ · ~~La Sacerdotessa Itfat~~ ✓ · **Tafti la Sacerdotessa 2** ← non ancora arrivato |

Con i volumi IV e V il corso base si chiude: le tre promesse del vol. I sono tutte sciolte e
il principio dello specchio, appena abbozzato nel vol. III, è diventato una parte intera della
mappa (Parte VII, sette principi + amalgama + Arbitro + dieci tecniche + pulizia + correzione,
più — dal ciclo Tafti — l'uomo di carta/impostazione dell'immagine e l'impostazione del
riflesso). Il gancio verso il seguito resta **il Proiettore**: il vol. V chiude sul «portiere
dell'Eternità» e sull'idea che la realtà si proietti, non si costruisca — non ancora arrivato.
Nel frattempo *Scardinare il Sistema Tecnogeno* ha aperto la **Parte VIII, La tecnosfera**
(5 sezioni: la tecnosfera, ricevitori e trasmettitori, le mollette mentali, l'artefatto
d'intenzione, il proiettore e i due taccuini), la prima parte della mappa nata da un libro solo
invece che dal confluire di più letture. La sua stessa novella di chiusura, *Una festa in
arancione*, introduce Sottomarino Giallo e Mucca Arancione — gli stessi personaggi con cui si
apre *La Sacerdotessa Itfat*, il prossimo libro in coda.

Al 6 settembre 2026 **in `pdf-sorgenti/` non resta nessun PDF non letto**: i nove file presenti sono tutti estratti e assorbiti. L'ultimo è stato *La Sacerdotessa Itfat* (voce 12 sopra). **Attenzione a tre coppie di titoli quasi identici e di autori diversi:** `cosa-non-ha-detto-tafti-vadim-zeland.txt` (Zeland) ≠ `cosa-ci-ha-detto-tafti.txt` (Nagal); `tafti-la-sacerdotessa-…` (il saggio, 2017) ≠ `la-sacerdotessa-itfat-…` (il romanzo, 2018); *Transurfing Vivo* (4.0) ≠ *Scardinare il Sistema Tecnogeno* (5.0). Il prossimo libro atteso è **Tafti la Sacerdotessa 2**, non ancora arrivato.

> Attenzione ai titoli: *Transurfing in 78 giorni*, *Transurfing del Sé* e *L'Artefice della
> Realtà* comparivano in un elenco precedente ma **non sono stati verificati** nel catalogo
> italiano. Non mandare l'utente a cercarli finché non si conferma che esistono.

### Trappola già incontrata: PDF con pagine doppie

Le scansioni Macro dei Zeland emettono **ogni pagina due volte di fila**: raddoppiano il file
senza aggiungere una parola. `estrai.py` le riconosce e le collassa (soglia: 40% di pagine
consecutive identiche), stampando «pagine doppie collassate». Se un libro esce con il doppio
delle pagine attese, è quello.

### Trappola già incontrata: PDF senza strato di testo

Il vol. III è una **scansione pura**: `pypdf` restituisce zero caratteri. Ricostruito con
`pdftoppm -r 300 -gray -png` + `tesseract -l ita --psm 3` pagina per pagina. Usare **psm 3**,
non psm 6: su pagine a due colonne psm 6 le fonde e mescola le righe. Nota: il tool Read non
vede `/opt/homebrew/bin`, quindi il rendering va fatto a mano da Bash e poi si legge il .txt.
L'OCR è mediocre — `b` per `è`, `piir` per `più`, `Tiansurfing` — ma perfettamente leggibile.

### Trappola già incontrata: non tre elenchi paralleli, ma quattro

Aggiungendo la Parte VIII (La tecnosfera) è emerso un **quarto elenco parallelo**, mai
documentato prima: l'array `var PARTI = [...]` dentro lo switcher JS (vicino alla fine del file,
prima di `instrada(location.hash, true)`). `mostra(nome)` assegna la classe `on` **solo** alle
parti elencate lì — una parte assente dall'array resta nel DOM, ha un bottone nella barra, ma
`location.hash` puntato su una sua sezione non la mostra mai (rimane sempre `display:none`,
senza errori in console). Si scopre solo aprendo l'anteprima su un'ancora della parte nuova.
`strumenti/verifica.py` ora controlla anche questo elenco insieme agli altri tre.

### Trappola già incontrata: `scrollTo({behavior:"smooth"})` non fa nulla e non lancia

Il bottone «Su» (`#su`, in basso a destra, compare oltre i 700px di scroll) all'inizio usava
`window.scrollTo({top:0, behavior:"smooth"})`. **Non scrollava, e non lanciava eccezioni**,
quindi il `try/catch` con il fallback non scattava mai. La forma semplice
`window.scrollTo(0, 0)` funziona ovunque **e resta morbida lo stesso**, perché la pagina
dichiara già `html{scroll-behavior:smooth}` e la regola `prefers-reduced-motion` la
disattiva da sé. Usare sempre la forma a due argomenti.

Correlato, sul provare queste cose: **in Chrome headless uno `scrollTo` programmatico non
emette l'evento `scroll`**, quindi un test che si aspetta di vedere reagire un ascoltatore
deve emetterlo a mano (`window.dispatchEvent(new Event("scroll"))`). Senza, il test dà
falsi negativi — ed è già capitato di inseguire un bug che non c'era. Attenzione anche a
verificare le transizioni CSS: 120 ms dopo il cambio di classe `opacity` è a metà strada,
quindi si controlla `classList.contains(...)`, non il valore calcolato.

### Trappola già incontrata: un toggle di classe non va dentro il `requestAnimationFrame` condiviso

`aggiornaSu()` era stato agganciato allo stesso rAF di `aggiornaPartNav()`. Quel rAF esiste
perché `aggiornaPartNav` **misura** la pagina (`getBoundingClientRect`) e va throttlato; ma
se il fotogramma non arriva, il bottone «Su» resta acceso a pagina in cima. Ha un suo
ascoltatore `passive` che legge solo `pageYOffset` e accende una classe.

### Trappola già incontrata: `white-space:nowrap` sul riferimento di pagina

`.src .pagg` aveva `white-space:nowrap`. Con un riferimento solo («pagg. 14-15») non si
vedeva nulla; con due o tre libri dichiarati il blocco non poteva andare a capo, **usciva
dalla colonna dell'aside (240px) e finiva stampato sopra il testo della sezione** — succedeva
in **otto** sezioni, la peggiore `#treccina` con 623px di contenuto in 240 di colonna.
Segnalato dall'utente su `#scardinamento`.

Non basta togliere `nowrap`: **anche un riferimento singolo può eccedere la colonna**
(«Cosa non ha detto Tafti pagg. 160-161» sono 37 caratteri ≈ 259px). La soluzione è tenere
unito **solo il numero di pagina**: ogni `<span class="pagg">` racchiude il suo `pagg. N-M`
in un `<i>` (`white-space:nowrap`, `font-style:normal`), e il nome del libro va a capo
liberamente. Se si rigenerano i riferimenti di pagina, va rifatto anche questo.

**Come si trova un problema del genere**: non a occhio sul sorgente ma misurando il DOM
renderizzato — per ogni `.src`, `scrollWidth > clientWidth`. Vale per qualunque elemento
con `nowrap` dentro una colonna stretta.

### Trappola già incontrata: `display:grid` su un `<li>` con un marcatore via `::before`

Due componenti (`.checks`, la lista a rombi di "I fini e le porte altrui", e `ol.algo`, gli
elenchi numerati di tecniche usati in quattro sezioni) impostavano il singolo `<li>` a
`display:grid` con due colonne — una stretta per il marcatore (`◇` o il numero), una larga per il
testo — generato con `::before`. **In CSS Grid ogni figlio diretto diventa un item a sé, e lo
pseudo-elemento `::before` conta come un item in più**: se il testo del `<li>` è scritto come
contenuto misto diretto (es. `<b>Titolo.</b> resto del testo <i>corsivo</i>.`, senza un `<div>` o
`<p>` che lo racchiuda), ogni tag inline diventa un item a parte oltre al marcatore. Con solo due
colonne dichiarate, il terzo item va a capo nella colonna stretta — 20-44px — e il testo si spezza
**una parola per riga** per tutta la sua lunghezza. Capitava solo quando il `<li>` non incapsulava
il testo in un unico blocco: uno dei quattro `ol.algo` (quello con `<div><span>…</span><p>…</p></div>`
dentro al `<li>`) non ne soffriva per caso, gli altri tre sì. **Fix**: mai `display:grid`/`flex`
sul contenitore diretto di un marcatore-via-pseudo-elemento più testo misto — usare invece
`position:relative` sul `<li>` e `position:absolute` sul marcatore. Se si aggiunge un nuovo
componente con marcatore + testo, verificarlo aprendo l'anteprima su quella sezione, non fidarsi
della sola lettura del sorgente: il bug non dà errori né in `verifica.py` né in console.

## Rapporto Vesica — lettura in corso (1/8 parti lette)

Iniziato il 6-9-2026. **2.559 pagine**, strato di testo pulito, ~15,8 MB estratti in
`testi/rapporto-vesica-v-16-08-2026.txt`. Non ha un sommario tradizionale: ha un **indice di
468 enunciati** compresso in tre pagine dense (pagg. 8-10, righe 407-887 del testo estratto),
dove ogni enunciato diventa poi un titolo di paragrafo nel corpo del libro — un'enciclopedia
in sequenza, non un saggio argomentativo.

**`note/vesica-indice-completo.md` è la checklist canonica**: le 468 voci, raggruppate negli
otto blocchi tematici sotto, ognuna spuntabile quando viene letta e trasferita in una sezione
vera. È la fonte di verità sulla copertura — non fidarsi della sola mappa per sapere cosa manca.

Le otto parti (dopo la Parte I «Il libro», che è la sola meta-sezione):

| Parte | Voci | Cosa |
|---|---|---|
| II · Gli strumenti d'indagine | 40 · **letta** | logica, matematica, metodo scientifico — sette sezioni, 45 citazioni verificate |
| III · La fabbrica del consenso | 22 | propaganda, PNL, manipolazione mediatica |
| IV · Le architetture del potere | 91 | geopolitica, banche centrali, società segrete |
| V · DNA, energia e materia | 104 | genetica, fisica quantistica, energia libera |
| VI · Geometria sacra e luoghi anomali | 37 | piramidi, megaliti, solidi platonici |
| VII · Ufologia ed esopolitica | 33 | fenomeno UFO, disclosure, razze aliene |
| VIII · Mitologia e cosmologia perduta | 128 | mitologia greca/sumera, Anunnaki, «Keylontic Science» |
| IX · Coscienza e responsabilità | 13 | chiusura del trattato, dalla diagnosi all'azione |

**Ogni parte è oggi un elenco, non un riassunto**: una sola sezione (`#<id>-stato`) che
dichiara «N voci individuate, 0 lette» e le elenca in una `<ul class="checks">`. Si passa da
elenco a sezione vera **una voce alla volta**, leggendo il testo integrale prima di scrivere
— stesso principio dei libri di Zeland, mai riassunti a memoria.

**Perché è il perno della biblioteca, in pratica**: quando una voce di Vesica coincide con un
argomento che un'altra mappa già tratta per esteso (es. propaganda, fisica, mitologia), la
sezione **non ripete**: usa il rimando `href="transurfing:sezione"` e aggiunge solo ciò che
Vesica dice in più. Vedi la nota sui rimandi fra mappe più sotto.

**Trappola incontrata e corretta scrivendo questa parte**: la chiusura di `<div class="wrap"
id="contenuto">` e il divisore `.perf` erano scritti in coda **all'ultima parte di Transurfing**
invece che in un pezzo del telaio — un'assunzione implicita («chi capita per ultimo chiude il
contenitore») che si è rotta al primo urto con una mappa diversa: l'ultima parte di Vesica non
chiudeva nulla, e `verifica.py` (esteso in questa stessa occasione a controllare **tutte** le
mappe della biblioteca, non solo Transurfing) ha trovato un `<div>` mai chiuso. Ora è un pezzo
esplicito del telaio, `corpo/03b-contenuto-chiude.html`, inserito da `costruisci.py` dopo
l'ultima parte di ogni mappa.

## La regola che viene prima di tutte: Zeland di qua, gli altri di là

Deciso il 6-9-2026 su richiesta dell'utente, dopo aver riletto *Surfare nell'Ologramma*.
Per un anno il materiale di Klod Nagal è stato **innestato dentro le sezioni di Zeland**,
perché era arrivato per primo e sembrava commentarlo. Era un errore di struttura, e a
smentirlo è Nagal stesso: «Io e Zeland abbiamo due concezioni di realtà Matrix distinte,
alla mia concezione di realtà ho fatto calzare il Transurfing, e viceversa». Non espone
Zeland — se ne serve dentro un impianto suo (arconti, trappola della reincarnazione,
simulazione), e vende lezioni e libri dentro il testo.

**Parte XI, «Le altre voci»** (`parte-voci`, `--pc:var(--teal)`) è la sede di **tutto ciò
che non è di Zeland**. Dentro è organizzata **per autore**: ogni voce apre con una banda
`.voce-testa` (nome, corpus, tre righe su chi è) e ogni sua sezione porta una
`<span class="firma">` che dice di chi è. L'utente ha già annunciato un secondo autore:
si aggiunge una banda e le sue sezioni, **senza creare una parte nuova** — la barra non
deve crescere e il confine deve restare uno solo.

Ci sono finite, spostate dalle parti di Zeland: `#leggi`, `#terreno`, `#tecniche`,
`#algoritmo`, `#trappola`, `#limiti`; più due sezioni nuove, `#nagal` (chi è, come tratta
Zeland, lo strato commerciale, dove è migliore) e `#moksha` (i sette capitoli che non sono
Transurfing: decreti, perdono karmico, trasmutazione, protezioni, ricapitolazione tolteca,
mindfulness, I Ching — più l'arte come tecnica, che invece lo è).

**Il costo, che è anche una scoperta:** l'Officina perde l'algoritmo in cinque passi e il
catalogo delle tecniche. Non è un danno — è una verità che la vecchia struttura nascondeva:
*i pezzi più operativi della mappa non erano di Zeland.*

**Restano sei sezioni miste** (`#varianti`, `#anima`, `#pendoli`, `#treccina`, `#fonte`)
dove il materiale di Nagal è intrecciato a quello di Zeland e non si estrae con un taglio
netto. Vanno riviste una per una: è il lavoro rimasto aperto.

**Criterio d'inclusione, diverso da quello usato per Zeland.** Di Zeland la mappa documenta
il *metodo*, e i capitoli dietetici restano fuori. Di un altro autore documenta anche
*l'autore*, perché è lui il punto in discussione: togliere i sette capitoli esoterici di
Nagal lo farebbe sembrare più zelandiano di quanto sia. Deciso dall'utente.

## Convenzioni della mappa

- **La struttura è a undici parti**, ognuna un `<div class="part" id="parte-…">`, più il banco
  (`parte-casa`), per un totale di 66 sezioni e una galleria di 51 storie.
  Il **vocabolario non è più una sezione**: vive nel pannello a destra (linguetta
  «Vocabolario»), e il suo `<dl id="gloss-main">` resta nel DOM dentro `#gloss-sorgente`
  come sorgente da cui il pannello copia — nascosto da `html.js #gloss-sorgente`, così
  senza JS il vocabolario resta comunque leggibile in fondo ai Riferimenti. La barra in alto ne mostra una per volta; senza JS restano tutte visibili
  (`html.js .part{display:none}` — l'attributo `js` lo mette uno script inline subito dopo
  il `</style>`, per evitare il lampo di tutto il documento).
  Un libro nuovo, di norma, arricchisce una sezione o ne aggiunge una dentro la parte giusta —
  ma se la sua scala di discorso non ha equivalenti nella struttura esistente (com'è successo con
  *Scardinare il Sistema Tecnogeno*, l'unico libro finora a valere una parte a sé), può guadagnarsi
  una parte intera: è un'eccezione, non un precedente da ripetere alla leggera.
- **I quattro elenchi paralleli non si scrivono più a mano.** Erano la trappola più costosa del
  progetto — barra, ordine fisico, `BRANCHES` del diagramma e `PARTI` dello switcher —
  e dimenticarne uno non dava errori: la parte semplicemente non compariva mai. Dal 6-9-2026
  **si generano tutti da `parti` in `mappa.json`**: per aggiungere una parte si aggiunge una
  voce lì e il file della parte in `parti/`. Resta da scrivere a mano il solo `part-toc` dentro
  la testata della parte. `strumenti/verifica.py` continua a controllare i quattro elenchi sul
  file costruito: ora è una rete di sicurezza contro le regressioni, non più l'unica difesa.
- **«Da dove comincio se…»** (`#porte`, in fondo al banco) è il secondo ingresso alla mappa:
  diciotto situazioni di vita — *una persona se n'è andata*, *devo cambiare lavoro*, *questo
  problema non ha soluzione* — ognuna con la riga che la riformula nei termini del metodo e
  due o tre link alle sezioni che la trattano davvero. Non è una sezione e non entra nel
  conteggio. **Regola:** una porta non deve mai promettere qualcosa che la sezione linkata non
  contiene — se serve, si aggiunge prima il materiale alla sezione (è già successo con l'amore
  non corrisposto e la solitudine, aggiunti al catalogo delle mollette per non lasciare due
  porte a vuoto). `verifica.py` intercetta i link morti, non le promesse non mantenute.
- **Le sezioni nuove vanno scritte citando i testi**, non riassumendo a memoria: rileggere
  il passaggio in `testi/` prima di scrivere. Gli aneddoti della Parte IX sono il posto dove
  finiscono gli esempi narrativi; le sezioni tengono la dottrina. Le voci del `part-toc` sono
  numerate **in progressione continua su tutta la pagina** (01→63): aggiungendo una sezione **non
  rinumerare a mano** — si aggiunge la voce nel `part-toc` con un numero qualsiasi e si lancia
  `python3 strumenti/rinumera.py --scrivi`, che rifà tutta la progressione in ordine di
  documento e avverte se una voce punta a una sezione inesistente o se il sommario è
  fuori ordine. A mano si sbaglia: una nota rimandava alla «sezione 30» che nel frattempo era
  diventata un'altra.
- **Il banco ha tre porte d'ingresso alla mappa**, ed è voluto: il **diagramma** entra dalla
  dottrina, **`#percorsi`** («In che ordine leggerlo») entra dall'ordine, **`#porte`** («Da dove
  comincio se…») entra dalla vita. I tre percorsi — *il primo giro* (10 passi), *quando il primo
  giro ha funzionato* (8), *il ciclo Tafti e la tecnosfera* (9) — non sono un corso: ogni passo
  porta il **perché viene adesso**, che è l'unica cosa che un elenco di link non dà. Nessuno
  stato, nessuna spunta, nessuna percentuale: sarebbe un tracker travestito. La gerarchia fra i
  percorsi non è nostra, è di Zeland, che chiama il corso base «la scuola primaria».
- **`#tavola` («Tutte le tecniche in una tavola», in fondo all'Officina)** mette le venti
  tecniche di otto libri su cinque colonne: *tecnica · a cosa serve · quanto dura · da dove
  viene · quando non usarla*. L'ultima colonna è la ragione per cui esiste. Aggiungendo una
  tecnica da un libro nuovo va aggiunta anche lì, con la sezione di rimando.
- **`#divergenze` («Dove i libri non dicono la stessa cosa», in Riferimenti)** è l'unica
  sezione che non espone il metodo ma lo confronta con se stesso: le posizioni in cui Zeland
  contraddice o retrocede i propri libri precedenti. Contiene una tabella di **conteggi
  verificabili** (occorrenze di *pendolo · diapositiva · treccina · matrix* nei sette libri di
  Zeland letti). **Leggendo un libro nuovo va aggiunto anche all'elenco `LIBRI` di
  `strumenti/cita.py`**, altrimenti tutte le citazioni che ne vengono risultano «non trovate».
  Se si legge un libro nuovo, i conteggi vanno rifatti e la riga aggiunta:
  `grep -oic 'pendol' testi/<libro>.txt` e simili. Non arbitrare fra gli strati — la sezione
  esiste proprio per non farlo.
- **La ricerca (`#ric-veil`, si apre con ⌘K/Ctrl+K, `/` o il bottone in coda alla barra)**
  copre tutta la mappa. **L'indice si costruisce da solo dal DOM al caricamento**: non c'è
  nessun elenco da tenere aggiornato quando si aggiunge una sezione, un blocco o una storia —
  purché si usino i componenti esistenti (`section.branch`, `.move`, `ul.tree > li`,
  `article.story`, `.door`, `article.percorso`, `table.tools tbody tr`, `#gloss-main > div`).
  Un componente nuovo che non rientri in questi va aggiunto al costruttore dell'indice,
  altrimenti il suo testo non si trova.
  - **Perché non è una ricerca a sottostringa**: in italiano sarebbe inservibile. La mappa
    scrive «affossare», e chi cerca «affossamento» non troverebbe nulla. Il termine cercato
    viene ridotto alla radice (elenco `SUFF`) e cercato come **inizio di parola**; la
    corrispondenza piena vale più di quella per radice, così l'ordine non si sporca.
  - **I gruppi si ordinano per il punteggio del loro esito migliore**, non per un ordine fisso:
    con l'ordine fisso, cercando «pendolo» il primo risultato era una parte qualsiasi invece
    della sezione che ne parla. È già stato sbagliato una volta.
  - Le virgolette (`"…"` o `«…»`) cercano la **frase esatta**; più parole valgono come
    tutte-presenti. I risultati del vocabolario non portano nella pagina: aprono il pannello
    a destra già filtrato.
  - Ogni risultato porta il colore della sua parte, coerente con la codifica dei ruoli.
  - **All'arrivo le parole cercate vengono evidenziate nel testo vero** (`mark.ric-eco`),
    spezzando solo nodi di testo: il markup non viene toccato e `pulisciEco()` ricompone i
    nodi com'erano. Restano finché non si cerca altro o non si preme `esc` (una targhetta in
    basso lo dice e fa da bottone). Lo scroll va sulla **prima parola evidenziata**, non sul
    blocco: in una sezione lunga il centro del blocco può essere altrove.
- **Ogni ramo dichiara la fonte** (`<p class="src">`) — serve a sapere da dove viene cosa
  man mano che i libri si accumulano.
- **Colore = ruolo, non decorazione**: blu com'è fatto il terreno, ruggine ciò che ti
  agisce contro, salvia ciò che hai dalla tua, ambra ciò che si esegue, prugna la fonte,
  **verderame (`--teal`) le voci che non sono di Zeland**.
  La legenda sopra il diagramma dichiara questa codifica: se cambia, va cambiata lì.
- **La numerazione si usa solo dove c'è davvero una sequenza** (l'algoritmo in 5 passi).
  I rami non sono un percorso obbligato e non vanno presentati come tale.
- **Le citazioni tra virgolette sono letterali**, dai testi. Se una formulazione è una
  sintesi, non va tra virgolette. **Lo verifica `strumenti/cita.py`**, che prende ogni «…»
  del sito, la cerca in tutti i libri letti e dice in quale e a che pagina. Al 6-9-2026:
  1082 citazioni, 654 trovate alla lettera nel libro dichiarato, 239 riconosciute a meno
  dell'OCR, **0 attribuite male**, 189 non trovate (di cui 75 nei volumi I e III, che sono
  scansioni OCR: lì la corrispondenza carattere per carattere è impossibile per costruzione).
- **Innestando materiale di un libro nuovo in una sezione esistente, aggiornare la sua
  `<p class="src">`.** È l'errore sistematico che `cita.py` ha scoperto la prima volta che è
  stato eseguito: sette citazioni innestate da *Tafti* e *Cosa non ha detto Tafti* dentro
  sezioni che dichiaravano solo i volumi del corso base, più una attribuita al vol. III
  quando stava nel vol. II. Tutte corrette.
- **I riferimenti di pagina** (`<span class="pagg">` dentro la fonte) sono generati, non
  scritti a mano: si ricavano dalle citazioni verificate, e si tengono solo quando sono
  affidabili — almeno due riscontri per libro e un arco non superiore a 60 pagine, altrimenti
  è un'indicazione vaga che finge precisione. 46 sezioni su 64 ne hanno uno. Se il libro è uno
  solo si scrivono le sole pagine, perché la fonte lo nomina già.

## Vincolo di progettazione del banco di lavoro

Il banco (la parte operativa in cima alla pagina) non deve mai diventare un tracker
motivazionale: **niente streak, niente badge, niente rosso, nessuna metrica di
fallimento, nessun promemoria che rimprovera.** Un contatore che ti fa sentire in debito
crea *importanza*, e l'importanza è il potenziale superfluo che il metodo esiste per
sciogliere — sarebbe anti-Transurfing e farebbe più danno dell'assenza dello strumento.

Il registro ✓ celebra e basta: nei libri il marker serve a *festeggiare*, e festeggiare
è la causa degli effetti che si attirano.

Correlato: la **regola del silenzio** ("non dire a nessuno la tua prossima mossa") è il
motivo per cui i dati stanno su una pagina privata e non vengono mai esposti o condivisi.

## Audit di copertura

Dopo ogni libro assorbito, verificare che nessuna sezione dell'indice sia rimasta fuori.
Il metodo: estrarre l'indice dal .txt (di solito nelle ultime 100 righe, cercare `Indice`),
poi per ogni sezione scegliere una **sonda** — una parola o frase distintiva che comparirebbe
solo se quel materiale è stato scritto — e cercarla nel testo del sito ripulito dai tag:

```python
import re, unicodedata
from pathlib import Path
t = Path("sito/mappa-transurfing.html").read_text(encoding="utf-8")
t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
t = re.sub(r"<[^>]+>", " ", t)
low = re.sub(r"\s+", " ",
      unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower())
# poi: sonda in low
```

Attenzione a due trappole già incontrate:

- **Sonde troppo corte danno falsi positivi.** `ufo` si trova dentro altre parole, `bell`
  dentro «bello», `magi` dentro «immagina». Usare `\bparola\b` o frasi di due-tre parole.
- **Sonde troppo generiche danno falsi negativi al contrario**: una parola comune risulta
  «presente» anche se il capitolo non c'è. Meglio una citazione breve e caratteristica
  («accettare e lasciar andare», «acqua di riserva», «apparire ridicolo»).

Al 5 settembre 2026 l'audit sui **cinque** Zeland passa al 100%: nessuna sezione dei loro
indici è priva di corrispondenza nel sito. **La trilogia di Nagal non è stata sottoposta allo stesso
setaccio** — se l'utente lo chiede, servono i suoi indici.
