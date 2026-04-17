#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MKDOCS = ROOT / "mkdocs.yml"
DOCS = ROOT / "docs"

def title_from_filename(stem: str) -> str:
    # hek293 -> HEK293, raw-264-7 -> RAW 264.7, a549 -> A549
    s = stem.replace("_", "-").strip()

    # Special-case patterns like raw-264-7 -> RAW 264.7
    m = re.fullmatch(r"raw-?264-?7", s, re.IGNORECASE)
    if m:
        return "RAW 264.7"

    # HEK293 / A549 style: make letters uppercase, keep digits
    if re.fullmatch(r"[a-zA-Z]+\d+([\-\.]\d+)*", s):
        # split letters then rest
        m2 = re.match(r"^([a-zA-Z]+)(.*)$", s)
        return m2.group(1).upper() + m2.group(2).replace("-", ".")
    # default: Title Case with spaces
    return s.replace("-", " ").title()

def collect_cell_lines():
    cl_dir = DOCS / "cell-lines"
    if not cl_dir.exists():
        return []
    pages = sorted([p for p in cl_dir.glob("*.md") if p.is_file()])
    items = []
    for p in pages:
        rel = p.relative_to(DOCS).as_posix()
        items.append((title_from_filename(p.stem), rel))
    return items

def ensure_file(path: Path, content: str):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

def main():
    # Ensure core pages exist (prevents nav missing-file issues)
    ensure_file(DOCS / "index.md",
"""# Cell Line Repository

Static repository of cell line culture/handling notes with references.
""")

    ensure_file(DOCS / "schema.md",
"""# Schema

Define required fields and headings for each cell line page.
""")

    ensure_file(DOCS / "contributing.md",
"""# Contributing

- Cite sources for non-trivial claims.
- Mark unknowns as **Unknown**.
""")

    cell_lines = collect_cell_lines()

    nav_block = []
    nav_block.append("nav:")
    nav_block.append("  - Home: index.md")
    nav_block.append("  - Cell lines:")
    if cell_lines:
        for title, rel in cell_lines:
            nav_block.append(f"      - {title}: {rel}")
    else:
        nav_block.append("      - (none yet): index.md")
    nav_block.append("  - Schema: schema.md")
    nav_block.append("  - Contributing: contributing.md")
    nav_text = "\n".join(nav_block) + "\n"

    mk = MKDOCS.read_text(encoding="utf-8") if MKDOCS.exists() else ""
    if "nav:" in mk:
        # Replace existing nav: block (from 'nav:' to end of file)
        mk = re.sub(r"\nnav:\n(?:.*\n)*\Z", "\n" + nav_text, mk, flags=re.MULTILINE)
        # If the regex didn’t match (nav not at end), do a simpler replace:
        if "nav:" in mk and nav_text not in mk and not mk.strip().endswith("contributing.md"):
            mk = re.sub(r"nav:\n(?:.*\n)*?(?=\n\w|\Z)", nav_text, mk, flags=re.MULTILINE)
    else:
        mk = mk.rstrip() + "\n\n" + nav_text

    MKDOCS.write_text(mk, encoding="utf-8")
    print("mkdocs.yml nav synced with docs/ contents.")

if __name__ == "__main__":
    main()
