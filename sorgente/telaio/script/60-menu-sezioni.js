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
