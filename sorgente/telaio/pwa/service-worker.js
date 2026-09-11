// Service worker della Biblioteca — solo per l'uso in locale (Termux o server
// sulla stessa rete). Non ha alcun effetto se la pagina è aperta da file://
// o dentro l'Artifact: il registro è protetto da un controllo a monte in
// anteprima.py, e il browser stesso rifiuta di registrare un worker fuori
// da un contesto sicuro (https, o http://localhost).
//
// Strategia: "cache prima, rete per aggiornare". Ogni richiesta GET che va a
// buon fine viene salvata; alla richiesta successiva si risponde subito dalla
// cache (niente attesa, funziona anche se il server locale è appena partito
// dopo un riavvio del telefono) mentre in sottofondo si va comunque a
// controllare se c'è una versione più recente, che finisce in cache per la
// volta dopo. Le 907 immagini di Risveglio non vengono precaricate tutte:
// entrano in cache una per una, alla prima apertura di ciascuna pagina.

const CACHE = "biblioteca-v2";

const PRECARICA = [
  "/index.html",
  "/mappa-transurfing.html",
  "/vesica.html",
  "/risveglio.html",
  "/pwa/manifest.json",
  "/pwa/icone/icona-192.png",
  "/pwa/icone/icona-512.png",
  "/pwa/icone/icona-maskable-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(PRECARICA))
      .catch(() => {})   // una singola pagina mancante non deve bloccare l'installazione
  );
  self.skipWaiting();
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches.keys().then((nomi) =>
      Promise.all(nomi.filter((n) => n !== CACHE).map((n) => caches.delete(n)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (evento) => {
  if (evento.request.method !== "GET") return;

  evento.respondWith(
    caches.match(evento.request).then((dallaCache) => {
      const dallaRete = fetch(evento.request)
        .then((risposta) => {
          if (risposta && risposta.status === 200) {
            const copia = risposta.clone();
            caches.open(CACHE).then((cache) => cache.put(evento.request, copia));
          }
          return risposta;
        })
        .catch(() => dallaCache);   // server locale non ancora sveglio: usa la cache
      return dallaCache || dallaRete;
    })
  );
});
