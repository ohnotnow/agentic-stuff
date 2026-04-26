#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = [
#   "markdown>=3.5",
#   "pymdown-extensions>=10.0",
# ]
# ///
"""Convert a markdown plan into a single self-contained HTML file.

Run with uv (no install needed):
    uv run plan_to_html.py PLAN.md

Or with a regular Python that has the deps installed:
    pip install markdown pymdown-extensions
    python plan_to_html.py PLAN.md
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
import sys
from pathlib import Path

import markdown


SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CSS = SCRIPT_DIR.parent / "theme.css"

EXTENSIONS = [
    "extra",          # fenced_code, tables, attr_list, footnotes, def_list, abbr, md_in_html
    "sane_lists",
    "toc",
    "smarty",
    "pymdownx.tasklist",
]
EXTENSION_CONFIGS = {
    "pymdownx.tasklist": {"custom_checkbox": False, "clickable_checkbox": False},
    "toc": {"permalink": False},
}


LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")


def normalise_list_breaks(md_text: str) -> str:
    """Insert a blank line before a list that immediately follows a paragraph.

    Strict markdown requires a blank line before a list; GFM does not. Plans
    are usually written in GFM style, so we forgive the missing blank.
    Stays out of fenced code blocks so we don't disturb examples.
    """
    lines = md_text.splitlines()
    out: list[str] = []
    prev = ""
    in_fence = False
    fence_marker: str | None = None

    for line in lines:
        stripped = line.lstrip()

        if in_fence:
            out.append(line)
            if fence_marker and stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = None
            prev = line
            continue

        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = True
            fence_marker = stripped[:3]
            out.append(line)
            prev = line
            continue

        if LIST_RE.match(line) and prev.strip() and not LIST_RE.match(prev):
            out.append("")
        out.append(line)
        prev = line

    return "\n".join(out)


def split_leading_h1(md_text: str) -> tuple[str | None, str]:
    """Pull off a leading ATX H1 (skipping blank lines) and return (title, rest)."""
    lines = md_text.splitlines()
    i = 0
    while i < len(lines) and lines[i].strip() == "":
        i += 1
    if i < len(lines):
        stripped = lines[i].strip()
        if stripped.startswith("# ") and not stripped.startswith("## "):
            title = stripped[2:].strip()
            rest = "\n".join(lines[i + 1 :])
            return title, rest.lstrip("\n")
    return None, md_text


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-") or "plan"


def render(md_text: str) -> str:
    md = markdown.Markdown(extensions=EXTENSIONS, extension_configs=EXTENSION_CONFIGS)
    return md.convert(md_text)


def build_preamble(preamble_md: str | None) -> str:
    if not preamble_md or not preamble_md.strip():
        return ""
    inner = render(normalise_list_breaks(preamble_md))
    return (
        '<details class="plan-context">\n'
        '<summary><span class="plan-context__label">Background</span></summary>\n'
        f'<div class="plan-context__body">\n{inner}\n</div>\n'
        '</details>\n'
    )


PRINT_EXPAND_SCRIPT = (
    "window.addEventListener('beforeprint',"
    "function(){document.querySelectorAll('details').forEach(function(d){d.open=true;});});"
)


def build_html(*, title: str, body_html: str, css: str, author: str | None, date_str: str, preamble_html: str = "") -> str:
    meta_parts = [f"<span>{html.escape(date_str)}</span>"]
    if author:
        meta_parts.append(f"<span>{html.escape(author)}</span>")
    meta_html = "".join(meta_parts)

    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<style>
{css}
</style>
</head>
<body>
<header class="plan-header">
  <div class="plan-header__inner">
    <h1 class="plan-header__title">{html.escape(title)}</h1>
    <p class="plan-header__meta">{meta_html}</p>
  </div>
</header>
<main class="plan-main">
{preamble_html}{body_html}
</main>
<footer class="plan-footer">
  Generated with plan-to-html · {html.escape(date_str)}
</footer>
<script>{PRINT_EXPAND_SCRIPT}</script>
</body>
</html>
"""


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert a markdown plan into a single self-contained HTML file."
    )
    p.add_argument("input", type=Path, help="Path to the markdown plan file")
    p.add_argument("-o", "--output", type=Path, help="Output HTML path (default: derived from title + date)")
    p.add_argument("-t", "--title", help="Override the document title (default: first H1, then filename)")
    p.add_argument("-a", "--author", help="Optional author shown in the header band")
    p.add_argument("--preamble-file", type=Path, help="Markdown file rendered into a collapsed 'Background' accordion above the plan")
    p.add_argument("--css", type=Path, default=DEFAULT_CSS, help=f"CSS file to inline (default: {DEFAULT_CSS})")
    p.add_argument("--date", help="Override the date string (default: today, formatted '26 April 2026')")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not args.input.is_file():
        print(f"error: input file not found: {args.input}", file=sys.stderr)
        return 1
    if not args.css.is_file():
        print(f"error: css file not found: {args.css}", file=sys.stderr)
        return 1

    md_text = args.input.read_text(encoding="utf-8")
    css = args.css.read_text(encoding="utf-8")

    md_text = normalise_list_breaks(md_text)
    leading_title, body_md = split_leading_h1(md_text)
    fallback_title = args.input.stem.replace("-", " ").replace("_", " ").title()
    title = args.title or leading_title or fallback_title
    date_str = args.date or dt.date.today().strftime("%-d %B %Y")

    body_html = render(body_md)

    preamble_md = ""
    if args.preamble_file:
        if not args.preamble_file.is_file():
            print(f"error: preamble file not found: {args.preamble_file}", file=sys.stderr)
            return 1
        preamble_md = args.preamble_file.read_text(encoding="utf-8")
    preamble_html = build_preamble(preamble_md)

    document = build_html(
        title=title,
        body_html=body_html,
        css=css,
        author=args.author,
        date_str=date_str,
        preamble_html=preamble_html,
    )

    output = args.output
    if output is None:
        slug = slugify(title)
        output = Path(f"{slug}-{dt.date.today().isoformat()}.html")

    output.write_text(document, encoding="utf-8")
    print(f"wrote {output} ({len(document):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
