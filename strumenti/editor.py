#!/usr/bin/env python3
"""Modalità modifica: correggere e ampliare una sezione direttamente dalla pagina.

    python3 strumenti/editor.py             costruisce, avvia il server, apre il portale
    python3 strumenti/editor.py --porta 8901

Come funziona: passando il mouse su una sezione compare una **matita** in alto a
destra. Cliccandola si apre l'editor della sezione — a sinistra il testo vero
(quello che sta in `sorgente/`), a destra l'anteprima dal vivo di come viene. Si
corregge quello che c'è, si aggiunge quello che manca, si salva.

**Il salvataggio scrive in `sorgente/`**, nel file della parte a cui la sezione
appartiene, ricostruisce la mappa e rilancia `verifica.py`. La pagina si ricarica
sulla sezione appena modificata, così quello che vedi è il risultato vero, non
un'anteprima.

Reti di sicurezza, in ordine:

1. prima di scrivere, la versione precedente del file finisce in `.storico/`
   (cartella locale, ignorata da git);
2. il frammento viene controllato prima di toccare il disco: deve cominciare con
   `<section`, finire con `</section>`, conservare l'id della sezione, avere i tag
   bilanciati e niente `<script>`;
3. se dopo la scrittura `costruisci.py` fallisce (per esempio un rimando a
   un'ancora che non esiste), il file viene **rimesso com'era** e l'errore
   compare nell'editor;
4. `verifica.py` gira comunque e il suo esito viene mostrato: id duplicati, link
   morti, elenchi paralleli fuori posto.

Quello che questo strumento **non** fa, di proposito: non verifica le citazioni.
`cita.py` va lanciato a parte (~30 s) quando si aggiungono virgolette — la regola
del progetto resta che ogni «...» è letterale e va riscontrata sui testi.

Il server ascolta solo su 127.0.0.1 e vive finché resta aperto il terminale
(Ctrl+C per chiuderlo).
"""
import json
import re
import shutil
import subprocess
import sys
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verifica import Bilancia  # stesso controllo di bilanciamento usato prima di pubblicare
import scheda as mod_scheda    # la modifica a campi, senza mettere le mani nel codice

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "sorgente"
MAPPE = SORGENTE / "mappe"
SITO = RADICE / "sito"
STORICO = RADICE / ".storico"
VENDOR = Path(__file__).resolve().parent / "vendor"
PORTA_DI_DEFAULT = 8901

# CodeMirror sta in strumenti/vendor/, non su un CDN: l'editor deve funzionare
# anche senza rete, come il resto del progetto. Se la cartella non c'è, l'editor
# ripiega su una textarea semplice invece di rompersi.
CODEMIRROR = [
    ("css", "lib/codemirror.css"),
    ("css", "addon/dialog/dialog.css"),
    ("css", "addon/fold/foldgutter.css"),
    ("css", "addon/search/matchesonscrollbar.css"),
    ("js", "lib/codemirror.js"),
    ("js", "mode/xml/xml.js"),
    ("js", "mode/javascript/javascript.js"),
    ("js", "mode/css/css.js"),
    ("js", "mode/htmlmixed/htmlmixed.js"),
    ("js", "addon/fold/xml-fold.js"),
    ("js", "addon/edit/closetag.js"),
    ("js", "addon/edit/closebrackets.js"),
    ("js", "addon/edit/matchtags.js"),
    ("js", "addon/edit/matchbrackets.js"),
    ("js", "addon/fold/foldcode.js"),
    ("js", "addon/fold/foldgutter.js"),
    ("js", "addon/fold/brace-fold.js"),
    ("js", "addon/dialog/dialog.js"),
    ("js", "addon/search/searchcursor.js"),
    ("js", "addon/search/search.js"),
    ("js", "addon/search/jump-to-line.js"),
    ("js", "addon/scroll/annotatescrollbar.js"),
    ("js", "addon/search/matchesonscrollbar.js"),
    ("js", "addon/search/match-highlighter.js"),
    ("js", "addon/selection/active-line.js"),
    ("js", "addon/comment/comment.js"),
]


def codemirror_c_e():
    return (VENDOR / "codemirror" / "lib" / "codemirror.js").exists()


def tag_codemirror():
    if not codemirror_c_e():
        return ""
    righe = []
    for tipo, f in CODEMIRROR:
        if tipo == "css":
            righe.append(f'<link rel="stylesheet" href="/vendor/codemirror/{f}">')
        else:
            righe.append(f'<script src="/vendor/codemirror/{f}"></script>')
    return "\n".join(righe) + "\n"

GUSCIO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{ color-scheme: light dark }}
  body {{ margin: 0; font: 14px system-ui, -apple-system, sans-serif }}
  img {{ max-width: 100% }}
  [hidden] {{ display: none !important }}
</style>
</head>
<body>
{corpo}
{editor}
</body>
</html>
"""


# --------------------------------------------------------------- le mappe e i pezzi

def mappe():
    """id mappa -> cartella in sorgente/mappe/."""
    return {json.loads((d / "mappa.json").read_text(encoding="utf-8"))["id"]: d
            for d in sorted(MAPPE.iterdir()) if (d / "mappa.json").exists()}


def pagina_di(cfg_id):
    # la mappa del Transurfing tiene il nome storico (come in costruisci.py)
    return ("mappa-transurfing" if cfg_id == "transurfing" else cfg_id) + ".html"


def cartella_della_pagina(pagina):
    for mid, d in mappe().items():
        if pagina_di(mid) == pagina:
            return d
    return None


def fine_sezione(testo, inizio):
    """Indice dopo il </section> che chiude la sezione aperta a `inizio`."""
    profondita = 0
    for t in re.finditer(r"<section\b|</section\s*>", testo[inizio:]):
        if t.group(0).startswith("</"):
            profondita -= 1
            if profondita == 0:
                return inizio + t.end()
        else:
            profondita += 1
    raise ValueError("la sezione non si chiude")


def trova_sezione(cartella, sezione):
    """(file, inizio, fine, testo del file, frammento) — o None se non c'è."""
    for f in sorted((cartella / "parti").glob("*.html")):
        testo = f.read_text(encoding="utf-8")
        m = re.search(r'<section\b[^>]*\sid="' + re.escape(sezione) + r'"', testo)
        if not m:
            continue
        fine = fine_sezione(testo, m.start())
        return f, m.start(), fine, testo, testo[m.start():fine]
    return None


def sezioni_modificabili(pagina):
    """Gli id che questo editor sa davvero ritrovare in sorgente/ — e solo quelli:
    la matita non deve comparire su qualcosa che poi non si riesce a salvare."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return []
    ids = []
    for f in sorted((cartella / "parti").glob("*.html")):
        testo = f.read_text(encoding="utf-8")
        ids += re.findall(r'<section\b[^>]*\sid="([A-Za-z0-9_-]+)"', testo)
    return ids


# ------------------------------------------------------------------- i controlli

def controlla_frammento(frammento, sezione):
    problemi = []
    if not frammento.lstrip().startswith("<section"):
        problemi.append("deve cominciare con <section")
    if not frammento.rstrip().endswith("</section>"):
        problemi.append("deve finire con </section>")
    if not re.search(r'\sid="' + re.escape(sezione) + r'"', frammento):
        problemi.append(f"l'id della sezione («{sezione}») non si cambia da qui: "
                        "sposterebbe i rimandi di tutta la biblioteca")
    if "<script" in frammento.lower():
        problemi.append("niente <script> dentro una sezione")
    b = Bilancia()
    b.feed(frammento)
    if b.pila:
        b.errori.append("mai chiusi: " + ", ".join(f"<{t}>" for t, _ in b.pila))
    problemi += b.errori[:8]
    return problemi


def corri(script, *argomenti):
    esito = subprocess.run(
        [sys.executable, str(RADICE / "strumenti" / script), *argomenti],
        capture_output=True, text=True)
    return esito.returncode, (esito.stdout + esito.stderr).strip()


def salva_sezione(pagina, sezione, frammento):
    """Scrive la sezione in sorgente/, ricostruisce, verifica. Torna un dizionario
    per l'editor: {ok, errori[], verifica, file}."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errori": [f"pagina sconosciuta: {pagina}"]}

    problemi = controlla_frammento(frammento, sezione)
    if problemi:
        return {"ok": False, "errori": problemi}

    trovata = trova_sezione(cartella, sezione)
    if trovata is None:
        return {"ok": False, "errori": [f"la sezione «{sezione}» non è in sorgente/"]}
    f, inizio, fine, testo, vecchio = trovata

    if frammento == vecchio:
        return {"ok": True, "invariata": True, "file": str(f.relative_to(RADICE)),
                "verifica": "niente da salvare: il testo è identico a prima."}

    # 1. copia di sicurezza prima di toccare il disco
    STORICO.mkdir(exist_ok=True)
    quando = datetime.now().strftime("%Y%m%d-%H%M%S")
    riserva = STORICO / f"{quando}-{cartella.name}-{f.name}"
    riserva.write_text(testo, encoding="utf-8")

    # 2. scrittura
    f.write_text(testo[:inizio] + frammento + testo[fine:], encoding="utf-8")

    # 3. ricostruzione: se fallisce si torna indietro, senza lasciare macerie
    codice, uscita_build = corri("costruisci.py")
    if codice != 0:
        shutil.copyfile(riserva, f)
        corri("costruisci.py")
        return {"ok": False, "errori": ["la costruzione è fallita, ho rimesso il file com'era:",
                                        uscita_build]}

    # 4. verifica di coerenza (informativa: dice se qualcosa si è rotto altrove)
    _, uscita_verifica = corri("verifica.py")
    return {"ok": True, "file": str(f.relative_to(RADICE)),
            "storico": str(riserva.relative_to(RADICE)),
            "verifica": uscita_verifica}


# ------------------------------------------------- modifica a campi (senza codice)

def leggi_scheda(pagina, sezione):
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errore": f"pagina sconosciuta: {pagina}"}
    trovata = trova_sezione(cartella, sezione)
    if trovata is None:
        return {"ok": False, "errore": f"«{sezione}» non è in sorgente/"}
    f, _, _, _, frammento = trovata
    try:
        s = mod_scheda.analizza_sezione(frammento)
    except Exception as e:                                            # noqa: BLE001
        return {"ok": False, "errore": f"questa sezione non si legge a campi: {e}"}
    return {"ok": True, "scheda": s, "file": str(f.relative_to(RADICE))}


