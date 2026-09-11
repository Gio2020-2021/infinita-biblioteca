    /* ---------- mini-indice fisso a destra: segue lo scroll dentro la parte ---------- */
    if (window.IntersectionObserver) {
      var partNavEl = $("part-nav");
      var osservaSezioni = new IntersectionObserver(function (voci) {
        voci.forEach(function (v) {
          if (!v.isIntersecting || !partNavEl) return;
          var bersaglio = "#" + v.target.id;
          partNavEl.querySelectorAll("a").forEach(function (a) {
            a.classList.toggle("cur", a.getAttribute("href") === bersaglio);
          });
        });
      }, { rootMargin: "-100px 0px -65% 0px", threshold: 0 });
      document.querySelectorAll(".branch").forEach(function (sec) { osservaSezioni.observe(sec); });

    }

    /* ---------- la stessa lista, da tendina, sotto i 1080px ----------
       Sotto la soglia della colonna fissa il pannello diventa un cassetto che
       entra da destra (20-mappa.css) e si apre col tasto §. Nessun contenuto
       proprio: è sempre #part-nav, riempito da popolaPartNav() a ogni cambio
       di parte — per questo il tasto va aggiornato da lì, non una volta sola
       all'avvio. Gli elementi si cercano ogni volta invece di tenerli in una
       var: popolaPartNav() gira anche prima che questo file sia stato letto
       (gli script della mappa finiscono in un unico <script>, e le funzioni
       dichiarate sono sollevate mentre le var no). */
    function aggiornaTastoSezioni() {
      var tasto = $("sez-tab"), pannello = $("part-nav");
      if (!tasto || !pannello) return;
      /* una parte senza sommario (il banco, la galleria delle storie) non ha
         sezioni da elencare: niente tasto invece di un cassetto vuoto */
      tasto.hidden = pannello.children.length === 0;
      if (tasto.hidden) chiudiSezioni();
    }
    function chiudiSezioni() {
      var tasto = $("sez-tab"), pannello = $("part-nav"), velo = $("sez-backdrop");
      if (pannello) pannello.classList.remove("aperto");
      if (velo) velo.classList.remove("aperto");
      if (tasto) {
        tasto.classList.remove("aperto");
        tasto.setAttribute("aria-expanded", "false");
      }
    }
    (function () {
      var tasto = $("sez-tab"), pannello = $("part-nav"), velo = $("sez-backdrop");
      if (!tasto || !pannello) return;
      function apri() {
        pannello.classList.add("aperto");
        if (velo) velo.classList.add("aperto");
        tasto.classList.add("aperto");
        tasto.setAttribute("aria-expanded", "true");
        /* il vocabolario occupa lo stesso lato: aperti insieme si coprirebbero */
        if (typeof chiudiGlossario === "function") chiudiGlossario();
      }
      tasto.addEventListener("click", function () {
        if (pannello.classList.contains("aperto")) chiudiSezioni(); else apri();
      });
      if (velo) velo.addEventListener("click", chiudiSezioni);
      /* scegliere una sezione chiude il cassetto: il salto all'ancora avviene
         comunque, ed è quello che si vuole vedere subito dopo */
      pannello.addEventListener("click", function (ev) {
        if (ev.target.closest("a")) chiudiSezioni();
      });
      document.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && pannello.classList.contains("aperto")) chiudiSezioni();
      });
    })();
    aggiornaTastoSezioni();

    /* accensione del pannello: ricalcolata a ogni scroll dalla posizione dei
       badge, non da un osservatore che scatta solo sui cambi di stato */
    var inAttesa = false;
    function chiediAggiornamento() {
      if (inAttesa) return;
      inAttesa = true;
      requestAnimationFrame(function () {
        inAttesa = false;
        aggiornaPartNav();
      });
    }
    /* il bottone «Su» compare solo quando serve davvero, cioè quando l'inizio
       del capitolo è uscito di scena da un pezzo */
    var suEl = $("su");
    function aggiornaSu() {
      if (!suEl) return;
      suEl.classList.toggle("on", window.pageYOffset > 700);
    }
    if (suEl) {
      /* forma semplice di proposito: `scrollTo({behavior:"smooth"})` in alcuni
         contesti non fa nulla e non lancia, quindi un fallback non scatterebbe
         mai. La morbidezza la dà già `html{scroll-behavior:smooth}`, che la
         regola su prefers-reduced-motion disattiva da sé. */
      suEl.addEventListener("click", function () { window.scrollTo(0, 0); });
    }
    aggiornaSu();
    /* ascoltatore suo, non dentro il rAF condiviso con il menu di sezione:
       quello serve perché aggiornaPartNav misura la pagina, mentre qui basta
       leggere lo scroll e accendere una classe. Legandolo al rAF, se il
       fotogramma non arriva il bottone resta acceso a pagina in cima. */
    window.addEventListener("scroll", aggiornaSu, { passive: true });
    window.addEventListener("scroll", chiediAggiornamento, { passive: true });
    window.addEventListener("resize", chiediAggiornamento);
    aggiornaPartNav();
