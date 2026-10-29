#!/usr/bin/env python3
"""Builds Skerry Arcade into dist/.

    python3 build.py                 -> dist/ (the real site; the workflow copies the games into dist/play/)
    python3 build.py --preview FILE  -> one self-contained preview page

Content lives in two files:
  games.json       every game: texts, categories, tags, colours, date added
  categories.json  every category: name, colour, icon, short text (only categories with games are shown)
Add a game: add it to games.json, add covers to assets/covers/, add its repo to .github/workflows/deploy.yml.
"""
import base64, html, json, mimetypes, os, shutil, sys
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://skerryarcade.com"
NAME = "Skerry Arcade"
GA_ID = ""            # the portal's GA4 Measurement ID (G-XXXXXXXXXX); visitors are asked before it loads
GSC_VERIFICATION = "" # Google Search Console "HTML tag" code (only the content="..." value); not needed with DNS verification
CONTACT = "hello@skerryarcade.com"
OWNER = "AsterIQ Ab"
NEW_DAYS = 14         # "New" badge for games added within this many days
SPOTLIGHT = 3         # games in the big block at the top of the home page
HOME_ROW_MIN = 6      # a category gets its own row on the home page once it has this many games

GAMES = json.load(open(os.path.join(ROOT, "games.json"), encoding="utf-8"))
CATS_ALL = json.load(open(os.path.join(ROOT, "categories.json"), encoding="utf-8"))
GAMES.sort(key=lambda g: g.get("added", ""), reverse=True)
BY_SLUG = {g["slug"]: g for g in GAMES}
CATS = [c for c in CATS_ALL if any(c["slug"] in g["categories"] for g in GAMES)]
CAT = {c["slug"]: c for c in CATS_ALL}
for c in CATS: c["games"] = [g for g in GAMES if c["slug"] in g["categories"]]
CATS.sort(key=lambda c: -len(c["games"]))
E = lambda s: html.escape(str(s), quote=True)
TODAY = date.today()

def is_new(g):
    try: return (TODAY - date.fromisoformat(g["added"])).days <= NEW_DAYS
    except Exception: return False

# ---------------------------------------------------------------- icons
def I(name, cls="i"):
    P = {
        "home": '<path d="M4 11.5 12 5l8 6.5V19a1 1 0 0 1-1 1h-4.5v-5h-5v5H5a1 1 0 0 1-1-1z"/>',
        "new": '<path d="M12 3c.8 4.6 3.4 7.2 8 8-4.6.8-7.2 3.4-8 8-.8-4.6-3.4-7.2-8-8 4.6-.8 7.2-3.4 8-8z"/>',
        "recent": '<circle cx="12" cy="12" r="8"/><path d="M12 7.5V12l3 2"/>',
        "grid": '<rect x="4" y="4" width="7" height="7" rx="2"/><rect x="13" y="4" width="7" height="7" rx="2"/><rect x="4" y="13" width="7" height="7" rx="2"/><rect x="13" y="13" width="7" height="7" rx="2"/>',
        "dice": '<rect x="4" y="4" width="16" height="16" rx="4"/><circle cx="9" cy="9" r="1.2" fill="currentColor"/><circle cx="15" cy="15" r="1.2" fill="currentColor"/><circle cx="15" cy="9" r="1.2" fill="currentColor"/><circle cx="9" cy="15" r="1.2" fill="currentColor"/>',
        "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/>',
        "bolt": '<path d="M13 3 5 13.5h6L10 21l8-10.5h-6z"/>',
        "duo": '<circle cx="8.5" cy="8.5" r="3"/><circle cx="16" cy="9.5" r="2.5"/><path d="M3.5 19c.5-3.2 2.4-5 5-5s4.5 1.8 5 5M14 14.3c.6-.2 1.3-.3 2-.3 2.2 0 3.8 1.6 4.3 4.5"/>',
        "ball": '<circle cx="12" cy="12" r="8"/><path d="M4.5 9.5c4.5 1.5 10.5 1.5 15 0M4.5 14.5c4.5-1.5 10.5-1.5 15 0"/>',
        "plane": '<path d="M10.5 4.5c0-1 .7-1.5 1.5-1.5s1.5.5 1.5 1.5V9l7 4v2l-7-2v4l2 1.5V20l-3.5-1-3.5 1v-1.5l2-1.5v-4l-7 2v-2l7-4z"/>',
        "flag": '<path d="M6 21V4M6 4.5c4-2 8 2 12 0V13c-4 2-8-2-12 0"/>',
        "flame": '<path d="M12 21c-3.9 0-6.5-2.6-6.5-6 0-3.6 3-5.3 3.5-9 2 1.3 3 3 3 4.6 1-.6 1.6-1.7 1.8-3 2.6 2 4.7 4.8 4.7 7.6 0 3.3-2.6 5.8-6.5 5.8z"/>',
        "smile": '<circle cx="12" cy="12" r="8"/><path d="M8.5 13.5c1.8 2.2 5.2 2.2 7 0"/><circle cx="9.3" cy="9.8" r="1" fill="currentColor"/><circle cx="14.7" cy="9.8" r="1" fill="currentColor"/>',
        "piece": '<path d="M5 9h3.2a2.3 2.3 0 1 1 4.6 0H16v3.2a2.3 2.3 0 1 1 0 4.6V20H5z"/>',
        "wheel": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="2.5"/><path d="M12 4v5.5M5 15.5l5-2M19 15.5l-5-2"/>',
        "globe": '<circle cx="12" cy="12" r="8"/><path d="M4 12h16M12 4c2.4 2.4 2.4 13.6 0 16M12 4c-2.4 2.4-2.4 13.6 0 16"/>',
        "play": '<path d="M8 5.5v13l10.5-6.5z" fill="currentColor" stroke-linejoin="round"/>',
        "fs": '<path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/>',
        "share": '<path d="M12 3v12M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/>',
        "out": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    }
    return '<svg class="%s" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % (cls, P[name])