def salva_scheda(pagina, sezione, dal_browser):
    """Rilegge la sezione dal disco, ci innesta i soli campi toccati e passa il
    risultato a salva_sezione, che ha già tutte le reti di sicurezza."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errori": [f"pagina sconosciuta: {pagina}"]}
    trovata = trova_sezione(cartella, sezione)
    if trovata is None:
        return {"ok": False, "errori": [f"«{sezione}» non è in sorgente/"]}
    _, _, _, _, frammento = trovata
    vera = mod_scheda.analizza_sezione(frammento)
    fusa = mod_scheda.unisci(vera, dal_browser)
    nuovo = mod_scheda.componi_sezione(fusa, frammento)
    return salva_sezione(pagina, sezione, nuovo)


def anteprima_scheda(pagina, sezione, dal_browser):
    """Il frammento che il salvataggio scriverebbe, senza scriverlo: è la stessa
    fusione e la stessa composizione, così l'anteprima non può divergere da ciò
    che finisce su disco."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errore": f"pagina sconosciuta: {pagina}"}
    trovata = trova_sezione(cartella, sezione)
    if trovata is None:
        return {"ok": False, "errore": f"«{sezione}» non è in sorgente/"}
    _, _, _, _, frammento = trovata
    vera = mod_scheda.analizza_sezione(frammento)
    nuovo = mod_scheda.componi_sezione(mod_scheda.unisci(vera, dal_browser), frammento)
    return {"ok": True, "html": nuovo}


def struttura(pagina):
    """Le parti della mappa con le loro sezioni: serve a scegliere dove infilarne
    una nuova."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errore": f"pagina sconosciuta: {pagina}"}
    parti = []
    for f in sorted((cartella / "parti").glob("*.html")):
        testo = f.read_text(encoding="utf-8")
        m = re.search(r'<div class="part" id="parte-([A-Za-z0-9_-]+)"([^>]*)>', testo)
        if not m:
            continue
        colore = re.search(r"--pc:\s*var\(--([a-z]+)\)", m.group(2) or "")
        titolo = re.search(r"<h2>(.*?)</h2>", testo, re.S)
        sezioni = [{"id": i, "titolo": re.sub(r"<[^>]+>", "", t).strip()}
                   for i, t in re.findall(
                       r'<section class="branch" id="([A-Za-z0-9_-]+)".*?<h2>(.*?)</h2>',
                       testo, re.S)]
        parti.append({"id": m.group(1), "file": f.name,
                      "titolo": re.sub(r"<[^>]+>", "", titolo.group(1)).strip() if titolo else m.group(1),
                      "colore": colore.group(1) if colore else "amber",
                      "sezioni": sezioni})
    return {"ok": True, "parti": parti}


def tutti_gli_id():
    """Gli id di sezione di TUTTA la biblioteca: un id nuovo non deve scontrarsi
    con nessuno, perché i rimandi fra mappe girano su quelli."""
    ids = set()
    for d in mappe().values():
        for f in (d / "parti").glob("*.html"):
            ids |= set(re.findall(r'<section\b[^>]*\sid="([A-Za-z0-9_-]+)"',
                                  f.read_text(encoding="utf-8")))
    return ids


def crea_sezione(pagina, parte, dopo, titolo, sid=""):
    """Scrive una sezione nuova dentro una parte esistente, aggiunge la sua voce
    nel sommario della parte e rinumera. Se qualcosa va storto rimette il file
    com'era, come fa il salvataggio normale."""
    cartella = cartella_della_pagina(pagina)
    if cartella is None:
        return {"ok": False, "errori": [f"pagina sconosciuta: {pagina}"]}
    titolo = (titolo or "").strip()
    if not titolo:
        return {"ok": False, "errori": ["serve un titolo"]}

    dati = struttura(pagina)
    quella = next((p for p in dati.get("parti", []) if p["id"] == parte), None)
    if quella is None:
        return {"ok": False, "errori": [f"la parte «{parte}» non c'è"]}

    sid = (sid or f"{parte}-{mod_scheda.sigla(titolo)}").strip()
    if not re.fullmatch(r"[a-z][a-z0-9-]*", sid):
        return {"ok": False, "errori": ["l'indirizzo può avere solo lettere minuscole, "
                                        "cifre e trattini, e comincia con una lettera"]}
    if sid in tutti_gli_id():
        return {"ok": False, "errori": [f"l'indirizzo «{sid}» è già usato da un'altra "
                                        "sezione della biblioteca"]}

    f = cartella / "parti" / quella["file"]
    testo = f.read_text(encoding="utf-8")

    # dove infilarla: dopo la sezione scelta, o in cima se non se n'è scelta una
    if dopo:
        trovata = re.search(r'<section class="branch" id="' + re.escape(dopo) + r'"', testo)
        if not trovata:
            return {"ok": False, "errori": [f"«{dopo}» non è in questa parte"]}
        punto = fine_sezione(testo, trovata.start())
    else:
        chiusura_testa = testo.find("</ul>")
        punto = testo.find("</div>", chiusura_testa)
        punto = testo.find("\n", punto) if punto > 0 else chiusura_testa
    if punto <= 0:
        return {"ok": False, "errori": ["non capisco dove infilarla in questo file"]}

    nuova = mod_scheda.scheletro_sezione(sid, titolo, quella["colore"])
    voce_toc = f'        <li><a href="#{sid}"><b>00</b>{titolo}</a></li>\n'
    # da che numero parte il sommario di QUESTA parte: Risveglio e Vesica
    # ricominciano da 01 a ogni parte, Transurfing prosegue su tutta la pagina
    numeri = [int(n) for n in re.findall(r'<li><a href="#[^"]+"><b>(\d+)</b>', testo)]
    partenza = min(numeri) if numeri else 1

    # la voce nel sommario della parte, nella stessa posizione
    if dopo:
        m_toc = re.search(r'<li><a href="#' + re.escape(dopo) + r'">.*?</li>\n', testo, re.S)
        toc_punto = m_toc.end() if m_toc else None
    else:
        m_toc = re.search(r'<ul class="part-toc">\n', testo)
        toc_punto = m_toc.end() if m_toc else None
    if toc_punto is None:
        return {"ok": False, "errori": ["non trovo il sommario della parte"]}

    STORICO.mkdir(exist_ok=True)
    quando = datetime.now().strftime("%Y%m%d-%H%M%S")
    riserva = STORICO / f"{quando}-{cartella.name}-{f.name}"
    riserva.write_text(testo, encoding="utf-8")

    # si scrive dal punto più avanti al più indietro, così gli indici restano buoni
    if toc_punto < punto:
        fuori = testo[:toc_punto] + voce_toc + testo[toc_punto:punto] + "\n" + nuova + "\n" + testo[punto:]
    else:
        fuori = testo[:punto] + "\n" + nuova + "\n" + testo[punto:toc_punto] + voce_toc + testo[toc_punto:]

    # rinumerazione del sommario della parte, in ordine di documento
    contatore = [partenza - 1]

    def _numera(m):
        contatore[0] += 1
        return f"{m.group(1)}<b>{contatore[0]:02d}</b>"

    fuori = re.sub(r'(<li><a href="#[^"]+">)<b>\d+</b>', _numera, fuori)
    f.write_text(fuori, encoding="utf-8")

    codice, uscita = corri("costruisci.py")
    if codice != 0:
        shutil.copyfile(riserva, f)
        corri("costruisci.py")
        return {"ok": False, "errori": ["la costruzione è fallita, ho rimesso il file com'era:",
                                        uscita]}
    # la numerazione del sommario la rifà lo strumento apposta, non si scrive a mano
    corri("rinumera.py", "--scrivi")
    _, uscita_verifica = corri("verifica.py")
    return {"ok": True, "sezione": sid, "file": str(f.relative_to(RADICE)),
            "storico": str(riserva.relative_to(RADICE)), "verifica": uscita_verifica}


# ------------------------------------------------------------------ le pagine servite

