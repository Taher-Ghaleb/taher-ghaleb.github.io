#!/usr/bin/env python3
"""Build publications.json from the BibTeX source, and normalize titles.

Single source of truth: papers/taher-ghaleb-publications.bib

What it does:
  1. Rewrites every `title={...}` in the .bib to consistent Title Case
     (initial caps), preserving acronyms (CI/CD, LLM, AI, GitHub, ...).
  2. Emits papers/publications.json grouped into journal / conference / patent,
     each entry with title, authors (name + self flag), venue text, and year.

Run from the repo root:  python scripts/build_publications.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIB = ROOT / "papers" / "taher-ghaleb-publications.bib"
OUT = ROOT / "papers" / "publications.json"

# Words kept lowercase unless first/last or after a colon or question mark.
MINOR = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if", "in",
    "into", "nor", "of", "off", "on", "onto", "or", "per", "the", "to", "up",
    "via", "vs", "with",
}

# All-lowercase tokens that must render as a fixed acronym / brand form.
ACRONYMS = {
    "llm": "LLM", "llms": "LLMs", "ci": "CI", "cd": "CD", "ci/cd": "CI/CD",
    "cicd": "CI/CD", "ai": "AI", "ml": "ML", "github": "GitHub", "api": "API",
    "apis": "APIs", "xml": "XML", "us": "US", "devops": "DevOps",
    "emse": "EMSE", "icsme": "ICSME", "icse": "ICSE", "msr": "MSR",
    "saner": "SANER", "ease": "EASE", "fse": "FSE", "icst": "ICST",
    "esem": "ESEM", "cascon": "CASCON", "vissoft": "VISSOFT", "iccis": "ICCIS",
}

warnings = []


def _fix_core(core, allow_minor):
    low = core.lower()
    if low in ACRONYMS:
        return ACRONYMS[low]
    if any(c.isupper() for c in core):
        return core  # already an acronym / camelCase; leave as-is
    if allow_minor and low in MINOR:
        return low
    return core[:1].upper() + core[1:]


def _title_token(token, force):
    # Split on hyphen/slash but keep the delimiters so "black-box" -> "Black-Box".
    out = []
    for i, part in enumerate(re.split(r"([-/])", token)):
        if part in ("-", "/") or part == "":
            out.append(part)
            continue
        m = re.match(r"^(\W*)(.*?)(\W*)$", part, re.UNICODE)
        pre, core, suf = m.group(1), m.group(2), m.group(3)
        if not core:
            out.append(part)
            continue
        allow_minor = not (force and i == 0)
        out.append(pre + _fix_core(core, allow_minor) + suf)
    return "".join(out)


def titlecase(title):
    words = [w for w in title.split(" ")]
    n = len(words)
    result = []
    force_next = True  # first word
    for i, w in enumerate(words):
        if w == "":
            result.append(w)
            continue
        force = force_next or (i == n - 1)
        result.append(_title_token(w, force))
        s = w.rstrip()
        force_next = s.endswith(":") or s.endswith("?") or s.endswith(".")
    return " ".join(result)


def normalize_bib_titles(text):
    def repl(m):
        return f"{m.group(1)}{titlecase(m.group(2))}{m.group(3)}"
    # title = {....},  (single line in this file)
    return re.sub(r"(title=\{)(.*?)(\},?\s*$)", repl, text, flags=re.MULTILINE)


def parse_entries(text):
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, flags=re.DOTALL):
        etype, key, body = m.group(1), m.group(2).strip(), m.group(3)
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*\{(.*?)\}\s*,?\s*(?=\n\s*\w+\s*=|\Z)",
                              body, flags=re.DOTALL):
            fields[fm.group(1).lower()] = " ".join(fm.group(2).split())
        entries.append((etype.lower(), key, fields))
    return entries


def fmt_author(raw):
    raw = raw.strip()
    if "," in raw:
        last, first = (x.strip() for x in raw.split(",", 1))
    else:
        parts = raw.split()
        last, first = parts[-1], " ".join(parts[:-1])
        if first:
            warnings.append(f"Author missing comma, guessed order: '{raw}'")
    if last.lower() == "ghaleb":
        return {"name": "Taher A. Ghaleb", "self": True}
    name = f"{first} {last}".strip()
    return {"name": name, "self": False}


def strip_leading_year(s):
    return re.sub(r"^\d{4}\s+", "", s).strip()


def build():
    text = BIB.read_text(encoding="utf-8")
    text = normalize_bib_titles(text)
    BIB.write_text(text, encoding="utf-8", newline="\r\n")

    data = {"journal": [], "conference": [], "patent": []}
    seen_titles = {}

    for etype, key, f in parse_entries(text):
        title = f.get("title", "").strip()
        year = f.get("year", "").strip()
        authors = [fmt_author(a) for a in re.split(r"\s+and\s+", f.get("author", "")) if a.strip()]

        key_title = title.lower()
        if key_title in seen_titles:
            warnings.append(f"Duplicate title: '{title}' ({key} and {seen_titles[key_title]})")
        seen_titles[key_title] = key

        if etype == "article":
            venue = f.get("journal", "").strip()
            if re.search(r"under review|accepted|submitted|to appear", venue, re.I):
                warnings.append(f"Excluded in-progress entry: '{title}' [{key}] ({venue})")
                continue
            venue_text = f"{venue} ({year})" if year else venue
            cat = "journal"
        elif etype == "inproceedings":
            short = f.get("shortvenue", "").strip()
            if short:
                venue_text = short
            else:
                venue = strip_leading_year(f.get("booktitle", "").strip())
                venue_text = venue if (year and year in venue) else f"{venue} ({year})"
                warnings.append(f"No shortvenue, using booktitle: '{title}' [{key}]")
            cat = "conference"
        elif etype == "patent":
            note = f.get("note", "").strip()
            num = re.sub(r"(?i)^us\s+patent\s+", "US ", note)
            venue_text = f"US Patent and Trademark Office ({year}) - Patent No: {num}"
            cat = "patent"
        else:
            warnings.append(f"Unknown entry type @{etype} [{key}]")
            continue

        data[cat].append({
            "title": title, "authors": authors,
            "venue": venue_text, "year": int(year) if year.isdigit() else 0,
        })

    for cat in data:
        data[cat].sort(key=lambda e: e["year"], reverse=True)

    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote {OUT.relative_to(ROOT)}")
    print(f"  journal={len(data['journal'])} conference={len(data['conference'])} patent={len(data['patent'])}")
    if warnings:
        print("\nWARNINGS (review the .bib):")
        for w in dict.fromkeys(warnings):
            print(f"  - {w}")


if __name__ == "__main__":
    build()
