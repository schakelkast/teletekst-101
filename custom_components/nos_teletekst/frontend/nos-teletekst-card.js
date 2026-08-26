/*
 * NOS Teletekst-kaart voor Home Assistant
 * ---------------------------------------
 * Rendert een teletekstpagina exact zoals de NOS hem uitzendt: 40x24 tekens in
 * het originele Android_VeraMono-font, waarin F020-F07F de blokgrafiek bevat,
 * en de acht teletekstkleuren.
 *
 * De JSON-API van de NOS stuurt geen CORS-headers, dus de browser mag hem niet
 * rechtstreeks ophalen. Het verkeer loopt daarom via de bijbehorende integratie,
 * die de pagina serverkant ophaalt en aanbiedt op /api/nos_teletekst/<pagina>.
 *
 * Deze kaart wordt door die integratie automatisch geladen; een Lovelace-resource
 * toevoegen is niet nodig.
 */

const FONT = "veramonofont2web2";
const FONT_URL = "/nos_teletekst_frontend/Android_VeraMono.woff";
const KOLOMMEN = 40;
const REGELS = 25;
// Gemeten aan de NOS-render: tekenbreedte 0,60188 em, regelhoogte 1,2037 em.
const TEKEN_BREEDTE = 0.60188;
const REGEL_HOOGTE = 1.2037;

// Verhouding breedte:hoogte van een teken-cel.
//  - De NOS-website zet 40x25 in een 4:5-vlak; dat geeft smalle, hoge letters.
//  - Op tv staat teletekst op een 4:3-beeld: (4/40) / (3/25) = 0,833. Daar zijn
//    de letters dus flink breder. Dat is het beeld van de schotel.
// De kaart rekt mee met het scherm en stopt bij de tv-verhouding, zodat een
// breed scherm gevuld wordt zonder dat het beeld onnatuurlijk uitgerekt raakt.
const CEL_WEB = TEKEN_BREEDTE / REGEL_HOOGTE; // 0,50
const CEL_TV = (4 / KOLOMMEN) / (3 / REGELS); // 0,833

// Het font moet in het document staan; een @font-face binnen een shadow root
// wordt door de browser genegeerd.
function laadFont() {
  if (document.getElementById("teletekst-font")) return;
  const st = document.createElement("style");
  st.id = "teletekst-font";
  st.textContent =
    "@font-face{font-family:'" + FONT + "';" +
    "src:url('" + FONT_URL + "') format('woff');" +
    "font-weight:normal;font-style:normal;font-display:block;}";
  document.head.appendChild(st);
}