STILE_EDITOR = """
<style>
  .ed-sez { position: relative }
  /* la matita sta nella colonna laterale, che è già sticky: così non finisce mai
     sotto la barra fissa in cima, e resta a portata ovunque si sia nella sezione.
     Solo se la sezione non ha colonna laterale ripiega sull'angolo in alto. */
  .ed-matita {
    margin-top: 14px; z-index: 40;
    display: inline-flex; align-items: center; gap: 6px;
    font-family: var(--f-mono, ui-monospace, monospace);
    font-size: 10px; letter-spacing: .08em; text-transform: uppercase;
    padding: 6px 10px; border-radius: 3px; cursor: pointer;
    background: var(--surface, #1B1D27); color: var(--muted, #8B8D9E);
    border: 1px solid var(--line, #2E3140);
    opacity: 0; transition: opacity .15s ease, color .15s, border-color .15s;
  }
  .ed-sez:hover .ed-matita, .ed-matita:focus-visible { opacity: 1 }
  .ed-matita:hover { color: var(--amber, #E8A33D); border-color: var(--amber, #E8A33D) }
  .ed-matita.ed-angolo { position: absolute; top: 10px; right: 0; margin-top: 0 }

  #ed-velo { position: fixed; inset: 0; z-index: 300; background: rgba(6,6,10,.6);
    display: none; padding: 22px; }
  #ed-velo.on { display: block }
  #ed-scatola {
    display: flex; flex-direction: column; height: 100%;
    background: var(--ground, #12131A); border: 1px solid var(--line, #2E3140);
    border-radius: 6px; overflow: hidden;
    box-shadow: 0 30px 70px -30px rgba(0,0,0,.9);
  }
  #ed-testa {
    display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
    padding: 12px 16px; border-bottom: 1px solid var(--line, #2E3140);
    background: var(--surface, #1B1D27);
  }
  #ed-testa h3 { margin: 0; font-family: var(--f-body, Georgia, serif);
    font-size: 15px; color: var(--ink, #E6E4DC); font-weight: 600 }
  #ed-dove { font-family: var(--f-mono, monospace); font-size: 11px; color: var(--muted, #8B8D9E) }
  #ed-testa .ed-spinta { margin-left: auto; display: flex; gap: 8px }
  #ed-testa button, .ed-inserti button {
    font-family: var(--f-mono, monospace); font-size: 11px; letter-spacing: .05em;
    padding: 7px 12px; border-radius: 4px; cursor: pointer;
    border: 1px solid var(--line, #2E3140); background: transparent;
    color: var(--ink-dim, #B4B3AC);
  }
  #ed-testa button:hover, .ed-inserti button:hover { color: var(--ink, #E6E4DC); border-color: var(--amber, #E8A33D) }
  #ed-salva { background: var(--amber, #E8A33D) !important; color: #14140f !important;
    border-color: var(--amber, #E8A33D) !important; font-weight: 600 }
  #ed-corpo { display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr);
    flex: 1; min-height: 0 }
  #ed-sinistra { display: flex; flex-direction: column; min-height: 0;
    border-right: 1px solid var(--line, #2E3140) }
  .ed-inserti { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; padding: 8px 10px;
    border-bottom: 1px solid var(--line-soft, #242734); background: var(--surface-2, #232633) }
  .ed-misura { margin-left: auto; display: flex; align-items: center; gap: 6px;
    font-family: var(--f-mono, monospace); font-size: 10px; letter-spacing: .08em;
    text-transform: uppercase; color: var(--muted, #8B8D9E) }
  .ed-misura select {
    font-family: var(--f-mono, monospace); font-size: 11px; padding: 5px 8px;
    border-radius: 4px; cursor: pointer;
    border: 1px solid var(--line, #2E3140); background: var(--surface, #1B1D27);
    color: var(--ink-dim, #B4B3AC);
  }
  .ed-misura select:hover { color: var(--ink, #E6E4DC); border-color: var(--amber, #E8A33D) }
  /* la misura del codice è una preferenza di chi scrive, non del documento:
     vive in una variabile e viene ricordata nel browser */
  #ed-testo { flex: 1; min-height: 0; width: 100%; box-sizing: border-box; resize: none;
    border: 0; outline: none; padding: 14px 16px; tab-size: 2;
    font-family: var(--f-mono, ui-monospace, monospace);
    font-size: var(--ed-misura, 11px); line-height: 1.6;
    background: var(--ground, #12131A); color: var(--ink, #E6E4DC) }
  /* CodeMirror: prende i colori dalla pagina, così segue il tema chiaro/scuro
     invece di portarsene uno suo che stona */
  #ed-sinistra .CodeMirror {
    flex: 1; min-height: 0; height: auto;
    font-family: var(--f-mono, ui-monospace, monospace);
    font-size: var(--ed-misura, 11px); line-height: 1.6;
    background: var(--ground, #12131A); color: var(--ink, #E6E4DC);
  }
  .CodeMirror-gutters { background: var(--surface, #1B1D27); border-right: 1px solid var(--line, #2E3140) }
  .CodeMirror-linenumber { color: var(--muted, #8B8D9E) }
  .CodeMirror-cursor { border-left: 2px solid var(--amber, #E8A33D) }
  .CodeMirror-activeline-background { background: var(--surface-2, #232633) }
  .CodeMirror-selected, .CodeMirror-focused .CodeMirror-selected { background: var(--blue-soft, rgba(127,168,201,.22)) !important }
  .CodeMirror-matchingtag, .CodeMirror-matchingbracket {
    background: var(--amber-soft, rgba(232,163,61,.18)); color: var(--amber, #E8A33D) !important }
  .cm-s-default .cm-tag { color: var(--blue, #7FA8C9) }
  .cm-s-default .cm-attribute { color: var(--sage, #8AA878) }
  .cm-s-default .cm-string { color: var(--amber, #E8A33D) }
  .cm-s-default .cm-comment { color: var(--muted, #8B8D9E); font-style: italic }
  .cm-s-default .cm-bracket { color: var(--ink-dim, #B4B3AC) }
  .CodeMirror-dialog {
    background: var(--surface, #1B1D27); color: var(--ink, #E6E4DC);
    border-bottom: 1px solid var(--line, #2E3140);
    font-family: var(--f-mono, monospace); font-size: 12px; padding: 8px 10px }
  .CodeMirror-dialog input {
    font-family: var(--f-mono, monospace); font-size: 12px;
    background: var(--ground, #12131A); color: var(--ink, #E6E4DC);
    border: 1px solid var(--line, #2E3140); border-radius: 3px; padding: 4px 6px; outline: none }
  .cm-searching { background: var(--amber-soft, rgba(232,163,61,.25)) }
  #ed-scorciatoie { font-family: var(--f-mono, monospace); font-size: 10px;
    color: var(--muted, #8B8D9E); letter-spacing: .04em }
  #ed-destra { overflow: auto; padding: 0 26px; background: var(--ground, #12131A) }
  #ed-etichetta-anteprima { position: sticky; top: 0; z-index: 2; padding: 8px 0 6px;
    background: var(--ground, #12131A); font-family: var(--f-mono, monospace);
    font-size: 10px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted, #8B8D9E) }
  #ed-esiti { padding: 0 16px; max-height: 34vh; overflow: auto;
    font-family: var(--f-mono, monospace); font-size: 11.5px; line-height: 1.6;
    white-space: pre-wrap; color: var(--ink-dim, #B4B3AC);
    border-top: 1px solid var(--line, #2E3140); background: var(--surface, #1B1D27) }
  #ed-esiti:empty { display: none }
  #ed-esiti.male { color: #E8938A }
  #ed-esiti .ed-riga-esito { padding: 10px 0 }
  /* la richiesta di conferma è un modale della pagina, non il confirm() del
     browser: quello arriva con l'indirizzo del server in testa e non c'entra
     niente con il resto */
  #ed-conferma { position: fixed; inset: 0; z-index: 360; background: rgba(6,6,10,.55);
    display: none; align-items: center; justify-content: center; padding: 24px }
  #ed-conferma.on { display: flex }
  #ed-conferma-scatola {
    width: min(560px, 100%); background: var(--surface, #1B1D27);
    border: 1px solid var(--line, #2E3140); border-top: 3px solid var(--amber, #E8A33D);
    border-radius: 6px; padding: 22px 24px 18px;
    box-shadow: 0 30px 70px -30px rgba(0,0,0,.9);
    font-family: var(--f-body, Georgia, serif);
  }
  #ed-conferma h4 { margin: 0 0 8px; font-family: var(--f-display, Georgia, serif);
    font-size: 20px; font-weight: 600; color: var(--ink, #E6E4DC) }
  #ed-conferma p { margin: 0 0 20px; font-size: 14.5px; line-height: 1.55;
    color: var(--ink-dim, #B4B3AC); max-width: 46ch }
  /* i tre tasti stanno su una riga sola: nowrap più il testo che non si spezza,
     e la scatola larga abbastanza da contenerli */
  #ed-conferma-tasti { display: flex; justify-content: flex-end; gap: 8px; flex-wrap: nowrap }
  #ed-conferma-tasti button {
    font-family: var(--f-mono, monospace); font-size: 11px; letter-spacing: .05em;
    padding: 8px 14px; border-radius: 4px; cursor: pointer; white-space: nowrap;
    border: 1px solid var(--line, #2E3140); background: transparent;
    color: var(--ink-dim, #B4B3AC);
  }
  #ed-conferma-tasti button:hover { color: var(--ink, #E6E4DC); border-color: var(--amber, #E8A33D) }
  #ed-conferma-tasti button.ed-primario {
    background: var(--amber, #E8A33D); color: #14140f;
    border-color: var(--amber, #E8A33D); font-weight: 600 }
  #ed-conferma-tasti button:focus-visible { outline: 2px solid var(--amber, #E8A33D); outline-offset: 2px }
  /* i tre tasti occupano ~420px: sotto questa soglia non ci stanno più in riga */
  @media (max-width: 520px) { #ed-conferma-tasti { flex-wrap: wrap } }
  #ed-briciola { position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%);
    z-index: 320; font-family: var(--f-mono, monospace); font-size: 12px;
    padding: 10px 18px; border-radius: 4px; background: var(--surface, #1B1D27);
    border: 1px solid var(--amber, #E8A33D); color: var(--ink, #E6E4DC);
    opacity: 0; pointer-events: none; transition: opacity .2s ease }
  #ed-briciola.on { opacity: 1 }
  @media (max-width: 900px) { #ed-corpo { grid-template-columns: 1fr } #ed-destra { display: none } }
</style>
"""

