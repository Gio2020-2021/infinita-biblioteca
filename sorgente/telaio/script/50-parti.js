    /* ---------- commutatore delle parti ---------- */
    var PARTI = {{PARTI}};
    var bottoni = Array.prototype.slice.call(document.querySelectorAll("nav.parts button"));
    var barra = document.querySelector("nav.parts");

    function partediEl(el) {
      while (el && el !== document.body) {
        if (el.classList && el.classList.contains("part")) return el;
        el = el.parentNode;
      }
      return null;
    }
    function allaBarra() {
      if (!barra) return;
      window.scrollTo(0, barra.offsetTop);
    }
    function mostra(nome) {
      var ok = false;
      PARTI.forEach(function (p) {
        var el = document.getElementById("parte-" + p);
        if (!el) return;
        var acceso = (p === nome);
        el.classList.toggle("on", acceso);
        if (acceso) ok = true;
      });
      bottoni.forEach(function (b) {
        b.setAttribute("aria-current", b.getAttribute("data-part") === nome ? "true" : "false");
      });
      popolaPartNav(nome);
      return ok;
    }
    function popolaPartNav(nome) {
      var partNav = $("part-nav");
      if (!partNav) return;
      var parte = document.getElementById("parte-" + nome);
      var toc = parte && parte.querySelector(".part-head .part-toc");
      partNav.innerHTML = "";
      if (toc) {
        partNav.style.setProperty("--pc", parte.style.getPropertyValue("--pc"));
        toc.querySelectorAll("a").forEach(function (a, i) {
          var voce = a.cloneNode(true);
          if (i === 0) voce.classList.add("cur");
          partNav.appendChild(voce);
        });
      }
      aggiornaPartNav();
    }
    /* il pannello si accende solo quando i badge in testa alla parte sono
       usciti sopra la barra: si ricalcola sempre dalla posizione reale, così
       non resta spento dopo un click su una sua voce */
    function aggiornaPartNav() {
      var partNav = $("part-nav");
      if (!partNav) return;
      var parte = document.querySelector(".part.on");
      var toc = parte && parte.querySelector(".part-head .part-toc");
      var acceso = !!toc && partNav.children.length > 0 &&
        toc.getBoundingClientRect().bottom < 104;
      partNav.classList.toggle("on", acceso);
    }
    function segna(hash) {
      try { history.replaceState(null, "", hash); } catch (e) { /* sandbox */ }
    }
    function instrada(hash, primaVolta) {
      var id = (hash || "").replace(/^#/, "");
      if (!id) { mostra("casa"); return; }
      if (id.indexOf("parte-") === 0) {
        if (mostra(id.slice(6))) { if (!primaVolta) allaBarra(); }
        else mostra("casa");
        return;
      }
      var bersaglio = document.getElementById(id);
      if (!bersaglio) { mostra("casa"); return; }
      var p = partediEl(bersaglio);
      mostra(p ? p.id.replace("parte-", "") : "casa");
      requestAnimationFrame(function () {
        bersaglio.scrollIntoView({ behavior: primaVolta ? "auto" : "smooth", block: "start" });
      });
    }

    bottoni.forEach(function (b) {
      b.addEventListener("click", function () {
        var nome = b.getAttribute("data-part");
        mostra(nome);
        allaBarra();
        segna("#parte-" + nome);
      });
    });
    if (gN) {
      gN.addEventListener("click", function (ev) {
        var a = ev.target.closest ? ev.target.closest("a") : null;
        if (!a) return;
        var h = a.getAttribute("href") || "";
        if (h.indexOf("#parte-") !== 0) return;
        ev.preventDefault();
        mostra(h.slice(7));
        allaBarra();
        segna(h);
      });
    }
    window.addEventListener("hashchange", function () { instrada(location.hash, false); });
    instrada(location.hash, true);
