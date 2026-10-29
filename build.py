#!/usr/bin/env python3
"""Builds Skerry Arcade into dist/.

    python3 build.py                 -> dist/ (the real site; the games are copied into dist/play/ by the workflow)
    python3 build.py --preview FILE  -> one self-contained preview page (used for the Claude preview)

All game texts live in games.json. Add a game there, add its covers to assets/covers/, and add its
repo to .github/workflows/deploy.yml.
"""
import base64, html, json, mimetypes, os, shutil, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://skerryarcade.com"
NAME = "Skerry Arcade"
GA_ID = ""            # paste the portal's GA4 Measurement ID here (G-XXXXXXXXXX) to turn on analytics with consent
CONTACT = "hello@skerryarcade.com"
OWNER = "AsterIQ Ab, Åland, Finland"

GAMES = json.load(open(os.path.join(ROOT, "games.json"), encoding="utf-8"))
E = lambda s: html.escape(str(s), quote=True)

LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M16 8.5 31 3v11z" fill="#FFC24B" opacity=".32"/>'
        '<path d="M2.5 25c2.6-5.4 6.6-6.8 10.4-5.6 2.2-3.6 7.4-3.7 10.3-.4 3-.6 5.6 1.6 6.6 6z" fill="#D98A74"/>'
        '<rect x="14.2" y="9.5" width="3.6" height="10.5" rx=".6" fill="#E8F0EC"/><rect x="14.2" y="13" width="3.6" height="2" fill="#D98A74"/>'
        '<circle cx="16" cy="8" r="2.6" fill="#FFC24B"/><path d="M3 28.5h26" stroke="#93A8AD" stroke-width="1.4" stroke-linecap="round" opacity=".6"/></svg>')
PLAY = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15a1 1 0 0 0 1.5.86l12.5-7.5a1 1 0 0 0 0-1.72L8.5 3.64A1 1 0 0 0 7 4.5z" fill="currentColor"/></svg>'
ICON_FS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>'
ICON_SHARE = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>'
ICON_OUT = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>'
FONTS = "https://fonts.googleapis.com/css2?family=Familjen+Grotesk:ital,wght@0,400;0,500;0,600;0,700;1,500&family=Unbounded:wght@300;600;700;800&display=swap"


class Ctx:
    """Differences between the real site and the one-file preview."""
    def __init__(self, preview=False):
        self.preview = preview
    def page(self, slug):            # link to a page
        if self.preview: return "#" + (slug or "home")
        return "/" + (slug + "/" if slug else "")
    def asset(self, path):           # path under assets/
        if not self.preview: return "/assets/" + path
        full = os.path.join(ROOT, "assets", path)
        mt = mimetypes.guess_type(full)[0] or ("image/webp" if full.endswith(".webp") else "application/octet-stream")
        return "data:%s;base64,%s" % (mt, base64.b64encode(open(full, "rb").read()).decode())
    def src(self, g):                # what the player loads
        if self.preview: return g.get("previewSrc", "")
        return "/play/%s/%s" % (g["slug"], g["entry"])


def game_data(ctx):
    out = []
    for g in GAMES:
        out.append({"slug": g["slug"], "title": g["title"], "accent": g["accent"], "tagline": g["tagline"],
                    "href": ctx.page(g["slug"]), "thumb": ctx.asset("covers/%s-sm.webp" % g["slug"]),
                    "src": ctx.src(g), "orientation": g.get("touchOrientation", "any"),
                    "share": SITE + "/" + g["slug"] + "/"})
    return out


def header(ctx, current=""):
    games_href = ctx.page("") + "#games" if not ctx.preview else "#games"
    return ('<header class="top"><div class="wrap">'
            '<a class="brand" href="%s" aria-label="%s home">%s<b>Skerry<span> </span>Arcade</b></a>'
            '<nav class="nav" aria-label="Main"><a href="%s"%s>Games</a><a class="hide-s" href="%s"%s>About</a></nav>'
            '</div></header>') % (ctx.page(""), NAME, LOGO, games_href, ' aria-current="page"' if current == "games" else "",
                                  (ctx.page("") + "#made") if not ctx.preview else "#made", "")


