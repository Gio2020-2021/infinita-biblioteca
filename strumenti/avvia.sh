#!/usr/bin/env bash
# Avvia la biblioteca in locale, da qualunque cartella ci si trovi.
#
#     bash ~/infinita-biblioteca/strumenti/avvia.sh
#     bash ~/infinita-biblioteca/strumenti/avvia.sh 8081   (altra porta)
#
# Nato sul telefono: i comandi a mano vanno dati dalla radice del progetto, e
# darli mentre si è già dentro sito/locale li fa fallire uno per uno — l'ultimo
# però parte lo stesso e serve i file vecchi, quindi sembra che l'aggiornamento
# "non funzioni" quando in realtà non è mai stato scaricato. Qui la cartella si
# ricava dalla posizione dello script, non da dove si è.

set -e

PORTA="${1:-8080}"
RADICE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RADICE"

echo "== scarico gli aggiornamenti =="
git pull

echo
echo "== ricostruisco =="
python3 strumenti/anteprima.py

echo
echo "== server acceso su http://127.0.0.1:$PORTA =="
echo "   (Ctrl+C per fermarlo)"
cd sito/locale
python3 -m http.server "$PORTA"
