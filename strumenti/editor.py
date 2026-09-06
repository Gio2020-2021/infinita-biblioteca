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

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "sorgente"
MAPPE = SORGENTE / "mappe"
SITO = RADICE / "sito"
STORICO = RADICE / ".storico"
PORTA_DI_DEFAULT = 8901

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
  #ed-briciola { position: fixed; bottom: 26px; left: 50%; transform: translateX(-50%);
    z-index: 320; font-family: var(--f-mono, monospace); font-size: 12px;
    padding: 10px 18px; border-radius: 4px; background: var(--surface, #1B1D27);
    border: 1px solid var(--amber, #E8A33D); color: var(--ink, #E6E4DC);
    opacity: 0; pointer-events: none; transition: opacity .2s ease }
  #ed-briciola.on { opacity: 1 }
  @media (max-width: 900px) { #ed-corpo { grid-template-columns: 1fr } #ed-destra { display: none } }
</style>
"""

SCRIPT_EDITOR = r"""
<div id="ed-velo">
  <div id="ed-scatola">
    <div id="ed-testa">
      <h3 id="ed-titolo"></h3>
      <span id="ed-dove"></span>
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

  function anteprima() {
    document.getElementById("ed-anteprima").innerHTML = document.getElementById("ed-testo").value;
  }

  function appendiMatita(sez) {
    if (sez.querySelector(".ed-matita")) return;
    sez.classList.add("ed-sez");
    var m = document.createElement("button");
    m.type = "button";
    m.className = "ed-matita";
    m.innerHTML = "✎ modifica";
    m.title = "Modifica questa sezione";
    m.addEventListener("click", function (e) { e.preventDefault(); apri(sez); });
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
    var ta = document.getElementById("ed-testo");
    ta.value = "caricamento…";
    document.getElementById("ed-velo").classList.add("on");
    fetch("/sorgente?pagina=" + encodeURIComponent(PAGINA) + "&sezione=" + encodeURIComponent(sez.id))
      .then(function (r) { return r.json(); })
      .then(function (r) {
        if (!r.ok) { esiti(r.errore || "non riesco a leggere la sezione", true); ta.value = ""; return; }
        ta.value = r.html;
        testoIniziale = r.html;
        document.getElementById("ed-dove").textContent = "#" + sez.id + " · " + r.file;
        anteprima();
        ta.focus();
        ta.setSelectionRange(0, 0);
      })
      .catch(function () { esiti("il server locale non risponde", true); });
  }

  function chiudi(forza) {
    var ta = document.getElementById("ed-testo");
    if (!forza && ta.value !== testoIniziale &&
        !confirm("Ci sono modifiche non salvate. Chiudere lo stesso?")) return;
    document.getElementById("ed-velo").classList.remove("on");
    sezioneAperta = null;
  }

  function salva() {
    if (!sezioneAperta) return;
    var testo = document.getElementById("ed-testo").value;
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
    document.getElementById("ed-testo").focus();
  });

  document.getElementById("ed-annulla").addEventListener("click", function () { chiudi(false); });
  document.getElementById("ed-salva").addEventListener("click", salva);
  document.getElementById("ed-testo").addEventListener("input", anteprima);
  document.addEventListener("keydown", function (e) {
    var aperto = document.getElementById("ed-velo").classList.contains("on");
    if (!aperto) return;
    if (e.key === "Escape") { e.preventDefault(); chiudi(false); }
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "s") { e.preventDefault(); salva(); }
  });

  document.querySelectorAll(".ed-inserti button").forEach(function (b) {
    b.addEventListener("click", function () {
      var ta = document.getElementById("ed-testo");
      var t = INSERTI[b.dataset.inserto] || "";
      var i = ta.selectionStart, j = ta.selectionEnd;
      ta.value = ta.value.slice(0, i) + t + ta.value.slice(j);
      ta.focus();
      ta.setSelectionRange(i + t.length, i + t.length);
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
            editor = STILE_EDITOR + (SCRIPT_EDITOR
                                     .replace("__PAGINA__", p.name)
                                     .replace("__EDITABILI__", json.dumps(ids)))
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
        if urlparse(self.path).path != "/salva-sezione":
            self.send_response(404)
            self.end_headers()
            return
        try:
            lunghezza = int(self.headers.get("Content-Length", 0))
            dati = json.loads(self.rfile.read(lunghezza).decode("utf-8"))
            sezione = dati["sezione"]
            if not re.fullmatch(r"[A-Za-z0-9_-]+", sezione):
                raise ValueError("id sezione non valido")
            esito = salva_sezione(dati["pagina"], sezione, dati["html"])
        except Exception as e:
            esito = {"ok": False, "errori": [str(e)]}
        if esito.get("ok") and not esito.get("invariata"):
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
