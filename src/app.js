/* Skerry Arcade: site script. No dependencies. */
(() => {
  "use strict";
  const DATA = window.SKERRY || { games: [] };
  const GAMES = Object.fromEntries(DATA.games.map(g => [g.slug, g]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const isPhone = () => matchMedia("(hover: none) and (pointer: coarse)").matches || innerWidth < 760;

  /* ---------------- analytics, only after consent ---------------- */
  const GA_ID = document.documentElement.dataset.ga || "";
  function track(name, params) { try { window.gtag && window.gtag("event", name, params || {}); } catch (e) {} }
  function loadGA() {
    if (!GA_ID || window.gtag) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date()); gtag("config", GA_ID, { anonymize_ip: true });
    const s = document.createElement("script"); s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_ID);
    document.head.appendChild(s);
  }
  function consent() {
    if (!GA_ID) return;
    const c = store.get("skerry.consent", null);
    if (c === "yes") return loadGA();
    if (c === "no") return;
    const box = document.createElement("div");
    box.className = "consent"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Analytics");
    box.innerHTML = '<p>May we count visits with Google Analytics? It shows us which games people enjoy. No ads, no personal profile. <a href="' + (DATA.privacy || "/privacy/") + '">Privacy</a></p><div class="btns"><button class="pill-btn sun" data-c="yes">Allow</button><button class="pill-btn" data-c="no">No thanks</button></div>';
    box.addEventListener("click", e => {
      const v = e.target.closest("[data-c]"); if (!v) return;
      store.set("skerry.consent", v.dataset.c); box.remove(); if (v.dataset.c === "yes") loadGA();
    });
    document.body.appendChild(box);
  }

  /* ---------------- toast ---------------- */
  let toastT;
  function toast(msg) {
    let t = $(".toast"); if (!t) { t = document.createElement("div"); t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg; t.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 2200);
  }

  /* ---------------- tiles built in the browser ---------------- */
  function tileHTML(g) {
    const b = (g.isNew ? '<span class="badge">New</span>' : "") + (g.duo ? '<span class="badge duo">2 Player</span>' : "");
    return '<a class="tile" href="' + g.href + '" style="--g:' + g.accent + '"><img src="' + g.thumb + '" alt="' + esc(g.title) + '" width="640" height="360" loading="lazy">' +
      (b ? '<span class="badges">' + b + "</span>" : "") + '<span class="name">' + esc(g.title) + "</span></a>";
  }

  /* ---------------- continue playing ---------------- */
  function remember(slug) {
    const list = store.get("skerry.recent", []).filter(s => s !== slug);
    list.unshift(slug); store.set("skerry.recent", list.slice(0, 12));
  }
  function renderRecent() {
    $$("[data-recent]").forEach(sec => {
      const list = store.get("skerry.recent", []).filter(s => GAMES[s]);
      if (!list.length) { sec.hidden = true; return; }
      $(".tiles", sec).innerHTML = list.map(s => tileHTML(GAMES[s])).join("");
      sec.hidden = false;
    });
  }

  /* ---------------- search ---------------- */
  const norm = s => String(s).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  function find(q) {
    q = norm(q).trim(); if (!q) return [];
    const words = q.split(/\s+/);
    return DATA.games.map(g => {
      const title = norm(g.title), hay = norm([g.title, g.tagline, g.cats.join(" "), g.tags.join(" ")].join(" "));
      if (!words.every(w => hay.includes(w))) return null;
      return { g, score: (title.startsWith(q) ? 3 : 0) + (title.includes(q) ? 2 : 0) + (norm(g.cats.join(" ")).includes(q) ? 1 : 0) };
    }).filter(Boolean).sort((a, b) => b.score - a.score).map(r => r.g);
  }
  function initSearch() {
    $$("[data-search]").forEach(form => {
      const input = $("input", form), box = $(".results", form);
      let sel = -1, hits = [];
      const close = () => { box.hidden = true; sel = -1; };
      const render = () => {
        hits = find(input.value).slice(0, 8);
        if (!input.value.trim()) return close();
        box.innerHTML = hits.length ? hits.map((g, i) => '<a href="' + g.href + '"' + (i === sel ? ' class="sel"' : "") + '><img src="' + g.thumb + '" alt=""><span><b>' + esc(g.title) + "</b><small>" + esc(g.cats.join(", ")) + "</small></span></a>").join("")
          : '<div class="none">No games match \u201C' + esc(input.value.trim()) + '\u201D. Try a category, such as action or sports.</div>';
        box.hidden = false;
      };
      input.addEventListener("input", () => { sel = -1; render(); });
      input.addEventListener("focus", render);
      input.addEventListener("keydown", e => {
        if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); if (!hits.length) return; sel = (sel + (e.key === "ArrowDown" ? 1 : hits.length - 1)) % hits.length; render(); }
        if (e.key === "Escape") { close(); input.blur(); }
      });
      form.addEventListener("submit", e => {
        e.preventDefault();
        const pick = hits[sel >= 0 ? sel : -1];
        if (pick) { location.href = pick.href; return; }
        if (hits.length === 1) { location.href = hits[0].href; return; }
        const base = form.getAttribute("action") || "/search/";
        if (base.startsWith("#")) { location.hash = "search"; showSearch(input.value); }
        else location.href = base + "?q=" + encodeURIComponent(input.value.trim());
        close();
      });
      document.addEventListener("click", e => { if (!form.contains(e.target)) close(); });
    });
    addEventListener("keydown", e => {
      if (e.key === "/" && !/input|textarea/i.test((document.activeElement || {}).tagName || "")) { const i = $("[data-search] input"); if (i) { e.preventDefault(); i.focus(); } }
    });
    const q = new URLSearchParams(location.search).get("q");
    if ($("[data-search-results]")) showSearch(q || "");
  }
  function showSearch(q) {
    const out = $("[data-search-results]"); if (!out) return;
    const hits = find(q || "");
    const title = $("[data-search-title]"), sub = $("[data-search-sub]");
    const input = $("[data-search] input"); if (input && q) input.value = q;
    if (!q) { title.textContent = "Search"; out.innerHTML = DATA.games.map(tileHTML).join(""); return; }
    title.textContent = "Results for \u201C" + q + "\u201D";
    sub.textContent = hits.length ? (hits.length === 1 ? "1 game" : hits.length + " games") : "Nothing matched. Here is everything else you can play.";
    out.innerHTML = (hits.length ? hits : DATA.games).map(tileHTML).join("");
  }

  /* ---------------- random game ---------------- */
  function initRandom() {
    $$("[data-random]").forEach(b => b.addEventListener("click", () => {
      const here = (document.querySelector("[data-game]:not([hidden] *)") || {}).dataset;
      const pool = DATA.games.filter(g => !here || g.slug !== here.game);
      const g = pool[Math.floor(Math.random() * pool.length)];
      if (g) { track("random_game", { game: g.slug }); location.href = g.href; }
    }));
  }

  /* ---------------- spotlight dots (phones) ---------------- */
  function initSpot() {
    $$("[data-spot]").forEach(spot => {
      const dots = spot.nextElementSibling ? $$("i", spot.nextElementSibling) : [];
      if (!dots.length) return;
      const upd = () => {
        const kids = Array.from(spot.children); const x = spot.scrollLeft;
        let best = 0, bd = 1e9; kids.forEach((k, i) => { const d = Math.abs(k.offsetLeft - spot.offsetLeft - x); if (d < bd) { bd = d; best = i; } });
        dots.forEach((d, i) => d.classList.toggle("on", i === best));
      };
      spot.addEventListener("scroll", () => requestAnimationFrame(upd), { passive: true }); upd();
    });
  }

  /* ---------------- hover previews (when a game has a video) ---------------- */
  function initVideos() {
    if (matchMedia("(hover: none)").matches) return;
    $$(".tile[data-video]").forEach(t => {
      let v;
      t.addEventListener("mouseenter", () => {
        if (!v) { v = document.createElement("video"); v.muted = true; v.loop = true; v.playsInline = true; v.preload = "none"; v.src = t.dataset.video; t.insertBefore(v, t.children[1]); }
        v.play().then(() => t.classList.add("vid")).catch(() => {});
      });
      t.addEventListener("mouseleave", () => { if (v) { v.pause(); t.classList.remove("vid"); } });
    });
  }

  /* ---------------- player ---------------- */
  const ICON_BACK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>';
  const ICON_ROT = '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="14" width="30" height="20" rx="4"/><path d="M20 6a14 14 0 0 1 14 6M34 6v6h-6"/></svg>';
  let overlay = null, overlayOpen = false;
  function buildOverlay() {
    overlay = document.createElement("div");
    overlay.className = "player"; overlay.hidden = true;
    overlay.innerHTML = '<div class="bar"><button type="button" data-close>' + ICON_BACK + 'Back</button><span class="name"><img alt=""><span></span></span></div><div class="host"><div class="rotate">' + ICON_ROT + '<b>Turn your phone sideways</b><span>This game plays best in landscape.</span><button type="button" class="pill-btn" data-rot>Play in portrait</button></div></div>';
    document.body.appendChild(overlay);
    overlay.addEventListener("click", e => {
      if (e.target.closest("[data-close]")) closeOverlay(true);
      if (e.target.closest("[data-rot]")) overlay.classList.add("dismiss-rotate");
    });
  }
  function makeFrame(g) {
    const f = document.createElement("iframe");
    f.src = g.src; f.title = g.title;
    f.allow = "autoplay; fullscreen; gamepad; accelerometer; gyroscope; clipboard-write; web-share; screen-wake-lock";
    f.setAttribute("allowfullscreen", "");
    f.addEventListener("load", () => { try { f.focus(); } catch (e) {} const l = f.parentNode && f.parentNode.querySelector(".loading"); l && l.remove(); });
    return f;
  }
  function loading(g) { const l = document.createElement("div"); l.className = "loading"; l.textContent = "Loading " + g.title; return l; }
  function openOverlay(g) {
    if (!overlay) buildOverlay();
    overlay.style.setProperty("--g", g.accent);
    $(".name span", overlay).textContent = g.title; $(".name img", overlay).src = g.icon;
    overlay.classList.toggle("wants-landscape", g.orientation === "landscape");
    overlay.classList.remove("dismiss-rotate");
    const host = $(".host", overlay);
    $$("iframe,.loading", host).forEach(n => n.remove());
    host.appendChild(loading(g)); host.appendChild(makeFrame(g));
    overlay.hidden = false; overlayOpen = true;
    document.documentElement.classList.add("lock");
    try { history.pushState({ skerryPlay: g.slug }, "", location.href.split("#")[0] + (location.hash && location.hash !== "#play" ? location.hash + "-play" : "#play")); } catch (e) {}
  }
  function closeOverlay(viaButton) {
    if (!overlay || !overlayOpen) return;
    overlayOpen = false; overlay.hidden = true;
    $$("iframe,.loading", overlay).forEach(n => n.remove());
    document.documentElement.classList.remove("lock");
    if (viaButton && history.state && history.state.skerryPlay) history.back();
  }
  addEventListener("popstate", () => { if (overlayOpen) closeOverlay(false); });

  function startGame(stage, g) {
    remember(g.slug); renderRecent();
    track("game_start", { game: g.slug, mode: isPhone() ? "overlay" : "inline" });
    if (isPhone()) return openOverlay(g);
    if (stage.classList.contains("on")) return;
    stage.classList.add("on");
    stage.appendChild(loading(g)); stage.appendChild(makeFrame(g));
  }
  function fullscreen(stage, g) {
    if (isPhone()) return openOverlay(g);
    if (!stage.classList.contains("on")) startGame(stage, g);
    const req = stage.requestFullscreen || stage.webkitRequestFullscreen;
    if (req) { try { const p = req.call(stage); p && p.catch && p.catch(() => openOverlay(g)); } catch (e) { openOverlay(g); } }
    else openOverlay(g);
  }
  async function share(g) {
    const data = { title: g.title + " on Skerry Arcade", text: g.tagline, url: g.share };
    try { if (navigator.share) { await navigator.share(data); return; } } catch (e) { if (e && e.name === "AbortError") return; }
    try { await navigator.clipboard.writeText(g.share); toast("Link copied"); } catch (e) { toast(g.share); }
  }
  function initGamePages() {
    $$("[data-game]").forEach(page => {
      const g = GAMES[page.dataset.game]; if (!g) return;
      const stage = $(".stage", page);
      $$("[data-start]", page).forEach(b => b.addEventListener("click", () => startGame(stage, g)));
      $$("[data-fullscreen]", page).forEach(b => b.addEventListener("click", () => fullscreen(stage, g)));
      $$("[data-share]", page).forEach(b => b.addEventListener("click", () => share(g)));
    });
  }

  /* ---------------- one-file preview: views switched by the hash ---------------- */
  function initPreview() {
    const views = $$("[data-view]"); if (!views.length) return;
    const show = () => {
      let id = (location.hash || "#home").slice(1);
      if (/(^|-)play$/.test(id)) return;
      if (overlayOpen) closeOverlay(false);
      const v = views.find(x => x.dataset.view === id) || views[0];
      views.forEach(x => {
        x.hidden = x !== v;
        if (x !== v) $$(".stage.on", x).forEach(s => { s.classList.remove("on"); $$("iframe,.loading", s).forEach(n => n.remove()); });
      });
      const key = v.dataset.key;
      $$(".side .nav-i").forEach(a => a.toggleAttribute("aria-current", a.getAttribute("href") === "#" + (key === "home" ? "home" : key.replace("/", "-"))));
      $$(".side .nav-i[aria-current]").forEach(a => a.setAttribute("aria-current", "page"));
      if (v.dataset.view === "search") showSearch(($("[data-search] input") || {}).value || "");
      scrollTo(0, 0);
    };
    addEventListener("hashchange", show); show();
  }

  function boot() {
    renderRecent(); initSearch(); initRandom(); initSpot(); initVideos(); initGamePages(); initPreview(); consent();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