MARK = ('<svg class="mark" viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="12" fill="#FFD23F"/>'
        '<path d="M5.5 30.5c2.6-6.4 7.3-8.6 11.6-6.6 3-5.3 10.6-5.4 13.8-.2 2.4-.2 3.9 2.3 3.9 6.8z" fill="#11132A"/>'
        '<path d="M5 34.6c2.6 0 2.6-1.6 5-1.6s2.6 1.6 5 1.6 2.6-1.6 5-1.6 2.6 1.6 5 1.6 2.6-1.6 5-1.6 2.6 1.6 5 1.6" fill="none" stroke="#11132A" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M26.5 5.5c.6 3.4 2.6 5.4 6 6-3.4.6-5.4 2.6-6 6-.6-3.4-2.6-5.4-6-6 3.4-.6 5.4-2.6 6-6z" fill="#FF6B9A"/></svg>')
ROTATE = '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="9" y="14" width="30" height="20" rx="4"/><path d="M20 6a14 14 0 0 1 14 6M34 6v6h-6"/></svg>'
FONTS = "https://fonts.googleapis.com/css2?family=Familjen+Grotesk:wght@400;500;600;700&family=Unbounded:wght@600;700;800&display=swap"


class Ctx:
    """Differences between the real site and the one-file preview."""
    def __init__(self, preview=False):
        self.preview = preview
        self.cache = {}
    def page(self, path=""):
        """path: '' home, 'snowfeud', 'c/action', 'privacy', 'search', 'games'"""
        if self.preview: return "#" + (path.replace("/", "-") if path else "home")
        return "/" + (path + "/" if path else "")
    def asset(self, path):
        if not self.preview: return "/assets/" + path
        if path not in self.cache:
            full = os.path.join(ROOT, "assets", path)
            mt = mimetypes.guess_type(full)[0] or ("image/webp" if full.endswith(".webp") else "application/octet-stream")
            self.cache[path] = "data:%s;base64,%s" % (mt, base64.b64encode(open(full, "rb").read()).decode())
        return self.cache[path]
    def src(self, g):
        if self.preview: return g.get("previewSrc", "")
        return "/play/%s/%s" % (g["slug"], g["entry"])


# ---------------------------------------------------------------- pieces
def badges(g):
    b = []
    if is_new(g): b.append('<span class="badge">New</span>')
    if "two-player" in g["categories"]: b.append('<span class="badge duo">2 Player</span>')
    return '<span class="badges">%s</span>' % "".join(b) if b else ""

