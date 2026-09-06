#!/usr/bin/env python3
"""Riassembla sito/mappa-transurfing.html dai pezzi in sorgente/.

Il file pubblicabile resta uno solo — l'involucro dell'Artifact non ha un passo
di bundling e la CSP non ammette fogli di stile esterni — ma il sorgente è
spezzato per parte, per componente di stile e per modulo di script, così che
aggiungere un autore o un capitolo tocchi un file solo.

    python3 strumenti/costruisci.py            costruisce
    python3 strumenti/costruisci.py --controlla  dice solo se il file è allineato

REGOLA: da qui in avanti si modifica `sorgente/`, mai `sito/mappa-transurfing.html`,
che è generato. Se il file generato viene toccato a mano, `--controlla` se ne
accorge e lo dice invece di sovrascrivere in silenzio.
"""
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "sorgente"
USCITA = RADICE / "sito" / "mappa-transurfing.html"
ORDINE = SORGENTE / "ordine.txt"


def elenco():
    if not ORDINE.exists():
        sys.exit(f"manca {ORDINE.relative_to(RADICE)}")
    fuori = []
    for riga in ORDINE.read_text(encoding="utf-8").splitlines():
        riga = riga.strip()
        if not riga or riga.startswith("#"):
            continue
        p = SORGENTE / riga
        if not p.exists():
            sys.exit(f"in ordine.txt c'è {riga}, ma il file non esiste")
        fuori.append(p)
    return fuori


def componi(pezzi):
    return "\n".join(p.read_text(encoding="utf-8") for p in pezzi)


def main():
    pezzi = elenco()
    nuovo = componi(pezzi)
    vecchio = USCITA.read_text(encoding="utf-8") if USCITA.exists() else None

    if "--controlla" in sys.argv:
        if vecchio is None:
            print("il file costruito non esiste ancora")
            sys.exit(1)
        if vecchio == nuovo:
            print(f"allineato · {len(pezzi)} pezzi · {len(nuovo) // 1024} KB")
            sys.exit(0)
        print("DISALLINEATO: sito/mappa-transurfing.html non corrisponde a sorgente/.")
        print("  O è stato modificato a mano (le modifiche vanno riportate nei pezzi),")
        print("  oppure basta ricostruirlo: python3 strumenti/costruisci.py")
        # dove diverge
        a, b = vecchio.split("\n"), nuovo.split("\n")
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                print(f"  prima differenza alla riga {i + 1}:")
                print(f"    generato: {a[i][:90]}")
                print(f"    sorgente: {b[i][:90]}")
                break
        else:
            print(f"  righe: generato {len(a)}, da sorgente {len(b)}")
        sys.exit(1)

    if vecchio is not None and vecchio != nuovo:
        print("attenzione: il file esistente differisce da sorgente/ — lo sovrascrivo.")
        print("  se le modifiche erano a mano sul file generato, sono perse.")
    USCITA.write_text(nuovo, encoding="utf-8")
    invariato = " (invariato)" if vecchio == nuovo else ""
    print(f"scritto  {USCITA.relative_to(RADICE)}  ({len(nuovo) // 1024} KB, {len(pezzi)} pezzi){invariato}")


if __name__ == "__main__":
    main()
