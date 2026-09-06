#!/usr/bin/env python3
"""
Crea sito/anteprima-locale.html: la pagina avvolta come fa l'Artifact al momento
della pubblicazione (doctype, charset, viewport, reset minimo), così aprendola
in locale si vede esattamente quello che vedranno gli altri.

    python3 strumenti/anteprima.py
    python3 strumenti/anteprima.py --apri     # e la apre nel browser

Il file generato è usa-e-getta: la copia di verità resta sito/mappa-transurfing.html,
ed è quella che si pubblica. Non modificare mai l'anteprima.

Nota: le capability (registro, filtro dell'anima) vivono solo dentro il visualizzatore
di claude.ai. In anteprima locale non rispondono e la pagina ripiega sul salvataggio
nel browser — è previsto, non è un errore.
"""

import os
import subprocess
import sys

RADICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORGENTE = os.path.join(RADICE, "sito", "mappa-transurfing.html")
USCITA = os.path.join(RADICE, "sito", "anteprima-locale.html")

INVOLUCRO = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root{color-scheme:light dark}
  body{margin:0;font:14px system-ui,-apple-system,sans-serif}
  img{max-width:100%%}
  [hidden]{display:none!important}
</style>
</head>
<body>
%s
</body>
</html>
"""


def main():
    if not os.path.exists(SORGENTE):
        print("Manca %s" % SORGENTE)
        return 1
    with open(SORGENTE) as f:
        corpo = f.read()
    if "<!doctype" in corpo.lower() or "<html" in corpo.lower():
        print("ATTENZIONE: il sorgente contiene già doctype o <html>.")
        print("L'Artifact lo avvolge da sé: quei tag vanno tolti prima di pubblicare.")
    with open(USCITA, "w") as f:
        f.write(INVOLUCRO % corpo)
    print("scritto  %s  (%.0f KB)" % (os.path.relpath(USCITA, RADICE),
                                      os.path.getsize(USCITA) / 1024))
    if "--apri" in sys.argv:
        subprocess.run(["open", USCITA], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
