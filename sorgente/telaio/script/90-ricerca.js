      TIPI.forEach(function (x) { ETI[x.k] = x.et; PESO[x.k] = x.peso; });

      /* appiattisce per il confronto: via accenti, apostrofi e punteggiatura.
         Così «dell'importanza» e «importanza» si trovano a vicenda, e una
         frase esatta non si perde per una virgola di differenza. */
      function piatto(s) {
        return (s || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "")
          .toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
      }
      /* la stessa cosa, ma tenendo la corrispondenza con il testo originale:
         serve solo per gli estratti, quindi si calcola a richiesta */
      function piattoMap(s) {
        var out = [], map = [], spazio = true;
        for (var i = 0; i < s.length; i++) {
          var d = s[i].normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
          if (/^[a-z0-9]$/.test(d)) { out.push(d); map.push(i); spazio = false; }
          else if (!spazio) { out.push(" "); map.push(i); spazio = true; }
        }
        while (out.length && out[out.length - 1] === " ") { out.pop(); map.pop(); }
        return { s: out.join(""), map: map };
      }
      function testo(el) { return ((el && el.textContent) || "").replace(/\s+/g, " ").trim(); }
      function esc(s) {
        return s.replace(/[&<>"]/g, function (c) {
          return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
        });
      }

      /* ---- costruzione dell'indice ---- */
      var IDX = [];
      var NOMI = {};
      Array.prototype.forEach.call(document.querySelectorAll("nav.parts button[data-part]"), function (b) {
        var i = b.querySelector("i");
        NOMI[b.getAttribute("data-part")] = testo(b).replace(i ? testo(i) : "", "").trim();
      });

      /* il colore del risultato è quello della sua parte: nella mappa il colore
         è un ruolo (blu il terreno, ruggine ciò che ti agisce contro, salvia ciò
         che hai dalla tua, ambra ciò che si esegue), e l'elenco lo conserva */
      var COL = {};
      function agg(k, el, titolo, corpo, parte, dove, ancora) {
        if (!titolo && !corpo) return;
        IDX.push({
          k: k, el: el, titolo: titolo, corpo: corpo, parte: parte, dove: dove, ancora: ancora,
          col: (parte && COL[parte]) || "var(--blue)",
          tn: piatto(titolo), cn: piatto(corpo)
        });
      }
      /* il corpo di un blocco è il suo testo meno il titolo, che sta già a parte */
      function senzaTitolo(el, titolo) {
        var tutto = testo(el);
        return titolo && tutto.indexOf(titolo) === 0 ? tutto.slice(titolo.length).trim() : tutto;
      }

      Array.prototype.forEach.call(document.querySelectorAll(".part"), function (parte) {
        var pid = parte.id.replace("parte-", "");
        var nomeParte = NOMI[pid] || pid;
        COL[pid] = (parte.style.getPropertyValue("--pc") || "").trim() || "var(--amber)";
        var testa = parte.querySelector(".part-head");
        if (testa) {
          var ht = testa.querySelector("h2"), pd = testa.querySelector(".pd");
          agg("parte", testa, testo(ht), testo(pd), pid, nomeParte, "parte-" + pid);
        }

        Array.prototype.forEach.call(parte.querySelectorAll("section.branch"), function (sez) {
          var h = sez.querySelector(".branch-aside h2") || sez.querySelector("h2");
          var tSez = testo(h), anc = sez.id || null;
          var carta = [];
          [".gist", ".quote", ".src"].forEach(function (s) {
            var e = sez.querySelector(s); if (e) carta.push(testo(e));
          });
          agg("sezione", sez, tSez, carta.join(" · "), pid, nomeParte, anc);

          Array.prototype.forEach.call(sez.querySelectorAll(".move"), function (m) {
            var t3 = testo(m.querySelector("h3")) || tSez;
            agg("blocco", m, t3, senzaTitolo(m, t3), pid, nomeParte + " · " + tSez, anc);
          });
          Array.prototype.forEach.call(sez.querySelectorAll("ul.tree > li"), function (li) {
            var tn = testo(li.querySelector(".n-t")) || tSez;
            agg("passo", li, tn, senzaTitolo(li, tn), pid, nomeParte + " · " + tSez, anc);
          });
          Array.prototype.forEach.call(sez.querySelectorAll("table.tools tbody tr"), function (tr) {
            var cel = tr.querySelectorAll("td");
            if (!cel.length) return;
            var resto = [];
            Array.prototype.slice.call(cel, 1).forEach(function (td) { resto.push(testo(td)); });
            agg("tecnica", tr, testo(cel[0]), resto.join(" · "), pid, nomeParte + " · " + tSez, anc);
          });
        });

        Array.prototype.forEach.call(parte.querySelectorAll("article.story"), function (a) {
          var t3 = testo(a.querySelector("h3"));
          agg("storia", a, t3, senzaTitolo(a, testo(a.querySelector(".bk")) + " " + t3), pid, nomeParte + " · Storie", "storie");
        });
        Array.prototype.forEach.call(parte.querySelectorAll(".door"), function (d) {
          var t3 = testo(d.querySelector("h3"));
          agg("porta", d, t3, senzaTitolo(d, t3), pid, nomeParte + " · Da dove comincio se…", "porte");
        });
        Array.prototype.forEach.call(parte.querySelectorAll("article.percorso"), function (a) {
          var t3 = testo(a.querySelector("h3"));
          agg("percorso", a, t3, senzaTitolo(a, testo(a.querySelector(".p-n")) + " " + t3), pid, nomeParte + " · In che ordine leggerlo", "percorsi");
        });
      });

      /* il vocabolario vive nel pannello a destra: i suoi risultati non
         portano da nessuna parte nella pagina, aprono il pannello filtrato */
      var sorgenteGloss = $("gloss-main");
      if (sorgenteGloss) {
        Array.prototype.forEach.call(sorgenteGloss.children, function (d) {
          var dt = d.querySelector("dt"), dd = d.querySelector("dd");
          agg("voce", d, testo(dt), testo(dd), null, "Vocabolario", null);
        });
      }

      /* ---- interrogazione ----
         In italiano una ricerca a sola sottostringa è inservibile: la mappa
         scrive «affossare», e chi cerca «affossamento» non troverebbe nulla.
         Si toglie quindi al termine cercato la desinenza e si cerca la radice
         come inizio di parola. La corrispondenza piena vale sempre più di
         quella per radice, così l'ordine dei risultati non si sporca. */
      var SUFF = ["issimamente", "issimo", "issima", "issimi", "issime", "amento", "imento",
        "azione", "uzione", "zione", "mente", "abile", "ibile", "aggio", "ando", "endo",
        "anza", "enza", "ismo", "ista", "ione", "are", "ere", "ire", "ato", "ata", "ati",
        "ate", "ito", "ita", "iti", "ite", "uto", "uta", "uti", "ute", "ivo", "iva", "ivi",
        "ive", "oso", "osa", "osi", "ose", "ile", "e", "i", "o", "a"];
      SUFF.sort(function (a, b) { return b.length - a.length; });
      function radice(t) {
        if (t.length < 5) return t;
        for (var i = 0; i < SUFF.length; i++) {
          var s = SUFF[i];
          if (t.length - s.length >= 4 && t.slice(-s.length) === s) return t.slice(0, t.length - s.length);
        }
        return t;
      }
      /* posizione di una radice presa come inizio di parola, -1 se non c'è */
      function inizioParola(hay, r) {
        if (!r || !hay) return -1;
        if (hay.lastIndexOf(r, 0) === 0) return 0;
        var j = hay.indexOf(" " + r);
        return j === -1 ? -1 : j + 1;
      }

      function analizza(raw) {
        var frasi = [], resto = String(raw || "");
        resto = resto.replace(/[«"“”]([^«»"“”]+)[»"“”]/g, function (_, g) {
          var f = piatto(g); if (f) frasi.push(f); return " ";
        });
        var termini = piatto(resto).split(" ").filter(function (w) { return w.length >= 2; })
          .map(function (w) { return { t: w, r: radice(w) }; });
        return { frasi: frasi, termini: termini, tutto: piatto(raw), vuota: !frasi.length && !termini.length };
      }

      function punteggio(u, q) {
        var s = 0, i;
        for (i = 0; i < q.frasi.length; i++) {
          var f = q.frasi[i];
          if (u.tn.indexOf(f) !== -1) s += 130;
          else if (u.cn.indexOf(f) !== -1) s += 75;
          else return 0;
        }
        for (i = 0; i < q.termini.length; i++) {
          var t = q.termini[i].t, r = q.termini[i].r;
          var inT = u.tn.indexOf(t), inC = u.cn.indexOf(t);
          var pT = inT !== -1 ? inT : inizioParola(u.tn, r);
          var pC = inC !== -1 ? inC : inizioParola(u.cn, r);
          if (pT === -1 && pC === -1) return 0;
          if (pT !== -1) s += inT !== -1 ? ((inT === 0 || u.tn.indexOf(" " + t) !== -1) ? 62 : 38) : 30;
          if (pC !== -1) s += (inC !== -1 ? 14 : 8) + Math.max(0, 8 - Math.floor(pC / 500));
        }
        if (q.tutto && q.tutto.length > 2 && u.tn.indexOf(q.tutto) !== -1) s += 90;
        s += PESO[u.k] || 5;
        s -= Math.min(12, Math.floor(u.cn.length / 2600));
        return s;
      }

      /* estratto con le corrispondenze evidenziate, calcolato sul testo vero */
      function evidenzia(raw, q, finestra) {
        if (!raw) return "";
        var m = piattoMap(raw);
        var chiavi = [];
        q.frasi.forEach(function (f) { chiavi.push({ s: f, radice: false }); });
        q.termini.forEach(function (x) {
          chiavi.push({ s: x.t, radice: false });
          if (x.r !== x.t) chiavi.push({ s: x.r, radice: true });
        });
        var punti = [];
        chiavi.forEach(function (c) {
          var da = 0, j;
          while (punti.length < 300 && (j = m.s.indexOf(c.s, da)) !== -1) {
            var fin = j + c.s.length;
            if (c.radice) {
              /* una radice si evidenzia solo a inizio parola, e fino alla sua fine */
              if (j !== 0 && m.s[j - 1] !== " ") { da = fin; continue; }
              var sp = m.s.indexOf(" ", fin);
              fin = sp === -1 ? m.s.length : sp;
            }
            punti.push([j, fin]); da = fin;
          }
        });
        function rawA(k) { return k >= m.map.length ? raw.length : m.map[k]; }
        function rawB(k) { return k <= 0 ? 0 : (k - 1 < m.map.length ? m.map[k - 1] + 1 : raw.length); }
        if (!punti.length) {
          var corto = raw.slice(0, rawA(Math.min(finestra, m.s.length)));
          return esc(corto) + (corto.length < raw.length ? "…" : "");
        }
        punti.sort(function (a, b) { return a[0] - b[0]; });
        var fusi = [punti[0].slice()];
        for (var i = 1; i < punti.length; i++) {
          var last = fusi[fusi.length - 1];
          if (punti[i][0] <= last[1]) last[1] = Math.max(last[1], punti[i][1]);
          else fusi.push(punti[i].slice());
        }
        var inizio = Math.max(0, fusi[0][0] - Math.floor(finestra * 0.3));
        var fine = Math.min(m.s.length, inizio + finestra);
        var out = "", cur = inizio;
        fusi.forEach(function (r) {
          if (r[1] <= inizio || r[0] >= fine) return;
          var a = Math.max(r[0], inizio), b = Math.min(r[1], fine);
          out += esc(raw.slice(rawA(cur), rawA(a)));
          out += "<mark>" + esc(raw.slice(rawA(a), rawB(b))) + "</mark>";
          cur = b;
        });
        out += esc(raw.slice(rawA(cur), rawB(fine)));
        return (inizio > 0 ? "…" : "") + out + (fine < m.s.length ? "…" : "");
      }

      /* ---- resa ---- */
      var MAXTOT = 60, MAXGRUPPO = 12;
      var SEMI = ["importanza", "«intenzione esterna»", "treccina", "affossamento", "amalgama", "«accettare e lasciar andare»"];

      function vuoto() {
        esiti.innerHTML =
          '<div class="ric-vuoto">' +
          '<p>Cerca in tutta la mappa: sezioni, blocchi, passaggi, storie, tecniche, porte e vocabolario. ' +
          'Più parole valgono come <b>tutte presenti</b>; per una <b>frase esatta</b> mettila fra virgolette.</p>' +
          '<div class="ric-semi">' + SEMI.map(function (s) {
            return '<button type="button" data-seme="' + esc(s) + '">' + esc(s) + "</button>";
          }).join("") + "</div></div>";
        if (contaEl) contaEl.textContent = "";
      }

      var correnti = [], qCorrente = null;
      function disegna(q) {
        qCorrente = q;
        var esito = [];
        for (var i = 0; i < IDX.length; i++) {
          var s = punteggio(IDX[i], q);
          if (s > 0) esito.push({ u: IDX[i], s: s });
        }
        esito.sort(function (a, b) { return b.s - a.s; });
        if (contaEl) contaEl.textContent = esito.length ? (esito.length + (esito.length === 1 ? " esito" : " esiti")) : "";
        if (!esito.length) {
          esiti.innerHTML = '<div class="ric-vuoto"><p>Nessun risultato. Prova con una parola sola, ' +
            'o togli le virgolette se stavi cercando una frase esatta.</p></div>';
          correnti = [];
          return;
        }
        var gruppi = {};
        esito.forEach(function (r) { (gruppi[r.u.k] = gruppi[r.u.k] || []).push(r); });

        /* i gruppi si ordinano per quanto vale il loro risultato migliore, non
           per un ordine fisso: altrimenti cercando «pendolo» il primo esito
           sarebbe una parte qualsiasi invece della sezione che ne parla. */
        var chiaviG = Object.keys(gruppi).sort(function (a, b) {
          var d = gruppi[b][0].s - gruppi[a][0].s;
          return d !== 0 ? d : ORDINE.indexOf(a) - ORDINE.indexOf(b);
        });

        var html = [], mostrati = 0;
        correnti = [];
        chiaviG.forEach(function (k) {
          var g = gruppi[k];
          if (!g || mostrati >= MAXTOT) return;
          var quanti = Math.min(g.length, MAXGRUPPO, MAXTOT - mostrati);
          html.push('<div class="ric-gruppo"><span>' + esc(ETI[k]) + "</span><span>" +
            g.length + (g.length > quanti ? " (primi " + quanti + ")" : "") + "</span></div>");
          for (var i = 0; i < quanti; i++) {
            var u = g[i].u, n = correnti.length;
            correnti.push(u);
            html.push(
              '<button type="button" class="ric-voce" role="option" data-n="' + n +
              '" style="--c:' + u.col + '">' +
              '<span class="ric-t">' + evidenzia(u.titolo, q, 90) + "</span>" +
              (u.corpo ? '<span class="ric-p">' + evidenzia(u.corpo, q, 170) + "</span>" : "") +
              '<span class="ric-dove"><b>' + esc(ETI[k]) + "</b> · " + esc(u.dove) + "</span></button>");
            mostrati++;
          }
        });
        esiti.innerHTML = html.join("");
        seleziona(0);
      }

      function seleziona(i) {
        var voci = esiti.querySelectorAll(".ric-voce");
        if (!voci.length) return;
        var n = Math.max(0, Math.min(voci.length - 1, i));
        Array.prototype.forEach.call(voci, function (v, j) { v.classList.toggle("sel", j === n); });
        var sel = voci[n];
        if (sel) sel.scrollIntoView({ block: "nearest" });
      }
      function muovi(d) {
        var voci = Array.prototype.slice.call(esiti.querySelectorAll(".ric-voce"));
        if (!voci.length) return;
        var cur = voci.findIndex(function (v) { return v.classList.contains("sel"); });
        seleziona((cur < 0 ? 0 : cur + d + voci.length) % voci.length);
      }

      /* ---- evidenziazione nel punto d'arrivo ----
         Il lampo segnala il blocco, non la parola. Qui le occorrenze cercate
         vengono avvolte in <mark> dentro il testo vero, spezzando solo nodi di
         testo: il markup della pagina non viene toccato, e la rimozione
         ricompone i nodi com'erano. */
      var ECO = [], ecoVia = null;

      function pulisciEco() {
        ECO.forEach(function (m) {
          var pa = m.parentNode;
          if (!pa) return;
          pa.replaceChild(document.createTextNode(m.textContent), m);
          pa.normalize();
        });
        ECO = [];
        if (ecoVia && ecoVia.parentNode) ecoVia.parentNode.removeChild(ecoVia);
        ecoVia = null;
      }

      function evidenziaDom(radice, q) {
        pulisciEco();
        if (!radice || !q) return 0;
        var chiavi = [];
        q.frasi.forEach(function (f) { chiavi.push({ s: f, radice: false }); });
        q.termini.forEach(function (x) {
          chiavi.push({ s: x.t, radice: false });
          if (x.r !== x.t) chiavi.push({ s: x.r, radice: true });
        });
        if (!chiavi.length) return 0;

        var nodi = [], w = document.createTreeWalker(radice, NodeFilter.SHOW_TEXT, {
          acceptNode: function (n) {
            if (!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
            var pa = n.parentNode;
            if (pa && /^(script|style|mark)$/i.test(pa.nodeName)) return NodeFilter.FILTER_REJECT;
            return NodeFilter.FILTER_ACCEPT;
          }
        });
        var n;
        while ((n = w.nextNode())) nodi.push(n);

        nodi.forEach(function (nodo) {
          if (ECO.length > 250) return;
          var raw = nodo.nodeValue, m = piattoMap(raw);
          if (!m.s) return;
          var punti = [];
          chiavi.forEach(function (c) {
            var da = 0, j;
            while ((j = m.s.indexOf(c.s, da)) !== -1) {
              var fin = j + c.s.length;
              if (c.radice) {
                if (j !== 0 && m.s[j - 1] !== " ") { da = fin; continue; }
                var sp = m.s.indexOf(" ", fin);
                fin = sp === -1 ? m.s.length : sp;
              }
              punti.push([j, fin]);
              da = fin;
            }
          });
          if (!punti.length) return;
          punti.sort(function (a, b) { return a[0] - b[0]; });
          var fusi = [punti[0].slice()];
          for (var i = 1; i < punti.length; i++) {
            var last = fusi[fusi.length - 1];
            if (punti[i][0] <= last[1]) last[1] = Math.max(last[1], punti[i][1]);
            else fusi.push(punti[i].slice());
          }
          function rawA(k) { return k >= m.map.length ? raw.length : m.map[k]; }
          function rawB(k) { return k <= 0 ? 0 : (k - 1 < m.map.length ? m.map[k - 1] + 1 : raw.length); }
          /* dall'ultima alla prima, così gli offset precedenti restano validi */
          for (var j2 = fusi.length - 1; j2 >= 0; j2--) {
            var a = rawA(fusi[j2][0]), b = rawB(fusi[j2][1]);
            if (b <= a) continue;
            var coda = nodo.splitText(b), mezzo = nodo.splitText(a);
            var mk = document.createElement("mark");
            mk.className = "ric-eco";
            mezzo.parentNode.replaceChild(mk, mezzo);
            mk.appendChild(mezzo);
            ECO.push(mk);
            void coda;
          }
        });

        if (ECO.length) {
          ecoVia = document.createElement("button");
          ecoVia.type = "button";
          ecoVia.className = "ric-eco-via";
          ecoVia.innerHTML = "<span>" + ECO.length +
            (ECO.length === 1 ? " occorrenza evidenziata" : " occorrenze evidenziate") +
            "</span><kbd>esc</kbd><span>togli</span>";
          ecoVia.addEventListener("click", pulisciEco);
          document.body.appendChild(ecoVia);
        }
        return ECO.length;
      }

      /* ---- apertura del risultato ---- */
      function vai(u) {
        chiudi();
        if (u.k === "voce") {
          if (typeof apriGlossario === "function") apriGlossario();
          var q2 = $("gloss-q2");
          if (q2) { q2.value = u.titolo; q2.dispatchEvent(new Event("input", { bubbles: true })); }
          evidenziaDom($("gloss-panel-list"), qCorrente);
          return;
        }
        if (u.parte) mostra(u.parte);
        if (u.ancora) segna("#" + u.ancora);
        var quante = evidenziaDom(u.el, qCorrente);
        u.el.classList.remove("ric-bersaglio");
        void u.el.offsetWidth;
        u.el.classList.add("ric-bersaglio");
        setTimeout(function () { u.el.classList.remove("ric-bersaglio"); }, 2200);
        /* lo scroll invece aspetta un fotogramma: la parte è appena comparsa */
        requestAnimationFrame(function () {
          /* se una parola è stata evidenziata si va su quella, non sul blocco:
             in una sezione lunga il centro del blocco può essere altrove */
          var primo = quante ? u.el.querySelector("mark.ric-eco") : null;
          (primo || u.el).scrollIntoView({ block: "center" });
          if (typeof aggiornaPartNav === "function") aggiornaPartNav();
        });
      }

      /* ---- apertura e chiusura ---- */
      var attesa = null, ultimaFocus = null;
      function cerca() {
        var q = analizza(campo.value);
        if (q.vuota) { vuoto(); correnti = []; return; }
        disegna(q);
      }
      function apriRic(seme) {
        if (!veil.hidden) return;
        pulisciEco();
        ultimaFocus = document.activeElement;
        veil.hidden = false;
        document.body.style.overflow = "hidden";
        if (typeof seme === "string") campo.value = seme;
        cerca();
        campo.focus();
        campo.select();
      }
      function chiudi() {
        if (veil.hidden) return;
        veil.hidden = true;
        document.body.style.overflow = "";
        if (ultimaFocus && ultimaFocus.focus) { try { ultimaFocus.focus(); } catch (e) { } }
      }

      campo.addEventListener("input", function () {
        clearTimeout(attesa);
        attesa = setTimeout(cerca, 80);
      });
      esiti.addEventListener("click", function (ev) {
        var seme = ev.target.closest && ev.target.closest("[data-seme]");
        if (seme) { campo.value = seme.getAttribute("data-seme"); cerca(); campo.focus(); return; }
        var v = ev.target.closest && ev.target.closest(".ric-voce");
        if (!v) return;
        var u = correnti[+v.getAttribute("data-n")];
        if (u) vai(u);
      });
      veil.addEventListener("mousedown", function (ev) { if (ev.target === veil) chiudi(); });
      if (bottone) bottone.addEventListener("click", function () { apriRic(""); });

      function scrivendo(el) {
        if (!el) return false;
        var tag = (el.tagName || "").toLowerCase();
        return tag === "input" || tag === "textarea" || el.isContentEditable;
      }
      document.addEventListener("keydown", function (e) {
        if ((e.metaKey || e.ctrlKey) && (e.key === "k" || e.key === "K")) {
          e.preventDefault();
          if (veil.hidden) apriRic(""); else chiudi();
          return;
        }
        if (veil.hidden) {
          if (e.key === "Escape" && ECO.length) { e.preventDefault(); pulisciEco(); return; }
          if (e.key === "/" && !scrivendo(e.target) && !e.metaKey && !e.ctrlKey && !e.altKey) {
            e.preventDefault(); apriRic("");
          }
          return;
        }
        if (e.key === "Escape") { e.preventDefault(); chiudi(); }
        else if (e.key === "ArrowDown") { e.preventDefault(); muovi(1); }
        else if (e.key === "ArrowUp") { e.preventDefault(); muovi(-1); }
        else if (e.key === "Enter") {
          e.preventDefault();
          var sel = esiti.querySelector(".ric-voce.sel");
          if (sel) sel.click();
        }
      });

      /* su Windows e Linux la scorciatoia si scrive diversamente */
      var kbd = $("ric-kbd");
      if (kbd && !/Mac|iPhone|iPad/.test(navigator.platform || "")) kbd.textContent = "Ctrl K";

      vuoto();
    })();

  })();