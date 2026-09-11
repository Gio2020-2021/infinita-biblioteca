    /* ---------- vocabolario sempre a portata ---------- */
    var glossOrigine = $("gloss-main");
    var glossPanelLista = $("gloss-panel-list");
    if (glossOrigine && glossPanelLista) {
      glossPanelLista.innerHTML = glossOrigine.innerHTML;
    }

    function collegaRicercaGlossario(input, contenitore, conta, vuoto) {
      if (!input || !contenitore) return;
      var voci = contenitore.querySelectorAll(":scope > div");
      input.addEventListener("input", function () {
        var q = input.value.trim().toLowerCase();
        var trovate = 0;
        Array.prototype.forEach.call(voci, function (voce) {
          var ok = !q || voce.textContent.toLowerCase().indexOf(q) !== -1;
          voce.hidden = !ok;
          if (ok) trovate++;
        });
        if (conta) conta.textContent = q ? (trovate + (trovate === 1 ? " voce" : " voci")) : "";
        if (vuoto) vuoto.hidden = !q || trovate > 0;
      });
    }
    collegaRicercaGlossario($("gloss-q"), $("gloss-main"), $("gloss-count"), $("gloss-empty"));
    collegaRicercaGlossario($("gloss-q2"), $("gloss-panel-list"), $("gloss-count2"), $("gloss-empty2"));

    var glossTab = $("gloss-tab"), glossPanel = $("gloss-panel"), glossBackdrop = $("gloss-backdrop"),
      glossClose = $("gloss-panel-close"), glossQ2 = $("gloss-q2");
    function apriGlossario() {
      if (!glossPanel) return;
      /* i due pannelli entrano dallo stesso lato: aperti insieme si
         coprirebbero. Il contrario lo fa già apri() in 60-menu-sezioni.js */
      if (typeof chiudiSezioni === "function") chiudiSezioni();
      glossPanel.classList.add("open");
      if (glossBackdrop) glossBackdrop.classList.add("open");
      if (glossTab) { glossTab.classList.add("aperto"); glossTab.setAttribute("aria-expanded", "true"); }
      if (glossQ2) glossQ2.focus();
    }
    function chiudiGlossario() {
      if (!glossPanel) return;
      glossPanel.classList.remove("open");
      if (glossBackdrop) glossBackdrop.classList.remove("open");
      if (glossTab) { glossTab.classList.remove("aperto"); glossTab.setAttribute("aria-expanded", "false"); glossTab.focus(); }
    }
    if (glossTab) glossTab.addEventListener("click", function () {
      if (glossPanel && glossPanel.classList.contains("open")) chiudiGlossario();
      else apriGlossario();
    });
    if (glossClose) glossClose.addEventListener("click", chiudiGlossario);
    if (glossBackdrop) glossBackdrop.addEventListener("click", chiudiGlossario);
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && glossPanel && glossPanel.classList.contains("open")) chiudiGlossario();
    });

    /* ---------- ricerca in tutta la mappa ----------
       L'indice non è sul testo grezzo della pagina ma sulle sue unità reali
       (sezioni, blocchi, passaggi, storie, voci, tecniche): così un risultato
       porta esattamente sul pezzo che contiene la risposta, e non in cima a
       una sezione lunga dentro cui bisogna poi ricercare a occhio. */
    (function () {
      var veil = $("ric-veil"), campo = $("ric-q"), esiti = $("ric-esiti"),
        contaEl = $("ric-conta"), bottone = $("ric-apri");
      if (!veil || !campo || !esiti) return;

      var TIPI = [
        { k: "parte", et: "Parti", peso: 16 },
        { k: "sezione", et: "Sezioni", peso: 14 },
        { k: "voce", et: "Vocabolario", peso: 12 },
        { k: "blocco", et: "Blocchi", peso: 9 },
        { k: "storia", et: "Storie", peso: 9 },
        { k: "tecnica", et: "Tavola delle tecniche", peso: 9 },
        { k: "passo", et: "Passaggi", peso: 6 },
        { k: "porta", et: "Da dove comincio se…", peso: 6 },
        { k: "percorso", et: "Percorsi di lettura", peso: 5 }
      ];
      var ORDINE = TIPI.map(function (x) { return x.k; });
      var ETI = {}, PESO = {};