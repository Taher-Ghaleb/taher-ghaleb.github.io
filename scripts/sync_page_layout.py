#!/usr/bin/env python3
"""Copy the homepage header/footer into the standalone pages.

Run after changing navigation or footer content in index.html. Output stays
plain HTML, so the site works with both GitHub Pages and the local web server.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def sync():
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    header = re.search(r'<nav\b.*?</nav>', home, re.S).group()
    footer = re.search(r'<footer\b.*?</footer>', home, re.S).group()
    header = header.replace("site-navbar-target", "standalone-navigation")
    # The standalone pages link to homepage sections instead of local anchors.
    header = re.sub(r'href="#([^"]+)"', r'href="index.html#\1"', header)
    footer = re.sub(r'href="#([^"]+)"', r'href="index.html#\1"', footer)
    fonts = re.search(r'<link href="https://fonts.googleapis.com/[^>]+>', home).group()
    icons = '\n'.join(re.findall(r'<link rel="stylesheet" href="https://[^>]+>', home))
    for name in ("members.html", "publications.html"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(r'<nav\b.*?</nav>', lambda _: header, text, count=1, flags=re.S)
        text = re.sub(r'<footer\b.*?</footer>', lambda _: footer, text, count=1, flags=re.S)
        text = re.sub(r'<link href="https://fonts.googleapis.com/[^>]+>', lambda _: fonts, text)
        text = re.sub(r'\s*<link rel="stylesheet" href="https://[^>]+>', '', text)
        text = text.replace('<link rel="stylesheet" href="css/style.css">', icons + '\n  <link rel="stylesheet" href="css/style.css">')
        if 'src="js/navigation.js"' not in text:
            text = text.replace('</body>', '  <script src="js/navigation.js" defer></script>\n</body>')
        path.write_text(text, encoding="utf-8", newline="\r\n")
        print(f"Updated header and footer: {name}")


if __name__ == "__main__":
    sync()
