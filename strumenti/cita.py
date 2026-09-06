#!/usr/bin/env python3
"""Verifica le citazioni del sito contro i testi originali, e ne trova la pagina.

La convenzione del progetto dice che le frasi fra virgolette basse sono
letterali. Questo strumento lo controlla davvero: prende ogni «…» della pagina,
la cerca in tutti i libri letti, e dice dove sta — libro e numero di pagina, dai
marcatori `=== PAGINA n ===` prodotti da estrai.py.

Tre esiti, in ordine di gravità:

  ATTRIBUITA MALE   la frase esiste, ma in un libro che quella sezione non
                    dichiara fra le sue fonti. È il caso peggiore, perché il
                    lettore attribuisce la citazione al primo libro dell'elenco.
  NON TROVATA       nessun libro la contiene alla lettera. O è una sintesi
                    messa fra virgolette (da correggere), o è vol. III, che
                    essendo ricostruito via OCR non combacia mai carattere per
                    carattere: per questo c'è la ricerca approssimata, che
                    propone il passo più simile e quanto lo è.
  TROVATA           libro e pagina. Da qui si possono mettere i riferimenti
                    precisi nel sito.

    python3 strumenti/cita.py                 # solo i problemi
    python3 strumenti/cita.py --tutte         # anche le citazioni a posto
    python3 strumenti/cita.py --pagine        # elenco «sezione → libro, pag.»
"""
import difflib
import re
import sys
import unicodedata
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SITO = RADICE / "sito" / "mappa-transurfing.html"
TESTI = RADICE / "testi"

# nome leggibile -> file, e le sigle con cui il sito lo può dichiarare in `src`
LIBRI = [
    ("Zeland vol. I", "1-reality-transurfing-lo-spazio-delle-varianti-vadim-zeland.txt",
     [r"vol\.?\s*1\b", r"vol\.?\s*i\b(?!i)"]),
    ("Zeland vol. II", "2-reality-transurfing-fruscio-delle-stelle-del-mattino-vadim-zeland.txt",
     [r"vol\.?\s*2\b", r"vol\.?\s*ii\b(?!i)"]),
    ("Zeland vol. III", "3-reality-transurfing-avanti-nel-passato-vadim-zeland.txt",
     [r"vol\.?\s*3\b", r"vol\.?\s*iii\b"]),
    ("Zeland vol. IV-V", "reality-transurfing-le-regole-dello-specchio-vadim-zeland.txt",
     [r"vol\.?\s*4\b", r"vol\.?\s*iv\b", r"vol\.?\s*5\b", r"vol\.?\s*v\b(?!i)", r"specchio", r"mele"]),
    ("Transurfing Vivo", "transurfing-vivo-vadim-zeland.txt",
     [r"transurfing vivo", r"\bvivo\b", r"4\.0"]),
    ("Scardinare", "reality-transurfing-5-0-scardinare-il-sistema-tecnogeno-vadim-zeland.txt",
     [r"scardinare", r"tecnogen"]),
    ("Tafti la Sacerdotessa", "tafti-la-sacerdotessa-camminando-dal-vivo-in-un-film-vadim-zeland.txt",
     [r"tafti la sacerdotessa", r"sacerdotessa(?!\s+itfat)"]),
    ("La Sacerdotessa Itfat", "la-sacerdotessa-itfat-vadim-zeland.txt",
     [r"itfat"]),
    ("Cosa non ha detto Tafti", "cosa-non-ha-detto-tafti-vadim-zeland.txt",
     [r"cosa non ha detto"]),
    ("Nagal · Hackerare", "transurfing-hackerare.txt", [r"nagal\s*1", r"hackerare", r"\bnagal\b"]),
    ("Nagal · Ologramma", "surfare-nell-ologramma.txt", [r"nagal\s*2", r"ologramma", r"\bnagal\b"]),
    ("Nagal · Cosa ci ha detto", "cosa-ci-ha-detto-tafti.txt",
     [r"nagal\s*3", r"cosa ci ha detto", r"\bnagal\b"]),
]

MIN_CAR = 30      # sotto questa lunghezza una citazione è troppo generica
SOMIGLIANZA = .72  # soglia della ricerca approssimata