def tile(ctx, g, extra_cls="", big=False):
    img = ctx.asset("covers/%s%s.webp" % (g["slug"], "" if big else "-sm"))
    vid = (' data-video="%s"' % E(g["preview"])) if g.get("preview") and not ctx.preview else ""
    cta = ""
    if "hero" in extra_cls or "side-tile" in extra_cls:
        cta = '<span class="cta"><h2>%s</h2><p>%s</p><span class="pill-btn sun">%s Play now</span></span>' % (E(g["title"]), E(g["tagline"]), I("play"))
    return ('<a class="tile %s" href="%s" style="--g:%s"%s><img src="%s" alt="%s" width="%d" height="%d" loading="%s" decoding="async">%s<span class="name">%s</span>%s</a>'
            % (extra_cls, ctx.page(g["slug"]), g["accent"], vid, img, E(g["title"]), 1280 if big else 640, 720 if big else 360,
               "eager" if big else "lazy", badges(g), E(g["title"]), cta))

def tiles(ctx, games, cls="", list_id=""):
    return '<div class="tiles %s"%s>%s</div>' % (cls, (' data-list="%s"' % list_id) if list_id else "", "".join(tile(ctx, g) for g in games))

def cat_icon(c):
    return '<span class="ic">%s</span>' % I(c["icon"])

def side(ctx, current):
    def item(href, label, icon, color, key, n=""):
        cur = ' aria-current="page"' if key == current else ""
        cl = (' data-cat-link="%s"' % key.split("/")[-1]) if key.startswith("c/") else ""
        return '<a class="nav-i" href="%s" style="--c:%s"%s%s><span class="ic">%s</span><span>%s</span>%s</a>' % (href, color, cur, cl, I(icon), label, n)
    top = [item(ctx.page(""), "Home", "home", "#FFD23F", "home"),
           item(ctx.page("games"), "All games", "grid", "#A0A6CC", "games"),
           item(ctx.page("c/new"), "New", "new", "#FF6B9A", "c/new")]
    cats = [item(ctx.page("c/" + c["slug"]), c["name"], c["icon"], c["color"], "c/" + c["slug"]) for c in CATS]
    return '<aside class="side" aria-label="Categories"><nav>%s<div class="group">Categories</div>%s</nav></aside>' % ("".join(top), "".join(cats))

def chips(ctx, current):
    items = [("", "Home", "home", "#FFD23F"), ("c/new", "New", "new", "#FF6B9A")] + [("c/" + c["slug"], c["name"], c["icon"], c["color"]) for c in CATS]
    return '<nav class="chips" aria-label="Categories">%s</nav>' % "".join(
        '<a href="%s" style="--c:%s"%s%s><span class="ic">%s</span>%s</a>' % (ctx.page(p), col, ' aria-current="page"' if (p or "home") == current else "",
                                                      (' data-cat-link="%s"' % p[2:]) if p.startswith("c/") else "", I(ic), n)
        for p, n, ic, col in items)

def header(ctx):
    return ('<header class="top">'
            '<a class="brand" href="%s" aria-label="%s, home">%s<span class="word"><b>skerry</b><span>arcade</span></span></a>'
            '<form class="search" role="search" action="%s" data-search><label class="sr" for="q">Search games</label>%s'
            '<input id="q" name="q" type="search" placeholder="Search games" autocomplete="off" enterkeyhint="search"><kbd>/</kbd>'
            '<div class="results" hidden></div></form>'
            '<div class="top-actions"><button class="pill-btn" type="button" data-random title="Play a random game">%s<span class="lbl">Random</span></button></div>'
            '</header>') % (ctx.page(""), NAME, MARK, ctx.page("search") if not ctx.preview else "#search", I("search"), I("dice"))

def footer(ctx):
    cat_links = "".join('<li><a href="%s">%s games</a></li>' % (ctx.page("c/" + c["slug"]), E(c["name"])) for c in CATS[:6])
    return ('<footer class="foot"><div class="about"><a class="brand" href="%s">%s<span class="word"><b>skerry</b><span>arcade</span></span></a>'
            '<p>Free online games you can start in a second, on phone, tablet or computer.</p></div>'
            '<div><h3>Categories</h3><ul>%s</ul></div>'
            '<div><h3>Skerry Arcade</h3><ul><li><a href="%s">All games</a></li><li><a href="%s">New games</a></li><li><a href="%s">Privacy</a></li><li>%s</li></ul></div>'
            '<p class="legal">© %d %s</p></footer>') % (ctx.page(""), MARK, cat_links, ctx.page("games"), ctx.page("c/new"), ctx.page("privacy"), E(CONTACT), TODAY.year, NAME)

