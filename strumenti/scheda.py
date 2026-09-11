#!/usr/bin/env python3
"""Legge una sezione come scheda a campi, e la ricompone.

    python3 strumenti/scheda.py --prova     mette alla prova il giro completo

È il motore dietro la modifica «senza codice» dell'editor: `analizza_sezione`
prende il frammento HTML di una sezione e ne tira fuori i campi della colonna di
sinistra (etichetta, titolo, sommario, citazione, fonte) e l'elenco dei blocchi
di quella di destra; `componi_sezione` fa il cammino inverso.

LA REGOLA CHE TIENE IN PIEDI TUTTO: non si ricostruisce, si innesta. Ogni pezzo
si porta dietro la propria posizione esatta nel frammento, e la ricomposizione
sostituisce **solo** i pezzi davvero toccati, lasciando tutto il resto identico
byte per byte — indentazione, commenti, righe vuote, andate a capo dentro i
paragrafi. Ricostruire tutto da capo, come faceva la prima stesura di questo
file, riformatterebbe l'intera sezione a ogni salvataggio: su 373 sezioni
scritte a mano in anni sarebbe un disastro silenzioso, e il progetto ha già la
regola che un rifacimento che sposta anche un solo spazio non è un rifacimento.

I blocchi che il modulo non conosce non vengono persi né rifiutati: diventano
blocchi di tipo «codice», mostrati così come sono. Si spostano e si cancellano,
e si modificano solo a mano. Sono il 4% del totale — figure con SVG scritto a
mano, tabelle, elenchi speciali.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent

VUOTI = {"img", "br", "hr", "input", "meta", "link", "source", "col", "use",
         "path", "circle", "line", "rect", "polygon", "polyline", "ellipse", "stop"}

# blocco riconosciuto -> tipo della scheda. Tutto il resto diventa «codice».
TIPI = {
    ("ul", "tree"): "voci",
    ("div", "move"): "blocco",
    ("figure", "fonte-img"): "immagine",
    ("div", "fonte-img-riga"): "riga-immagini",
    ("div", "galleria"): "galleria",
    ("p", "n-d"): "paragrafo",
    ("p", ""): "paragrafo",
}

CAMPI_ASIDE = {("span", "tag"): "etichetta", ("h2", ""): "titolo",
               ("p", "gist"): "sommario", ("p", "quote"): "citazione",
               ("p", "src"): "fonte"}


def _classe(attrs):
    c = (dict(attrs).get("class") or "").split()
    return c[0] if c else ""


class _Lettore(HTMLParser):
    """Percorre il frammento tenendo la pila dei tag e gli indici nel testo, così
    ogni pezzo si può ritagliare esatto dal sorgente."""

    def __init__(self, testo):
        super().__init__(convert_charrefs=False)
        self.testo = testo
        self.righe = [0]
        for r in testo.split("\n")[:-1]:
            self.righe.append(self.righe[-1] + len(r) + 1)
        self.pila = []
        self.eventi = []          # (tipo, tag, classe, attrs, inizio, fine, profondità)

    def _qui(self):
        riga, col = self.getpos()
        return self.righe[riga - 1] + col

    def _fine_tag(self, inizio):
        chiuso = self.testo.find(">", inizio)
        return chiuso + 1 if chiuso >= 0 else len(self.testo)

    def handle_starttag(self, tag, attrs):
        i = self._qui()
        self.eventi.append(("apre", tag, _classe(attrs), dict(attrs), i,
                            self._fine_tag(i), len(self.pila)))
        if tag not in VUOTI:
            self.pila.append(tag)

    def handle_startendtag(self, tag, attrs):
        i = self._qui()
        self.eventi.append(("apre", tag, _classe(attrs), dict(attrs), i,
                            self._fine_tag(i), len(self.pila)))

    def handle_endtag(self, tag):
        if tag in VUOTI:
            return
        while self.pila:
            if self.pila.pop() == tag:
                break
        i = self._qui()
        self.eventi.append(("chiude", tag, "", {}, i, self._fine_tag(i), len(self.pila)))


def _elemento(testo, eventi, k):
    """(contenuto interno, indice di fine dell'elemento intero)."""
    _, tag, _, _, inizio, dopo_apertura, prof = eventi[k]
    if tag in VUOTI:
        return "", dopo_apertura
    for j in range(k + 1, len(eventi)):
        t, tg, _, _, i2, f2, p2 = eventi[j]
        if t == "chiude" and tg == tag and p2 == prof:
            return testo[dopo_apertura:i2], f2
    return testo[dopo_apertura:], len(testo)


def _figure_in(testo, eventi, da, a):
    """Le <figure> comprese fra due indici."""
    fuori = []
    for k, (t, tag, cls, at, i, f, prof) in enumerate(eventi):
        if t != "apre" or tag != "figure" or not (da <= i < a):
            continue
        _, fine = _elemento(testo, eventi, k)
        grezzo = testo[i:fine]
        mi = re.search(r"<img\b[^>]*>", grezzo)
        src = alt = ""
        if mi:
            src = (re.search(r'src="([^"]*)"', mi.group(0)) or [None, ""])[1] \
                if re.search(r'src="([^"]*)"', mi.group(0)) else ""
            alt = (re.search(r'alt="([^"]*)"', mi.group(0)) or [None, ""])[1] \
                if re.search(r'alt="([^"]*)"', mi.group(0)) else ""
        mc = re.search(r"<figcaption[^>]*>(.*?)</figcaption>", grezzo, re.S)
        fuori.append({"src": src, "alt": alt,
                      "didascalia": mc.group(1).strip() if mc else "",
                      "grezzo": grezzo, "inizio": i, "fine": fine})
    return fuori


def _solo_testo(html):
    """Il testo leggibile, senza tag né spaziatura: due versioni che differiscono
    solo nell'impaginazione danno la stessa stringa."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


def _impronta(html):
    """Testo leggibile + sequenza dei tag con la loro prima classe. Confrontare
    solo il testo non basterebbe: due paragrafi fusi in uno direbbero le stesse
    parole con una struttura diversa, e la differenza salterebbe fuori solo dopo
    aver salvato."""
    tag = tuple(n + ("." + c.split()[0] if c else "")
                for n, c in re.findall(r'<(\w+)(?:[^>]*?\sclass="([^"]*)")?[^>]*>', html))
    return _solo_testo(html), tag


def _fedele(originale, generato):
    """Il generato dice davvero la stessa cosa dell'originale, e nello stesso modo?"""
    return _impronta(originale) == _impronta(generato)


def paragrafi(testo):
    """Un rigo vuoto separa un paragrafo dal successivo: è la sola convenzione di
    scrittura che la scheda chiede di conoscere."""
    return [x.strip() for x in re.split(r"\n\s*\n", testo or "") if x.strip()]


def _genera_voce(v, rientro):
    piccolo = (f' <small>{v.get("sottotitolo", "").strip()}</small>'
               if v.get("sottotitolo", "").strip() else "")
    righe = [rientro + f'<li><span class="n-t">{v.get("titolo", "").strip()}{piccolo}</span>']
    for par in paragrafi(v.get("testo", "")):
        righe.append(rientro + f'  <p class="n-d">{par}</p>')
    righe.append(rientro + "</li>")
    return "\n".join(righe)


def _rientro(testo, i):
    """Gli spazi che precedono l'indice i sulla sua riga."""
    inizio_riga = testo.rfind("\n", 0, i) + 1
    return testo[inizio_riga:i] if testo[inizio_riga:i].strip() == "" else ""


def analizza_sezione(frammento):
    """Frammento <section>…</section> -> scheda. Ogni pezzo porta i propri indici
    (`inizio`/`fine`) nel frammento: è ciò che permette di innestare invece di
    ricostruire."""
    let = _Lettore(frammento)
    let.feed(frammento)
    ev = let.eventi
    if not ev or ev[0][1] != "section":
        raise ValueError("il frammento non comincia con <section>")

    scheda = {"id": ev[0][3].get("id", ""),
              "apertura": frammento[ev[0][4]:ev[0][5]],
              "aside": {}, "blocchi": [], "lunghezza": len(frammento)}

    # --- colonna di sinistra ---
    fine_aside = None
    for k, (t, tag, cls, at, i, f, prof) in enumerate(ev):
        if t == "apre" and tag == "div" and cls == "branch-aside" and fine_aside is None:
            _, fine_aside = _elemento(frammento, ev, k)
            continue
        if fine_aside is None or i >= fine_aside:
            continue
        nome = CAMPI_ASIDE.get((tag, cls))
        if nome and nome not in scheda["aside"]:
            corpo, fine = _elemento(frammento, ev, k)
            scheda["aside"][nome] = {"html": corpo.strip(), "grezzo": frammento[i:fine],
                                     "inizio": i, "fine": fine, "tag": tag,
                                     "apertura": frammento[i:f]}

    # --- colonna di destra: la sequenza dei blocchi ---
    colonna_da = colonna_a = prof_colonna = None
    vista_aside = False
    for k, (t, tag, cls, at, i, f, prof) in enumerate(ev):
        if t == "apre" and tag == "div" and cls == "branch-aside":
            vista_aside = True
            continue
        if vista_aside and t == "apre" and tag == "div" and cls == "" and colonna_da is None:
            _, colonna_a = _elemento(frammento, ev, k)
            colonna_da, prof_colonna = f, prof + 1
            break
    if colonna_da is None:
        scheda["blocchi_da"] = scheda["blocchi_a"] = None
        return scheda

    for k, (t, tag, cls, at, i, f, prof) in enumerate(ev):
        if t != "apre" or not (colonna_da <= i < colonna_a) or prof != prof_colonna:
            continue
        corpo, fine = _elemento(frammento, ev, k)
        b = {"tipo": TIPI.get((tag, cls), "codice"), "grezzo": frammento[i:fine],
             "inizio": i, "fine": fine}

        if b["tipo"] == "voci":
            b["voci"] = []
            for k2, (t2, tag2, _c2, _a2, i2, f2, p2) in enumerate(ev):
                if not (t2 == "apre" and tag2 == "li" and i <= i2 < fine and p2 == prof + 1):
                    continue
                corpo_li, fine_li = _elemento(frammento, ev, k2)
                titolo = sottotitolo = testo = ""
                m = re.search(r'<span class="n-t">(.*?)</span>', corpo_li, re.S)
                if m:
                    ms = re.search(r"<small>(.*?)</small>", m.group(1), re.S)
                    sottotitolo = ms.group(1).strip() if ms else ""
                    titolo = re.sub(r"<small>.*?</small>", "", m.group(1), flags=re.S).strip()
                testo = "\n\n".join(x.strip() for x in
                                     re.findall(r'<p class="n-d">(.*?)</p>', corpo_li, re.S))
                b["voci"].append({"titolo": titolo, "sottotitolo": sottotitolo,
                                  "testo": testo, "grezzo": frammento[i2:fine_li],
                                  "inizio": i2, "fine": fine_li})
        elif b["tipo"] == "blocco":
            mh = re.search(r"<h3[^>]*>(.*?)</h3>", corpo, re.S)
            intero = mh.group(1) if mh else ""
            ms = re.search(r"<small>(.*?)</small>", intero, re.S)
            b["sottotitolo"] = ms.group(1).strip() if ms else ""
            b["titolo"] = re.sub(r"<small>.*?</small>", "", intero, flags=re.S).strip()
            b["testo"] = "\n\n".join(x.strip() for x in
                                      re.findall(r"<p[^>]*>(.*?)</p>", corpo, re.S))
        elif b["tipo"] == "paragrafo":
            b["testo"] = corpo.strip()
        elif b["tipo"] == "immagine":
            f0 = _figure_in(frammento, ev, i, fine + 1)
            if f0:
                b.update({x: f0[0][x] for x in ("src", "alt", "didascalia")})
        elif b["tipo"] in ("riga-immagini", "galleria"):
            b["figure"] = _figure_in(frammento, ev, i, fine)
            mh = re.search(r"<h4[^>]*>(.*?)</h4>", corpo, re.S)
            mp = re.search(r"<p[^>]*>(.*?)</p>", corpo, re.S)
            b["titolo"] = mh.group(1).strip() if mh else ""
            b["testo"] = mp.group(1).strip() if mp else ""
        # Il parser si mette alla prova da sé: rigenera il blocco dai campi che
        # ha appena estratto e controlla di riottenere lo stesso testo. Se non
        # ci riesce vuol dire che quel blocco contiene qualcosa che il modello a
        # campi non sa rappresentare (più paragrafi in una voce, un elemento
        # annidato, una forma inconsueta): declassato a «codice», si conserva
        # tale e quale invece di essere riscritto perdendo pezzi. È il motivo
        # per cui una modifica dalla scheda non può mangiarsi del contenuto.
        for v in b.get("voci", []):
            v["semplice"] = _fedele(v["grezzo"], _genera_voce(v, ""))
        if b["tipo"] != "codice" and not _fedele(b["grezzo"], genera_blocco(dict(b), "")):
            b = {"tipo": "codice", "grezzo": b["grezzo"],
                 "inizio": b["inizio"], "fine": b["fine"]}

        # la posizione di partenza: serve a riconoscere se la sequenza è stata
        # rimescolata (aggiunte, cancellazioni, spostamenti) oppure no
        b["origine"] = len(scheda["blocchi"])
        scheda["blocchi"].append(b)

    primo = scheda["blocchi"][0] if scheda["blocchi"] else None
    ultimo = scheda["blocchi"][-1] if scheda["blocchi"] else None
    scheda["blocchi_da"] = primo["inizio"] if primo else colonna_da
    scheda["blocchi_a"] = ultimo["fine"] if ultimo else colonna_da
    scheda["rientro_blocchi"] = _rientro(frammento, primo["inizio"]) if primo else " " * 10
    return scheda


# ------------------------------------------------------------------ ricomposizione

def _testo_campo(c):
    """Il campo dell'aside riscritto, conservando il suo tag di apertura (che può
    portare uno style col colore della parte)."""
    apertura = c.get("apertura") or f'<{c.get("tag", "p")}>'
    tag = c.get("tag", "p")
    return f'{apertura}{c.get("html", "").strip()}</{tag}>'


def genera_blocco(b, rientro="          "):
    """Il testo HTML di un blocco, generato da zero. Si usa solo per i blocchi
    nuovi o toccati: quelli intatti riemettono il proprio `grezzo`."""
    r, r2, r4 = rientro, rientro + "  ", rientro + "    "
    tipo = b.get("tipo")

    if tipo == "voci":
        righe = [r + '<ul class="tree">']
        for v in b.get("voci", []):
            # una voce intatta, o che il parser non sa rappresentare a campi,
            # riemette il proprio testo esatto
            if (not v.get("mod") or v.get("semplice") is False) and v.get("grezzo"):
                righe.append(r2 + v["grezzo"].strip())
                continue
            righe.append(_genera_voce(v, r2))
        righe.append(r + "</ul>")
        return "\n".join(righe)

    if tipo == "blocco":
        piccolo = (f' <small>{b.get("sottotitolo", "").strip()}</small>'
                   if b.get("sottotitolo", "").strip() else "")
        righe = [r + '<div class="move">',
                 r2 + f'<h3>{b.get("titolo", "").strip()}{piccolo}</h3>']
        for par in paragrafi(b.get("testo", "")):
            righe.append(r2 + f"<p>{par}</p>")
        righe.append(r + "</div>")
        return "\n".join(righe)

    if tipo == "paragrafo":
        return r + f'<p class="n-d">{b.get("testo", "").strip()}</p>'

    if tipo == "immagine":
        return "\n".join([r + '<figure class="fonte-img">',
                          r2 + f'<img src="{b.get("src", "")}" alt="{b.get("alt", "")}">',
                          r2 + f'<figcaption>{b.get("didascalia", "").strip()}</figcaption>',
                          r + "</figure>"])

    if tipo in ("riga-immagini", "galleria"):
        galleria = tipo == "galleria"
        righe = [r + f'<div class="{"galleria" if galleria else "fonte-img-riga"}">']
        dentro = r2
        if galleria:
            if b.get("titolo", "").strip():
                righe.append(r2 + f'<h4>{b["titolo"].strip()}</h4>')
            if b.get("testo", "").strip():
                righe.append(r2 + f'<p>{b["testo"].strip()}</p>')
            righe.append(r2 + '<div class="galleria-griglia">')
            dentro = r4
        for fig in b.get("figure", []):
            if not fig.get("mod") and fig.get("grezzo"):
                righe.append(dentro + fig["grezzo"].strip())
                continue
            cls = "" if galleria else ' class="fonte-img"'
            righe.append(dentro + f"<figure{cls}>")
            righe.append(dentro + "  " + f'<img src="{fig.get("src", "")}" alt="{fig.get("alt", "")}">')
            righe.append(dentro + "  " + f'<figcaption>{fig.get("didascalia", "").strip()}</figcaption>')
            righe.append(dentro + "</figure>")
        if galleria:
            righe.append(r2 + "</div>")
        righe.append(r + "</div>")
        return "\n".join(righe)

    return b.get("grezzo", "")


def _testo_blocco(b, rientro):
    if not b.get("mod") and b.get("grezzo"):
        return b["grezzo"]
    return genera_blocco(b, rientro).lstrip() if b.get("primo_senza_rientro") \
        else genera_blocco(b, rientro)


def componi_sezione(scheda, originale):
    """Scheda + frammento di partenza -> frammento nuovo, con innestate SOLO le
    parti toccate. Se non è stato toccato nulla torna `originale` tale e quale."""
    innesti = []                                     # (inizio, fine, testo nuovo)

    for c in scheda.get("aside", {}).values():
        if c.get("mod") and c.get("inizio") is not None:
            innesti.append((c["inizio"], c["fine"], _testo_campo(c)))

    blocchi = scheda.get("blocchi", [])
    da, a = scheda.get("blocchi_da"), scheda.get("blocchi_a")
    rientro = scheda.get("rientro_blocchi", " " * 10)

    # La sequenza è cambiata (aggiunta, cancellazione, spostamento)? Allora si
    # riscrive l'intera regione dei blocchi; altrimenti si tocca solo chi cambia.
    origini = [b.get("origine") for b in blocchi]
    sequenza_intatta = origini == list(range(len(origini)))

    if not sequenza_intatta and da is not None:
        pezzi = [_testo_blocco(b, rientro).lstrip() if k == 0 else _testo_blocco(b, rientro)
                 for k, b in enumerate(blocchi)]
        innesti.append((da, a, ("\n" + rientro).join(p.lstrip() if i else p
                                                     for i, p in enumerate(pezzi))))
    else:
        for b in blocchi:
            tocco = b.get("mod") or any(v.get("mod") for v in b.get("voci", []) or []) \
                or any(f.get("mod") for f in b.get("figure", []) or [])
            if tocco and b.get("inizio") is not None:
                innesti.append((b["inizio"], b["fine"],
                                genera_blocco(b, rientro).lstrip()))

    if not innesti:
        return originale

    fuori = originale
    for inizio, fine, testo in sorted(innesti, key=lambda x: -x[0]):
        fuori = fuori[:inizio] + testo + fuori[fine:]
    return fuori


# ------------------------------------------------------------------------- prova

def sezioni_del_progetto():
    for mappa in sorted((RADICE / "sorgente" / "mappe").iterdir()):
        for f in sorted((mappa / "parti").glob("*.html")):
            testo = f.read_text(encoding="utf-8")
            for m in re.finditer(r'<section class="branch"', testo):
                prof = 0
                for t in re.finditer(r"<section\b|</section\s*>", testo[m.start():]):
                    if t.group(0).startswith("</"):
                        prof -= 1
                        if prof == 0:
                            yield f, testo[m.start():m.start() + t.end()]
                            break
                    else:
                        prof += 1


def prova():
    tot = intatte = 0
    tipi = {}
    guasti = []

    for f, frammento in sezioni_del_progetto():
        tot += 1
        try:
            scheda = analizza_sezione(frammento)
        except Exception as e:                                        # noqa: BLE001
            guasti.append((f.name, "?", f"non si legge: {e}"))
            continue
        for b in scheda["blocchi"]:
            tipi[b["tipo"]] = tipi.get(b["tipo"], 0) + 1

        # 1. senza toccare nulla, deve tornare identico byte per byte
        if componi_sezione(scheda, frammento) == frammento:
            intatte += 1
        else:
            guasti.append((f.name, scheda["id"], "cambia pur senza modifiche"))
            continue

        # 2. marcando TUTTO come modificato, il contenuto leggibile non deve
        #    cambiare: è la prova vera dei generatori
        for c in scheda["aside"].values():
            c["mod"] = True
        for b in scheda["blocchi"]:
            if b["tipo"] != "codice":
                b["mod"] = True
        rifatto = componi_sezione(scheda, frammento)
        if _solo_testo(rifatto) != _solo_testo(frammento):
            a, b2 = _solo_testo(frammento), _solo_testo(rifatto)
            i = next((k for k, (x, y) in enumerate(zip(a, b2)) if x != y), min(len(a), len(b2)))
            guasti.append((f.name, scheda["id"],
                           f"riscritto perde contenuto · atteso …{a[max(0,i-40):i+60]!r} "
                           f"· ottenuto …{b2[max(0,i-40):i+60]!r}"))

    print(f"sezioni provate: {tot}")
    print(f"intatte senza modifiche (byte per byte): {intatte}")
    print(f"guasti: {len(guasti)}")
    print("\nblocchi riconosciuti:")
    for k, v in sorted(tipi.items(), key=lambda x: -x[1]):
        print(f"  {v:5}  {k}")
    for nome, sid, msg in guasti[:8]:
        print(f"\n  ✗ {nome} · {sid}\n    {msg}")
    return 1 if guasti else 0


if __name__ == "__main__":
    sys.exit(prova() if "--prova" in sys.argv else (print(__doc__) or 0))
