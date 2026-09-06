    /* ---------- stato locale di ripiego ---------- */
    var LS = {
      get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
      set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) { } }
    };

    /* ---------- registro: rendering ---------- */
    var logList = $("log-list"), logEmpty = $("log-empty");
    function renderLog(items) {
      if (!logList) return;
      logList.innerHTML = "";
      if (!items || !items.length) { if (logEmpty) logEmpty.hidden = false; return; }
      if (logEmpty) logEmpty.hidden = true;
      items.forEach(function (it) {
        var li = document.createElement("li");
        var m = document.createElement("span"); m.className = "mark"; m.textContent = "✓";
        var t = document.createElement("span"); t.className = "txt"; t.textContent = it.testo || "";
        var w = document.createElement("span"); w.className = "when"; w.textContent = when(it.quando);
        li.appendChild(m); li.appendChild(t); li.appendChild(w);
        logList.appendChild(li);
      });
    }

    /* ---------- capability: db ---------- */
    var DB = null, localLog = [];
    try { localLog = JSON.parse(LS.get("tr.log") || "[]"); } catch (e) { localLog = []; }
    renderLog(localLog);
    if ($("fine-t")) $("fine-t").value = LS.get("tr.fine.t") || "";
    if ($("fine-d")) $("fine-d").value = LS.get("tr.fine.d") || "";
    if ($("am-t")) $("am-t").value = LS.get("tr.am") || "";
    currentFine = LS.get("tr.fine.t") || "";

    function saveLogLocal() { LS.set("tr.log", JSON.stringify(localLog.slice(0, 120))); }

    if (window.claude && typeof window.claude.use === "function") {
      window.claude.use("db").then(function (db) {
        if (!db) return;
        DB = db;
        db.doc("pratica/fine").onSnapshot(function (s) {
          if (!s.exists) return;
          var d = s.data() || {};
          if ($("fine-t") && document.activeElement !== $("fine-t")) $("fine-t").value = d.titolo || "";
          if ($("fine-d") && document.activeElement !== $("fine-d")) $("fine-d").value = d.diapositiva || "";
          currentFine = d.titolo || "";
        }, function () { });
        db.doc("pratica/amalgama").onSnapshot(function (s) {
          if (!s.exists) return;
          var d = s.data() || {};
          if ($("am-t") && document.activeElement !== $("am-t")) $("am-t").value = d.testo || "";
        }, function () { });
        db.collection("registro").orderBy("quando", "desc").limit(60)
          .onSnapshot(function (q) {
            var items = q.docs.map(function (d) { return d.data() || {}; });
            renderLog(items);
          }, function () { });
        db.doc("pratica/risveglio").onSnapshot(function (s) {
          if (s.exists && s.data() && s.data().ultimo)
            say($("wake-note"), "ultimo: " + when(s.data().ultimo));
        }, function () { });
      }, function () { });
    }

    /* ---------- azioni ---------- */
    if ($("fine-save")) $("fine-save").addEventListener("click", function () {
      var t = ($("fine-t").value || "").trim(), d = ($("fine-d").value || "").trim();
      if (!t) { say($("fine-note"), "Scrivi il fine, anche in tre parole."); return; }
      currentFine = t;
      LS.set("tr.fine.t", t); LS.set("tr.fine.d", d);
      if (DB) {
        DB.doc("pratica/fine").set({ titolo: t, diapositiva: d, quando: Date.now() })
          .then(function () { say($("fine-note"), "Fine impostato. Ora non dirlo a nessuno.", "ok"); })
          .catch(function () { say($("fine-note"), "Salvato solo su questo browser."); });
      } else {
        say($("fine-note"), "Fine impostato. Ora non dirlo a nessuno.", "ok");
      }
    });

    function addMark() {
      var t = ($("log-t").value || "").trim();
      if (!t) { say($("log-note"), "Cos'è successo?"); return; }
      var entry = { testo: t, quando: Date.now() };
      $("log-t").value = "";
      say($("log-note"), "✓ segnato. La tua intenzione si sta realizzando.", "ok");
      if (DB) {
        DB.collection("registro").add(entry).catch(function () {
          localLog.unshift(entry); saveLogLocal(); renderLog(localLog);
        });
      } else {
        localLog.unshift(entry); saveLogLocal(); renderLog(localLog);
      }
    }
    if ($("log-add")) $("log-add").addEventListener("click", addMark);
    if ($("log-t")) $("log-t").addEventListener("keydown", function (e) { if (e.key === "Enter") addMark(); });

    if ($("imp-go")) $("imp-go").addEventListener("click", function () {
      var out = $("imp-out");
      if (out) out.hidden = false;
    });

    if ($("wake")) $("wake").addEventListener("click", function () {
      var now = Date.now();
      say($("wake-note"), "ultimo: " + when(now));
      LS.set("tr.wake", String(now));
      if (DB) DB.doc("pratica/risveglio").set({ ultimo: now }).catch(function () { });
    });
    var w0 = LS.get("tr.wake");
    if (w0) say($("wake-note"), "ultimo: " + when(Number(w0)));

    if ($("am-save")) $("am-save").addEventListener("click", function () {
      var t = ($("am-t").value || "").trim();
      if (!t) { say($("am-note"), "Scrivi l'amalgama."); return; }
      if (/\bnon\b|\bmai\b|\bsenza\b/i.test(t))
        say($("am-note"), "Attenzione: contiene una negazione. La forma-pensiero dev'essere affermativa.");
      else
        say($("am-note"), "Salvata. Foglio, bicchiere sopra, palmi attorno, pronuncia, bevi.", "ok");
      LS.set("tr.am", t);
      if (DB) DB.doc("pratica/amalgama").set({ testo: t, quando: Date.now() }).catch(function () { });
    });

    /* ---------- capability: sample ---------- */
    var SAMPLE = null;
    var CRITERI = "Sei un lettore attento del Transurfing di Vadim Zeland. Rispondi in italiano, "
      + "massimo 90 parole, diretto, senza preamboli e senza elenchi puntati.";

    function ask(btn, out, prompt, working) {
      if (!SAMPLE) return;
      btn.disabled = true;
      out.hidden = false;
      out.textContent = working;
      SAMPLE(prompt, { onText: function (e) { out.textContent = e.text; } })
        .then(function (r) { out.textContent = r.text; })
        .catch(function (e) {
          if (e && e.code === "cancelled") { out.hidden = true; return; }
          if (e && e.text) { out.textContent = e.text; return; }
          out.textContent = (e && e.code === "rate_limited")
            ? "Troppe richieste in poco tempo. Riprova fra un momento."
            : "Non è stato possibile chiedere adesso.";
        })
        .then(function () { btn.disabled = false; });
    }

    if (window.claude && typeof window.claude.use === "function") {
      window.claude.use("sample").then(function (s) {
        if (!s) return;
        SAMPLE = s;
        if ($("fine-check")) $("fine-check").hidden = false;
        if ($("am-forge")) $("am-forge").hidden = false;
      }, function () { });
    }

    if ($("fine-check")) $("fine-check").addEventListener("click", function () {
      var t = ($("fine-t").value || "").trim(), d = ($("fine-d").value || "").trim();
      if (!t) { say($("fine-note"), "Scrivi prima il fine."); return; }
      ask(this, $("fine-out"),
        CRITERI + "\n\nApplica i criteri del Transurfing a questo obiettivo e dimmi, senza addolcire, "
        + "se sembra venire dall'anima o da un pendolo. I criteri sono: all'anima si illuminano gli occhi; "
        + "un desiderio che suscita disagio, dubbio, dovere o senso di colpa viene dalla ragione, cioè dai "
        + "pendoli; il denaro non è mai il fine ma un attributo del fine; un obiettivo formulato come mezzo "
        + "(per essere accettato, per dimostrare qualcosa) non è dell'anima. Se serve, riformula il fine in "
        + "una riga come lo formulerebbe l'anima.\n\nFINE: " + t + "\nDIAPOSITIVA: " + (d || "(non ancora scritta)"),
        "Sto guardando…");
    });

    if ($("am-forge")) $("am-forge").addEventListener("click", function () {
      var t = ($("fine-t").value || "").trim() || ($("am-t").value || "").trim();
      if (!t) { say($("am-note"), "Serve prima un fine o un'intenzione."); return; }
      ask(this, $("am-out"),
        CRITERI + "\n\nTrasforma questa intenzione in un'amalgama secondo le regole di Zeland: "
        + "affermativa (mai la particella negativa), concreta, laconica, al presente, diretta al fine, "
        + "nessuna astrazione e nessun augurio prolisso, da una a tre frasi brevi. "
        + "Rispondi con la sola amalgama, niente spiegazioni.\n\nINTENZIONE: " + t,
        "Sto forgiando…");
    });