def sec(ctx, title, icon, color, body, more=None):  # body: tiles(..., list_id=...)
    m = ('<a class="more" href="%s">See all</a>' % more) if more else ""
    return '<section class="sec"><div class="sec-head"><h2><span class="ic" style="--c:%s">%s</span>%s</h2>%s</div>%s</section>' % (color, I(icon), E(title), m, body)

# ---------------------------------------------------------------- pages
def home_body(ctx):
    feat = [g for g in GAMES if g.get("featured")][:SPOTLIGHT] or GAMES[:SPOTLIGHT]
    spot = ""
    if feat:
        spot = '<div class="spot" data-spot data-list="spotlight">%s%s</div><div class="dots" aria-hidden="true">%s</div>' % (
            tile(ctx, feat[0], "hero", True), "".join(tile(ctx, g, "side-tile", True) for g in feat[1:]),
            "".join("<i></i>" for _ in feat))
    out = [chips(ctx, "home"), spot,
           '<section class="sec" data-recent hidden><div class="sec-head"><h2><span class="ic" style="--c:#7DE3FF">%s</span>Continue playing</h2></div><div class="tiles" data-list="continue_playing"></div></section>' % I("recent")]
    if len(GAMES) > 8:   # with only a few games the full list below already shows them
        out.append(sec(ctx, "New games", "new", "#FF6B9A", tiles(ctx, GAMES[:12], list_id="home_new"), ctx.page("c/new")))
    for c in CATS:
        if len(c["games"]) >= HOME_ROW_MIN:
            out.append(sec(ctx, c["name"] + " games", c["icon"], c["color"], tiles(ctx, c["games"][:12], list_id="home_" + c["slug"]), ctx.page("c/" + c["slug"])))
    out.append(sec(ctx, "All games", "grid", "#A0A6CC", tiles(ctx, GAMES[:48], list_id="home_all"), ctx.page("games") if len(GAMES) > 48 else None))
    out.append('<div class="blurb"><h2>Free online games on Skerry Arcade</h2><p>Every game here runs straight in your browser. There is nothing to download and no account to make, so you can go from tap to play in a second. '
               'Pick something quick for a short break, duel a friend over a link, or settle in for a longer run. Your progress is saved on your device.</p></div>')
    return "".join(out)

def list_body(ctx, key, title, sub, icon, color, games, blurb=""):
    return '%s<div class="phead" style="--c:%s"><span class="ic">%s</span><div><h1>%s</h1><p>%s</p></div></div>%s%s' % (
        chips(ctx, key), color, I(icon), E(title), E(sub), tiles(ctx, games, list_id=key.replace("c/", "category_")) if games else '<p class="empty-state">No games here yet.</p>',
        ('<div class="blurb"><p>%s</p></div>' % blurb) if blurb else "")