STILE_SCHEDA = """
<style>
  /* ============ LA SCHEDA: modifica senza mettere le mani nel codice ============ */
  #sc-velo { position: fixed; inset: 0; z-index: 300; background: rgba(6,6,10,.6);
    display: none; align-items: stretch; justify-content: center; padding: 24px }
  #sc-velo.on { display: flex }
  #sc-scatola { width: min(1000px, 100%); display: flex; flex-direction: column;
    background: var(--ground, #12131A); border: 1px solid var(--line, #2E3140);
    border-radius: 6px; overflow: hidden }
  #sc-testa { display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
    padding: 12px 16px; border-bottom: 1px solid var(--line, #2E3140);
    background: var(--surface, #1B1D27) }
  #sc-testa h3 { margin: 0; font-family: var(--f-display, serif); font-size: 18px;
    font-weight: 600; color: var(--ink, #E6E4DC) }
  #sc-dove { font-family: var(--f-mono, monospace); font-size: 11px;
    color: var(--muted, #8B8D9E) }
  .sc-spinta { margin-left: auto; display: flex; gap: 8px }
  #sc-testa button, .sc-agg button, .sc-carta-tasti button, .sc-barra button {
    background: transparent; border: 1px solid var(--line, #2E3140); border-radius: 3px;
    padding: 6px 11px; font-family: var(--f-mono, monospace); font-size: 11px;
    letter-spacing: .06em; text-transform: uppercase; color: var(--ink-dim, #B4B3AC);
    cursor: pointer }
  #sc-testa button:hover, .sc-agg button:hover, .sc-carta-tasti button:hover,
  .sc-barra button:hover { color: var(--ink, #E6E4DC); border-color: var(--amber, #E8A33D) }
  #sc-salva { background: var(--amber, #E8A33D) !important; color: #14140f !important;
    border-color: var(--amber, #E8A33D) !important; font-weight: 600 }
  #sc-corpo { flex: 1 1 auto; min-height: 0; display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) }
  #sc-modulo { overflow-y: auto; padding: 18px 16px 26px }
  #sc-lato { overflow-y: auto; border-left: 1px solid var(--line, #2E3140);
    background: var(--ground, #12131A) }
  #sc-lato-etichetta { position: sticky; top: 0; z-index: 2; padding: 8px 16px 6px;
    background: var(--ground, #12131A); border-bottom: 1px solid var(--line-soft, #242734);
    font-family: var(--f-mono, monospace); font-size: 10px; letter-spacing: .12em;
    text-transform: uppercase; color: var(--muted, #8B8D9E) }
  #sc-anteprima { padding: 4px 16px 30px }
  /* l'anteprima è la sezione vera: le sue regole vogliono la griglia a due
     colonne, che qui dentro non ci sta. Una colonna sola, come sul telefono. */
  #sc-anteprima .branch-grid { grid-template-columns: 1fr; gap: 18px }
  #sc-anteprima .branch-aside { position: static }
  #sc-anteprima section.branch { padding: 0; border-bottom: 0 }
  .sc-gruppo { max-width: 860px; margin: 0 auto 26px }
  .sc-intestazione { font-family: var(--f-mono, monospace); font-size: 10px;
    letter-spacing: .16em; text-transform: uppercase; color: var(--muted, #8B8D9E);
    margin: 0 0 10px }
  .sc-campo { margin-bottom: 14px }
  .sc-campo > label { display: block; font-family: var(--f-mono, monospace);
    font-size: 10px; letter-spacing: .12em; text-transform: uppercase;
    color: var(--muted, #8B8D9E); margin-bottom: 5px }
  .sc-scrivi { min-height: 38px; padding: 9px 11px; border-radius: 3px;
    border: 1px solid var(--line, #2E3140); background: var(--surface, #1B1D27);
    color: var(--ink, #E6E4DC); font-family: var(--f-body, Georgia, serif);
    font-size: 15px; line-height: 1.55; outline: none }
  .sc-scrivi:focus { border-color: var(--amber, #E8A33D) }
  .sc-scrivi p { margin: 0 0 .7em }
  .sc-scrivi p:last-child { margin-bottom: 0 }
  .sc-scrivi[data-corto="1"] { font-family: var(--f-mono, monospace); font-size: 12px }
  /* la barretta compare solo sul campo in uso: una per ogni campo sarebbe rumore */
  .sc-barra { display: none; gap: 4px; margin-bottom: 5px }
  .sc-campo.sc-attivo .sc-barra { display: flex }
  .sc-barra button { padding: 4px 9px; text-transform: none; letter-spacing: 0 }
  .sc-barra button b { font-family: var(--f-body, serif); font-size: 13px }
  .sc-barra button i { font-family: var(--f-body, serif); font-size: 13px }
  .sc-carta { border: 1px solid var(--line, #2E3140); border-radius: 4px;
    margin-bottom: 12px; background: var(--surface, #1B1D27) }
  .sc-carta-testa { display: flex; align-items: center; gap: 10px; padding: 8px 12px;
    border-bottom: 1px solid var(--line-soft, #242734) }
  .sc-tipo { font-family: var(--f-mono, monospace); font-size: 10px; letter-spacing: .14em;
    text-transform: uppercase; color: var(--amber, #E8A33D) }
  .sc-carta-tasti { margin-left: auto; display: flex; gap: 5px }
  .sc-carta-tasti button { padding: 3px 8px }
  .sc-carta-dentro { padding: 12px }
  .sc-voce { border-left: 2px solid var(--line, #2E3140); padding-left: 12px;
    margin-bottom: 14px }
  .sc-voce:last-child { margin-bottom: 0 }
  .sc-codice { width: 100%; min-height: 120px; box-sizing: border-box;
    font-family: var(--f-mono, monospace); font-size: 12px; line-height: 1.5;
    background: var(--ground, #12131A); color: var(--ink-dim, #B4B3AC);
    border: 1px solid var(--line, #2E3140); border-radius: 3px; padding: 9px }
  .sc-avviso { font-size: 12px; color: var(--muted, #8B8D9E); margin: 0 0 8px;
    font-family: var(--f-mono, monospace) }
  .sc-agg { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 14px }
  #sc-esiti { padding: 10px 16px; border-top: 1px solid var(--line, #2E3140);
    font-family: var(--f-mono, monospace); font-size: 11.5px; white-space: pre-wrap;
    max-height: 150px; overflow-y: auto; color: var(--muted, #8B8D9E) }
  #sc-esiti.male { color: var(--rust, #C4574B) }
  /* il cercasezioni per i collegamenti */
  #sc-scelta { position: fixed; z-index: 340; width: 300px; max-height: 280px;
    overflow-y: auto; background: var(--surface, #1B1D27); border-radius: 4px;
    border: 1px solid var(--amber, #E8A33D); box-shadow: 0 18px 40px -20px #000;
    display: none; padding: 8px }
  #sc-scelta.on { display: block }
  #sc-scelta input { width: 100%; box-sizing: border-box; margin-bottom: 6px;
    padding: 7px 9px; border-radius: 3px; border: 1px solid var(--line, #2E3140);
    background: var(--ground, #12131A); color: var(--ink, #E6E4DC);
    font-family: var(--f-mono, monospace); font-size: 12px }
  #sc-scelta button { display: block; width: 100%; text-align: left; background: transparent;
    border: 0; padding: 6px 8px; border-radius: 3px; cursor: pointer;
    color: var(--ink-dim, #B4B3AC); font-family: var(--f-body, serif); font-size: 13px }
  #sc-scelta button:hover { background: var(--surface-2, #232633); color: var(--ink, #E6E4DC) }
  #sc-scelta button small { display: block; font-family: var(--f-mono, monospace);
    font-size: 10px; color: var(--muted, #8B8D9E) }
  /* il tasto per aggiungere una sezione, in testa a ogni parte */
  .sc-nuova-sez { display: inline-flex; align-items: center; gap: 6px; margin: 14px auto 0;
    background: transparent; border: 1px dashed var(--line, #2E3140); border-radius: 3px;
    padding: 7px 14px; font-family: var(--f-mono, monospace); font-size: 10.5px;
    letter-spacing: .12em; text-transform: uppercase; color: var(--muted, #8B8D9E);
    cursor: pointer; opacity: .35; transition: opacity .15s, border-color .15s, color .15s }
  .part-head:hover .sc-nuova-sez, .sc-nuova-sez:focus-visible { opacity: 1 }
  .sc-nuova-sez:hover { color: var(--amber, #E8A33D); border-color: var(--amber, #E8A33D) }
  @media (max-width: 980px) {
    #sc-corpo { grid-template-columns: 1fr }
    #sc-lato { display: none }
  }
  @media (max-width: 720px) { #sc-velo { padding: 0 } #sc-scatola { border-radius: 0 } }
</style>
"""