def footer(ctx):
    links = "".join('<a href="%s">%s</a>' % (ctx.page(g["slug"]), E(g["title"])) for g in GAMES)
    return ('<footer class="foot"><div class="wrap"><span>© %d %s. Made on Åland.</span>%s<a href="%s">Privacy</a></div></footer>'
            % (date.today().year, NAME, links, ctx.page("privacy")))


def card(ctx, g, size="sm"):
    meta = [("Genre", g["facts"]["Genre"]), ("", g["facts"]["A round"])]
    return ('<a class="card" href="%s" style="--g:%s"><div class="frame">'
            '<img src="%s" alt="%s gameplay" width="640" height="360" loading="lazy" decoding="async">'
            '<span class="hover-play">%s</span></div>'
            '<div class="txt"><h3><span class="dot"></span>%s</h3><p>%s</p>'
            '<div class="meta"><span>%s</span><span>%s</span><span>Desktop and mobile</span></div></div></a>') % (
        ctx.page(g["slug"]), g["accent"], ctx.asset("covers/%s-sm.webp" % g["slug"]), E(g["title"]), PLAY,
        E(g["title"]), E(g["summary"]), E(g["facts"]["Genre"]), E(g["facts"]["A round"]))


def home_body(ctx):
    feat = GAMES[0]
    n = len(GAMES)
    words = {2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight"}.get(n, str(n))
    cards = "".join(card(ctx, g) for g in GAMES)
    own = [g for g in GAMES if g.get("ownSite")]
    own_txt = ""
    if own:
        own_txt = "<p>A few of them also have a home of their own: %s. Progress and duel links work in both places.</p>" % (
            " and ".join('<a href="%s" rel="noopener">%s</a>' % (g["ownSite"], g["ownSite"].split("//")[1].replace("www.", "")) for g in own))
    return """
<section class="chart" aria-label="Featured">
  <canvas data-chart aria-hidden="true"></canvas>
  <div class="wrap hero">
    <div class="hero-copy" data-chart-avoid>
      <span class="coords"><i></i>60°06′N 19°56′E, Åland</span>
      <h1>Small games<span class="l2">from the skerries</span></h1>
      <p>%(words)s free games made on an island in the Baltic Sea. They run in your browser on phone or computer, with nothing to install and no account.</p>
      <div class="actions"><a class="btn btn-lamp" href="%(fhref)s">%(play)s Play %(ftitle)s</a><a class="btn btn-ghost" href="#games">See all games</a></div>
    </div>
    <a class="feature" data-chart-hide href="%(fhref)s" aria-label="Play %(ftitle)s">
      <img class="art" src="%(fimg)s" alt="%(ftitle)s" width="1280" height="720" fetchpriority="high">
      %(badge)s
      <div class="cap"><p>%(ftag)s</p><span class="play">%(play)s</span></div>
    </a>
  </div>
</section>
<section class="section" id="games">
  <div class="wrap">
    <div class="section-head"><h2>All games</h2><p>%(n)d games, all free</p></div>
    <div class="recent" data-recent hidden></div>
    <div class="grid">%(cards)s</div>
  </div>
</section>
<section class="section made" id="made">
  <div class="wrap">
    <h2>Made on Åland</h2>
    <div class="body">
      <p>Åland is a group of about 6,500 islands and skerries between Sweden and Finland. The games here are designed and built on one of them.</p>
      <p>Every game is a small, complete thing you can start in a few seconds: a survival night, a penguin snowball war, a round of golf against a friend's ghost, a flight over the real archipelago. New games arrive when they are good enough to share.</p>
      %(own)s
    </div>
  </div>
</section>""" % dict(words=words, fhref=ctx.page(feat["slug"]), ftitle=E(feat["title"]), play=PLAY,
                     fimg=ctx.asset("covers/%s.webp" % feat["slug"]), ftag=E(feat["tagline"]),
                     badge=('<span class="badge">%s</span>' % E(feat["badge"])) if feat.get("badge") else "",
                     n=n, cards=cards, own=own_txt)


def game_body(ctx, g):
    others = [o for o in GAMES if o["slug"] != g["slug"]][:3]
    facts = "".join("<dt>%s</dt><dd>%s</dd>" % (E(k), E(v)) for k, v in g["facts"].items())
    ctrl = "".join("<tr><th scope=\"row\">%s</th><td>%s</td><td>%s</td></tr>" % tuple(E(x) for x in c) for c in g["controls"])
    feats = "".join("<li>%s</li>" % E(f) for f in g["features"])
    about = "".join("<p>%s</p>" % E(p) for p in g["about"])
    also = ""
    if g.get("ownSite"):
        host = g["ownSite"].split("//")[1].replace("www.", "")
        also = '<p class="also">%s also has its own site at <a href="%s" rel="noopener">%s</a>. Duel links from either place work.</p>' % (E(g["title"]), g["ownSite"], host)
    hint = ('<span class="h-d">Plays right here. Full screen is one click away</span><span class="h-m">%s</span>'
            % ("Plays full screen" if g.get("touchOrientation") != "landscape" else "Plays full screen, best held sideways"))
    unavailable = ctx.preview and not ctx.src(g)
    if unavailable:
        start = ('<a class="start" href="https://tommykalmer.github.io/alandsflyg/" target="_blank" rel="noopener"><span class="ring">%s</span>'
                 '<span class="lbl">Play %s</span><span class="hint">Too big for this preview. Opens the current version in a new tab</span></a>') % (ICON_OUT, E(g["title"]))
    else:
        start = ('<button class="start" type="button" data-start><span class="ring">%s</span><span class="lbl">Play %s</span>'
                 '<span class="hint">%s</span></button>') % (PLAY, E(g["title"]), hint)
    return """
<div data-game="%(slug)s" style="--g:%(accent)s">
  <div class="wrap g-top">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="%(home)s">Games</a><span aria-hidden="true">/</span><span>%(title)s</span></nav>
    <div class="stage">
      <img class="poster" src="%(cover)s" alt="" width="1280" height="720" fetchpriority="high">
      <div class="shade"></div>
      %(start)s
    </div>
    <div class="g-bar">
      <div class="t"><h1><span class="dot"></span>%(title)s</h1><p>%(tagline)s</p></div>
      <div class="tools">
        %(fsbtn)s
        <button class="icon-btn" type="button" data-share>%(share)s Share</button>
      </div>
    </div>
  </div>
  <div class="wrap g-info">
    <div class="prose">
      <h2>About the game</h2>
      %(about)s
      <ul class="features">%(feats)s</ul>
      %(also)s
    </div>
    <aside class="side">
      <div><h2>At a glance</h2><dl class="facts">%(facts)s</dl></div>
      <div><h2>How to play</h2>
        <div style="overflow-x:auto"><table class="controls"><thead><tr><th scope="col"></th><th scope="col">Computer</th><th scope="col">Phone</th></tr></thead><tbody>%(ctrl)s</tbody></table></div>
      </div>
    </aside>
  </div>
  <section class="section more" aria-labelledby="more-%(slug)s">
    <div class="wrap">
      <div class="section-head"><h2 id="more-%(slug)s">More games</h2></div>
      <div class="grid">%(others)s</div>
    </div>
  </section>
</div>""" % dict(slug=g["slug"], accent=g["accent"], home=ctx.page("") if not ctx.preview else "#home", title=E(g["title"]),
                 cover=ctx.asset("covers/%s.webp" % g["slug"]), start=start, tagline=E(g["tagline"]),
                 fsbtn="" if unavailable else '<button class="icon-btn" type="button" data-fullscreen>%s Full screen</button>' % ICON_FS,
                 share=ICON_SHARE, about=about, feats=feats, also=also, facts=facts, ctrl=ctrl,
                 others="".join(card(ctx, o) for o in others))


def privacy_body(ctx):
    return """
<div class="wrap legal"><div class="prose">
  <h1>Privacy</h1>
  <p>Skerry Arcade is run by %(owner)s. This page explains what the site stores and why. Questions go to %(contact)s.</p>
  <h2>What stays on your device</h2>
  <p>The games save your progress, settings and best scores in your browser's local storage, on your device only. The site also remembers which games you played last so it can show them on the front page. Nothing of this is sent to us. Clearing your browser data removes it.</p>
  <h2>Duel links</h2>
  <p>In Snowfeud and GolfFeud a duel is stored entirely inside the link you send: shots, scores and the course. The link is not saved on any server. Anyone who has the link can open the duel.</p>
  <h2>Analytics</h2>
  <p>If you allow it, we use Google Analytics to count visits and see which games are played. It uses cookies and shortened IP addresses and does not build an advertising profile. If you choose No thanks, no analytics script is loaded. You can change your mind by clearing this site's data in your browser.</p>
  <h2>Ads</h2>
  <p>The site shows no ads today. If that changes, this page will be updated first and you will be asked before any ad cookies are used.</p>
  <h2>Your rights</h2>
  <ul><li>Ask what data we hold about you (normally none).</li><li>Ask us to delete analytics data linked to your device.</li><li>Complain to the Data Protection Ombudsman in Finland.</li></ul>
</div></div>""" % dict(owner=E(OWNER), contact=E(CONTACT))


def head(ctx, title, desc, path, image, jsonld=None):
    url = SITE + path
    ld = ('<script type="application/ld+json">%s</script>' % json.dumps(jsonld, ensure_ascii=False)) if jsonld else ""
    meta = ""
    if not ctx.preview:
        meta = ('<link rel="canonical" href="%(url)s"><meta property="og:type" content="website"><meta property="og:site_name" content="%(name)s">'
                '<meta property="og:title" content="%(t)s"><meta property="og:description" content="%(d)s"><meta property="og:url" content="%(url)s">'
                '<meta property="og:image" content="%(img)s"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
                '<meta name="twitter:card" content="summary_large_image">'
                '<link rel="icon" href="/assets/icon.svg" type="image/svg+xml"><link rel="icon" href="/assets/favicon-32.png" sizes="32x32">'
                '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
                ) % dict(url=url, name=NAME, t=E(title), d=E(desc), img=SITE + image)
    return ('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><meta name="claude:viewport-fit-sides" content="cover"><meta name="description" content="%s"><meta name="theme-color" content="#0A1821">%s'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="%s">%s') % (E(title), E(desc), meta, FONTS, ld)


def assets_tags(ctx):
    data = json.dumps({"games": game_data(ctx), "root": "/" if not ctx.preview else "#"}, ensure_ascii=False)
    if ctx.preview:
        css = open(os.path.join(ROOT, "src/style.css"), encoding="utf-8").read()
        js = open(os.path.join(ROOT, "src/app.js"), encoding="utf-8").read()
        return "<style>%s</style>" % css, "<script>window.SKERRY=%s</script><script>%s</script>" % (data, js)
    return ('<link rel="stylesheet" href="/assets/style.css?v=%s">' % VERSION,
            '<script>window.SKERRY=%s</script><script src="/assets/app.js?v=%s" defer></script>' % (data, VERSION))


def document(ctx, title, desc, path, image, body, jsonld=None):
    css, js = assets_tags(ctx)
    return ('<!doctype html><html lang="en" data-ga="%s"><head>%s%s</head><body>%s<main>%s</main>%s%s</body></html>'
            % (GA_ID, head(ctx, title, desc, path, image, jsonld), css, header(ctx), body, footer(ctx), js))


def write(rel, text):
    full = os.path.join(ROOT, "dist", rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)


ORG = {"@type": "Organization", "name": NAME, "url": SITE + "/"}
HOME_DESC = "Free browser games made on Åland: Ember Vigil, Snowfeud, GolfFeud and Ålandsflyg. Play instantly on phone or computer, no download or account."


def build_site():
    global VERSION
    VERSION = date.today().strftime("%Y%m%d") + os.environ.get("GITHUB_RUN_NUMBER", "")
    ctx = Ctx(False)
    dist = os.path.join(ROOT, "dist")
    if os.path.isdir(dist):
        for n in os.listdir(dist):
            if n != "play": shutil.rmtree(os.path.join(dist, n)) if os.path.isdir(os.path.join(dist, n)) else os.remove(os.path.join(dist, n))
    os.makedirs(dist, exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(dist, "assets"), dirs_exist_ok=True)
    shutil.copy(os.path.join(ROOT, "src/style.css"), os.path.join(dist, "assets/style.css"))
    shutil.copy(os.path.join(ROOT, "src/app.js"), os.path.join(dist, "assets/app.js"))

    home_ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": NAME, "url": SITE + "/", "publisher": ORG},
        {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": "%s/%s/" % (SITE, g["slug"]), "name": g["title"]} for i, g in enumerate(GAMES)]}]}
    write("index.html", document(ctx, "Skerry Arcade: free browser games from Åland", HOME_DESC, "/",
                                 "/assets/covers/%s-og.jpg" % GAMES[0]["slug"], home_body(ctx), home_ld))
    for g in GAMES:
        desc = "Play %s free in your browser. %s No download, no account." % (g["title"], g["summary"])
        ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": g["title"], "url": "%s/%s/" % (SITE, g["slug"]),
              "description": g["summary"], "image": "%s/assets/covers/%s.webp" % (SITE, g["slug"]), "genre": g["facts"]["Genre"],
              "gamePlatform": ["Web browser", "Mobile", "Desktop"], "applicationCategory": "Game", "operatingSystem": "Any",
              "playMode": "MultiPlayer" if "2" in g["facts"].get("Players", "") else "SinglePlayer", "keywords": g["keywords"],
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "publisher": ORG}
        write(g["slug"] + "/index.html", document(ctx, "%s: play free online | Skerry Arcade" % g["title"], desc, "/%s/" % g["slug"],
                                                 "/assets/covers/%s-og.jpg" % g["slug"], game_body(ctx, g), ld))
    write("privacy/index.html", document(ctx, "Privacy | Skerry Arcade", "What Skerry Arcade stores and why.", "/privacy/",
                                         "/assets/covers/%s-og.jpg" % GAMES[0]["slug"], privacy_body(ctx)))
    nf = ('<div class="wrap notfound"><h1>Off the chart</h1><p>This page does not exist. The games are all still here.</p>'
          '<a class="btn btn-lamp" href="/">Back to all games</a></div>')
    write("404.html", document(ctx, "Page not found | Skerry Arcade", "Page not found.", "/404.html", "/assets/covers/%s-og.jpg" % GAMES[0]["slug"], nf))
    urls = ["/"] + ["/%s/" % g["slug"] for g in GAMES] + ["/privacy/"]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(
        "  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, date.today().isoformat()) for u in urls))
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE)
    write("CNAME", SITE.split("//")[1] + "\n")
    write(".nojekyll", "")
    write("manifest.webmanifest", json.dumps({"name": NAME, "short_name": "Skerry", "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0A1821", "theme_color": "#0A1821", "icons": [
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, indent=2))
    # /play/<slug>/ without a file name goes to the game page
    for g in GAMES:
        if g["entry"] != "index.html":
            write("play/%s/index.html" % g["slug"], '<!doctype html><meta charset="utf-8"><title>%s</title><link rel="canonical" href="%s/%s/"><meta http-equiv="refresh" content="0;url=/%s/">' % (E(g["title"]), SITE, g["slug"], g["slug"]))
    print("Built dist/ with %d games" % len(GAMES))


def build_preview(out):
    ctx = Ctx(True)
    for g in GAMES:
        if g["slug"] != "alandsflyg": g["previewSrc"] = "play/%s.html" % g["slug"]
    css, js = assets_tags(ctx)
    views = ['<section data-view="home">%s</section>' % home_body(ctx)]
    views += ['<section data-view="%s" hidden>%s</section>' % (g["slug"], game_body(ctx, g)) for g in GAMES]
    views += ['<section data-view="privacy" hidden>%s</section>' % privacy_body(ctx)]
    page = ('<title>Skerry Arcade</title><meta name="claude:viewport-fit-sides" content="cover">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="%s">%s%s<main>%s</main>%s%s') % (FONTS, css, header(ctx), "".join(views), footer(ctx), js)
    open(out, "w", encoding="utf-8").write(page)
    print("Preview written to", out, "(%d kB)" % (len(page) // 1024))


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview": build_preview(sys.argv[2])
    else: build_site()
