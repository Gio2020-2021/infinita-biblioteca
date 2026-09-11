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
<meta name="theme-color" content="#12131A">
<link rel="manifest" href="/pwa/manifest.json">
<link rel="icon" href="/pwa/icone/icona-192.png">
<link rel="apple-touch-icon" href="/pwa/icone/icona-192.png">
<style>
  :root {{ color-scheme: light dark }}
  body {{ margin: 0; font: 14px system-ui, -apple-system, sans-serif }}
  img {{ max-width: 100% }}
  [hidden] {{ display: none !important }}
</style>
</head>
<body>
{corpo}
<script>
  // Il service worker esiste solo per l'uso in locale (Termux, o un server
  // sulla stessa rete): richiede un "contesto sicuro" — https, o
  // http://localhost/127.0.0.1 — che file:// non è. Se la pagina è aperta
  // così (come fa "anteprima.py --apri" su un computer), la registrazione
  // semplicemente non parte, senza errori visibili: è previsto, non un guasto.
  if ("serviceWorker" in navigator && (location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1")) {{
    navigator.serviceWorker.register("/service-worker.js").catch(() => {{}});
  }}
</script>
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

    # le cartelle <id>-immagini/ (materiale originale dei libri, non generato)
    # vanno copiate anche qui: i riferimenti nel sorgente sono relativi e restano
    # identici sia in sito/ sia in sito/locale/.
    for cartella in SITO.glob("*-immagini"):
        shutil.copytree(cartella, LOCALE / cartella.name)

    # manifest, service worker e icone della PWA: servono solo qui, in locale.
    # service-worker.js sta alla radice (vedi costruisci.py:copia_pwa) perché
    # il suo scope di default è la cartella dello script: da /pwa/ non
    # controllerebbe le pagine delle mappe, che stanno fuori da quella cartella.
    pwa = SITO / "pwa"
    if pwa.is_dir():
        shutil.copytree(pwa, LOCALE / "pwa")
    sw = SITO / "service-worker.js"
    if sw.is_file():
        shutil.copy2(sw, LOCALE / "service-worker.js")

    indice = LOCALE / "index.html"
    print(f"\npronto  {n} pagine in {LOCALE.relative_to(RADICE)}/")
    print(f"apri    {indice}")
    if "--apri" in sys.argv:
        subprocess.run(["open", str(indice)], check=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
