#!/usr/bin/env python3
"""Prepara la biblioteca per aprirla in locale e la apre.

    python3 strumenti/anteprima.py            costruisce e prepara
    python3 strumenti/anteprima.py --apri     e apre il portale nel browser

Cosa fa: chiama `costruisci.py`, poi avvolge ogni pagina generata nel guscio
che l'Artifact aggiunge al momento della pubblicazione (doctype, charset,
viewport, reset minimo) e la scrive in `sito/locale/`. I nomi dei file restano
gli stessi, così i rimandi fra una mappa e l'altra funzionano identici qui e là.

`sito/locale/` è usa-e-getta e non va versionata né modificata: la copia di
verità è `sorgente/`, i file in `sito/` sono generati da quella.

Nota: le capability (registro, diario, filtro dell'anima) vivono solo dentro il
visualizzatore di claude.ai. In locale non rispondono e la pagina ripiega sul
salvataggio nel browser — è previsto, non è un errore.
"""
import shutil
import subprocess
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent
SITO = RADICE / "sito"
LOCALE = SITO / "locale"

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
</body>
</html>
"""

# le pagine generate dalla costruzione; i mockup restano fuori, sono già pagine intere
def pagine():
    for p in sorted(SITO.glob("*.html")):
        if p.name.startswith("mockup-") or p.name == "anteprima-locale.html":
            continue
        yield p


def main():
    esito = subprocess.run([sys.executable, str(RADICE / "strumenti" / "costruisci.py")])
    if esito.returncode != 0:
        return esito.returncode

    if LOCALE.exists():
        shutil.rmtree(LOCALE)
    LOCALE.mkdir(parents=True)

    n = 0
    for p in pagine():
        corpo = p.read_text(encoding="utf-8")
        if "<!doctype" in corpo.lower() or "<html" in corpo.lower():
            print(f"ATTENZIONE: {p.name} contiene già doctype o <html>.")
            print("  L'Artifact lo avvolge da sé: quei tag vanno tolti prima di pubblicare.")
        (LOCALE / p.name).write_text(GUSCIO.format(corpo=corpo), encoding="utf-8")
        n += 1

    indice = LOCALE / "index.html"
    print(f"\npronto  {n} pagine in {LOCALE.relative_to(RADICE)}/")
    print(f"apri    {indice}")
    if "--apri" in sys.argv:
        subprocess.run(["open", str(indice)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