def norm(s):
    # l'apostrofo va neutralizzato PRIMA di buttare via il non-ASCII: quello
    # tipografico (’) sparirebbe del tutto, incollando le parole — «l’anima»
    # diventerebbe «lanima» nel libro e «l anima» nel sito, e non combacerebbero
    s = s.replace("\u2019", " ").replace("\u2018", " ").replace("'", " ")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def carica_libri():
    """Per ogni libro: il testo normalizzato di seguito, e da quale pagina
    viene ogni carattere di quel testo."""
    fuori = []
    for nome, f, sigle in LIBRI:
        p = TESTI / f
        if not p.exists():
            continue
        # le scansioni spezzano le parole a fine riga con un trattino
        # («men-\nmo cosi»): ricucirle prima di normalizzare, o metà delle
        # citazioni dei volumi OCR non si trova mai
        grezzo = p.read_text(encoding="utf-8")
        grezzo = re.sub(r"[-\u2010\u2011]\n(?!=== PAGINA)", "", grezzo)

        pezzi, pagine, pagina, lung = [], [], 0, 0
        for riga in grezzo.split("\n"):
            m = re.match(r"=== PAGINA (\d+) ===", riga)
            if m:
                pagina = int(m.group(1))
                continue
            n = norm(riga)
            if not n:
                continue
            pagine.append((lung, pagina))
            pezzi.append(n)
            lung += len(n) + 1
        fuori.append({"nome": nome, "sigle": sigle, "testo": " ".join(pezzi), "pagine": pagine})
    return fuori


def pagina_di(libro, pos):
    ultima = 0
    for inizio, pag in libro["pagine"]:
        if inizio > pos:
            break
        ultima = pag
    return ultima


def sezioni_del_sito():
    """(id sezione, titolo, fonte dichiarata, [citazioni]) per ogni sezione."""
    t = SITO.read_text(encoding="utf-8")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S)
    tagli = list(re.finditer(r'<section class="branch" id="([^"]+)"', t))
    fuori = []
    for i, m in enumerate(tagli):
        # la sezione finisce al suo </section>: fermarsi alla sezione .branch
        # successiva le farebbe inghiottire quello che sta in mezzo — fra la
        # Parte VIII e i Riferimenti c'è la galleria delle 46 storie, e le sue
        # citazioni finivano tutte attribuite all'ultima sezione precedente
        chiusura = t.find("</section>", m.end())
        prossima = tagli[i + 1].start() if i + 1 < len(tagli) else len(t)
        fine = min(chiusura if chiusura > 0 else prossima, prossima)
        blocco = t[m.end():fine]
        titolo = re.search(r"<h2>(.*?)</h2>", blocco, re.S)
        src = re.search(r'<p class="src">(.*?)</p>', blocco, re.S)
        spoglia = lambda x: re.sub(r"\s+", " ", re.sub("<[^>]+>", "", x)).strip()
        citazioni = [spoglia(c) for c in re.findall(r"«(.*?)»", blocco, re.S)]
        fuori.append({
            "id": m.group(1),
            "titolo": spoglia(titolo.group(1)) if titolo else "",
            "src": spoglia(src.group(1)) if src else "",
            "citazioni": [c for c in citazioni if len(c) >= MIN_CAR],
        })
    return fuori


def libri_dichiarati(src, libri):
    n = norm(src)
    return [l for l in libri if any(re.search(s, n) for s in l["sigle"])]


def cerca(frase, libri):
    ago = norm(frase)
    for l in libri:
        pos = l["testo"].find(ago)
        if pos >= 0:
            return l, pagina_di(l, pos), 1.0
    return None, None, 0.0