SCRIPT_SCHEDA = r"""
<div id="sc-velo">
  <div id="sc-scatola">
    <div id="sc-testa">
      <h3 id="sc-titolo"></h3>
      <span id="sc-dove"></span>
      <span class="sc-spinta">
        <button type="button" id="sc-codice" title="Apri la stessa sezione come HTML">&lt;/&gt; codice</button>
        <button type="button" id="sc-annulla">Chiudi (Esc)</button>
        <button type="button" id="sc-salva">Salva (&#8984;S)</button>
      </span>
    </div>
    <div id="sc-corpo">
      <div id="sc-modulo"></div>
      <div id="sc-lato">
        <div id="sc-lato-etichetta">anteprima dal vivo</div>
        <div id="sc-anteprima"></div>
      </div>
    </div>
    <div id="sc-esiti"></div>
  </div>
</div>
<div id="sc-scelta"><input type="search" placeholder="cerca una sezione…" id="sc-scelta-q"><div id="sc-scelta-elenco"></div></div>
<script>
(function () {
  var PAGINA = "__PAGINA__";
  var scheda = null, sezioneAperta = null, SEZIONI = [];

  var $ = function (id) { return document.getElementById(id); };
  function esiti(t, male) {
    var e = $("sc-esiti");
    e.textContent = t || "";
    e.className = male ? "male" : "";
  }

  /* ---------- ripulitura: dal contenteditable esce solo il vocabolario del
     progetto. Senza questo, incollando da un'altra pagina entrerebbero <span
     style>, <font>, classi altrui — e la mappa userebbe tag che i suoi fogli
     di stile non conoscono. ---------- */
  var AMMESSI = { B: "b", STRONG: "b", I: "i", EM: "i", SMALL: "small", A: "a" };
  function ripulisci(nodo) {
    var fuori = "";
    for (var n = nodo.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 3) {
        fuori += n.nodeValue.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      } else if (n.nodeType === 1) {
        var t = AMMESSI[n.tagName];
        if (!t) { fuori += ripulisci(n); continue; }
        if (t === "a") {
          var h = n.getAttribute("href") || "";
          /* solo rimandi interni: un link a caso romperebbe il controllo dei
             rimandi che costruisci.py fa in costruzione */
          if (!/^#[A-Za-z0-9_-]+$/.test(h) && !/^[a-z-]+:[A-Za-z0-9_-]+$/.test(h)) {
            fuori += ripulisci(n); continue;
          }
          fuori += '<a href="' + h + '">' + ripulisci(n) + "</a>";
        } else {
          fuori += "<" + t + ">" + ripulisci(n) + "</" + t + ">";
        }
      }
    }
    return fuori;
  }
  /* più paragrafi: un figlio di blocco per paragrafo, riuniti con un rigo vuoto
     — la stessa convenzione che legge scheda.py */
  function leggiCampo(el) {
    var blocchi = [];
    for (var n = el.firstChild; n; n = n.nextSibling) {
      if (n.nodeType === 1 && /^(P|DIV)$/.test(n.tagName)) blocchi.push(ripulisci(n).trim());
    }
    if (blocchi.length) return blocchi.filter(Boolean).join("\n\n");
    return ripulisci(el).trim();
  }
  function scriviCampo(el, testo) {
    var pezzi = (testo || "").split(/\n\s*\n/);
    el.innerHTML = pezzi.length > 1
      ? pezzi.map(function (p) { return "<p>" + p + "</p>"; }).join("")
      : (testo || "");
  }

  function campo(etichetta, valore, corto) {
    var d = document.createElement("div");
    d.className = "sc-campo";
    d.innerHTML = '<label>' + etichetta + '</label>' +
      '<div class="sc-barra">' +
      '<button type="button" data-fa="grassetto" title="Grassetto"><b>G</b></button>' +
      '<button type="button" data-fa="corsivo" title="Corsivo"><i>C</i></button>' +
      '<button type="button" data-fa="virgolette" title="Virgolette di citazione">« »</button>' +
      '<button type="button" data-fa="legame" title="Collegamento a una sezione">⛓ collega</button>' +
      '</div>';
    var scrivi = document.createElement("div");
    scrivi.className = "sc-scrivi";
    scrivi.contentEditable = "true";
    if (corto) scrivi.setAttribute("data-corto", "1");
    scriviCampo(scrivi, valore);
    scrivi.dataset.iniziale = leggiCampo(scrivi);
    scrivi.addEventListener("focus", function () {
      var a = document.querySelector(".sc-campo.sc-attivo");
      if (a) a.classList.remove("sc-attivo");
      d.classList.add("sc-attivo");
    });
    d.appendChild(scrivi);
    d.querySelectorAll(".sc-barra button").forEach(function (b) {
      b.addEventListener("mousedown", function (e) { e.preventDefault(); });
      b.addEventListener("click", function () { formatta(b.dataset.fa, scrivi); });
    });
    return { riquadro: d, scrivi: scrivi };
  }

  function formatta(cosa, dove) {
    dove.focus();
    if (cosa === "grassetto") return document.execCommand("bold");
    if (cosa === "corsivo") return document.execCommand("italic");
    if (cosa === "virgolette") {
      var s = window.getSelection();
      var t = s.toString();
      return document.execCommand("insertText", false, t ? "«" + t + "»" : "«»");
    }
    if (cosa === "legame") apriScelta(dove);
  }

  /* ---------- scelta della sezione da collegare ---------- */
  var perLegame = null, rangeSalvato = null;
  function apriScelta(dove) {
    var s = window.getSelection();
    rangeSalvato = s.rangeCount ? s.getRangeAt(0).cloneRange() : null;
    perLegame = dove;
    var scatola = $("sc-scelta");
    var r = dove.getBoundingClientRect();
    scatola.style.left = Math.min(r.left, innerWidth - 320) + "px";
    scatola.style.top = Math.min(r.top + 30, innerHeight - 300) + "px";
    scatola.classList.add("on");
    $("sc-scelta-q").value = "";
    elencoScelta("");
    $("sc-scelta-q").focus();
  }
  function elencoScelta(filtro) {
    var f = (filtro || "").toLowerCase();
    var e = $("sc-scelta-elenco");
    e.innerHTML = "";
    SEZIONI.filter(function (s) {
      return !f || s.titolo.toLowerCase().indexOf(f) >= 0 || s.id.indexOf(f) >= 0;
    }).slice(0, 40).forEach(function (s) {
      var b = document.createElement("button");
      b.type = "button";
      b.innerHTML = s.titolo + "<small>#" + s.id + "</small>";
      b.addEventListener("click", function () { metteLegame(s.id); });
      e.appendChild(b);
    });
  }
  function metteLegame(id) {
    $("sc-scelta").classList.remove("on");
    if (!perLegame) return;
    perLegame.focus();
    if (rangeSalvato) {
      var s = window.getSelection();
      s.removeAllRanges();
      s.addRange(rangeSalvato);
    }
    var testo = window.getSelection().toString();
    document.execCommand("insertHTML", false,
      '<a href="#' + id + '">' + (testo || "questa sezione") + "</a>");
  }
  $("sc-scelta-q").addEventListener("input", function () { elencoScelta(this.value); });
  document.addEventListener("mousedown", function (e) {
    if (!$("sc-scelta").contains(e.target)) $("sc-scelta").classList.remove("on");
  });

  /* ---------- le carte dei blocchi ---------- */
  var NOMI = { voci: "elenco di voci", blocco: "blocco in evidenza",
               paragrafo: "paragrafo", immagine: "immagine",
               "riga-immagini": "riga di immagini", galleria: "galleria di immagini",
               codice: "blocco avanzato (codice)" };

  function carta(b, indice) {
    var c = document.createElement("div");
    c.className = "sc-carta";
    c.dataset.origine = (b.origine === undefined || b.origine === null) ? "" : b.origine;
    c.dataset.tipo = b.tipo;
    c.innerHTML = '<div class="sc-carta-testa"><span class="sc-tipo">' +
      (NOMI[b.tipo] || b.tipo) + '</span><span class="sc-carta-tasti">' +
      '<button type="button" data-fa="su" title="Sposta in su">↑</button>' +
      '<button type="button" data-fa="giu" title="Sposta in giù">↓</button>' +
      '<button type="button" data-fa="via" title="Togli questo blocco">🗑</button>' +
      '</span></div>';
    var dentro = document.createElement("div");
    dentro.className = "sc-carta-dentro";
    c.appendChild(dentro);

    if (b.tipo === "voci") {
      (b.voci || []).forEach(function (v, k) { dentro.appendChild(carteVoce(v, k)); });
      var agg = document.createElement("div");
      agg.className = "sc-agg";
      agg.innerHTML = '<button type="button" data-fa="piu-voce">+ voce</button>';
      agg.querySelector("button").addEventListener("click", function () {
        agg.parentNode.insertBefore(carteVoce({ titolo: "", sottotitolo: "", testo: "" }, null), agg);
      });
      dentro.appendChild(agg);
    } else if (b.tipo === "blocco") {
      dentro.appendChild(campo("Titolo", b.titolo || "", true).riquadro);
      dentro.appendChild(campo("Sottotitolo (facoltativo)", b.sottotitolo || "", true).riquadro);
      dentro.appendChild(campo("Testo — un rigo vuoto separa i paragrafi", b.testo || "").riquadro);
    } else if (b.tipo === "paragrafo") {
      dentro.appendChild(campo("Testo", b.testo || "").riquadro);
    } else if (b.tipo === "immagine") {
      dentro.appendChild(campo("File dell'immagine", b.src || "", true).riquadro);
      dentro.appendChild(campo("Descrizione per chi non vede (alt)", b.alt || "", true).riquadro);
      dentro.appendChild(campo("Didascalia", b.didascalia || "").riquadro);
    } else if (b.tipo === "riga-immagini" || b.tipo === "galleria") {
      if (b.tipo === "galleria") {
        dentro.appendChild(campo("Titolo della galleria", b.titolo || "", true).riquadro);
        dentro.appendChild(campo("Introduzione", b.testo || "").riquadro);
      }
      (b.figure || []).forEach(function (fg, k) {
        var v = document.createElement("div");
        v.className = "sc-voce";
        v.dataset.origine = k;
        v.appendChild(campo("File", fg.src || "", true).riquadro);
        v.appendChild(campo("Descrizione (alt)", fg.alt || "", true).riquadro);
        v.appendChild(campo("Didascalia", fg.didascalia || "").riquadro);
        dentro.appendChild(v);
      });
    } else {
      var p = document.createElement("p");
      p.className = "sc-avviso";
      p.textContent = "Questo blocco ha una forma che la scheda non sa rappresentare a campi " +
        "(di solito una figura disegnata a mano o una tabella). Resta esattamente com'è; " +
        "qui sotto puoi comunque correggerlo a mano.";
      dentro.appendChild(p);
      var ta = document.createElement("textarea");
      ta.className = "sc-codice";
      ta.value = b.grezzo || "";
      ta.dataset.iniziale = ta.value;
      dentro.appendChild(ta);
    }

    c.querySelectorAll(".sc-carta-tasti button").forEach(function (t) {
      t.addEventListener("click", function () { muovi(c, t.dataset.fa); });
    });
    return c;
  }

  function carteVoce(v, indice) {
    var d = document.createElement("div");
    d.className = "sc-voce";
    d.dataset.origine = (indice === null || indice === undefined) ? "" : indice;
    if (v.semplice === false) {
      var p = document.createElement("p");
      p.className = "sc-avviso";
      p.textContent = "Voce dalla forma non rappresentabile a campi: resta com'è.";
      d.appendChild(p);
      var ta = document.createElement("textarea");
      ta.className = "sc-codice";
      ta.value = v.grezzo || "";
      ta.dataset.iniziale = ta.value;
      ta.dataset.tenere = "1";
      d.appendChild(ta);
      return d;
    }
    d.appendChild(campo("Titolo della voce", v.titolo || "", true).riquadro);
    d.appendChild(campo("Sottotitolo (facoltativo)", v.sottotitolo || "", true).riquadro);
    d.appendChild(campo("Testo — un rigo vuoto separa i paragrafi", v.testo || "").riquadro);
    var via = document.createElement("div");
    via.className = "sc-agg";
    via.innerHTML = '<button type="button">togli questa voce</button>';
    via.querySelector("button").addEventListener("click", function () { d.remove(); });
    d.appendChild(via);
    return d;
  }

  function muovi(c, dove) {
    if (dove === "via") { c.remove(); return; }
    var altro = dove === "su" ? c.previousElementSibling : c.nextElementSibling;
    if (!altro || !altro.classList.contains("sc-carta")) return;
    if (dove === "su") c.parentNode.insertBefore(c, altro);
    else c.parentNode.insertBefore(altro, c);
  }

  /* ---------- apertura ---------- */
  function apriScheda(sez) {
    sezioneAperta = sez.id;
    $("sc-titolo").textContent = (sez.querySelector("h2") || {}).textContent || sez.id;
    $("sc-dove").textContent = "#" + sez.id;
    $("sc-modulo").innerHTML = "";
    $("sc-anteprima").innerHTML = "";
    esiti("caricamento…");
    $("sc-velo").classList.add("on");
    fetch("/scheda?pagina=" + encodeURIComponent(PAGINA) + "&sezione=" + encodeURIComponent(sez.id))
      .then(function (r) { return r.json(); })
      .then(function (r) {
        if (!r.ok) { esiti(r.errore || "non riesco a leggere la sezione", true); return; }
        scheda = r.scheda;
        $("sc-dove").textContent = "#" + sez.id + " · " + r.file;
        disegna();
        chiediAnteprima();
        esiti("");
      })
      .catch(function () { esiti("il server locale non risponde", true); });
  }

  function disegna() {
    var corpo = $("sc-modulo");
    corpo.innerHTML = "";
    var g1 = document.createElement("div");
    g1.className = "sc-gruppo";
    g1.innerHTML = '<p class="sc-intestazione">La colonna di sinistra</p>';
    [["etichetta", "Etichetta", true], ["titolo", "Titolo", true],
     ["sommario", "Sommario"], ["citazione", "Citazione a fianco"],
     ["fonte", "Fonte", true]].forEach(function (c) {
      if (!scheda.aside[c[0]]) return;
      var f = campo(c[1], scheda.aside[c[0]].html || "", c[2]);
      f.riquadro.dataset.campo = c[0];
      g1.appendChild(f.riquadro);
    });
    corpo.appendChild(g1);

    var g2 = document.createElement("div");
    g2.className = "sc-gruppo";
    g2.innerHTML = '<p class="sc-intestazione">I blocchi</p>';
    var elenco = document.createElement("div");
    elenco.id = "sc-elenco";
    (scheda.blocchi || []).forEach(function (b, i) { elenco.appendChild(carta(b, i)); });
    g2.appendChild(elenco);
    var agg = document.createElement("div");
    agg.className = "sc-agg";
    ["voci", "blocco", "paragrafo", "immagine"].forEach(function (t) {
      var b = document.createElement("button");
      b.type = "button";
      b.textContent = "+ " + NOMI[t];
      b.addEventListener("click", function () {
        var vuoto = { tipo: t, origine: null, voci: t === "voci" ? [{ titolo: "", sottotitolo: "", testo: "" }] : [] };
        elenco.appendChild(carta(vuoto, null));
      });
      agg.appendChild(b);
    });
    g2.appendChild(agg);
    corpo.appendChild(g2);
  }

  /* ---------- raccolta e salvataggio ---------- */
  function raccogliCampo(riquadro) {
    var el = riquadro.querySelector(".sc-scrivi");
    var ora = leggiCampo(el);
    return { html: ora, mod: ora !== el.dataset.iniziale };
  }

  function raccogli() {
    var fuori = { aside: {}, blocchi: [] };
    document.querySelectorAll("#sc-modulo .sc-campo[data-campo]").forEach(function (r) {
      fuori.aside[r.dataset.campo] = raccogliCampo(r);
    });
    document.querySelectorAll("#sc-elenco > .sc-carta").forEach(function (c) {
      var b = { tipo: c.dataset.tipo, mod: false };
      b.origine = c.dataset.origine === "" ? null : parseInt(c.dataset.origine, 10);
      if (b.origine === null) b.mod = true;
      var dentro = c.querySelector(".sc-carta-dentro");

      if (b.tipo === "voci") {
        b.voci = [];
        dentro.querySelectorAll(":scope > .sc-voce").forEach(function (v) {
          var tenere = v.querySelector('textarea[data-tenere="1"]');
          if (tenere) {
            b.voci.push({ origine: v.dataset.origine === "" ? null : parseInt(v.dataset.origine, 10),
                          mod: tenere.value !== tenere.dataset.iniziale, grezzo: tenere.value });
            if (tenere.value !== tenere.dataset.iniziale) b.mod = true;
            return;
          }
          var campi = v.querySelectorAll(":scope > .sc-campo");
          var t = raccogliCampo(campi[0]), s = raccogliCampo(campi[1]), x = raccogliCampo(campi[2]);
          var cambiata = t.mod || s.mod || x.mod || v.dataset.origine === "";
          if (cambiata) b.mod = true;
          b.voci.push({ origine: v.dataset.origine === "" ? null : parseInt(v.dataset.origine, 10),
                        mod: cambiata, titolo: t.html, sottotitolo: s.html, testo: x.html });
        });
        var originali = (scheda.blocchi[b.origine] || {}).voci || [];
        if (b.voci.length !== originali.length) b.mod = true;
      } else if (b.tipo === "codice") {
        var ta = dentro.querySelector("textarea");
        if (ta && ta.value !== ta.dataset.iniziale) { b.mod = true; b.grezzo = ta.value; }
      } else if (b.tipo === "riga-immagini" || b.tipo === "galleria") {
        var campi2 = dentro.querySelectorAll(":scope > .sc-campo");
        if (b.tipo === "galleria" && campi2.length >= 2) {
          var ti = raccogliCampo(campi2[0]), intro = raccogliCampo(campi2[1]);
          b.titolo = ti.html; b.testo = intro.html;
          if (ti.mod || intro.mod) b.mod = true;
        }
        b.figure = [];
        dentro.querySelectorAll(":scope > .sc-voce").forEach(function (v) {
          var c3 = v.querySelectorAll(":scope > .sc-campo");
          var s1 = raccogliCampo(c3[0]), s2 = raccogliCampo(c3[1]), s3 = raccogliCampo(c3[2]);
          var cambiata = s1.mod || s2.mod || s3.mod;
          if (cambiata) b.mod = true;
          b.figure.push({ origine: v.dataset.origine === "" ? null : parseInt(v.dataset.origine, 10),
                          mod: cambiata, src: s1.html, alt: s2.html, didascalia: s3.html });
        });
      } else {
        var c4 = dentro.querySelectorAll(":scope > .sc-campo");
        var valori = [];
        c4.forEach(function (r) { valori.push(raccogliCampo(r)); });
        if (valori.some(function (v) { return v.mod; })) b.mod = true;
        if (b.tipo === "blocco") {
          b.titolo = (valori[0] || {}).html || "";
          b.sottotitolo = (valori[1] || {}).html || "";
          b.testo = (valori[2] || {}).html || "";
        } else if (b.tipo === "paragrafo") {
          b.testo = (valori[0] || {}).html || "";
        } else if (b.tipo === "immagine") {
          b.src = (valori[0] || {}).html || "";
          b.alt = (valori[1] || {}).html || "";
          b.didascalia = (valori[2] || {}).html || "";
        }
      }
      fuori.blocchi.push(b);
    });
    return fuori;
  }

  /* ---------- anteprima dal vivo ----------
     Non la si ricostruisce qui: si manda la scheda al server, che applica la
     STESSA fusione e la stessa composizione del salvataggio e restituisce il
     frammento. Rifarla in JavaScript vorrebbe dire tenere due composizioni
     allineate a mano, e prima o poi divergerebbero — mostrando un'anteprima
     che non è ciò che verrebbe scritto. */
  var attesaAnteprima = null, anteprimaInCorso = false;
  function chiediAnteprima() {
    if (!sezioneAperta || !scheda) return;
    clearTimeout(attesaAnteprima);
    attesaAnteprima = setTimeout(function () {
      if (anteprimaInCorso) { chiediAnteprima(); return; }
      anteprimaInCorso = true;
      fetch("/anteprima-scheda", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pagina: PAGINA, sezione: sezioneAperta, scheda: raccogli() })
      }).then(function (r) { return r.json(); }).then(function (r) {
        anteprimaInCorso = false;
        if (r.ok) $("sc-anteprima").innerHTML = r.html;
      }).catch(function () { anteprimaInCorso = false; });
    }, 260);
  }
  /* un ascoltatore solo sul contenitore invece di uno per campo: le carte
     nascono e muoiono di continuo, e riagganciarli a ognuna sarebbe una fonte
     sicura di campi «muti» */
  $("sc-modulo").addEventListener("input", chiediAnteprima);
  $("sc-modulo").addEventListener("click", function (e) {
    if (e.target.closest(".sc-carta-tasti, .sc-agg, .sc-barra")) setTimeout(chiediAnteprima, 30);
  });

  function salva() {
    esiti("salvataggio…");
    fetch("/salva-scheda", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pagina: PAGINA, sezione: sezioneAperta, scheda: raccogli() })
    }).then(function (r) { return r.json(); }).then(function (r) {
      if (!r.ok) { esiti((r.errori || ["non salvato"]).join("\n"), true); return; }
      if (r.invariata) { esiti("niente da salvare: non è cambiato nulla."); return; }
      esiti("salvato in " + r.file + "\n" + (r.verifica || ""));
      setTimeout(function () { location.reload(); }, 500);
    }).catch(function () { esiti("il server locale non risponde", true); });
  }

  /* ---------- una sezione nuova ---------- */
  function nuovaSezione(parte, dopo) {
    var corpo = $("sc-modulo");
    sezioneAperta = null;
    scheda = null;
    $("sc-titolo").textContent = "Una sezione nuova";
    $("sc-dove").textContent = "in «" + parte.titolo + "»";
    corpo.innerHTML = "";
    var g = document.createElement("div");
    g.className = "sc-gruppo";
    g.innerHTML = '<p class="sc-intestazione">Dove e come</p>';
    var fTitolo = campo("Titolo della sezione", "", true);
    g.appendChild(fTitolo.riquadro);

    var dove = document.createElement("div");
    dove.className = "sc-campo";
    dove.innerHTML = '<label>Dopo quale sezione</label>';
    var scelta = document.createElement("select");
    scelta.className = "sc-scrivi";
    scelta.innerHTML = '<option value="">— all\'inizio della parte —</option>' +
      parte.sezioni.map(function (s) {
        return '<option value="' + s.id + '">' + s.titolo + "</option>";
      }).join("");
    if (dopo) scelta.value = dopo;
    dove.appendChild(scelta);
    g.appendChild(dove);

    var p = document.createElement("p");
    p.className = "sc-avviso";
    p.textContent = "L'indirizzo della sezione si ricava dal titolo e non si potrà più " +
      "cambiare: i rimandi di tutta la biblioteca ci girano sopra.";
    g.appendChild(p);
    corpo.appendChild(g);
    $("sc-anteprima").innerHTML = "";
    $("sc-velo").classList.add("on");
    esiti("");

    $("sc-salva").onclick = function () {
      var titolo = leggiCampo(fTitolo.scrivi).replace(/<[^>]+>/g, "").trim();
      if (!titolo) { esiti("serve un titolo", true); return; }
      esiti("creazione…");
      fetch("/nuova-sezione", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pagina: PAGINA, parte: parte.id, dopo: scelta.value, titolo: titolo })
      }).then(function (r) { return r.json(); }).then(function (r) {
        if (!r.ok) { esiti((r.errori || ["non creata"]).join("\n"), true); return; }
        esiti("creata #" + r.sezione + "\n" + (r.verifica || ""));
        setTimeout(function () { location.hash = "#" + r.sezione; location.reload(); }, 600);
      }).catch(function () { esiti("il server locale non risponde", true); });
    };
  }

  /* ---------- innesti nella pagina ---------- */
  fetch("/struttura?pagina=" + encodeURIComponent(PAGINA))
    .then(function (r) { return r.json(); })
    .then(function (r) {
      if (!r.ok) return;
      r.parti.forEach(function (p) {
        p.sezioni.forEach(function (s) { SEZIONI.push(s); });
        var testa = document.querySelector("#parte-" + p.id + " .part-head");
        if (!testa) return;
        var b = document.createElement("button");
        b.type = "button";
        b.className = "sc-nuova-sez";
        b.innerHTML = "+ sezione in questa parte";
        b.addEventListener("click", function () { nuovaSezione(p, ""); });
        testa.appendChild(b);
      });
    });

  function chiudi() {
    $("sc-velo").classList.remove("on");
    $("sc-salva").onclick = salva;
  }
  $("sc-annulla").addEventListener("click", chiudi);
  $("sc-salva").onclick = salva;
  $("sc-codice").addEventListener("click", function () {
    var id = sezioneAperta;
    chiudi();
    if (id && window.__apriCodice) window.__apriCodice(id);
  });
  document.addEventListener("keydown", function (e) {
    if (!$("sc-velo").classList.contains("on")) return;
    if (e.key === "Escape" && !$("sc-scelta").classList.contains("on")) { e.preventDefault(); chiudi(); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); $("sc-salva").onclick(); }
  });

  window.__apriScheda = apriScheda;
})();
</script>
"""



