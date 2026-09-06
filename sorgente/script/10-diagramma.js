  (function () {
    "use strict";

    /* ---------- diagramma radiale ---------- */
    var BRANCHES = [
      { n: "I", t: "IL TERRENO", id: "parte-terreno", c: "--blue" },
      { n: "II", t: "COSA TI SOTTRAE", id: "parte-avversario", c: "--rust" },
      { n: "III", t: "COSA HAI TU", id: "parte-forze", c: "--sage" },
      { n: "IV", t: "L'OFFICINA", id: "parte-officina", c: "--amber" },
      { n: "V", t: "GLI ALTRI", id: "parte-altri", c: "--sage" },
      { n: "VI", t: "COORDINAZIONE", id: "parte-coordinazione", c: "--amber" },
      { n: "VII", t: "LO SPECCHIO", id: "parte-specchio", c: "--amber" },
      { n: "VIII", t: "LA TECNOSFERA", id: "parte-tecnosfera", c: "--rust" },
      { n: "IX", t: "LE STORIE", id: "parte-aneddoti", c: "--plum" },
      { n: "X", t: "RIFERIMENTI", id: "parte-riferimenti", c: "--blue" },
      { n: "XI", t: "LE ALTRE VOCI", id: "parte-voci", c: "--teal" }
    ];
    var NS = "http://www.w3.org/2000/svg";
    var gN = document.getElementById("nodes"), gS = document.getElementById("spokes");
    if (gN && gS) {
      var CX = 550, CY = 380, RX = 400, RY = 278, W = 156, H = 44;
      BRANCHES.forEach(function (b, i) {
        var a = -Math.PI / 2 + i * (2 * Math.PI / BRANCHES.length);
        var x = CX + RX * Math.cos(a), y = CY + RY * Math.sin(a);
        var ln = document.createElementNS(NS, "line");
        ln.setAttribute("class", "spoke");
        ln.setAttribute("x1", CX); ln.setAttribute("y1", CY);
        ln.setAttribute("x2", Math.round(x)); ln.setAttribute("y2", Math.round(y));
        gS.appendChild(ln);

        var a2 = document.createElementNS(NS, "a");
        a2.setAttribute("class", "node-g");
        a2.setAttribute("href", "#" + b.id);
        a2.setAttribute("aria-label", "Ramo " + b.n + ": " + b.t);
        var r = document.createElementNS(NS, "rect");
        r.setAttribute("class", "node-box");
        r.setAttribute("x", Math.round(x - W / 2)); r.setAttribute("y", Math.round(y - H / 2));
        r.setAttribute("width", W); r.setAttribute("height", H); r.setAttribute("rx", 3);
        r.setAttribute("stroke", "var(" + b.c + ")");
        a2.appendChild(r);
        var t1 = document.createElementNS(NS, "text");
        t1.setAttribute("class", "node-i"); t1.setAttribute("x", Math.round(x));
        t1.setAttribute("y", Math.round(y - 7)); t1.setAttribute("text-anchor", "middle");
        t1.setAttribute("fill", "var(" + b.c + ")");
        t1.textContent = b.n;
        a2.appendChild(t1);
        var t2 = document.createElementNS(NS, "text");
        t2.setAttribute("class", "node-t"); t2.setAttribute("x", Math.round(x));
        t2.setAttribute("y", Math.round(y + 11)); t2.setAttribute("text-anchor", "middle");
        t2.textContent = b.t;
        a2.appendChild(t2);
        gN.appendChild(a2);
      });
    }
