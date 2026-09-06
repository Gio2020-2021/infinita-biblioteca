#!/usr/bin/env python3
"""Rinumera le voci dei `part-toc` in progressione continua su tutta la pagina.

Le voci sono numerate 01→N nell'ordine in cui compaiono nel documento, senza
riguardo alla parte: inserendo una sezione a metà mappa vanno rifatti tutti i
numeri a valle. Farlo a mano è come si sono già introdotti errori (una voce
rimandava alla "sezione 30" che nel frattempo era diventata un'altra).

Controlla anche che ogni voce del sommario punti a una sezione che esiste
davvero, e nell'ordine giusto: se un numero e la posizione fisica non
coincidono, il sommario sta mentendo al lettore.

    python3 strumenti/rinumera.py            # mostra cosa cambierebbe
    python3 strumenti/rinumera.py --scrivi   # applica
"""
import re
import sys
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "sito" / "mappa-transurfing.html"
VOCE = re.compile(r'(<li><a href="#([^"]+)"><b>)(\d+)(</b>)')


SORGENTE = Path(__file__).resolve().parent.parent / "sorgente"


def applica_ai_sorgenti(numeri):
    """Riscrive le voci di sommario nei pezzi di sorgente/.

    Il file in sito/ è generato: modificarlo direttamente lo farebbe divergere
    dai sorgenti al primo `costruisci.py`. Ogni voce `<li><a href="#id"><b>NN</b>`
    è unica nel documento, quindi si può ritrovare pezzo per pezzo.
    """
    if not SORGENTE.is_dir():
        return None
    toccati = 0
    for f in sorted(SORGENTE.rglob("*.html")):
        testo = f.read_text(encoding="utf-8")

        def uno(m):
            nuovo = numeri.get(m.group(2))
            return m.group(1) + (nuovo if nuovo else m.group(3)) + m.group(4)

        nuovo_testo = VOCE.sub(uno, testo)
        if nuovo_testo != testo:
            f.write_text(nuovo_testo, encoding="utf-8")
            toccati += 1
    return toccati


def main():
    scrivi = "--scrivi" in sys.argv
    testo = FILE.read_text(encoding="utf-8")

    # ordine fisico delle sezioni nel documento
    fisico = re.findall(r'<section class="branch" id="([^"]+)"', testo)
    posizione = {s: i for i, s in enumerate(fisico)}

    cambi, problemi, ordine, numeri = [], [], [], []
    contatore = 0

    def sostituisci(m):
        nonlocal contatore
        contatore += 1
        bersaglio, vecchio = m.group(2), m.group(3)
        nuovo = f"{contatore:02d}"
        if bersaglio not in posizione:
            problemi.append(f'la voce "{bersaglio}" non ha una sezione corrispondente')
        else:
            ordine.append((posizione[bersaglio], bersaglio))
        numeri.append((bersaglio, nuovo))
        if vecchio != nuovo:
            cambi.append(f"  {bersaglio}: {vecchio} → {nuovo}")
        return m.group(1) + nuovo + m.group(4)

    risultato = VOCE.sub(sostituisci, testo)

    # il sommario deve seguire l'ordine fisico delle sezioni
    for (a, na), (b, nb) in zip(ordine, ordine[1:]):
        if b < a:
            problemi.append(f'"{nb}" viene prima di "{na}" nel documento ma dopo nel sommario')

    print(f"{contatore} voci di sommario · {len(fisico)} sezioni nel documento")
    if problemi:
        print("\nPROBLEMI:")
        for p in problemi:
            print(" ·", p)
    if not cambi:
        print("numerazione già corretta.")
        return 1 if problemi else 0

    print(f"\n{len(cambi)} numeri da correggere:")
    for c in cambi[:40]:
        print(c)
    if len(cambi) > 40:
        print(f"  … e altri {len(cambi) - 40}")

    if scrivi:
        scritti = applica_ai_sorgenti(dict(numeri))
        if scritti is None:
            FILE.write_text(risultato, encoding="utf-8")
            print("\nscritto sul file (nessuna cartella sorgente/).")
        else:
            print(f"\nscritto su {scritti} file di sorgente/ — ricostruisco.")
            import subprocess
            subprocess.run([sys.executable, str(Path(__file__).resolve().parent / "costruisci.py")], check=True)
    else:
        print("\n(prova a vuoto — rilancia con --scrivi per applicare)")
    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
