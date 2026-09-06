    /* ---------- il diario: due taccuini più la giornata ---------- */
    (function () {
      var cal = $("d-cal");
      if (!cal) return;

      var MESI = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto",
        "Settembre", "Ottobre", "Novembre", "Dicembre"];
      var GIORNI = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
      var CAMPI = ["dichiarazione", "giornata", "constatazione"];

      var giorni = {};          /* chiave "AAAA-MM-GG" -> {dichiarazione, giornata, constatazione} */
      var DBD = null;           /* namespace db, quando arriva */
      var scelto = new Date();
      var mostrato = new Date();
      var attesa = null;
      var scelta = "mese";

      function chiave(d) {
        return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" +
          String(d.getDate()).padStart(2, "0");
      }
      function daChiave(k) {
        var p = k.split("-");
        return new Date(+p[0], +p[1] - 1, +p[2]);
      }
      function oggiK() { return chiave(new Date()); }
      function pieno(k) {
        var g = giorni[k];
        if (!g) return false;
        return CAMPI.some(function (c) { return (g[c] || "").trim(); });
      }

      /* --- memoria locale, sempre disponibile --- */
      function leggiLocale() {
        try { giorni = JSON.parse(LS.get("tr.diario") || "{}") || {}; }
        catch (e) { giorni = {}; }
      }
      function scriviLocale() {
        try { LS.set("tr.diario", JSON.stringify(giorni)); } catch (e) { }
      }

      /* --- schermo --- */
      function mostraGiorno() {
        var k = chiave(scelto), g = giorni[k] || {};
        CAMPI.forEach(function (c) {
          var el = $("d-" + c);
          if (el && document.activeElement !== el) el.value = g[c] || "";
        });
        $("d-titolo").textContent = GIORNI[scelto.getDay()] + " " + scelto.getDate() + " " +
          MESI[scelto.getMonth()].toLowerCase() +
          (scelto.getFullYear() !== new Date().getFullYear() ? " " + scelto.getFullYear() : "");
        var eOggi = k === oggiK();
        $("d-tag-oggi").hidden = !eOggi;
        $("d-oggi").hidden = eOggi;
        $("d-stato").textContent = "";
      }

      function disegnaCal() {
        cal.innerHTML = "";
        $("d-mese").textContent = MESI[mostrato.getMonth()] + " " + mostrato.getFullYear();
        ["l", "m", "m", "g", "v", "s", "d"].forEach(function (g) {
          var e = document.createElement("div");
          e.className = "dow";
          e.textContent = g;
          cal.appendChild(e);
        });
        var primo = new Date(mostrato.getFullYear(), mostrato.getMonth(), 1);
        var salto = (primo.getDay() + 6) % 7;
        for (var i = 0; i < salto; i++) cal.appendChild(document.createElement("div"));
        var ultimo = new Date(mostrato.getFullYear(), mostrato.getMonth() + 1, 0).getDate();
        for (var n = 1; n <= ultimo; n++) {
          var d = new Date(mostrato.getFullYear(), mostrato.getMonth(), n);
          var k = chiave(d);
          var b = document.createElement("button");
          b.type = "button";
          var cls = [];
          if (!pieno(k)) cls.push("senza");
          if (k === oggiK()) cls.push("oggi");
          if (k === chiave(scelto)) cls.push("scelto");
          b.className = cls.join(" ");
          var num = document.createElement("span");
          num.textContent = n;
          b.appendChild(num);
          if (pieno(k)) b.appendChild(document.createElement("i"));
          b.addEventListener("click", (function (data) {
            return function () { vaiA(data); };
          })(d));
          cal.appendChild(b);
        }
      }

      function vaiA(d) {
        salvaSubito();
        scelto = new Date(d.getFullYear(), d.getMonth(), d.getDate());
        mostrato = new Date(scelto.getFullYear(), scelto.getMonth(), 1);
        mostraGiorno();
        disegnaCal();
      }
      function muovi(n) {
        vaiA(new Date(scelto.getFullYear(), scelto.getMonth(), scelto.getDate() + n));
      }

      /* --- salvataggio --- */
      function raccogli() {
        var k = chiave(scelto);
        var g = giorni[k] || {};
        CAMPI.forEach(function (c) {
          var el = $("d-" + c);
          if (el) g[c] = el.value;
        });
        var vuoto = CAMPI.every(function (c) { return !(g[c] || "").trim(); });
        if (vuoto) delete giorni[k]; else giorni[k] = g;
        return { k: k, g: g, vuoto: vuoto };
      }

      function salvaSubito() {
        var r = raccogli();
        scriviLocale();
        disegnaCal();
        if (!DBD) return;
        var doc = DBD.doc("diario/" + r.k);
        var azione = r.vuoto ? doc.delete() : doc.set({
          dichiarazione: r.g.dichiarazione || "",
          giornata: r.g.giornata || "",
          constatazione: r.g.constatazione || "",
          aggiornato: Date.now()
        });
        azione.then(function () {
          $("d-stato").textContent = "salvato";
          setTimeout(function () {
            if ($("d-stato").textContent === "salvato") $("d-stato").textContent = "";
          }, 2200);
        }, function () {
          $("d-stato").textContent = "solo qui";
        });
      }

      function programmaSalvataggio() {
        $("d-stato").textContent = "…";
        clearTimeout(attesa);
        attesa = setTimeout(salvaSubito, 800);
      }

      CAMPI.forEach(function (c) {
        var el = $("d-" + c);
        if (el) {
          el.addEventListener("input", programmaSalvataggio);
          el.addEventListener("blur", salvaSubito);
        }
      });

      $("d-prec").addEventListener("click", function () { muovi(-1); });
      $("d-succ").addEventListener("click", function () { muovi(1); });
      $("d-oggi").addEventListener("click", function () { vaiA(new Date()); });
      $("d-mese-prec").addEventListener("click", function () {
        mostrato = new Date(mostrato.getFullYear(), mostrato.getMonth() - 1, 1);
        disegnaCal();
      });
      $("d-mese-succ").addEventListener("click", function () {
        mostrato = new Date(mostrato.getFullYear(), mostrato.getMonth() + 1, 1);
        disegnaCal();
      });

      /* --- ricerca --- */
      var box = $("d-risultati");
      $("d-cerca").addEventListener("input", function () {
        var q = this.value.trim().toLowerCase();
        box.innerHTML = "";
        if (q.length < 2) { box.hidden = true; return; }
        var trovati = Object.keys(giorni).filter(function (k) {
          return CAMPI.some(function (c) { return (giorni[k][c] || "").toLowerCase().indexOf(q) >= 0; });
        }).sort().reverse().slice(0, 12);
        box.hidden = false;
        if (!trovati.length) {
          var v = document.createElement("p");
          v.className = "vuoto";
          v.textContent = "Nessun giorno contiene «" + this.value.trim() + "».";
          box.appendChild(v);
          return;
        }
        trovati.forEach(function (k) {
          var testo = CAMPI.map(function (c) { return giorni[k][c] || ""; }).join(" ");
          var i = testo.toLowerCase().indexOf(q);
          var estratto = testo.slice(Math.max(0, i - 40), i + 90).replace(/\s+/g, " ").trim();
          var d = daChiave(k);
          var b = document.createElement("button");
          b.type = "button";
          var q1 = document.createElement("span");
          q1.className = "rq";
          q1.textContent = GIORNI[d.getDay()] + " " + d.getDate() + " " + MESI[d.getMonth()].toLowerCase() +
            " " + d.getFullYear();
          var q2 = document.createElement("span");
          q2.className = "rt";
          q2.textContent = "…" + estratto + "…";
          b.appendChild(q1); b.appendChild(q2);
          b.addEventListener("click", function () {
            vaiA(d);
            box.hidden = true;
            $("d-cerca").value = "";
          });
          box.appendChild(b);
        });
      });

      /* --- scarico --- */
      function selezionati() {
        var tutte = Object.keys(giorni).filter(pieno).sort();
        if (scelta === "tutto") return tutte;
        if (scelta === "giorno") return tutte.filter(function (k) { return k === chiave(scelto); });
        if (scelta === "mese") {
          var pre = mostrato.getFullYear() + "-" + String(mostrato.getMonth() + 1).padStart(2, "0");
          return tutte.filter(function (k) { return k.indexOf(pre) === 0; });
        }
        var limite = new Date();
        limite.setDate(limite.getDate() - 30);
        return tutte.filter(function (k) { return daChiave(k) >= limite; });
      }

      function aggiornaConteggio() {
        var n = selezionati().length;
        $("d-conteggio").textContent = n === 0 ? "nessun giorno scritto in questa selezione"
          : n === 1 ? "1 giorno" : n + " giorni";
        $("d-scarica").disabled = n === 0;
      }

      document.querySelectorAll("#d-veil [data-scelta]").forEach(function (b) {
        b.addEventListener("click", function () {
          scelta = b.getAttribute("data-scelta");
          document.querySelectorAll("#d-veil [data-scelta]").forEach(function (a) {
            a.setAttribute("aria-pressed", a === b ? "true" : "false");
          });
          aggiornaConteggio();
        });
      });

      function apriModale() {
        salvaSubito();
        $("d-veil").hidden = false;
        aggiornaConteggio();
      }
      function chiudiModale() {
        $("d-veil").hidden = true;
        $("d-scarica-nota").textContent = "";
      }
      $("d-scarica-apri").addEventListener("click", apriModale);
      $("d-annulla").addEventListener("click", chiudiModale);
      $("d-veil").addEventListener("click", function (e) {
        if (e.target === $("d-veil")) chiudiModale();
      });

      function componi(chiavi) {
        var righe = ["IL DIARIO DEL TRANSURFER", ""];
        if (chiavi.length) {
          var a = daChiave(chiavi[0]), b = daChiave(chiavi[chiavi.length - 1]);
          righe.push("dal " + a.getDate() + " " + MESI[a.getMonth()].toLowerCase() + " " + a.getFullYear() +
            " al " + b.getDate() + " " + MESI[b.getMonth()].toLowerCase() + " " + b.getFullYear());
          righe.push("");
        }
        chiavi.forEach(function (k) {
          var d = daChiave(k), g = giorni[k];
          righe.push("");
          righe.push("————————————————————————————————————");
          righe.push(GIORNI[d.getDay()].toUpperCase() + " " + d.getDate() + " " +
            MESI[d.getMonth()].toUpperCase() + " " + d.getFullYear());
          righe.push("————————————————————————————————————");
          if ((g.dichiarazione || "").trim()) {
            righe.push("", "DICHIARAZIONE — mattino", "", g.dichiarazione.trim());
          }
          if ((g.giornata || "").trim()) {
            righe.push("", "LA GIORNATA", "", g.giornata.trim());
          }
          if ((g.constatazione || "").trim()) {
            righe.push("", "CONSTATAZIONE — sera", "", g.constatazione.trim());
          }
          righe.push("");
        });
        return righe.join("\n");
      }

      $("d-scarica").addEventListener("click", function () {
        var chiavi = selezionati();
        if (!chiavi.length) return;
        var testo = componi(chiavi);
        var nota = $("d-scarica-nota");
        nota.textContent = "preparo…";
        if (!(window.claude && typeof window.claude.use === "function")) {
          nota.textContent = "lo scarico non è disponibile qui";
          return;
        }
        window.claude.use("downloads").then(function (dl) {
          if (!dl) { nota.textContent = "lo scarico non è disponibile qui"; return; }
          var nome = "diario-transurfing-" + chiavi[0] + "_" + chiavi[chiavi.length - 1] + ".txt";
          dl.save({ filename: nome, data: testo }).then(function () {
            nota.textContent = "scaricato.";
            setTimeout(chiudiModale, 900);
          }, function (err) {
            nota.textContent = (err && err.code === "declined") ? "annullato." : "non è riuscito.";
          });
        }, function () { nota.textContent = "lo scarico non è disponibile qui"; });
      });

      /* --- avvio: prima il locale, poi il database --- */
      leggiLocale();
      mostraGiorno();
      disegnaCal();

      if (window.claude && typeof window.claude.use === "function") {
        window.claude.use("db").then(function (db) {
          if (!db) return;
          DBD = db;
          db.collection("diario").orderBy("aggiornato", "desc").limit(500)
            .onSnapshot(function (q) {
              q.docs.forEach(function (doc) {
                var d = doc.data() || {};
                giorni[doc.id] = {
                  dichiarazione: d.dichiarazione || "",
                  giornata: d.giornata || "",
                  constatazione: d.constatazione || ""
                };
              });
              scriviLocale();
              mostraGiorno();
              disegnaCal();
            }, function () { });
          /* il fine e l'amalgama vengono dal banco: qui si leggono soltanto */
          db.doc("pratica/fine").onSnapshot(function (s) {
            var d = (s.exists && s.data()) || {};
            if ($("d-fine")) $("d-fine").textContent = d.titolo || "—";
            if ($("d-diapositiva")) $("d-diapositiva").textContent = d.diapositiva || "";
          }, function () { });
          db.doc("pratica/amalgama").onSnapshot(function (s) {
            var d = (s.exists && s.data()) || {};
            if ($("d-amalgama")) $("d-amalgama").textContent = d.testo || "—";
          }, function () { });
        }, function () { });
      }

      /* se il banco è già stato compilato solo in locale */
      if ($("d-fine") && LS.get("tr.fine.t")) $("d-fine").textContent = LS.get("tr.fine.t");
      if ($("d-diapositiva") && LS.get("tr.fine.d")) $("d-diapositiva").textContent = LS.get("tr.fine.d");
      if ($("d-amalgama") && LS.get("tr.am")) $("d-amalgama").textContent = LS.get("tr.am");
    })();
