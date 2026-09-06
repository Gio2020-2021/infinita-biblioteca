#!/usr/bin/env python3
"""Controlli sulla mappa prima di pubblicare.

Verifica che i tre elenchi paralleli coincidano (barra delle parti, ordine
fisico dei contenitori, array del diagramma), che ogni link interno abbia
un bersaglio, che non ci siano id duplicati e che i tag si chiudano.
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "sito" / "mappa-transurfing.html"
VUOTI = {"br", "hr", "img", "input", "meta", "link", "source", "circle",
         "line", "rect", "path", "use", "col", "area", "track", "wbr"}


class Bilancia(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pila = []
        self.errori = []

    def handle_starttag(self, tag, attrs):
        if tag not in VUOTI:
            self.pila.append((tag, self.getpos()))

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_endtag(self, tag):
        if tag in VUOTI:
            return
        if not self.pila:
            self.errori.append(f"</{tag}> senza apertura, riga {self.getpos()[0]}")
            return
        if self.pila[-1][0] != tag:
            aperto, pos = self.pila[-1]
            self.errori.append(
                f"</{tag}> alla riga {self.getpos()[0]} chiude <{aperto}> aperto alla riga {pos[0]}")
            for i in range(len(self.pila) - 1, -1, -1):
                if self.pila[i][0] == tag:
                    del self.pila[i:]
                    return
            return
        self.pila.pop()


def main():
    testo = FILE.read_text(encoding="utf-8")
    problemi = []

    # 1. id duplicati
    ids = re.findall(r'\sid="([^"]+)"', testo)
    doppi = sorted({i for i in ids if ids.count(i) > 1})
    if doppi:
        problemi.append(f"id duplicati: {doppi}")

    # 2. i quattro elenchi paralleli (il quarto, PARTI nel JS dello switcher, è
    # passato inosservato una volta: senza di esso una parte nuova resta nel DOM
    # ma mostra("nome") non le assegna mai la classe "on")
    barra = re.findall(r'<button type="button" data-part="([^"]+)"', testo)
    fisico = re.findall(r'<div class="part" id="parte-([^"]+)"', testo)
    diagramma = re.findall(r'id:\s*"parte-([^"]+)"', testo)
    m_parti = re.search(r'var PARTI\s*=\s*\[([^\]]*)\]', testo)
    switcher = re.findall(r'"([^"]+)"', m_parti.group(1)) if m_parti else None

    # il diagramma radiale elenca le parti di dottrina: le parti operative
    # (il banco e il diario) hanno un bottone nella barra ma non un nodo
    OPERATIVE = {"casa", "diario"}

    if barra != fisico:
        problemi.append(f"barra != ordine fisico\n  barra:  {barra}\n  fisico: {fisico}")
    if diagramma != [p for p in fisico if p not in OPERATIVE]:
        problemi.append(f"diagramma != parti di contenuto\n  diagramma: {diagramma}")
    if switcher is None:
        problemi.append("non trovo l'array PARTI nello switcher JS")
    elif switcher != fisico:
        problemi.append(f"PARTI (switcher JS) != ordine fisico\n  PARTI:  {switcher}\n  fisico: {fisico}")

    # 3. ogni link interno ha un bersaglio (solo nel markup: dentro <script>
    # può comparire lo stesso pattern come stringa JS, non è un vero link)
    fuori_script = re.sub(r'<script.*?</script>', ' ', testo, flags=re.S)
    ancore = set(ids)
    for href in sorted(set(re.findall(r'href="#([^"]+)"', fuori_script))):
        if href not in ancore:
            problemi.append(f'link "#{href}" senza bersaglio')

    # 4. ogni sezione .branch sta dentro una parte, e in una sola
    # (per posizione: da un marcatore di parte al successivo, non per indentazione
    # — il file viene riformattato dall'editor e i pattern basati su "\n</div>\n"
    # letterale si sono già rotti una volta)
    marcatori = list(re.finditer(r'<div class="part" id="parte-([^"]+)"', testo))
    conteggio = {}
    for i, m in enumerate(marcatori):
        nome = m.group(1)
        fine = marcatori[i + 1].start() if i + 1 < len(marcatori) else len(testo)
        fetta = testo[m.end():fine]
        for s in re.findall(r'<section class="branch" id="([^"]+)"', fetta):
            conteggio.setdefault(s, []).append(nome)
    tutte = set(re.findall(r'<section class="branch" id="([^"]+)"', testo))
    orfane = tutte - set(conteggio)
    if orfane:
        problemi.append(f"sezioni fuori da ogni parte: {sorted(orfane)}")
    multiple = {k: v for k, v in conteggio.items() if len(v) > 1}
    if multiple:
        problemi.append(f"sezioni in più parti: {multiple}")

    # 5. bilanciamento dei tag
    b = Bilancia()
    b.feed(testo)
    if b.pila:
        b.errori.append("mai chiusi: " + ", ".join(f"<{t}> riga {p[0]}" for t, p in b.pila))
    problemi += b.errori[:12]

    # 6. la regola dell'involucro (tollerante alla riformattazione dell'editor:
    # cerca la regola per struttura, non per stringa letterale con spazi fissi)
    if not re.search(r'\[hidden\]\s*\{\s*display\s*:\s*none\s*!important', testo):
        problemi.append("manca la regola [hidden] — il pannello del rituale non si chiuderà in locale")

    print(f"{FILE.name}: {len(testo)//1024} KB · {len(fisico)} parti · {len(tutte)} sezioni")
    if problemi:
        print("\nPROBLEMI:")
        for p in problemi:
            print(" ·", p)
        sys.exit(1)
    print("tutto coerente.")


if __name__ == "__main__":
    main()
