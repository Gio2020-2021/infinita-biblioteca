#!/usr/bin/env python3
"""Ricompone sito/mappa-transurfing.html nella struttura a otto parti.

Prende la prosa già esistente (che resta la copia di verità) e la ridispone
dentro i contenitori .part, inserendo le sezioni nuove scritte a parte.
Si esegue una volta sola: dopo, il file assemblato torna a essere l'originale
da modificare a mano.
"""
import re
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "sito" / "mappa-transurfing.html"


def leggi(p):
    return Path(p).read_text(encoding="utf-8")


def taglia(testo, inizio, fine, nome):
    i = testo.find(inizio)
    if i < 0:
        sys.exit(f"non trovo l'inizio di {nome}")
    j = testo.find(fine, i)
    if j < 0:
        sys.exit(f"non trovo la fine di {nome}")
    return testo[i:j + len(fine)]


def main():
    frammenti = Path(sys.argv[1])
    src = leggi(SORGENTE)

    # --- pezzi dell'originale -------------------------------------------
    testa = taglia(src, "<title>", "</style>", "testa")
    banco = taglia(src, '<section class="deck" id="banco">', "\n</section>", "banco")
    nucleo = taglia(src, '<div class="core">', "</div>\n\n<section class=\"diagram-sec\"", "nucleo")
    nucleo = nucleo[: nucleo.rfind("</div>") + len("</div>")]
    veil = taglia(src, '<div class="veil" id="veil" hidden>', "\n</div>", "veil")
    script = taglia(src, "<script>", "</script>", "script")

    rami = {}
    for m in re.finditer(r'<section class="branch" id="([^"]+)".*?\n</section>', src, re.S):
        rami[m.group(1)] = m.group(0)

    attesi = ["varianti", "corrente", "pendoli", "equilibrio", "imbuto", "onda",
              "anima", "leggi", "terreno", "tecniche", "treccina", "algoritmo",
              "trappola", "limiti", "fonte", "errori", "glossario"]
    mancanti = [r for r in attesi if r not in rami]
    if mancanti:
        sys.exit(f"rami mancanti nell'originale: {mancanti}")

    # --- pezzi nuovi ------------------------------------------------------
    css_nuovo = leggi(frammenti / "frag_css.css")
    top = leggi(frammenti / "frag_top.html")
    diagramma = leggi(frammenti / "frag_diagram.html")
    footer = leggi(frammenti / "frag_footer.html")
    gloss_extra = leggi(frammenti / "frag_gloss.html")

    teste = {}
    for blocco in leggi(frammenti / "frag_parts.html").split("@@"):
        if not blocco.strip():
            continue
        nome, _, corpo = blocco.partition("\n")
        teste[nome.strip()] = corpo

    def nuovo(nome):
        return leggi(frammenti / f"new_{nome}.html")

    for chiave in ("specchio", "sogni", "insicurezza", "finialtrui", "stereotipi",
                   "marionette", "intenzione", "mago", "energia", "diapositive",
                   "transfer", "fini", "freiling", "lavoro", "lettere",
                   "coordinazione", "mele", "transazione", "inversione",
                   "modello", "condizioni"):
        rami[chiave] = nuovo(chiave)

    # il glossario si allunga con i termini dei volumi II e III
    rami["glossario"] = rami["glossario"].replace(
        "      </dl>", gloss_extra + "      </dl>", 1)

    # --- composizione -----------------------------------------------------
    # innesti: materiale nuovo che entra in sezioni già esistenti
    innesti = {
        "intenzione": "ins_intenzione.html",
        "energia": "ins_energia.html",
        "imbuto": "ins_imbuto.html",
        "corrente": "ins_corrente.html",
        "diapositive": "ins_diapositive.html",
        "fini": "ins_fini.html",
        "pendoli": "ins_pendoli.html",
    }
    coda = "    </div>\n  </div>\n</section>"
    for chiave, nome in innesti.items():
        blocco = leggi(frammenti / nome)
        corpo = rami[chiave].rstrip()
        if not corpo.endswith(coda):
            sys.exit(f"coda inattesa nella sezione {chiave}: non so dove innestare")
        rami[chiave] = corpo[: -len(coda)] + blocco + coda

    struttura = [
        ("terreno", "--blue", ["varianti", "corrente", "sogni", "anima", "specchio"]),
        ("avversario", "--rust", ["pendoli", "marionette", "equilibrio", "imbuto",
                                  "insicurezza", "finialtrui", "stereotipi"]),
        ("forze", "--sage", ["intenzione", "mago", "onda", "energia", "leggi"]),
        ("officina", "--amber", ["diapositive", "transfer", "fini", "terreno",
                                 "tecniche", "treccina", "algoritmo"]),
        ("altri", "--sage", ["freiling", "lavoro", "lettere"]),
        ("coordinazione", "--amber", ["coordinazione", "mele", "transazione", "inversione"]),
        ("aneddoti", "--plum", []),
        ("riferimenti", "--blue", ["modello", "trappola", "errori", "limiti",
                                   "condizioni", "fonte", "glossario"]),
    ]

    out = [testa.replace("</style>", css_nuovo + "</style>")]
    out.append('\n<script>document.documentElement.className+=" js";</script>\n')
    out.append(top)
    out.append(banco + "\n\n" + nucleo + "\n\n" + diagramma + "\n</div>\n")

    for nome, colore, elenco in struttura:
        out.append(f'\n<!-- ============================================================ PARTE · {nome.upper()} -->\n')
        out.append(f'<div class="part" id="parte-{nome}" style="--pc:var({colore})">\n')
        out.append(teste[nome])
        if nome == "aneddoti":
            out.append(nuovo("aneddoti"))
        for r in elenco:
            out.append("\n" + rami[r] + "\n")
        out.append("</div>\n")

    out.append('\n</div>\n\n<div class="perf" role="presentation"></div>\n\n')
    out.append(footer)
    out.append("\n<!-- rituale -->\n" + veil + "\n\n")
    out.append(patch_script(script))

    dest = SORGENTE
    dest.write_text("".join(out), encoding="utf-8")
    print(f"scritto {dest} — {dest.stat().st_size // 1024} KB")


