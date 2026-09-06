    /* ---------- rituale della treccina ---------- */
    var STEPS = [
      { h: "Svegliati", p: "Porta l'attenzione al centro della coscienza: vedo me stesso e vedo la realtà. Non nei pensieri, non in ciò che accade fuori — nel punto in mezzo." },
      { h: "Attiva la treccina", p: "Concentrati sull'area tra le scapole. Un leggero formicolio, un calore. Meglio mentre espiri. Se non senti nulla, simula: funziona ugualmente." },
      { h: "Crea il fotogramma", p: "Davanti a te, sullo schermo esterno, la scena della tua realtà desiderata — con te dentro come protagonista, non come spettatore." },
      { h: "Illumina", p: "Tenendo l'attenzione insieme sulla treccina e sul fotogramma, la luce parte dalla punta, ti attraversa in avanti e illumina la scena. Ora muoviti lì dentro come se fosse ordinario.", arc: 45 },
      { h: "Scollega", p: "Espira e lascia andare ogni concentrazione. Il fotogramma svanisce, la treccina torna a riposo. Poi dimenticatene e torna alla vita normale.", last: true }
    ];
    var CTX = {
      attesa: "Stavi sperando. Non aspettare — imposta.",
      intenzione: "Stavi per agire. Prima imposta, poi vai.",
      problema: "È successo qualcosa. Non agitarti — imposta."
    };
    var veil = $("veil"), ritN = $("rit-n"), ritH = $("rit-h"), ritP = $("rit-p"),
      ritEcho = $("rit-echo"), ritArc = $("rit-arc"), ritArcB = $("rit-arc-b"),
      ritNext = $("rit-next"), ritEsc = $("rit-esc"), ritDots = $("rit-dots");
    var step = 0, arcTimer = null, lastFocus = null, currentFine = "";

    function paintDots() {
      if (!ritDots) return;
      ritDots.innerHTML = "";
      for (var i = 0; i < STEPS.length; i++) {
        var d = document.createElement("i");
        if (i <= step) d.className = "on";
        ritDots.appendChild(d);
      }
    }
    function stopArc() { if (arcTimer) { clearInterval(arcTimer); arcTimer = null; } }
    function render() {
      var s = STEPS[step];
      ritN.textContent = "Passo 0" + (step + 1) + " di 05";
      ritH.textContent = s.h;
      ritP.textContent = s.p;
      ritNext.textContent = s.last ? "Scollega e chiudi" : "Fatto";
      stopArc();
      ritArc.hidden = true; ritArcB.style.width = "0%";
      if (s.arc) {
        ritArc.hidden = false;
        var t0 = Date.now(), ms = s.arc * 1000;
        arcTimer = setInterval(function () {
          var p = Math.min(1, (Date.now() - t0) / ms);
          ritArcB.style.width = (p * 100).toFixed(1) + "%";
          if (p >= 1) stopArc();
        }, 120);
      }
      paintDots();
    }
    function openRitual(kind) {
      step = 0; lastFocus = document.activeElement;
      var bits = [];
      if (CTX[kind]) bits.push(CTX[kind]);
      if (currentFine) bits.push("Il tuo fine: " + currentFine);
      if (bits.length) { ritEcho.textContent = bits.join("  ·  "); ritEcho.hidden = false; }
      else ritEcho.hidden = true;
      veil.hidden = false;
      render();
      ritNext.focus();
    }
    function closeRitual() {
      stopArc();
      veil.hidden = true;
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }
    Array.prototype.forEach.call(document.querySelectorAll("[data-trigger]"), function (b) {
      b.addEventListener("click", function () { openRitual(b.getAttribute("data-trigger")); });
    });
    if (ritNext) ritNext.addEventListener("click", function () {
      if (step < STEPS.length - 1) { step++; render(); } else closeRitual();
    });
    if (ritEsc) ritEsc.addEventListener("click", closeRitual);
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && veil && !veil.hidden) closeRitual();
    });