def game_body(ctx, g):
    others = [o for o in GAMES if o["slug"] != g["slug"]]
    related = sorted(others, key=lambda o: -len(set(o["categories"]) & set(g["categories"])))
    facts = "".join("<dt>%s</dt><dd>%s</dd>" % (E(k), E(v)) for k, v in g["facts"].items())
    ctrl = "".join('<tr><th scope="row">%s</th><td>%s</td><td>%s</td></tr>' % tuple(E(x) for x in c) for c in g["controls"])
    feats = "".join("<li>%s</li>" % E(f) for f in g["features"])
    about = "".join("<p>%s</p>" % E(p) for p in g["about"])
    cats = "".join('<a class="tag" href="%s" style="--c:%s" data-cat-link="%s"><i></i>%s</a>' % (ctx.page("c/" + c), CAT[c]["color"], c, E(CAT[c]["name"])) for c in g["categories"] if c in CAT)
    tags = "".join('<span class="tag">%s</span>' % E(t) for t in g.get("tags", []))
    also = ""
    if g.get("ownSite"):
        host = g["ownSite"].split("//")[1].replace("www.", "")
        also = '<p class="also">Also at <a href="%s" rel="noopener">%s</a>. Duel links from both places work.</p>' % (g["ownSite"], host)
    hint = ('<span class="h-d">Click to play. Full screen is one click away</span><span class="h-m">%s</span>'
            % ("Plays full screen" if g.get("touchOrientation") != "landscape" else "Plays full screen, best held sideways"))
    sq = ctx.asset("covers/%s-sq.webp" % g["slug"])
    unavailable = ctx.preview and not ctx.src(g)
    if unavailable:
        start = ('<a class="start" href="https://tommykalmer.github.io/alandsflyg/" target="_blank" rel="noopener"><img class="thumb" src="%s" alt="">'
                 '<span class="lbl">%s</span><span class="go">%s Play</span><span class="hint">Too big for this preview, opens in a new tab</span></a>') % (sq, E(g["title"]), I("out"))
    else:
        start = ('<button class="start" type="button" data-start><img class="thumb" src="%s" alt=""><span class="lbl">%s</span>'
                 '<span class="go">%s Play</span><span class="hint">%s</span></button>') % (sq, E(g["title"]), I("play"), hint)
    first = CAT.get(g["categories"][0], {"name": ""})["name"]
    return """%(chips)s
<div class="gp" data-game="%(slug)s" style="--g:%(accent)s">
  <div>
    <div class="player-card">
      <div class="stage"><img class="poster" src="%(cover)s" alt="" width="1280" height="720">%(shade)s%(start)s</div>
      <div class="gbar">
        <img class="ico" src="%(sq)s" alt="" width="44" height="44">
        <div class="t"><h1>%(title)s</h1><small>%(first)s game</small></div>
        <div class="tools">%(fsbtn)s<button class="tool" type="button" data-share>%(ishare)s<span class="lbl">Share</span></button></div>
      </div>
    </div>
    <div class="info">
      <div class="card prose">
        <h2>%(tagline)s</h2>
        %(about)s
        <ul class="features">%(feats)s</ul>
        <div class="tags">%(cats)s%(tags)s</div>
        %(also)s
      </div>
      <div>
        <div class="card"><h2>Game info</h2><dl class="facts">%(facts)s</dl></div>
        <div class="card"><h2>Controls</h2><div style="overflow-x:auto"><table class="controls"><thead><tr><th scope="col"></th><th scope="col">Computer</th><th scope="col">Phone</th></tr></thead><tbody>%(ctrl)s</tbody></table></div></div>
      </div>
    </div>
  </div>
  <aside class="rail"><h2>More games</h2>%(rail)s</aside>
</div>
<div style="margin-top:40px">%(more)s</div>""" % dict(
        chips=chips(ctx, ""), slug=g["slug"], accent=g["accent"], cover=ctx.asset("covers/%s.webp" % g["slug"]),
        shade='<div class="shade"></div>', start=start, sq=sq, title=E(g["title"]), first=E(first),
        fsbtn="" if unavailable else '<button class="tool" type="button" data-fullscreen>%s<span class="lbl">Full screen</span></button>' % I("fs"),
        ishare=I("share"), tagline=E(g["tagline"]), about=about, feats=feats, cats=cats, tags=tags, also=also, facts=facts, ctrl=ctrl,
        rail=tiles(ctx, related[:8], "small", "game_rail"), more=sec(ctx, "You may also like", "new", "#FF6B9A", tiles(ctx, related[:12], list_id="game_also_like")))

def search_body(ctx):
    return ('%s<div class="phead" style="--c:#FFD23F"><span class="ic">%s</span><div><h1 data-search-title>Search</h1><p data-search-sub>Type a game, a category or something you like, such as golf or penguins.</p></div></div>'
            '<div class="tiles" data-search-results data-list="search_results"></div>') % (chips(ctx, "search"), I("search"))