SCRIPT_EDITOR = r"""
<div id="ed-velo">
  <div id="ed-scatola">
    <div id="ed-testa">
      <h3 id="ed-titolo"></h3>
      <span id="ed-dove"></span>
      <span id="ed-scorciatoie">tab indenta · &#8984;F cerca · &#8984;&#8997;F sostituisci · &#8984;/ commenta · &#8984;D duplica riga</span>
      <span class="ed-spinta">
        <button type="button" id="ed-annulla">Chiudi (Esc)</button>
        <button type="button" id="ed-salva">Salva (&#8984;S)</button>
      </span>
    </div>
    <div id="ed-corpo">
      <div id="ed-sinistra">
        <div class="ed-inserti">
          <button type="button" data-inserto="voce">+ voce d'elenco</button>
          <button type="button" data-inserto="blocco">+ blocco</button>
          <button type="button" data-inserto="citazione">+ citazione</button>
          <button type="button" data-inserto="paragrafo">+ paragrafo</button>
          <label class="ed-misura">codice
            <select id="ed-misura">
              <option value="9px">9</option>
              <option value="10px">10</option>
              <option value="11px">11</option>
              <option value="12px">12</option>
              <option value="13px">13</option>
              <option value="14px">14</option>
              <option value="16px">16</option>
            </select>
          </label>
        </div>
        <textarea id="ed-testo" spellcheck="false"></textarea>
      </div>
      <div id="ed-destra">
        <div id="ed-etichetta-anteprima">anteprima dal vivo</div>
        <div id="ed-anteprima"></div>
      </div>
    </div>
    <div id="ed-esiti"></div>
  </div>
</div>
<div id="ed-conferma">
  <div id="ed-conferma-scatola" role="dialog" aria-modal="true" aria-labelledby="ed-conferma-titolo">
    <h4 id="ed-conferma-titolo"></h4>
    <p id="ed-conferma-testo"></p>
    <div id="ed-conferma-tasti"></div>
  </div>
</div>
<div id="ed-briciola"></div>
<script>
(function () {
  var PAGINA = "__PAGINA__";
  var EDITABILI = __EDITABILI__;
  var sezioneAperta = null, testoIniziale = "";

  var INSERTI = {
    voce: '\n            <li><span class="n-t">TITOLO <small>sottotitolo</small></span>\n              <p class="n-d">Testo della voce.</p>\n            </li>',
    blocco: '\n          <div class="move">\n            <h3>Titolo del blocco <small>sottotitolo</small></h3>\n            <p>Testo del blocco.</p>\n          </div>',
    citazione: '<b>«...»</b>',
    paragrafo: '\n              <p class="n-d">Testo.</p>'
  };

  // ---- conferma: modale della pagina, al posto di confirm() ----------------
  var confermaInCorso = null;
  function conferma(titolo, testo, scelte) {
    return new Promise(function (risolvi) {
      var velo = document.getElementById("ed-conferma");
      var tasti = document.getElementById("ed-conferma-tasti");
      document.getElementById("ed-conferma-titolo").textContent = titolo;
      document.getElementById("ed-conferma-testo").textContent = testo;
      tasti.innerHTML = "";
      confermaInCorso = function (valore) {
        velo.classList.remove("on");
        confermaInCorso = null;
        risolvi(valore);
      };
      scelte.forEach(function (s) {
        var b = document.createElement("button");
        b.type = "button";
        b.textContent = s.etichetta;
        if (s.primario) b.className = "ed-primario";
        b.addEventListener("click", function () { confermaInCorso(s.valore); });
        tasti.appendChild(b);
      });
      velo.classList.add("on");
      var primo = tasti.querySelector("button");
      if (primo) primo.focus();
    });
  }
  document.getElementById("ed-conferma").addEventListener("click", function (e) {
    // clic fuori dalla scatola = annulla, come il velo dell'editor
    if (e.target.id === "ed-conferma" && confermaInCorso) confermaInCorso(null);
  });

  function briciola(msg) {
    var b = document.getElementById("ed-briciola");
    b.textContent = msg; b.classList.add("on");
    setTimeout(function () { b.classList.remove("on"); }, 2600);
  }

  function esiti(testo, male) {
    var e = document.getElementById("ed-esiti");
    e.className = male ? "male" : "";
    e.innerHTML = testo ? '<div class="ed-riga-esito"></div>' : "";
    if (testo) e.firstChild.textContent = testo;
  }

  // ---- il testo: CodeMirror se c'è, altrimenti la textarea nuda -------------
  var cm = null;
  function areaTesto() { return document.getElementById("ed-testo"); }
  function creaEditor() {
    if (cm || typeof CodeMirror === "undefined") return;
    cm = CodeMirror.fromTextArea(areaTesto(), {
      mode: "htmlmixed",
      lineNumbers: true,
      lineWrapping: true,
      indentUnit: 2,
      tabSize: 2,
      indentWithTabs: false,
      autoCloseTags: true,
      autoCloseBrackets: true,
      matchTags: { bothTags: true },
      matchBrackets: true,
      styleActiveLine: true,
      foldGutter: true,
      highlightSelectionMatches: { showToken: /[\w-]/, annotateScrollbar: true },
      gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
      extraKeys: {
        // il Tab indenta invece di saltare al campo successivo: era il difetto più fastidioso
        "Tab": function (c) {
          if (c.somethingSelected()) c.indentSelection("add");
          else c.replaceSelection(new Array(c.getOption("indentUnit") + 1).join(" "), "end");
        },
        "Shift-Tab": function (c) { c.indentSelection("subtract"); },
        "Cmd-S": function () { salva(); },
        "Ctrl-S": function () { salva(); },
        "Cmd-F": "findPersistent",
        "Ctrl-F": "findPersistent",
        "Cmd-G": "findNext",
        "Ctrl-G": "findNext",
        "Shift-Cmd-G": "findPrev",
        "Shift-Ctrl-G": "findPrev",
        "Cmd-Alt-F": "replace",
        "Shift-Ctrl-F": "replace",
        "Shift-Cmd-Alt-F": "replaceAll",
        "Alt-G": "jumpToLine",
        "Cmd-/": "toggleComment",
        "Ctrl-/": "toggleComment",
        "Cmd-D": function (c) {           // duplica la riga
          var r = c.getCursor().line, t = c.getLine(r);
          c.replaceRange(t + "\n", { line: r + 1, ch: 0 });
        },
        "Ctrl-D": function (c) {
          var r = c.getCursor().line, t = c.getLine(r);
          c.replaceRange(t + "\n", { line: r + 1, ch: 0 });
        }
      }
    });
    cm.on("change", anteprima);
  }
  function leggi() { return cm ? cm.getValue() : areaTesto().value; }
  function scrivi(v) {
    if (cm) { cm.setValue(v); cm.clearHistory(); cm.refresh(); }
    else areaTesto().value = v;
  }
  function metti(t) {
    if (cm) { cm.replaceSelection(t, "end"); cm.focus(); return; }
    var ta = areaTesto(), i = ta.selectionStart, j = ta.selectionEnd;
    ta.value = ta.value.slice(0, i) + t + ta.value.slice(j);
    ta.focus();
    ta.setSelectionRange(i + t.length, i + t.length);
  }
  function metteFuoco() { if (cm) cm.focus(); else areaTesto().focus(); }

  function anteprima() {
    document.getElementById("ed-anteprima").innerHTML = leggi();
  }

  function appendiMatita(sez) {
    if (sez.querySelector(".ed-matita")) return;
    sez.classList.add("ed-sez");
    var m = document.createElement("button");
    m.type = "button";
    m.className = "ed-matita";
    m.innerHTML = "✎ modifica";
    m.title = "Modifica questa sezione a campi";
    /* la matita apre la scheda a campi; il codice resta raggiungibile da lì con
       il tasto «</> codice», per i casi che i campi non coprono */
    m.addEventListener("click", function (e) {
      e.preventDefault();
      if (window.__apriScheda) window.__apriScheda(sez); else apri(sez);
    });
    var fianco = sez.querySelector(".branch-aside");
    if (fianco) {
      fianco.appendChild(m);          // segue la colonna sticky, sempre raggiungibile
    } else {
      m.classList.add("ed-angolo");   // sezioni senza fianco: angolo in alto a destra
      sez.appendChild(m);
    }
  }

  EDITABILI.forEach(function (id) {
    var sez = document.getElementById(id);
    if (sez && sez.tagName === "SECTION") appendiMatita(sez);
  });

  function titoloDi(sez) {
    var h = sez.querySelector("h2");
    return h ? h.textContent.trim() : sez.id;
  }

  function apri(sez) {
    sezioneAperta = sez.id;
    document.getElementById("ed-titolo").textContent = titoloDi(sez);
    document.getElementById("ed-dove").textContent = "#" + sez.id + " · " + PAGINA;
    esiti("");
    document.getElementById("ed-velo").classList.add("on");
    creaEditor();                 // dopo l'apertura del velo: CodeMirror misura il suo spazio
    scrivi("caricamento…");
    fetch("/sorgente?pagina=" + encodeURIComponent(PAGINA) + "&sezione=" + encodeURIComponent(sez.id))
      .then(function (r) { return r.json(); })
      .then(function (r) {
        if (!r.ok) { esiti(r.errore || "non riesco a leggere la sezione", true); scrivi(""); return; }
        scrivi(r.html);
        testoIniziale = r.html;
        document.getElementById("ed-dove").textContent = "#" + sez.id + " · " + r.file;
        anteprima();
        metteFuoco();
        if (cm) cm.setCursor({ line: 0, ch: 0 });
      })
      .catch(function () { esiti("il server locale non risponde", true); });
  }

  /* la scheda a campi chiama qui quando si preme «</> codice» */
  window.__apriCodice = function (id) {
    var sez = document.getElementById(id);
    if (sez) apri(sez);
  };

  function chiudiDavvero() {
    document.getElementById("ed-velo").classList.remove("on");
    sezioneAperta = null;
  }

  function chiudi(forza) {
    if (forza || leggi() === testoIniziale) { chiudiDavvero(); return; }
    conferma(
      "Modifiche non salvate",
      "Hai cambiato il testo di questa sezione senza salvarlo. Se chiudi adesso, le modifiche vanno perse.",
      [{ etichetta: "Torna all'editor", valore: null },
       { etichetta: "Chiudi e perdi", valore: "scarta" },
       { etichetta: "Salva e chiudi", valore: "salva", primario: true }]
    ).then(function (scelta) {
      if (scelta === "scarta") chiudiDavvero();
      else if (scelta === "salva") salva();
      else metteFuoco();
    });
  }

  function salva() {
    if (!sezioneAperta) return;
    var testo = leggi();
    esiti("salvo, ricostruisco e verifico…");
    fetch("/salva-sezione", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pagina: PAGINA, sezione: sezioneAperta, html: testo })
    }).then(function (r) { return r.json(); }).then(function (r) {
      if (!r.ok) { esiti((r.errori || ["errore sconosciuto"]).join("\n"), true); return; }
      if (r.invariata) { esiti(r.verifica); return; }
      // ricarico sulla sezione: quello che vedi è il file ricostruito, non un'anteprima
      sessionStorage.setItem("ed-appena-salvata", sezioneAperta + "|" + (r.verifica || ""));
      location.hash = "#" + sezioneAperta;
      location.reload();
    }).catch(function () { esiti("il server locale non risponde", true); });
  }

  // misura del codice: preferenza di chi scrive, ricordata fra una sessione e l'altra
  var misura = document.getElementById("ed-misura");
  var scelta = null;
  try { scelta = localStorage.getItem("ed.misura"); } catch (e) {}
  if (!scelta) scelta = "11px";
  document.documentElement.style.setProperty("--ed-misura", scelta);
  misura.value = scelta;
  if (misura.value !== scelta) misura.value = "11px";  // valore vecchio non più in elenco
  misura.addEventListener("change", function () {
    document.documentElement.style.setProperty("--ed-misura", misura.value);
    try { localStorage.setItem("ed.misura", misura.value); } catch (e) {}
    if (cm) cm.refresh();
    metteFuoco();
  });

  document.getElementById("ed-annulla").addEventListener("click", function () { chiudi(false); });
  document.getElementById("ed-salva").addEventListener("click", salva);
  areaTesto().addEventListener("input", anteprima);   // serve solo senza CodeMirror
  document.addEventListener("keydown", function (e) {
    // la conferma viene prima di tutto: Esc la annulla e basta
    if (confermaInCorso) {
      if (e.key === "Escape") { e.preventDefault(); confermaInCorso(null); metteFuoco(); }
      return;
    }
    var aperto = document.getElementById("ed-velo").classList.contains("on");
    if (!aperto) return;
    // se è aperta la finestrella di ricerca di CodeMirror, Esc la chiude: non il pannello
    if (e.key === "Escape" && !document.querySelector(".CodeMirror-dialog")) {
      e.preventDefault(); chiudi(false);
    }
    // con CodeMirror il salvataggio passa dalle sue scorciatoie; questa resta per la textarea
    if (!cm && (e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); salva(); }
  });

  document.querySelectorAll(".ed-inserti button").forEach(function (b) {
    b.addEventListener("click", function () {
      metti(INSERTI[b.dataset.inserto] || "");
      anteprima();
    });
  });

  var appena = sessionStorage.getItem("ed-appena-salvata");
  if (appena) {
    sessionStorage.removeItem("ed-appena-salvata");
    var pezzi = appena.split("|");
    briciola("salvata in sorgente/ · ricostruita · " +
      (pezzi[1] && pezzi[1].indexOf("PROBLEMI") === -1 ? "verifica ok" : "vedi la verifica"));
  }
})();
</script>
"""


