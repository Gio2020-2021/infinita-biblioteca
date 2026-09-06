    /* ---------- helpers ---------- */
    var $ = function (id) { return document.getElementById(id); };
    function say(el, msg, cls) { if (!el) return; el.textContent = msg || ""; el.className = "note" + (cls ? " " + cls : ""); }
    function when(ts) {
      var d = new Date(ts);
      if (isNaN(d)) return "";
      return d.toLocaleDateString("it-IT", { day: "2-digit", month: "short" }) + " · " +
        d.toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" });
    }
