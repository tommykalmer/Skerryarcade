"""Removes a game's own Google Analytics tag from its copy on Skerry Arcade.
The portal loads analytics itself, and only after the visitor says yes."""
import re, sys
for path in sys.argv[1:]:
    s = open(path, encoding="utf-8").read()
    n = re.sub(r'<script async src="https://www\.googletagmanager\.com/gtag/js\?id=[^"]*"></script>\s*<script>\s*window\.dataLayer[\s\S]*?</script>', "", s, count=1)
    if n != s:
        open(path, "w", encoding="utf-8").write(n)
        print("Removed GA tag from", path)
