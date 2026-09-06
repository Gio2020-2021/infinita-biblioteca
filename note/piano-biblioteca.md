# Da una mappa a una biblioteca — piano

Stato: tappe 1 e 2 **fatte** il 6-9-2026 (telaio estratto, elenchi generati da
`mappa.json`, file costruito identico byte per byte). Dalla 3 in poi: da fare. Mockup: `sito/mockup-biblioteca.html`.

## Il principio

Non una pagina che cresce, ma **una mappa per argomento**, tutte con lo stesso telaio,
più un portale che le tiene insieme e permette il confronto.

Ragione concreta: la mappa del Transurfing pesa 808 KB con **un** argomento. Dieci
argomenti in una pagina sola sarebbero ~8 MB: lenta ad aprirsi, e la ricerca dovrebbe
scorrere materiale che in quel momento non interessa.

## Struttura

```
sorgente/
  telaio/           identico per ogni mappa: corpo/ stile/ script/
  mappe/
    transurfing/    mappa.json · testata.html · parti/ · proprio/ (banco, diario)
    <altra>/        mappa.json · testata.html · parti/
  biblioteca/
    concetti.json   i concetti canonici e i sinonimi di ogni mappa
    confronti/      i confronti scritti a mano
sito/
  index.html        il portale                     ] generati da
  <mappa>.html      una per mappa                  ] costruisci.py
  confronti.html                                   ]
```

## Il guadagno vero: spariscono i quattro elenchi paralleli

Oggi aggiungere una parte significa aggiornare a mano la barra, l'ordine fisico,
`BRANCHES` e `PARTI` — la trappola più costosa del progetto, sbagliata due volte.
Con `mappa.json` quei quattro elenchi si **generano dallo stesso dato**:

```json
{
  "id": "transurfing",
  "nome": "Transurfing",
  "titolo": "Mappa del <em>Transurfing</em>",
  "accento": "--amber",
  "moduli": ["banco", "diario", "diagramma", "percorsi", "porte", "storie", "vocabolario"],
  "parti": [
    { "id": "casa",     "n": "·",  "t": "Il banco",      "c": "--amber", "operativa": true },
    { "id": "terreno",  "n": "I",  "t": "Il terreno",    "c": "--blue" },
    { "id": "voci",     "n": "XI", "t": "Le altre voci", "c": "--teal" }
  ]
}
```

Banco e diario diventano **moduli opzionali**: sono strumenti del Transurfing, non di
ogni argomento.

## Il confronto, in tre livelli

1. **I tag** — ogni sezione dichiara `data-concetti="attenzione importanza"`.
2. **La tavola dei concetti**, generata. Dice *«queste pagine parlano della stessa cosa»*,
   **non** *«dicono la stessa cosa»*. È un indice, non un giudizio, e va detto sulla pagina.
3. **I confronti scritti a mano** — citazioni letterali a fronte, fonte dichiarata,
   verificate da `cita.py`. Generalizzazione di `#divergenze`, che oggi confronta Zeland
   con sé stesso. **Se due autori si contraddicono, il confronto lo dice**: non si concilia
   a forza.

## Le due difficoltà vere, dette prima

- **La ricerca fra mappe.** Dentro una mappa resta com'è (piena). Fra le mappe non si può
  caricare un indice esterno: su `file://` il CORS blocca `fetch`. Soluzione: il portale
  incorpora un indice **ridotto** (titoli, gist, concetti — non il testo intero), che resta
  piccolo anche con dieci mappe. Chi vuole il testo pieno entra nella mappa.
- **La disciplina dei tag.** Un vocabolario di concetti si degrada in fretta se ogni mappa
  ne inventa di nuovi. Regola: `concetti.json` è chiuso, si aggiunge un concetto solo
  quando almeno **due** mappe lo toccano, e `verifica.py` segnala i tag non dichiarati.

## Rapporto Vesica: una mappa che fa da perno

L'utente ha annunciato un libro, **Rapporto Vesica**, che «parla di tutto e di più» e sarà
**un punto di contatto per molti altri argomenti e mappe**. Non è una mappa come le altre:
è un perno. Conseguenze sul disegno, da tenere presenti fin dalla tappa 1:

- **I rimandi fra mappe devono essere di prima classe**, non un'aggiunta. Serve un indirizzo
  stabile per ogni sezione — `mappa:sezione`, es. `transurfing:pendoli` — che `costruisci.py`
  risolve nel link giusto (`transurfing.html#pendoli`). Scritto così, un rimando non si rompe
  se una mappa cambia nome di file o se una sezione cambia parte.
- **Una mappa-perno tocca quasi tutti i concetti**: la tavola dei concetti deve reggere una
  colonna molto piena senza diventare illeggibile, e il perno va probabilmente mostrato per
  primo e in modo diverso dalle altre.
- **Il rischio da evitare**: che il perno diventi il posto dove si mette tutto ciò che non si
  sa dove mettere. Un rimando dal perno a una mappa deve puntare a una sezione che esiste
  davvero — la stessa regola già valida per `#porte`: *una porta non deve mai promettere
  qualcosa che la sezione linkata non contiene.*

## Tappe

1. **Estrarre il telaio** — nessun cambiamento visibile; `costruisci.py --controlla` deve
   dare un file identico byte per byte, come per lo spezzettamento del 6-9-2026.
2. **`mappa.json`** e generazione dei quattro elenchi.
3. **Il portale** più una seconda mappa, anche minima, per provare che il telaio regge.
4. **I tag** e la tavola dei concetti.
5. **I primi confronti scritti.**

Le tappe 1 e 2 non aggiungono niente di visibile: servono a rendere la 3 banale.