def privacy_body(ctx):
    return """<div class="legal-page">
  <h1>Privacy</h1>
  <p>Skerry Arcade is run by %(owner)s. This page explains what the site stores and why. Questions go to %(contact)s.</p>
  <h2>What stays on your device</h2>
  <p>The games save your progress, settings and best scores in your browser's local storage, on your device only. The site also remembers which games you played last so it can show them on the front page. Nothing of this is sent to us. Clearing your browser data removes it.</p>
  <h2>Duel links</h2>
  <p>In some games a duel with a friend is stored entirely inside the link you send: shots, scores and the course. The link is not saved on any server. Anyone who has the link can open the duel.</p>
  <h2>Analytics</h2>
  <p>If you allow it, we use Google Analytics to count visits and see which games are played. It uses cookies and shortened IP addresses and does not build an advertising profile. If you choose No thanks, no analytics script is loaded. You can change your mind by clearing this site's data in your browser.</p>
  <h2>Ads</h2>
  <p>The site shows no ads today. If that changes, this page will be updated first and you will be asked before any ad cookies are used.</p>
  <h2>Your rights</h2>
  <ul><li>Ask what data we hold about you (normally none).</li><li>Ask us to delete analytics data linked to your device.</li><li>Complain to your national data protection authority.</li></ul>
</div>""" % dict(owner=E(OWNER), contact=E(CONTACT))

def notfound_body(ctx):
    return ('<div class="notfound"><h1>Game over?</h1><p>This page does not exist, but every game is still here.</p>'
            '<a class="pill-btn sun" href="%s">%s Back to the games</a></div>%s') % (ctx.page(""), I("home"), sec(ctx, "Try one of these", "dice", "#FFD23F", tiles(ctx, GAMES[:8], list_id="not_found")))

# ---------------------------------------------------------------- documents
def game_data(ctx):
    return [{"slug": g["slug"], "title": g["title"], "accent": g["accent"], "tagline": g["tagline"],
             "href": ctx.page(g["slug"]), "thumb": ctx.asset("covers/%s-sm.webp" % g["slug"]), "icon": ctx.asset("covers/%s-sq.webp" % g["slug"]),
             "src": ctx.src(g), "orientation": g.get("touchOrientation", "any"), "share": SITE + "/" + g["slug"] + "/",
             "cats": [CAT[c]["name"] for c in g["categories"] if c in CAT], "tags": g.get("tags", []),
             "isNew": is_new(g), "duo": "two-player" in g["categories"]} for g in GAMES]

def assets_tags(ctx):
    data = json.dumps({"games": game_data(ctx), "privacy": ctx.page("privacy")}, ensure_ascii=False)
    if ctx.preview:
        css = open(os.path.join(ROOT, "src/style.css"), encoding="utf-8").read()
        js = open(os.path.join(ROOT, "src/app.js"), encoding="utf-8").read()
        return "<style>%s</style>" % css, "<script>window.SKERRY=%s</script><script>%s</script>" % (data, js)
    return ('<link rel="stylesheet" href="/assets/style.css?v=%s">' % VERSION,
            '<script>window.SKERRY=%s</script><script src="/assets/app.js?v=%s" defer></script>' % (data, VERSION))

def head(ctx, title, desc, path, image, jsonld=None, noindex=False):
    url = SITE + path
    ld = ('<script type="application/ld+json">%s</script>' % json.dumps(jsonld, ensure_ascii=False)) if jsonld else ""
    meta = ('<link rel="canonical" href="%(url)s"><meta property="og:type" content="website"><meta property="og:site_name" content="%(name)s">'
            '<meta property="og:title" content="%(t)s"><meta property="og:description" content="%(d)s"><meta property="og:url" content="%(url)s">'
            '<meta property="og:image" content="%(img)s"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">'
            '<meta name="twitter:card" content="summary_large_image">%(robots)s'
            '<link rel="icon" href="/assets/icon.svg" type="image/svg+xml"><link rel="icon" href="/assets/favicon-32.png" sizes="32x32">'
            '<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png"><link rel="manifest" href="/manifest.webmanifest">'
            ) % dict(url=url, name=NAME, t=E(title), d=E(desc), img=SITE + image, robots='<meta name="robots" content="noindex">' if noindex else "")
    return ('<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<title>%s</title><meta name="description" content="%s"><meta name="theme-color" content="#1A1D3B">%s%s'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="%s">%s') % (E(title), E(desc), meta,
                ('<meta name="google-site-verification" content="%s">' % E(GSC_VERIFICATION)) if GSC_VERIFICATION and path == "/" else "", FONTS, ld)