def pagine_costruite():
    for p in sorted(SITO.glob("*.html")):
        if p.name.startswith("mockup-") or p.name == "anteprima-locale.html":
            continue
        yield p


def pagine_pronte():
    pronte = {}
    for p in pagine_costruite():
        corpo = p.read_text(encoding="utf-8")
        ids = sezioni_modificabili(p.name)
        if ids:
            editor = (tag_codemirror() + STILE_EDITOR + STILE_SCHEDA
                      + SCRIPT_EDITOR.replace("__PAGINA__", p.name)
                                     .replace("__EDITABILI__", json.dumps(ids))
                      + SCRIPT_SCHEDA.replace("__PAGINA__", p.name))
        else:
            editor = ""
        pronte[p.name] = GUSCIO.format(corpo=corpo, editor=editor)
    return pronte


class ManoDiPagina(BaseHTTPRequestHandler):
    pronte = {}

    def log_message(self, formato, *args):
        pass

    def _json(self, dati):
        corpo = json.dumps(dati).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        pezzi = urlparse(self.path)

        # i file di CodeMirror, serviti da strumenti/vendor/ (niente CDN: deve
        # funzionare anche senza rete)
        if pezzi.path.startswith("/vendor/"):
            relativo = pezzi.path[len("/vendor/"):]
            f = (VENDOR / relativo).resolve()
            if not str(f).startswith(str(VENDOR.resolve())) or not f.is_file():
                self.send_response(404)
                self.end_headers()
                return
            tipo = {"js": "application/javascript", "css": "text/css"}.get(
                f.suffix.lstrip("."), "application/octet-stream")
            dati = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", tipo + "; charset=utf-8")
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)
            return

        # le immagini vere di una mappa (es. risveglio-immagini/pNNN-k.png):
        # copiate da costruisci.py in sito/<id>-immagini/, non tenute in memoria
        # come le pagine — vanno servite come file statici, non c'è pronte[...].
        if re.fullmatch(r"[a-z][a-z0-9-]*-immagini/[A-Za-z0-9_.-]+\.png", pezzi.path.lstrip("/")):
            f = (SITO / pezzi.path.lstrip("/")).resolve()
            if not str(f).startswith(str(SITO.resolve())) or not f.is_file():
                self.send_response(404)
                self.end_headers()
                return
            dati = f.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(dati)))
            self.end_headers()
            self.wfile.write(dati)
            return

        if pezzi.path == "/sorgente":
            q = parse_qs(pezzi.query)
            pagina = (q.get("pagina") or [""])[0]
            sezione = (q.get("sezione") or [""])[0]
            cartella = cartella_della_pagina(pagina)
            if cartella is None or not re.fullmatch(r"[A-Za-z0-9_-]+", sezione or ""):
                return self._json({"ok": False, "errore": "richiesta non valida"})
            trovata = trova_sezione(cartella, sezione)
            if trovata is None:
                return self._json({"ok": False, "errore": f"«{sezione}» non è in sorgente/"})
            f, _, _, _, frammento = trovata
            return self._json({"ok": True, "html": frammento,
                               "file": str(f.relative_to(RADICE))})

        if pezzi.path in ("/scheda", "/struttura"):
            q = parse_qs(pezzi.query)
            pagina = (q.get("pagina") or [""])[0]
            if pezzi.path == "/struttura":
                return self._json(struttura(pagina))
            sezione = (q.get("sezione") or [""])[0]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", sezione or ""):
                return self._json({"ok": False, "errore": "richiesta non valida"})
            return self._json(leggi_scheda(pagina, sezione))

        nome = pezzi.path.lstrip("/") or "index.html"
        corpo = self.pronte.get(nome)
        if corpo is None:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"non trovata")
            return
        dati = corpo.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(dati)))
        self.end_headers()
        self.wfile.write(dati)

    def do_POST(self):
        strada = urlparse(self.path).path
        if strada not in ("/salva-sezione", "/salva-scheda", "/nuova-sezione",
                          "/anteprima-scheda"):
            self.send_response(404)
            self.end_headers()
            return
        try:
            lunghezza = int(self.headers.get("Content-Length", 0))
            dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
            if strada == "/anteprima-scheda":
                esito = anteprima_scheda(dati["pagina"], dati["sezione"], dati["scheda"])
            elif strada == "/nuova-sezione":
                esito = crea_sezione(dati["pagina"], dati.get("parte", ""),
                                     dati.get("dopo", ""), dati.get("titolo", ""),
                                     dati.get("id", ""))
            else:
                sezione = dati["sezione"]
                if not re.fullmatch(r"[A-Za-z0-9_-]+", sezione):
                    raise ValueError("id sezione non valido")
                esito = (salva_scheda(dati["pagina"], sezione, dati["scheda"])
                         if strada == "/salva-scheda"
                         else salva_sezione(dati["pagina"], sezione, dati["html"]))
        except Exception as e:
            esito = {"ok": False, "errori": [str(e)]}
        if esito.get("ok") and not esito.get("invariata") and strada != "/anteprima-scheda":
            ManoDiPagina.pronte = pagine_pronte()  # la cache serviva il testo di prima
        self._json(esito)


def main():
    porta = PORTA_DI_DEFAULT
    if "--porta" in sys.argv:
        porta = int(sys.argv[sys.argv.index("--porta") + 1])

    codice, uscita = corri("costruisci.py")
    print(uscita)
    if codice != 0:
        return codice

    ManoDiPagina.pronte = pagine_pronte()
    server = ThreadingHTTPServer(("127.0.0.1", porta), ManoDiPagina)
    url = f"http://127.0.0.1:{porta}/index.html"
    print(f"\nmodalità modifica pronta su {url}")
    print("passa il mouse su una sezione: compare la matita in alto a destra")
    print("il salvataggio scrive in sorgente/, ricostruisce e verifica")
    print("copie di sicurezza in .storico/ · Ctrl+C per chiudere\n")
    if "--zitto" not in sys.argv:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())