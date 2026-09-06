#!/usr/bin/env python3
"""
Estrae il testo dai PDF e lo salva in testi/ come .txt leggibile.

    python3 strumenti/estrai.py                     # tutti i PDF non ancora estratti
    python3 strumenti/estrai.py --tutti             # ri-estrae tutto, anche l'esistente
    python3 strumenti/estrai.py "un libro.pdf"      # solo quel file

Cerca i PDF in pdf-sorgenti/ e, se non li trova lì, in ~/Downloads/KLOD NAGAL/.
Ogni pagina resta marcata con "=== PAGINA n ===" così le citazioni
restano rintracciabili nel PDF originale.

Richiede pypdf (già presente su questa macchina):  python3 -m pip install pypdf
"""

import os
import re
import sys
import textwrap
import unicodedata

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALI = os.path.join(RADICE, "pdf-sorgenti")
ESTERNI = os.path.expanduser("~/Downloads/KLOD NAGAL")
USCITA = os.path.join(RADICE, "testi")
COLONNA = 110


def slug(nome):
    base = os.path.splitext(os.path.basename(nome))[0]
    base = unicodedata.normalize("NFKD", base).encode("ascii", "ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+", "-", base).strip("-").lower()
    return re.sub(r"-+", "-", base)


def cartelle_pdf():
    for d in (LOCALI, ESTERNI):
        if os.path.isdir(d):
            yield d


def trova(nome=None):
    visti = set()
    for d in cartelle_pdf():
        for f in sorted(os.listdir(d)):
            if not f.lower().endswith(".pdf"):
                continue
            if nome and nome.lower() not in f.lower():
                continue
            if f in visti:          # pdf-sorgenti/ ha la precedenza
                continue
            visti.add(f)
            yield os.path.join(d, f)


def estrai(percorso):
    from pypdf import PdfReader

    lettore = PdfReader(percorso)

    pagine = []
    for pagina in lettore.pages:
        testo = pagina.extract_text() or ""
        righe = []
        for riga in testo.split("\n"):
            riga = " ".join(riga.split())
            if riga:
                righe.extend(textwrap.wrap(riga, COLONNA))
        pagine.append(righe)

    # Alcune scansioni (i Zeland di Macro, per esempio) emettono ogni pagina due
    # volte di fila: raddoppiano il file senza aggiungere una parola. Le pagine
    # consecutive identiche si collassano in una, e la numerazione viene rifatta
    # in modo che "=== PAGINA n ===" resti il numero reale della pagina scansionata.
    # Soglia larga: in un libro normale due pagine consecutive identiche non
    # esistono quasi mai, quindi anche il 40% è già la prova del raddoppio, e
    # copertine vuote o un'ultima pagina spaiata non fanno fallire il controllo.
    doppioni = sum(1 for a, b in zip(pagine, pagine[1:]) if a and a == b)
    piene = len([p for p in pagine if p]) or 1
    doppiate = doppioni / piene >= 0.40
    if doppiate:
        tenute, precedente = [], None
        for p in pagine:
            if p and p == precedente:
                precedente = None      # consuma la coppia, non collassa terzetti
                continue
            tenute.append(p)
            precedente = p
        pagine = tenute

    righe = []
    for i, p in enumerate(pagine, 1):
        righe.append("=== PAGINA %d ===" % i)
        righe.extend(p)
    return "\n".join(righe) + "\n", len(pagine), doppiate


def main():
    argomenti = [a for a in sys.argv[1:]]
    forza = "--tutti" in argomenti
    argomenti = [a for a in argomenti if not a.startswith("--")]
    filtro = argomenti[0] if argomenti else None

    os.makedirs(USCITA, exist_ok=True)
    trovati = list(trova(filtro))
    if not trovati:
        print("Nessun PDF trovato. Mettili in pdf-sorgenti/ oppure in %s" % ESTERNI)
        return 1

    for percorso in trovati:
        destinazione = os.path.join(USCITA, slug(percorso) + ".txt")
        if os.path.exists(destinazione) and not forza:
            print("  salto   %s (già estratto)" % os.path.basename(destinazione))
            continue
        try:
            testo, pagine, doppiate = estrai(percorso)
        except Exception as errore:                      # PDF rotto o cifrato
            print("  ERRORE  %s → %s" % (os.path.basename(percorso), errore))
            continue
        with open(destinazione, "w") as f:
            f.write(testo)
        utili = len([r for r in testo.split("\n") if not r.startswith("=== PAGINA")])
        print("  estratto %-44s %3d pagine, %5d righe%s" %
              (os.path.basename(destinazione), pagine, utili,
               "  (pagine doppie collassate)" if doppiate else ""))
        if utili < pagine:
            print("           ATTENZIONE: pochissimo testo, forse è un PDF scansionato")
    return 0


if __name__ == "__main__":
    sys.exit(main())