const STIJL = [
  ":host { display:block; }",
  "ha-card { background:#000; border:none; border-radius:0; box-shadow:none; overflow:hidden; padding:0;",
  "  height:100%; display:flex; flex-direction:column; justify-content:center; }",
  ".vak { width:100%; height:100%; display:flex; align-items:center; justify-content:center; gap:12px; }",
  ".vak.onder { flex-direction:column; }",
  ".vak.naast { flex-direction:row; }",
  ".scherm { background:#000; position:relative; overflow:hidden; flex:0 0 auto;",
  "  touch-action:pan-y; }",
  "pre.pagina { margin:0; padding:0; color:#fff; background:#000;",
  "  position:absolute; top:0; left:0; transform-origin:0 0;",
  "  font-family:'" + FONT + "','Vera Mono',monospace;",
  "  line-height:normal; white-space:pre; -webkit-font-smoothing:initial;",
  "  font-variant-ligatures:none; text-rendering:optimizeSpeed; }",
  // De acht teletekstkleuren, exact zoals de NOS ze definieert.
  "pre.pagina *.black{color:#000}   pre.pagina *.bg-black{background:#000}",
  "pre.pagina *.red{color:#f00}     pre.pagina *.bg-red{background:#f00}",
  "pre.pagina *.green{color:#0f0}   pre.pagina *.bg-green{background:#0f0}",
  "pre.pagina *.yellow{color:#ff0}  pre.pagina *.bg-yellow{background:#ff0}",
  "pre.pagina *.blue{color:#00f}    pre.pagina *.bg-blue{background:#00f}",
  "pre.pagina *.magenta{color:#f0f} pre.pagina *.bg-magenta{background:#f0f}",
  "pre.pagina *.cyan{color:#0ff}    pre.pagina *.bg-cyan{background:#0ff}",
  "pre.pagina *.white{color:#fff}   pre.pagina *.bg-white{background:#fff}",
  // Het horizontaal rekken legt de rand tussen twee gekleurde vlakken op een
  // halve pixel, waar de browser een haarlijn tekent. Elk vlakje krijgt daarom
  // een fractie extra achtergrond naar rechts, met een even grote negatieve
  // marge zodat de tekst geen millimeter opschuift.
  "pre.pagina span, pre.pagina a { padding-right:.03em; margin-right:-.03em; }",
  "pre.pagina a { color:inherit; text-decoration:none; cursor:pointer; }",
  "pre.pagina a:hover { outline:1px solid rgba(255,255,255,.6); }",
  ".balk { background:#000; color:#fff; font-family:'" + FONT + "','Vera Mono',monospace;",
  "  display:flex; flex-direction:column; gap:.35em; padding:.5em; flex:0 0 auto; }",
  ".vak.onder .balk { width:100%; }",
  ".rij { display:flex; gap:.25em; align-items:stretch; justify-content:center; flex-wrap:wrap; }",
  ".knop { flex:0 0 auto; cursor:pointer; user-select:none; background:#000;",
  "  border:none; border-radius:0; font-family:inherit; font-size:inherit; line-height:1.3;",
  "  padding:.45em .2em; text-align:center; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }",
  ".knop:disabled { opacity:.25; cursor:default; }",
  ".knop:not(:disabled):hover { background:#222; }",
  ".scheiding { color:#444; align-self:center; padding-inline:.5em; }",
  ".sublabel { color:#888; align-self:center; }",
  ".nav { color:#fff; flex:0 0 auto; padding-inline:.9em; }",
  ".nummer { flex:0 0 auto; width:5em; text-align:center; background:#000; color:#ff0;",
  "  border:1px solid #444; font-family:inherit; font-size:inherit; padding:.4em 0; }",
  ".nummer:focus { outline:1px solid #ff0; }",
  ".status { color:#888; text-align:center; font-size:.85em; }",
  ".status b { color:#0f0; font-weight:normal; }",
  ".fout { color:#f00; }",
  // Aanraakbediening: een cijferblok over de pagina, zoals je op de
  // afstandsbediening een paginanummer intikt.
  ".toetsen { position:absolute; inset:0; background:rgba(0,0,0,.86); z-index:2;",
  "  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:min(3vh,3vw); }",
  ".toetsen.verborgen { display:none; }",
  ".invoer { color:#ff0; font-size:min(6vh,6vw); letter-spacing:.2em; line-height:1; }",
  ".toetsrij { display:grid; grid-template-columns:repeat(3,1fr); gap:2.5%; width:62%; }",
  ".toets { background:#111; color:#fff; border:1px solid #333; border-radius:6px;",
  "  font-family:inherit; font-size:min(7vh,7vw); line-height:1; padding:.45em 0;",
  "  cursor:pointer; touch-action:manipulation; user-select:none; }",
  ".toets:active { background:#00f; }",
  ".toets.wis { color:#f00; } .toets.sluit { color:#0f0; }",
  // Op een aanraakscherm moeten de knoppen groter zijn dan de muisversie.
  "@media (pointer: coarse) { .knop { padding:.7em .55em; } .nummer { padding:.6em 0; width:5.5em; } }",
].join("\n");