def cerca_simile(frase, libri):
    """Per l'OCR e le citazioni ritoccate: il passo più somigliante.

    Confrontare finestra per finestra tutto il corpus è impraticabile (mezzo
    milione di caratteri per libro). Si parte invece dalle parole lunghe della
    frase, che nell'OCR hanno buone probabilità di essere sopravvissute intatte:
    si cercano quelle, e solo intorno alle loro posizioni si misura la
    somiglianza vera."""
    ago = norm(frase)
    parole = sorted(set(w for w in ago.split() if len(w) >= 6), key=len, reverse=True)[:4]
    if not parole:
        return (None, None, 0.0)
    meglio = (None, None, 0.0)
    for l in libri:
        testo = l["testo"]
        posizioni = set()
        for w in parole:
            i, quante = testo.find(w), 0
            while i >= 0 and quante < 60:
                posizioni.add(max(0, i - len(ago) // 2))
                i, quante = testo.find(w, i + 1), quante + 1
        for i in posizioni:
            finestra = testo[i:i + int(len(ago) * 1.5)]
            m = difflib.SequenceMatcher(None, ago, finestra)
            if m.quick_ratio() < SOMIGLIANZA:
                continue
            r = m.ratio()
            if r > meglio[2]:
                meglio = (l, pagina_di(l, i + len(ago) // 2), r)
    return meglio if meglio[2] >= SOMIGLIANZA else (None, None, 0.0)


def main():
    tutte = "--tutte" in sys.argv
    solo_pagine = "--pagine" in sys.argv

    libri = carica_libri()
    sezioni = sezioni_del_sito()
    trovate, male, perse = [], [], []

    ocr = []
    for s in sezioni:
        dichiarati = libri_dichiarati(s["src"], libri)
        for c in s["citazioni"]:
            # 1. alla lettera, nei libri che la sezione dichiara
            l, pag, _ = cerca(c, dichiarati) if dichiarati else (None, None, 0)
            if l:
                trovate.append((s, c, l, pag))
                continue
            # 2. approssimata, sempre nei libri dichiarati: il vol. III è
            #    ricostruito via OCR e non combacia mai carattere per carattere,
            #    quindi va confrontato così o sarebbe sempre un falso allarme
            if dichiarati:
                l, pag, r = cerca_simile(c, dichiarati)
                if l:
                    ocr.append((s, c, l, pag, r))
                    continue
            # 3. alla lettera, ma in un libro che la sezione non dichiara.
            #    Se però la sezione non dichiara nessun libro riconoscibile —
            #    le sezioni trasversali citano più libri e lo dicono nel testo —
            #    non c'è niente da contraddire: vale come trovata.
            l, pag, _ = cerca(c, libri)
            if l:
                (trovate if not dichiarati else male).append((s, c, l, pag))
                continue
            perse.append((s, c))

    totale = len(trovate) + len(ocr) + len(male) + len(perse)
    print(f"{totale} citazioni in {len(sezioni)} sezioni")
    print(f"  {len(trovate):>4} alla lettera, nel libro dichiarato")
    print(f"  {len(ocr):>4} riconosciute a meno dell'OCR, nel libro dichiarato")
    print(f"  {len(male):>4} ATTRIBUITE MALE — esistono, ma in un altro libro")
    print(f"  {len(perse):>4} non trovate da nessuna parte\n")

    if solo_pagine:
        for s, c, l, pag in trovate + [(a, b, c2, d) for a, b, c2, d, _ in ocr]:
            print(f"#{s['id']:<18} {l['nome']:<24} pag. {pag:>4}   «{c[:60]}…»")
        return 0

    if male:
        print("ATTRIBUITE MALE — la frase esiste, ma non nel libro dichiarato:")
        for s, c, l, pag in male:
            print(f"\n  #{s['id']} — {s['titolo']}")
            print(f"    dichiara: {s['src']}")
            print(f"    ma sta in: {l['nome']}, pag. {pag}")
            print(f"    «{c[:110]}…»")
        print()

    if perse:
        print("NON TROVATE ALLA LETTERA — cerco il passo più simile:")
        for s, c in perse:
            l, pag, r = cerca_simile(c, libri)
            print(f"\n  #{s['id']} — {s['titolo']}")
            print(f"    «{c[:110]}…»")
            if l:
                print(f"    simile al {r:.0%} in {l['nome']}, pag. {pag}"
                      f"{'  → probabile OCR' if 'III' in l['nome'] else '  → citazione da rivedere'}")
            else:
                print("    nessun passo somigliante: probabile sintesi messa fra virgolette")
        print()

    if tutte:
        print("LOCALIZZATE:")
        for s, c, l, pag in trovate:
            print(f"  #{s['id']:<18} {l['nome']:<24} pag. {pag:>4}")

    if not male and not perse:
        print("tutte le citazioni sono letterali e nel libro dichiarato.")
    return 1 if male else 0


if __name__ == "__main__":
    sys.exit(main())
