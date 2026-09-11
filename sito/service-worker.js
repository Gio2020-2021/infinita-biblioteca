// Service worker della Biblioteca — solo per l'uso in locale (Termux o server
// sulla stessa rete). Non ha alcun effetto se la pagina è aperta da file://
// o dentro l'Artifact: il registro è protetto da un controllo a monte in
// anteprima.py, e il browser stesso rifiuta di registrare un worker fuori
// da un contesto sicuro (https, o http://localhost).
//
// Strategia, diversa per le pagine e per il resto:
//
//   PAGINE (navigazioni)  prima la rete, la cache solo se la rete manca.
//     Il server sta sullo stesso telefono, quindi chiedere alla rete non costa
//     nulla e si vede sempre l'ultima versione ricostruita. La cache resta la
//     rete di sicurezza per quando il server non c'è ancora (subito dopo
//     l'accensione) o è spento: è lei che fa aprire comunque l'app.
//     Prima erano cache-first anche queste, ed era il motivo per cui dopo un
//     git pull si continuava a vedere la versione vecchia.
//
//   TUTTO IL RESTO       prima la cache, rete in sottofondo per aggiornarla.
//     Immagini, icone, manifest: pesano e non cambiano quasi mai, quindi qui
//     la cache serve davvero. Le 907 immagini di Risveglio non si precaricano
//     tutte: entrano una per una, alla prima apertura di ciascuna pagina.

const CACHE = "biblioteca-v4";

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

function inCache(richiesta, risposta) {
  if (risposta && risposta.status === 200) {
    const copia = risposta.clone();
    caches.open(CACHE).then((cache) => cache.put(richiesta, copia));
  }
  return risposta;
}

self.addEventListener("fetch", (evento) => {
  if (evento.request.method !== "GET") return;

  // Le PAGINE si chiedono prima alla rete. Il server sta sullo stesso telefono
  // (127.0.0.1): la "rete" è istantanea, quindi la cache non farebbe guadagnare
  // tempo — farebbe solo vedere la versione vecchia dopo un aggiornamento, che
  // è esattamente quello che succedeva. La cache resta la rete di sicurezza per
  // quando il server non è ancora sveglio (all'accensione del telefono) o è
  // spento: lì risponde lei, ed è il motivo per cui l'app si apre comunque.
  if (evento.request.mode === "navigate" || evento.request.destination === "document") {
    evento.respondWith(
      fetch(evento.request)
        .then((risposta) => inCache(evento.request, risposta))
        .catch(() => caches.match(evento.request).then((c) => c || caches.match("/index.html")))
    );
    return;
  }

  // Tutto il resto (le 907 immagini di Risveglio, le icone, il manifest) resta
  // "prima la cache": non cambia quasi mai e pesa, quindi qui la cache serve
  // davvero. L'aggiornamento arriva in sottofondo per la volta dopo.
  evento.respondWith(
    caches.match(evento.request).then((dallaCache) => {
      const dallaRete = fetch(evento.request)
        .then((risposta) => inCache(evento.request, risposta))
        .catch(() => dallaCache);
      return dallaCache || dallaRete;
    })
  );
});
