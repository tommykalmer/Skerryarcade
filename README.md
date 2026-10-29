# Skerry Arcade

Free online games. Live at **https://skerryarcade.com**

The portal is a small static site. The games are not copied into this repo: on every deploy the
workflow pulls the latest version of each game from its own repo and places it under `/play/<game>/`.
Keep working on the games in their own repos as before.

| Game | Repo | Page | Game file |
|---|---|---|---|
| Ember Vigil | EmberVigil | /ember-vigil/ | /play/ember-vigil/index.html |
| Snowfeud | Snowfeud | /snowfeud/ | /play/snowfeud/play.html |
| GolfFeud | Golfrundan | /golffeud/ | /play/golffeud/play.html |
| Ålandsflyg | alandsflyg | /alandsflyg/ | /play/alandsflyg/index.html |

## Files

| File | Purpose |
|---|---|
| `games.json` | Every game: texts, categories, tags, colours, date added, featured |
| `categories.json` | Categories: name, colour, icon, text. Only categories that have games are shown |
| `build.py` | Builds the pages into `dist/` (no dependencies, plain Python 3) |
| `src/style.css`, `src/app.js` | Design and site script (search, random game, continue playing, player, consent) |
| `assets/` | Covers per game (`covers/<game>.webp` 1280×720, `-sm.webp` 640×360, `-sq.webp` 256×256, `-og.jpg` 1200×630) and icons |
| `tools/strip_ga.py` | Removes GolfFeud's own analytics tag from the portal copy |
| `.github/workflows/deploy.yml` | Pulls the games, builds and publishes to GitHub Pages |

## One-time setup

1. **Pages**: Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. **Token for the private game repos** (Snowfeud and Golfrundan):
   GitHub → Settings (your profile) → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token.
   Repository access: *Only select repositories* → Snowfeud and Golfrundan. Permissions: **Contents: Read-only**. Expiration: up to 1 year.
   Copy the token, then in this repo: Settings → Secrets and variables → Actions → New repository secret, name `GAMES_TOKEN`.
3. **Domain**: Settings → Pages → Custom domain `skerryarcade.com`, then tick *Enforce HTTPS* once the certificate is ready.
   At the domain registrar, add four `A` records for `@` → `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`
   and a `CNAME` record for `www` → `tommykalmer.github.io`.
4. Actions → **Build and deploy** → Run workflow.

## Updating

- Game changes: push to the game's own repo. The portal picks it up within three hours, or right away with *Run workflow*.
- Text changes: edit `games.json`.
- New game: add it to `games.json` (with `categories`, `added` and optionally `featured`), add the four covers to `assets/covers/`, and add a checkout step for its repo in the workflow. Optional `preview`: a short muted mp4 that plays when the tile is hovered.

## Games that live on the portal

A game does not need a repo or domain of its own. Put it in `games/<slug>/` (with `index.html` as the entry),
add it to `games.json` with `"source": "local"`, and add its covers. It is published at `/play/<slug>/`.
Games made for the portal include `/assets/skerry-sdk.js` (see the top of `src/skerry-sdk.js`) to report
rounds, levels and big moments to Analytics.

## Analytics

Set `GA_ID` at the top of `build.py` to the portal's GA4 Measurement ID. Visitors are asked first. Events wait in the
browser and are only sent after a yes (then the current page is counted too). Nothing is sent after a no.

Every event has `page_type` (home, game, category, all_games, search, privacy). Events sent by the portal:

| Event | When | Parameters |
|---|---|---|
| `page_view` | every page (automatic) | content group = page_type, plus `game` / `category` |
| `game_click` | a game tile is clicked | `game`, `list` (spotlight, home_all, game_rail, search_results …), `position` |
| `category_click` | a category in the menu or on a game page | `category`, `from` |
| `search` / `search_suggest` / `search_no_results` | search used | `search_term`, `results` |
| `game_start` | Play pressed | `game`, `mode` (inline/overlay), `play_number`, `days_since_last_play`, `returning_player`, `games_tried` |
| `game_loaded` | game finished loading | `game`, `load_ms` |
| `game_play_time` | after 1, 3, 5, 10, 20, 30, 60 minutes of visible play | `game`, `minutes` |
| `game_end` | game closed, page left, other game started | `game`, `play_seconds`, `reason` |
| `fullscreen`, `share`, `random_game` | buttons | `game`, `method` |
| in-game events | anything a game sends with gtag() or the Skerry SDK | event's own parameters + `game`, `source=in_game` |

### One-time setup in Google Analytics
1. analytics.google.com → Admin → Create property "Skerry Arcade" → Web stream `https://skerryarcade.com`. Copy the Measurement ID into `GA_ID`.
2. Admin → Custom definitions → Create custom dimensions (scope Event): `game`, `list`, `mode`, `category`, `page_type`, `returning_player`, `reason`, `source`.
   Custom metrics (scope Event): `play_seconds` (unit seconds), `play_number`, `days_since_last_play`, `position`, `load_ms` (milliseconds).
3. Admin → Events → mark `game_start` as a key event.
4. Admin → Data retention → 14 months.
5. Admin → Product links → Search Console links → link the skerryarcade.com property.

### Google Search Console
1. search.google.com/search-console → Add property → **Domain** → `skerryarcade.com` → add the TXT record it shows at the domain registrar.
   (Or choose URL prefix → HTML tag and put the code in `GSC_VERIFICATION` in `build.py`.)
2. Sitemaps → submit `https://skerryarcade.com/sitemap.xml`.

## Ads

The games run in portal mode here (their own analytics, consent banners and service workers stay off), and the CrazyGames SDK inside them falls back to no-ops.
