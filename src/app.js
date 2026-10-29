/* Skerry Arcade — site script. No dependencies. */
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
  const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const isPhone = () => matchMedia("(hover: none) and (pointer: coarse)").matches || innerWidth < 760;

  /* ---------------- analytics (only after consent) ---------------- */
  const GA_ID = document.documentElement.dataset.ga || "";
  function track(name, params) { try { window.gtag && window.gtag("event", name, params || {}); } catch (e) {} }
  function loadGA() {
    if (!GA_ID || window.gtag) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { dataLayer.push(arguments); };
    gtag("js", new Date());
    gtag("config", GA_ID, { anonymize_ip: true });
    const s = document.createElement("script");
    s.async = true; s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(GA_ID);
    document.head.appendChild(s);
  }
  function consent() {
    if (!GA_ID) return;
    const c = store.get("skerry.consent", null);
    if (c === "yes") return loadGA();
    if (c === "no") return;
    const box = document.createElement("div");
    box.className = "consent"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Analytics");
    box.innerHTML = '<p>May we count visits with Google Analytics? It helps us see which games people enjoy. No ads, no personal profile. <a href="' + (DATA.root || "/") + 'privacy/">Privacy</a></p><div class="btns"><button class="btn btn-lamp" data-c="yes">Allow</button><button class="btn btn-ghost" data-c="no">No thanks</button></div>';
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

  /* ---------------- recently played ---------------- */
  function remember(slug) {
    const list = store.get("skerry.recent", []).filter(s => s !== slug);
    list.unshift(slug); store.set("skerry.recent", list.slice(0, 4));
  }
  function renderRecent() {
    $$("[data-recent]").forEach(box => {
      const list = store.get("skerry.recent", []).filter(s => GAMES[s]);
      if (!list.length) { box.hidden = true; return; }
      box.innerHTML = "<span>Jump back in</span>" + list.map(s => {
        const g = GAMES[s];
        return '<a href="' + g.href + '" style="--g:' + g.accent + '"><img src="' + g.thumb + '" alt="" width="44" height="30">' + g.title + "</a>";
      }).join("");
      box.hidden = false;
    });
  }

  /* ---------------- player ---------------- */
  const ICON_BACK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>';
  const ICON_ROT = '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="14" width="30" height="20" rx="4"/><path d="M20 6a14 14 0 0 1 14 6M34 6v6h-6"/></svg>';
  let overlay = null, overlayOpen = false;

  function buildOverlay() {
    overlay = document.createElement("div");
    overlay.className = "player"; overlay.hidden = true;
    overlay.innerHTML = '<div class="bar"><button type="button" data-close>' + ICON_BACK + 'Skerry Arcade</button><span class="name"><i></i><span></span></span></div><div class="host"><div class="rotate"><span>' + ICON_ROT + '</span><b>Turn your phone sideways</b><span>This game plays best in landscape.</span><button type="button" class="btn btn-ghost" data-rot>Play in portrait</button></div></div>';
    document.body.appendChild(overlay);
    overlay.addEventListener("click", e => {
      if (e.target.closest("[data-close]")) closeOverlay(true);
      if (e.target.closest("[data-rot]")) overlay.classList.add("dismiss-rotate");
    });
  }
  function makeFrame(g) {
    const f = document.createElement("iframe");
    f.src = g.src;
    f.title = g.title;
    f.allow = "autoplay; fullscreen; gamepad; accelerometer; gyroscope; clipboard-write; web-share; screen-wake-lock";
    f.setAttribute("allowfullscreen", "");
    f.addEventListener("load", () => { try { f.focus(); } catch (e) {} const l = f.parentNode && f.parentNode.querySelector(".loading"); l && l.remove(); });
    return f;
  }
  function openOverlay(g) {
    if (!overlay) buildOverlay();
    overlay.style.setProperty("--g", g.accent);
    $(".name span", overlay).textContent = g.title;
    overlay.classList.toggle("wants-landscape", g.orientation === "landscape");
    overlay.classList.remove("dismiss-rotate");
    const host = $(".host", overlay);
    $$("iframe,.loading", host).forEach(n => n.remove());
    const l = document.createElement("div"); l.className = "loading"; l.textContent = "Loading " + g.title;
    host.appendChild(l); host.appendChild(makeFrame(g));
    overlay.hidden = false; overlayOpen = true;
    document.documentElement.classList.add("lock");
    try { history.pushState({ skerryPlay: g.slug }, "", location.href.split("#")[0] + "#play"); } catch (e) {}
  }
  function closeOverlay(viaButton) {
    if (!overlay || !overlayOpen) return;
    overlayOpen = false;
    overlay.hidden = true;
    $$("iframe", overlay).forEach(n => n.remove());
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
    const l = document.createElement("div"); l.className = "loading"; l.textContent = "Loading " + g.title;
    stage.appendChild(l); stage.appendChild(makeFrame(g));
  }
  function fullscreen(stage, g) {
    if (isPhone()) return openOverlay(g);
    if (!stage.classList.contains("on")) startGame(stage, g);
    const req = stage.requestFullscreen || stage.webkitRequestFullscreen;
    if (req) { try { const p = req.call(stage); p && p.catch && p.catch(() => openOverlay(g)); } catch (e) { openOverlay(g); } }
    else openOverlay(g);
  }
  async function share(g) {
    const url = g.share || location.href.split("#")[0];
    const data = { title: g.title + " on Skerry Arcade", text: g.tagline, url };
    try { if (navigator.share) { await navigator.share(data); return; } } catch (e) { if (e && e.name === "AbortError") return; }
    try { await navigator.clipboard.writeText(url); toast("Link copied"); }
    catch (e) { toast(url); }
  }

  function initGamePages(root) {
    $$("[data-game]", root).forEach(page => {
      const g = GAMES[page.dataset.game]; if (!g) return;
      const stage = $(".stage", page);
      $$("[data-start]", page).forEach(b => b.addEventListener("click", () => startGame(stage, g)));
      $$("[data-fullscreen]", page).forEach(b => b.addEventListener("click", () => fullscreen(stage, g)));
      $$("[data-share]", page).forEach(b => b.addEventListener("click", () => share(g)));
    });
  }

  /* ---------------- the sea chart ---------------- */
  function chart(canvas) {
    const host = canvas.parentElement;
    const ctx = canvas.getContext("2d");
    let W = 0, H = 0, dpr = 1, dim, lit, tmp, haze, lh = { x: 0, y: 0 }, raf = 0, visible = true, t0 = performance.now(), last = 0;

    function rng(seed) { return () => { seed |= 0; seed = (seed + 0x6D2B79F5) | 0; let t = Math.imul(seed ^ (seed >>> 15), 1 | seed); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
    function noiseFn(seed) {
      const r = rng(seed), P = new Float32Array(512 * 2);
      for (let i = 0; i < P.length; i++) P[i] = r();
      const v = (ix, iy) => P[(((ix * 73856093) ^ (iy * 19349663)) >>> 0) % 1024];
      const sm = t => t * t * (3 - 2 * t);
      const n = (x, y) => { const ix = Math.floor(x), iy = Math.floor(y), fx = sm(x - ix), fy = sm(y - iy);
        const a = v(ix, iy), b = v(ix + 1, iy), c = v(ix, iy + 1), d = v(ix + 1, iy + 1);
        return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy; };
      return (x, y) => { let s = 0, amp = .55, f = 1; for (let o = 0; o < 5; o++) { s += amp * n(x * f, y * f); amp *= .5; f *= 2.03; } return s; };
    }
    const mk = () => { const c = document.createElement("canvas"); c.width = canvas.width; c.height = canvas.height; return c; };

    function build() {
      const rect = host.getBoundingClientRect();
      W = Math.max(1, Math.round(rect.width)); H = Math.max(1, Math.round(rect.height));
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
      dim = mk(); lit = mk(); tmp = mk(); haze = mk();
      const narrow = W < 900;
      const N = noiseFn(1907);                  // fixed seed, so the archipelago is the same on every visit
      const S = narrow ? 1 / 150 : 1 / 210;
      // keep open water behind the headline; islands gather around it and under the featured game
      const hr = host.getBoundingClientRect();
      const avoid = Array.from(host.querySelectorAll("[data-chart-avoid]")).map(el => { const r = el.getBoundingClientRect(); return { x0: r.left - hr.left, y0: r.top - hr.top, x1: r.right - hr.left, y1: r.bottom - hr.top }; });
      const hides = Array.from(host.querySelectorAll("[data-chart-hide]")).map(el => { const r = el.getBoundingClientRect(); return { x0: r.left - hr.left, y0: r.top - hr.top, x1: r.right - hr.left, y1: r.bottom - hr.top }; });
      const dist = (b, x, y) => Math.hypot(Math.max(b.x0 - x, 0, x - b.x1), Math.max(b.y0 - y, 0, y - b.y1));
      const field = (x, y) => {
        let h = N(x * S + 3.1, y * S + 7.7) - .45;
        for (const b of avoid) h -= Math.max(0, 1 - dist(b, x, y) / 60) * .35;
        return h * 1.7;
      };
      const g = 5, cols = Math.ceil(W / g) + 1, rows = Math.ceil(H / g) + 1;
      const F = new Float32Array(cols * rows);
      for (let j = 0; j < rows; j++) for (let i = 0; i < cols; i++) F[j * cols + i] = field(i * g, j * g);
      const at = (i, j) => F[j * cols + i];

      // land mask, upscaled smoothly
      const mask = document.createElement("canvas"); mask.width = cols; mask.height = rows;
      const mctx = mask.getContext("2d"), img = mctx.createImageData(cols, rows);
      for (let k = 0; k < F.length; k++) { const a = Math.max(0, Math.min(1, (F[k] + .012) / .024)); img.data[k * 4 + 3] = a * 255; img.data[k * 4] = img.data[k * 4 + 1] = img.data[k * 4 + 2] = 255; }
      mctx.putImageData(img, 0, 0);

      function contours(c, level) {
        c.beginPath();
        for (let j = 0; j < rows - 1; j++) for (let i = 0; i < cols - 1; i++) {
          const a = at(i, j) - level, b = at(i + 1, j) - level, cc = at(i + 1, j + 1) - level, d = at(i, j + 1) - level;
          const idx = (a > 0 ? 8 : 0) | (b > 0 ? 4 : 0) | (cc > 0 ? 2 : 0) | (d > 0 ? 1 : 0);
          if (idx === 0 || idx === 15) continue;
          const x = i * g, y = j * g;
          const T = [x + g * a / (a - b), y], R = [x + g, y + g * b / (b - cc)], B = [x + g * d / (d - cc), y + g], L = [x, y + g * a / (a - d)];
          const seg = (p, q) => { c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); };
          switch (idx) {
            case 1: case 14: seg(L, B); break; case 2: case 13: seg(B, R); break; case 3: case 12: seg(L, R); break;
            case 4: case 11: seg(T, R); break; case 6: case 9: seg(T, B); break; case 7: case 8: seg(L, T); break;
            case 5: seg(L, T); seg(B, R); break; case 10: seg(T, R); seg(L, B); break;
          }
        }
      }
      // soundings in open water
      const r = rng(42), sounds = [];
      for (let k = 0; k < (narrow ? 26 : 48); k++) {
        const x = 20 + r() * (W - 40), y = 20 + r() * (H - 40), h = field(x, y);
        if (h < -.06 && avoid.concat(hides).every(b => dist(b, x, y) > 14)) sounds.push([x, y, Math.round(3 + -h * 70)]);
      }
      // lighthouse: the highest ground in the right/lower part of the chart
      let best = -9;
      for (let j = 2; j < rows - 2; j++) for (let i = 2; i < cols - 2; i++) {
        const x = i * g, y = j * g;
        const ok = x > 24 && x < W - 24 && y > 30 && y < H - 16 && avoid.concat(hides).every(b => dist(b, x, y) > 34);
        const pref = narrow ? Math.hypot(x - W * .5, y - H) / W : Math.hypot(x - W * .52, y - H * .9) / W;
        const sc = Math.min(at(i, j), .12) - pref * .5;
        if (ok && at(i, j) > .02 && sc > best) { best = sc; lh = { x, y }; }
      }
      if (best < -1) lh = { x: W * .5, y: H - 30 };

      function paint(c2, k) {
        const c = c2.getContext("2d");
        c.setTransform(dpr, 0, 0, dpr, 0, 0);
        c.imageSmoothingEnabled = true;
        // land
        c.globalAlpha = k ? .38 : .15;
        c.drawImage(mask, 0, 0, cols, rows, -g / 2, -g / 2, cols * g, rows * g);
        c.globalCompositeOperation = "source-in";
        c.fillStyle = "#D98A74"; c.fillRect(0, 0, W, H);
        c.globalCompositeOperation = "source-over"; c.globalAlpha = 1;
        c.lineCap = "round";
        // depth contours, dashed like a chart
        c.strokeStyle = k ? "rgba(160,215,220,.42)" : "rgba(160,215,220,.15)"; c.lineWidth = 1;
        c.setLineDash([3, 5]); contours(c, -.09); c.stroke();
        c.setLineDash([1, 6]); contours(c, -.2); c.stroke();
        c.setLineDash([]);
        // elevation
        c.strokeStyle = k ? "rgba(255,214,190,.34)" : "rgba(255,214,190,.09)";
        contours(c, .1); c.stroke(); contours(c, .22); c.stroke();
        // coastline
        c.strokeStyle = k ? "rgba(255,236,205,.85)" : "rgba(232,240,236,.3)"; c.lineWidth = k ? 1.4 : 1.1;
        contours(c, 0); c.stroke();
        // soundings
        c.fillStyle = k ? "rgba(232,240,236,.75)" : "rgba(147,168,173,.32)";
        c.font = "italic 500 10px 'Familjen Grotesk', Arial, sans-serif"; c.textAlign = "center";
        sounds.forEach(s => c.fillText(s[2], s[0], s[1]));
      }
      paint(dim, 0); paint(lit, 1);
      // the lighthouse itself
      const d = dim.getContext("2d");
      d.fillStyle = "#E8F0EC"; d.fillRect(lh.x - 2, lh.y - 9, 4, 9);
      d.fillStyle = "#D98A74"; d.fillRect(lh.x - 2, lh.y - 6, 4, 2);
      draw(performance.now());
    }

    function draw(now) {
      if (!dim) return;
      const t = (now - t0) / 1000;
      const ang = reduceMotion ? -2.6 : -2.6 + t * .32;
      const R = Math.hypot(W, H) * 1.05;
      const cx = lh.x * dpr, cy = (lh.y - 8) * dpr;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(dim, 0, 0);
      const cone = (c, a1) => {
        const gr = c.createConicGradient ? c.createConicGradient(ang - .32, cx, cy) : null;
        if (!gr) return "rgba(255,255,255," + a1 + ")";
        gr.addColorStop(0, "rgba(255,255,255,0)");
        gr.addColorStop(.035, "rgba(255,255,255," + a1 * .55 + ")");
        gr.addColorStop(.051, "rgba(255,255,255," + a1 + ")");
        gr.addColorStop(.067, "rgba(255,255,255," + a1 * .55 + ")");
        gr.addColorStop(.102, "rgba(255,255,255,0)");
        gr.addColorStop(1, "rgba(255,255,255,0)");
        return gr;
      };
      const fall = c => { const gr = c.createRadialGradient(cx, cy, 0, cx, cy, R * dpr); gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(.55, "rgba(255,255,255,.55)"); gr.addColorStop(1, "rgba(255,255,255,0)"); return gr; };
      // lit chart inside the beam
      const tc = tmp.getContext("2d");
      tc.setTransform(1, 0, 0, 1, 0, 0); tc.globalCompositeOperation = "source-over";
      tc.clearRect(0, 0, tmp.width, tmp.height); tc.drawImage(lit, 0, 0);
      tc.globalCompositeOperation = "destination-in"; tc.fillStyle = cone(tc, 1); tc.fillRect(0, 0, tmp.width, tmp.height);
      tc.fillStyle = fall(tc); tc.fillRect(0, 0, tmp.width, tmp.height);
      ctx.drawImage(tmp, 0, 0);
      // the beam's haze
      const hc = haze.getContext("2d");
      hc.setTransform(1, 0, 0, 1, 0, 0); hc.globalCompositeOperation = "source-over";
      hc.clearRect(0, 0, haze.width, haze.height);
      hc.fillStyle = cone(hc, 1); hc.fillRect(0, 0, haze.width, haze.height);
      hc.globalCompositeOperation = "source-in"; hc.fillStyle = "rgba(255,194,75,1)"; hc.fillRect(0, 0, haze.width, haze.height);
      hc.globalCompositeOperation = "destination-in"; hc.fillStyle = fall(hc); hc.fillRect(0, 0, haze.width, haze.height);
      ctx.globalCompositeOperation = "lighter"; ctx.globalAlpha = .15; ctx.drawImage(haze, 0, 0);
      ctx.globalAlpha = 1;
      // lamp
      const pulse = .75 + .25 * Math.max(0, Math.cos(((ang % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2) - Math.PI * 1.5));
      const lg = ctx.createRadialGradient(cx, cy, 0, cx, cy, 26 * dpr);
      lg.addColorStop(0, "rgba(255,226,150," + pulse + ")"); lg.addColorStop(.25, "rgba(255,194,75," + .45 * pulse + ")"); lg.addColorStop(1, "rgba(255,194,75,0)");
      ctx.fillStyle = lg; ctx.beginPath(); ctx.arc(cx, cy, 26 * dpr, 0, Math.PI * 2); ctx.fill();
      ctx.globalCompositeOperation = "source-over";
    }
    function loop(now) {
      raf = 0;
      if (!visible || document.hidden) return;
      if (now - last > 33) { last = now; draw(now); }
      raf = requestAnimationFrame(loop);
    }
    const kick = () => { if (!reduceMotion && !raf && visible && !document.hidden) raf = requestAnimationFrame(loop); };
    let rt; new ResizeObserver(() => { clearTimeout(rt); rt = setTimeout(build, 120); }).observe(host);
    if ("IntersectionObserver" in window) new IntersectionObserver(es => { visible = es[0].isIntersecting; kick(); }).observe(host);
    document.addEventListener("visibilitychange", kick);
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => { build(); kick(); });
  }

  /* ---------------- boot ---------------- */
  function boot() {
    $$("canvas[data-chart]").forEach(chart);
    renderRecent();
    initGamePages(document);
    consent();
    // preview builds route between views with the hash
    const views = $$("[data-view]");
    if (views.length) {
      const show = () => {
        if (location.hash === "#play") return;
        if (overlayOpen) closeOverlay(false);
        const id = (location.hash || "#home").slice(1);
        const target = document.getElementById(id);
        const v = views.find(x => x.dataset.view === id) || (target && target.closest("[data-view]")) || views[0];
        views.forEach(x => {
          x.hidden = x !== v;
          if (x !== v) $$(".stage.on", x).forEach(s => { s.classList.remove("on"); $$("iframe,.loading", s).forEach(n => n.remove()); });
        });
        $$(".nav a").forEach(a => a.toggleAttribute("aria-current", a.getAttribute("href") === "#" + v.dataset.view));
        if (target && v.dataset.view !== id) target.scrollIntoView(); else scrollTo(0, 0);
      };
      addEventListener("hashchange", show); show();
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