def shell(ctx, current, body):
    return '%s<div class="shell">%s<main class="main" id="main">%s%s</main></div>' % (header(ctx), side(ctx, current), body, footer(ctx))

def page_meta(key):
    """What Analytics gets for each page: page_type (also the content group), and game / category where it applies."""
    if key == "home": return {"page-type": "home"}
    if key == "games": return {"page-type": "all_games"}
    if key == "c/new": return {"page-type": "category", "category": "new"}
    if key.startswith("c/"): return {"page-type": "category", "category": key[2:]}
    if key in BY_SLUG: return {"page-type": "game", "game": key, "category": BY_SLUG[key]["categories"][0]}
    return {"page-type": key or "not_found"}

def data_attrs(key):
    return "".join(' data-%s="%s"' % (k, E(v)) for k, v in page_meta(key).items())

def document(ctx, current, title, desc, path, image, body, jsonld=None, noindex=False):
    css, js = assets_tags(ctx)
    return ('<!doctype html><html lang="en" data-ga="%s"><head>%s%s</head><body%s>%s%s</body></html>'
            % (GA_ID, head(ctx, title, desc, path, image, jsonld, noindex), css, data_attrs(current), shell(ctx, current, body), js))

def write(rel, text):
    full = os.path.join(ROOT, "dist", rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w", encoding="utf-8").write(text)

ORG = {"@type": "Organization", "name": NAME, "url": SITE + "/"}
HOME_DESC = "Play free online games on Skerry Arcade: action, sports, 2 player duels, simulators and more. No download, no account. Works on phone, tablet and computer."
OG = lambda: "/assets/covers/%s-og.jpg" % GAMES[0]["slug"]

def pages(ctx):
    """(key, path, title, desc, body, jsonld, image, noindex)"""
    out = []
    home_ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebSite", "name": NAME, "url": SITE + "/", "publisher": ORG,
         "potentialAction": {"@type": "SearchAction", "target": SITE + "/search/?q={q}", "query-input": "required name=q"}},
        {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": "%s/%s/" % (SITE, g["slug"]), "name": g["title"]} for i, g in enumerate(GAMES)]}]}
    out.append(("home", "", "Skerry Arcade: free online games, play instantly", HOME_DESC, home_body(ctx), home_ld, OG(), False))
    out.append(("games", "games", "All games | Skerry Arcade", "Every free online game on Skerry Arcade, newest first.",
                list_body(ctx, "games", "All games", "Newest first", "grid", "#A0A6CC", GAMES), None, OG(), False))
    new = [g for g in GAMES if is_new(g)] or GAMES[:12]
    out.append(("c/new", "c/new", "New games | Skerry Arcade", "The newest free online games on Skerry Arcade.",
                list_body(ctx, "c/new", "New games", "Fresh on Skerry Arcade", "new", "#FF6B9A", new), None, OG(), False))
    for c in CATS:
        out.append(("c/" + c["slug"], "c/" + c["slug"], "%s games: play free online | Skerry Arcade" % c["name"],
                    "Play free %s games online on Skerry Arcade. %s" % (c["name"].lower() if c["slug"] != "two-player" else "2 player", c["blurb"]),
                    list_body(ctx, "c/" + c["slug"], c["name"] + " games", c["blurb"], c["icon"], c["color"], c["games"],
                              "All %s games on Skerry Arcade are free and play in your browser on phone and computer, with nothing to install." % c["name"].replace("2 Player", "2 player")),
                    None, "/assets/covers/%s-og.jpg" % c["games"][0]["slug"], False))
    for g in GAMES:
        ld = {"@context": "https://schema.org", "@type": "VideoGame", "name": g["title"], "url": "%s/%s/" % (SITE, g["slug"]),
              "description": g["summary"], "image": "%s/assets/covers/%s.webp" % (SITE, g["slug"]),
              "genre": [CAT[c]["name"] for c in g["categories"] if c in CAT], "gamePlatform": ["Web browser", "Mobile", "Desktop"],
              "applicationCategory": "Game", "operatingSystem": "Any", "keywords": g["keywords"],
              "playMode": "MultiPlayer" if "two-player" in g["categories"] else "SinglePlayer",
              "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "publisher": ORG}
        out.append((g["slug"], g["slug"], "%s: play free online | Skerry Arcade" % g["title"],
                    "Play %s free in your browser. %s No download, no account." % (g["title"], g["summary"]), game_body(ctx, g), ld,
                    "/assets/covers/%s-og.jpg" % g["slug"], False))
    out.append(("search", "search", "Search | Skerry Arcade", "Search free online games.", search_body(ctx), None, OG(), True))
    out.append(("privacy", "privacy", "Privacy | Skerry Arcade", "What Skerry Arcade stores and why.", privacy_body(ctx), None, OG(), False))
    return out

def build_site():
    global VERSION
    VERSION = TODAY.strftime("%Y%m%d") + os.environ.get("GITHUB_RUN_NUMBER", "")
    ctx = Ctx(False)
    dist = os.path.join(ROOT, "dist")
    if os.path.isdir(dist):
        for n in os.listdir(dist):
            p = os.path.join(dist, n)
            if n != "play": shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)
    os.makedirs(dist, exist_ok=True)
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(dist, "assets"), dirs_exist_ok=True)
    shutil.copy(os.path.join(ROOT, "src/style.css"), os.path.join(dist, "assets/style.css"))
    shutil.copy(os.path.join(ROOT, "src/app.js"), os.path.join(dist, "assets/app.js"))
    shutil.copy(os.path.join(ROOT, "src/skerry-sdk.js"), os.path.join(dist, "assets/skerry-sdk.js"))
    for g in GAMES:   # games that live in this repo (games/<slug>/) instead of a repo of their own
        if g.get("source") == "local":
            dst = os.path.join(dist, "play", g["slug"])
            if os.path.islink(dst): os.remove(dst)
            shutil.copytree(os.path.join(ROOT, "games", g["slug"]), dst, dirs_exist_ok=True)
    urls = []
    for key, path, title, desc, body, ld, img, noindex in pages(ctx):
        write((path + "/" if path else "") + "index.html", document(ctx, key, title, desc, "/" + (path + "/" if path else ""), img, body, ld, noindex))
        if not noindex: urls.append("/" + (path + "/" if path else ""))
    write("404.html", document(ctx, "not_found", "Page not found | Skerry Arcade", "Page not found.", "/404.html", OG(), notfound_body(ctx), None, True))
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n%s\n</urlset>\n' % "\n".join(
        "  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (SITE, u, TODAY.isoformat()) for u in urls))
    write("robots.txt", "User-agent: *\nAllow: /\nDisallow: /search/\nSitemap: %s/sitemap.xml\n" % SITE)
    write("CNAME", SITE.split("//")[1] + "\n")
    write(".nojekyll", "")
    write("manifest.webmanifest", json.dumps({"name": NAME, "short_name": "Skerry", "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#11132A", "theme_color": "#1A1D3B", "icons": [
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}]}, indent=2))
    for g in GAMES:   # /play/<slug>/ without a file name goes to the game page
        if g["entry"] != "index.html":
            write("play/%s/index.html" % g["slug"], '<!doctype html><meta charset="utf-8"><title>%s</title><link rel="canonical" href="%s/%s/"><meta http-equiv="refresh" content="0;url=/%s/">' % (E(g["title"]), SITE, g["slug"], g["slug"]))
    print("Built dist/: %d games, %d categories, %d pages" % (len(GAMES), len(CATS), len(urls) + 2))

def build_preview(out):
    ctx = Ctx(True)
    for g in GAMES:
        if g["slug"] != "alandsflyg": g["previewSrc"] = "play/%s.html" % g["slug"]
    css, js = assets_tags(ctx)
    views = []
    for key, path, title, desc, body, ld, img, noindex in pages(ctx):
        vid = path.replace("/", "-") if path else "home"
        views.append('<div data-view="%s" data-key="%s"%s>%s</div>' % (vid, key, "" if vid == "home" else " hidden", body))
    page = ('<meta charset="utf-8"><title>Skerry Arcade</title><meta name="claude:viewport-fit-sides" content="cover">'
            '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
            '<link rel="stylesheet" href="%s">%s%s%s') % (FONTS, css, shell(ctx, "home", "".join(views)), js)
    open(out, "w", encoding="utf-8").write(page)
    print("Preview written to", out, "(%d kB)" % (len(page) // 1024))

if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--preview": build_preview(sys.argv[2])
    else: build_site()
