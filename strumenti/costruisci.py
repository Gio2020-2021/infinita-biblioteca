#!/usr/bin/env python3
"""Costruisce le mappe della biblioteca dai pezzi in sorgente/.

Ogni mappa è una cartella in `sorgente/mappe/` con dentro il suo `mappa.json`;
tutto ciò che non è suo viene dal `telaio/`, che è identico per ogni mappa.

    python3 strumenti/costruisci.py                 costruisce tutte le mappe
    python3 strumenti/costruisci.py transurfing     costruisce solo quella
    python3 strumenti/costruisci.py --controlla     dice solo se sono allineate

REGOLA: si modifica `sorgente/`, mai i file in `sito/`, che sono generati.
Se un file generato viene toccato a mano, `--controlla` se ne accorge e dice
a quale riga diverge, invece di sovrascrivere in silenzio.

ORDINE. `mappa.json` elenca stile e script **nell'ordine di composizione**, e
ogni nome si cerca prima in `mappe/<id>/`, poi in `telaio/`. Serve perché i
fogli propri di una mappa (il banco, il diario) stanno in mezzo a quelli
generici: senza un ordine esplicito il risultato cambierebbe.
"""
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SORGENTE = RADICE / "sorgente"
TELAIO = SORGENTE / "telaio"
MAPPE = SORGENTE / "mappe"
SITO = RADICE / "sito"


def leggi(p):
    return p.read_text(encoding="utf-8")


# ---------------------------------------------------------------- generazione
# I quattro elenchi paralleli (barra · ordine fisico · PARTI · BRANCHES) sono
# stati la trappola più costosa del progetto: dimenticarne uno non dà errori,
# la parte semplicemente non compare. Qui nascono tutti dallo stesso dato.

def voci_barra(parti):
    righe = []
    for p in parti:
        righe.append(
            f'    <li><button type="button" data-part="{p["id"]}" '
            f'style="--pc:var({p["c"]})"><i>{p["n"]}</i>{p["barra"]}</button></li>')
    return "\n".join(righe)


def elenco_parti(parti):
    return "[" + ", ".join(f'"{p["id"]}"' for p in parti) + "]"


def rami_diagramma(parti):
    righe = []
    for p in parti:
        if p.get("operativa"):
            continue          # il banco e il diario stanno nella barra, non nel diagramma
        righe.append(f'      {{ n: "{p["n"]}", t: "{p["diagramma"]}", '
                     f'id: "parte-{p["id"]}", c: "{p["c"]}" }}')
    return ",\n".join(righe)


def riempi(testo, parti):
    if "{{VOCI}}" in testo:
        testo = testo.replace("{{VOCI}}", voci_barra(parti))
    if "{{PARTI}}" in testo:
        testo = testo.replace("{{PARTI}}", elenco_parti(parti))
    if "{{BRANCHES}}" in testo:
        testo = testo.replace("{{BRANCHES}}", rami_diagramma(parti))
    return testo


def risolvi(mappa_dir, sotto, nome, est):
    """Prima il pezzo proprio della mappa, poi quello del telaio."""
    for base in (mappa_dir, TELAIO):
        p = base / sotto / f"{nome}.{est}"
        if p.exists():
            return p
    sys.exit(f"[{mappa_dir.name}] manca il pezzo {sotto}/{nome}.{est}")


def componi(mappa_dir):
    cfg = json.loads(leggi(mappa_dir / "mappa.json"))
    parti = cfg["parti"]
    pezzi = []

    def metti(p):
        pezzi.append(riempi(leggi(p), parti))

    metti(mappa_dir / "titolo.txt")
    metti(TELAIO / "corpo" / "01-apertura.html")
    for n in cfg["stile"]:
        metti(risolvi(mappa_dir, "stile", n, "css"))
    metti(TELAIO / "corpo" / "02-stile-chiuso.html")
    metti(mappa_dir / "testata.html")
    metti(TELAIO / "corpo" / "barra.html")
    metti(TELAIO / "corpo" / "03-contenuto-apre.html")
    for p in parti:
        metti(mappa_dir / "parti" / f"{p['file']}.html")
    for nome in cfg.get("coda", []):
        metti(mappa_dir / f"{nome}.html")
    metti(TELAIO / "corpo" / "04-pannelli.html")
    for n in cfg["script"]:
        metti(risolvi(mappa_dir, "script", n, "js"))
    metti(TELAIO / "corpo" / "05-chiusura.html")

    return cfg, "\n".join(pezzi), len(pezzi)


def uscita(cfg):
    # la mappa del Transurfing tiene il nome storico: è quella già pubblicata
    nome = "mappa-transurfing" if cfg["id"] == "transurfing" else cfg["id"]
    return SITO / f"{nome}.html"


def elenco_mappe(argv):
    voluti = [a for a in argv[1:] if not a.startswith("--")]
    tutte = sorted(d for d in MAPPE.iterdir() if (d / "mappa.json").exists())
    if not voluti:
        return tutte
    scelte = []
    for v in voluti:
        d = MAPPE / v
        if not (d / "mappa.json").exists():
            sys.exit(f"non c'è una mappa chiamata «{v}» in sorgente/mappe/")
        scelte.append(d)
    return scelte


def main():
    controlla = "--controlla" in sys.argv
    mappe = elenco_mappe(sys.argv)
    if not mappe:
        sys.exit("nessuna mappa in sorgente/mappe/")

    problemi = 0
    for d in mappe:
        cfg, nuovo, n = componi(d)
        fuori = uscita(cfg)
        vecchio = leggi(fuori) if fuori.exists() else None
        rel = fuori.relative_to(RADICE)

        if controlla:
            if vecchio == nuovo:
                print(f"allineata · {cfg['nome']} · {n} pezzi · {len(nuovo) // 1024} KB")
                continue
            problemi += 1
            if vecchio is None:
                print(f"DA COSTRUIRE · {cfg['nome']} · {rel} non esiste")
                continue
            print(f"DISALLINEATA · {cfg['nome']} · {rel} non corrisponde a sorgente/")
            a, b = vecchio.split("\n"), nuovo.split("\n")
            for i in range(min(len(a), len(b))):
                if a[i] != b[i]:
                    print(f"  prima differenza alla riga {i + 1}:")
                    print(f"    generato: {a[i][:88]}")
                    print(f"    sorgente: {b[i][:88]}")
                    break
            else:
                print(f"  righe: generato {len(a)}, da sorgente {len(b)}")
            continue

        if vecchio is not None and vecchio != nuovo:
            print(f"  ({cfg['nome']}: il file esistente differiva da sorgente/, lo sovrascrivo)")
        fuori.write_text(nuovo, encoding="utf-8")
        uguale = " (invariato)" if vecchio == nuovo else ""
        print(f"scritta  {rel}  ({len(nuovo) // 1024} KB, {n} pezzi){uguale}")

    return 1 if problemi else 0


if __name__ == "__main__":
    sys.exit(main())