def patch_script(script):
    nodi = """  var BRANCHES = [
    {n:"I",    t:"IL TERRENO",     id:"parte-terreno",       c:"--blue"},
    {n:"II",   t:"COSA TI SOTTRAE",id:"parte-avversario",    c:"--rust"},
    {n:"III",  t:"COSA HAI TU",    id:"parte-forze",         c:"--sage"},
    {n:"IV",   t:"L'OFFICINA",     id:"parte-officina",      c:"--amber"},
    {n:"V",    t:"GLI ALTRI",      id:"parte-altri",         c:"--sage"},
    {n:"VI",   t:"COORDINAZIONE",  id:"parte-coordinazione", c:"--amber"},
    {n:"VII",  t:"LE STORIE",      id:"parte-aneddoti",      c:"--plum"},
    {n:"VIII", t:"RIFERIMENTI",    id:"parte-riferimenti",   c:"--blue"}
  ];"""
    script, n = re.subn(r"  var BRANCHES = \[.*?\n  \];", nodi, script, count=1, flags=re.S)
    if n != 1:
        sys.exit("non ho potuto sostituire l'array BRANCHES")

    switcher = r"""
  /* ---------- commutatore delle parti ---------- */
  var PARTI = ["casa","terreno","avversario","forze","officina","altri","coordinazione","aneddoti","riferimenti"];
  var bottoni = Array.prototype.slice.call(document.querySelectorAll("nav.parts button"));
  var barra = document.querySelector("nav.parts");

  function partediEl(el){
    while (el && el !== document.body) {
      if (el.classList && el.classList.contains("part")) return el;
      el = el.parentNode;
    }
    return null;
  }
  function allaBarra(){
    if (!barra) return;
    window.scrollTo(0, barra.offsetTop);
  }
  function mostra(nome){
    var ok = false;
    PARTI.forEach(function(p){
      var el = document.getElementById("parte-" + p);
      if (!el) return;
      var acceso = (p === nome);
      el.classList.toggle("on", acceso);
      if (acceso) ok = true;
    });
    bottoni.forEach(function(b){
      b.setAttribute("aria-current", b.getAttribute("data-part") === nome ? "true" : "false");
    });
    return ok;
  }
  function segna(hash){
    try { history.replaceState(null, "", hash); } catch (e) { /* sandbox */ }
  }
  function instrada(hash, primaVolta){
    var id = (hash || "").replace(/^#/, "");
    if (!id) { mostra("casa"); return; }
    if (id.indexOf("parte-") === 0) {
      if (mostra(id.slice(6))) { if (!primaVolta) allaBarra(); }
      else mostra("casa");
      return;
    }
    var bersaglio = document.getElementById(id);
    if (!bersaglio) { mostra("casa"); return; }
    var p = partediEl(bersaglio);
    mostra(p ? p.id.replace("parte-", "") : "casa");
    requestAnimationFrame(function(){
      bersaglio.scrollIntoView({behavior: primaVolta ? "auto" : "smooth", block: "start"});
    });
  }

  bottoni.forEach(function(b){
    b.addEventListener("click", function(){
      var nome = b.getAttribute("data-part");
      mostra(nome);
      allaBarra();
      segna("#parte-" + nome);
    });
  });
  if (gN) {
    gN.addEventListener("click", function(ev){
      var a = ev.target.closest ? ev.target.closest("a") : null;
      if (!a) return;
      var h = a.getAttribute("href") || "";
      if (h.indexOf("#parte-") !== 0) return;
      ev.preventDefault();
      mostra(h.slice(7));
      allaBarra();
      segna(h);
    });
  }
  window.addEventListener("hashchange", function(){ instrada(location.hash, false); });
  instrada(location.hash, true);

"""
    chiusura = "\n})();"
    if not script.rstrip().endswith("})();\n</script>") and "})();" not in script:
        sys.exit("chiusura dell'IIFE non trovata")
    i = script.rfind("})();")
    return script[:i] + switcher + script[i:]


if __name__ == "__main__":
    main()
