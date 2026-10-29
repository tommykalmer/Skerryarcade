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

## Analytics and ads

Set `GA_ID` at the top of `build.py` to the portal's GA4 Measurement ID. Visitors are asked first; nothing loads without a yes.
The games run in portal mode here (their own analytics, consent banners and service workers stay off), and the CrazyGames SDK inside them falls back to no-ops.