class NosTeletekstKaart extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._pagina = "100";
    this._data = null;
    this._bezig = false;
    this._timer = null;
    this._ratio = TEKEN_BREEDTE;
  }

  static getStubConfig() {
    return { page: "100", refresh: 60 };
  }

  setConfig(config) {
    this._config = Object.assign(
      { page: "100", refresh: 60, controls: true, max_height: 0, aspect: "auto" },
      config || {}
    );
    this._pagina = String(this._config.page);
    laadFont();
    this._bouw();
  }

  set hass(hass) {
    const eerste = !this._hass;
    this._hass = hass;
    if (eerste) this._haal();
  }

  getCardSize() {
    return this._config && this._config.controls ? 14 : 12;
  }

  connectedCallback() {
    this._startTimer();
    if (this._obs && this._scherm) this._obs.observe(this._scherm);
    if (!this._opResize) this._opResize = () => this._schaal();
    window.addEventListener("resize", this._opResize);
  }

  disconnectedCallback() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
    if (this._obs) this._obs.disconnect();
    if (this._opResize) window.removeEventListener("resize", this._opResize);
  }

  // ---------------------------------------------------------------- opbouw

  _bouw() {
    const root = this.shadowRoot;
    root.innerHTML =
      "<ha-card>" +
      '<div class="vak onder">' +
      '<div class="scherm"><pre class="pagina"></pre>' +
      '<div class="toetsen verborgen"><div class="invoer"></div>' +
      '<div class="toetsrij"></div></div></div>' +
      (this._config.controls ? '<div class="balk"></div>' : "") +
      "</div></ha-card>";

    this._vak = root.querySelector(".vak");
    this._scherm = root.querySelector(".scherm");
    this._toetsen = root.querySelector(".toetsen");
    this._pre = root.querySelector("pre.pagina");
    this._balk = root.querySelector(".balk");

    const st = document.createElement("style");
    st.textContent = STIJL;
    root.appendChild(st);

    this._pre.addEventListener("click", (e) => this._klikInPagina(e));
    this._bouwToetsen();
    this._swipeAan();
    // Cijfers intikken werkt zoals op de afstandsbediening: drie cijfers en hij springt.
    this.setAttribute("tabindex", "0");
    this.addEventListener("keydown", (e) => this._toetsAanslag(e));

    this._obs = new ResizeObserver(() => this._schaal());
    if (this.isConnected) this._obs.observe(this._scherm);

    // Zodra het font echt geladen is klopt de meting pas.
    if (document.fonts && document.fonts.load) {
      document.fonts.load("16px " + FONT).then(() => this._meet());
    }
    this._meet();
    this._startTimer();
  }

  /** Meet de werkelijke tekenbreedte, zodat 40 kolommen exact passen. */
  _meet() {
    const proef = document.createElement("span");
    proef.style.cssText =
      "position:absolute;visibility:hidden;white-space:pre;font-size:200px;" +
      "font-family:'" + FONT + "','Vera Mono',monospace";
    proef.textContent = "M".repeat(KOLOMMEN);
    document.body.appendChild(proef);
    const breedte = proef.getBoundingClientRect().width;
    proef.remove();
    if (breedte > 0) this._ratio = breedte / KOLOMMEN / 200;
    this._schaal();
  }

  /** Schaalt de pagina zo groot mogelijk binnen de ruimte die er echt is.
   *
   * De beschikbare hoogte wordt gemeten vanaf de positie van het scherm zelf,
   * zodat kop, navigatiebalk en knoppenbalk automatisch meetellen. Daarna
   * bepaalt de vorm van die ruimte hoe breed een teken-cel wordt: op een smal
   * scherm de NOS-verhouding, op een breed scherm die van tv, nooit breder.
   */
  _schaal() {
    if (!this._scherm || !this._vak) return;

    // De knoppenbalk schaalt op vensterhoogte, niet op paginagrootte: anders
    // beinvloeden de twee elkaar en blijft het schalen heen en weer springen.
    const bf = Math.max(10, Math.min(16, window.innerHeight * 0.021));
    if (this._balk) this._balk.style.fontSize = bf + "px";

    const totaalB = this._vak.clientWidth;
    if (!totaalB) return;

    let totaalH = Number(this._config.max_height) || 0;
    if (!totaalH) {
      const boven = this._vak.getBoundingClientRect().top;
      totaalH = window.innerHeight - Math.max(0, boven) - 8;
    }
    if (!(totaalH > 140)) totaalH = (totaalB * REGELS * CEL_WEB) / KOLOMMEN;

    // Vaste schattingen, zodat de keuze niet van de vorige uitkomst afhangt.
    const balkH = this._balk ? Math.round(bf * 3.6 + 18) : 0;
    const balkB = this._balk ? Math.max(150, Math.min(240, totaalB * 0.17)) : 0;
    const kier = 12;

    // Twee kandidaten: bediening onder de pagina, of ernaast in de zwarte rand.
    // De grootste pagina wint, dus op een breed scherm schuift de balk vanzelf
    // naar de zijkant en krijgt de pagina de volle hoogte.
    const onder = this._past(totaalB, totaalH - balkH - kier);
    const naast = this._balk ? this._past(totaalB - balkB - kier, totaalH) : null;
    const naastWint = naast && naast.celB * naast.celH > onder.celB * onder.celH;
    const gekozen = naastWint ? naast : onder;

    this._vak.classList.toggle("naast", !!naastWint);
    this._vak.classList.toggle("onder", !naastWint);
    if (this._balk) this._balk.style.width = naastWint ? balkB + "px" : "";

    // Celbreedte en -hoogte op hele beeldpunten afronden. Zonder dat landen de
    // randen tussen twee gekleurde vlakken op een halve pixel en tekent de
    // browser daar een haarlijn.
    const dpr = window.devicePixelRatio || 1;
    const celB = Math.max(1, Math.round(gekozen.celB * dpr)) / dpr;
    const celH = Math.max(1, Math.round(gekozen.celH * dpr)) / dpr;

    const fs = celH / REGEL_HOOGTE;
    this._scherm.style.width = celB * KOLOMMEN + "px";
    this._scherm.style.height = celH * REGELS + "px";
    this._pre.style.fontSize = fs + "px";
    this._pre.style.transform = "scaleX(" + celB / (fs * this._ratio) + ")";
  }

  /** Grootste cel die in deze doos past, binnen de toegestane verhouding. */
  _past(breedte, hoogte) {
    if (!(breedte > 0)) breedte = 1;
    if (!(hoogte > 0)) hoogte = 1;
    const grens = this._grenzen();
    let ar = breedte / KOLOMMEN / (hoogte / REGELS);
    ar = Math.min(Math.max(ar, grens[0]), grens[1]);
    let celH = hoogte / REGELS;
    let celB = celH * ar;
    if (celB * KOLOMMEN > breedte) {
      celB = breedte / KOLOMMEN;
      celH = celB / ar;
    }
    return { celB: celB, celH: celH };
  }

  /** Toegestane celverhouding: 'web' = smal als nos.nl, 'tv' = breed als 4:3. */
  _grenzen() {
    const v = String(this._config.aspect || "auto").toLowerCase();
    if (v === "web") return [CEL_WEB, CEL_WEB];
    if (v === "tv") return [CEL_TV, CEL_TV];
    return [CEL_WEB, CEL_TV];
  }

  _startTimer() {
    if (this._timer) clearInterval(this._timer);
    const s = Number(this._config && this._config.refresh);
    if (s > 0) this._timer = setInterval(() => this._haal(true), s * 1000);
  }

  // ------------------------------------------------------------- ophalen

  async _haal(stil) {
    if (!this._hass || this._bezig) return;
    this._bezig = true;
    if (!stil) this._status("pagina " + this._pagina + " wordt opgehaald...");
    try {
      const data = await this._hass.callApi(
        "GET",
        "nos_teletekst/" + encodeURIComponent(this._pagina)
      );
      if (!data || !data.content) throw new Error("lege pagina ontvangen");
      this._data = data;
      this._fout = null;
      this._teken();
    } catch (err) {
      this._fout = this._foutTekst(err);
      this._tekenBalk();
      this._status(null);
    } finally {
      this._bezig = false;
    }
  }

  /** De integratie geeft bij een fout een leesbare reden mee. */
  _foutTekst(err) {
    if (err && err.body && err.body.fout) return err.body.fout;
    if (err && err.status_code === 404) return "pagina " + this._pagina + " bestaat niet";
    if (err && err.status_code === 401) return "niet ingelogd";
    if (err && err.message) return err.message;
    return String(err);
  }

  ga(pagina) {
    const p = String(pagina || "").trim();
    if (!p) return;
    this._pagina = p;
    this._haal();
  }

  // -------------------------------------------------------------- tekenen

  _teken() {
    // De API levert kant-en-klare teletekst-HTML: spans met kleurklassen en
    // F020-F07F-tekens voor de blokgrafiek. Die gaat er ongewijzigd in.
    this._pre.innerHTML = this._data.content || "";
    this._schaal();
    this._tekenBalk();
    this._status(null);
  }

  _tekenBalk() {
    if (!this._balk) return;
    const d = this._data || {};

    // De gekleurde fastText-regel staat al onderaan de pagina zelf en is daar
    // gewoon aanklikbaar (<a id="fastText1Red" ...>), dus die wordt hier niet
    // nog eens herhaald. Alleen wat teletekst niet in beeld heeft staan:
    // bladeren, subpagina's en een invoerveld.
    const sub = d.prevSubPage || d.nextSubPage;
    const subKnoppen = sub
      ? '<span class="scheiding">&middot;</span>' +
        '<button class="knop nav" data-ga="' + (d.prevSubPage || "") + '"' +
        (d.prevSubPage ? "" : " disabled") + ' title="vorige subpagina">&#9664;</button>' +
        '<span class="sublabel">sub</span>' +
        '<button class="knop nav" data-ga="' + (d.nextSubPage || "") + '"' +
        (d.nextSubPage ? "" : " disabled") + ' title="volgende subpagina">&#9654;</button>'
      : "";

    this._balk.innerHTML =
      '<div class="rij">' +
      '<button class="knop nav" data-ga="' + (d.prevPage || "") + '"' +
      (d.prevPage ? "" : " disabled") + ' title="vorige pagina">&#9664;</button>' +
      '<input class="nummer" type="text" inputmode="numeric" maxlength="5" value="' +
      this._pagina + '" aria-label="paginanummer">' +
      '<button class="knop nav" data-ga="' + (d.nextPage || "") + '"' +
      (d.nextPage ? "" : " disabled") + ' title="volgende pagina">&#9654;</button>' +
      subKnoppen +
      "</div>" +
      '<div class="status"></div>';

    const self = this;
    this._balk.querySelectorAll("button[data-ga]").forEach(function (b) {
      b.addEventListener("click", function () {
        self.ga(b.dataset.ga);
      });
    });
    const inv = this._balk.querySelector(".nummer");
    if (inv) {
      inv.addEventListener("keydown", function (e) {
        if (e.key === "Enter") { self.ga(inv.value); inv.blur(); }
      });
      inv.addEventListener("focus", function () { inv.select(); });
      // Op een aanraakscherm is er vaak geen toetsenbord: dan het cijferblok.
      inv.addEventListener("pointerdown", function (e) {
        if (e.pointerType === "touch") {
          e.preventDefault();
          inv.blur();
          self._openToetsen();
        }
      });
      inv.addEventListener("blur", function () {
        if (inv.value.trim() && inv.value.trim() !== self._pagina) self.ga(inv.value);
      });
    }
  }

  _status(tekst) {
    const el = this._balk && this._balk.querySelector(".status");
    if (!el) return;
    if (this._fout) {
      el.innerHTML = '<span class="fout">' + this._fout + "</span>";
      return;
    }
    if (tekst) {
      el.textContent = tekst;
      return;
    }
    const nu = new Date();
    const tijd =
      String(nu.getHours()).padStart(2, "0") + ":" + String(nu.getMinutes()).padStart(2, "0");
    el.innerHTML = "pagina <b>" + this._pagina + "</b> &middot; bijgewerkt " + tijd;
  }

  // ------------------------------------------------------ aanraakbediening

  /** Cijferblok, zoals het intikken van een paginanummer op de afstandsbediening. */
  _bouwToetsen() {
    if (!this._toetsen) return;
    const rij = this._toetsen.querySelector(".toetsrij");
    const namen = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "wis", "0", "sluit"];
    rij.innerHTML = namen
      .map(function (k) {
        if (k === "wis") return '<button class="toets wis" data-toets="wis">&#9003;</button>';
        if (k === "sluit") return '<button class="toets sluit" data-toets="sluit">&#10005;</button>';
        return '<button class="toets" data-toets="' + k + '">' + k + "</button>";
      })
      .join("");

    const self = this;
    rij.querySelectorAll(".toets").forEach(function (b) {
      b.addEventListener("click", function () {
        const t = b.dataset.toets;
        if (t === "sluit") self._sluitToetsen();
        else if (t === "wis") self._cijfers = "";
        else self._cijfer(t);
        self._toonInvoer();
      });
    });
  }

  _openToetsen() {
    if (!this._toetsen) return;
    this._cijfers = "";
    this._toetsen.classList.remove("verborgen");
    this._toonInvoer();
  }

  _sluitToetsen() {
    if (!this._toetsen) return;
    this._cijfers = "";
    this._toetsen.classList.add("verborgen");
  }

  /** Drie cijfers vormen een paginanummer; dan springt hij vanzelf. */
  _cijfer(d) {
    this._cijfers = ((this._cijfers || "") + d).slice(0, 3);
    if (this._cijfers.length === 3) {
      const p = this._cijfers;
      this._sluitToetsen();
      this.ga(p);
    }
  }

  _toonInvoer() {
    const el = this._toetsen && this._toetsen.querySelector(".invoer");
    if (!el) return;
    const c = this._cijfers || "";
    el.textContent = (c + "___").slice(0, 3).split("").join(" ");
  }

  _toetsAanslag(e) {
    if (e.key >= "0" && e.key <= "9") {
      if (this._toetsen && this._toetsen.classList.contains("verborgen")) this._openToetsen();
      this._cijfer(e.key);
      this._toonInvoer();
      return;
    }
    const d = this._data || {};
    if (e.key === "ArrowRight") this.ga(d.nextPage);
    else if (e.key === "ArrowLeft") this.ga(d.prevPage);
    else if (e.key === "ArrowDown") this.ga(d.nextSubPage);
    else if (e.key === "ArrowUp") this.ga(d.prevSubPage);
    else if (e.key === "Escape") this._sluitToetsen();
  }

  /** Vegen over de pagina bladert, net als in de NOS-app. */
  _swipeAan() {
    const el = this._scherm;
    if (!el) return;
    let x0 = 0, y0 = 0, t0 = 0, bezig = false;
    const self = this;
    el.addEventListener("pointerdown", function (e) {
      x0 = e.clientX; y0 = e.clientY; t0 = Date.now(); bezig = true;
    });
    el.addEventListener("pointercancel", function () { bezig = false; });
    el.addEventListener("pointerup", function (e) {
      if (!bezig) return;
      bezig = false;
      if (Date.now() - t0 > 900) return;
      const dx = e.clientX - x0;
      const dy = e.clientY - y0;
      const d = self._data || {};
      if (Math.abs(dx) > 55 && Math.abs(dx) > Math.abs(dy) * 1.5) {
        self.ga(dx < 0 ? d.nextPage : d.prevPage);
      } else if (Math.abs(dy) > 55 && Math.abs(dy) > Math.abs(dx) * 1.5) {
        self.ga(dy < 0 ? d.nextSubPage : d.prevSubPage);
      }
    });
  }

  /** Paginanummers in de tekst zijn links (href="#101") — die vangen we af. */
  _klikInPagina(e) {
    const a = e.target.closest("a[href]");
    if (!a) return;
    e.preventDefault();
    const href = a.getAttribute("href") || "";
    const m = href.match(/#?(\d{3}(?:-\d+)?)/);
    if (m) this.ga(m[1]);
  }
}

customElements.define("nos-teletekst-card", NosTeletekstKaart);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "nos-teletekst-card",
  name: "NOS Teletekst",
  description: "Teletekstpagina's van de NOS, in de originele opmaak.",
  preview: true,
});

console.info(
  "%c NOS-TELETEKST-CARD %c geladen ",
  "background:#00f;color:#fff",
  "background:#ff0;color:#000"
);
