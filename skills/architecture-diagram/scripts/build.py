#!/usr/bin/env python3
"""Build an interactive architecture diagram as one self-contained HTML page.

Usage:
  python3 build.py DATA.json OUT.html       check the data, then build the page
  python3 build.py --check DATA.json        check the data only
  python3 build.py --extract PAGE.html      print the data embedded in a built page

Problems with the data are printed and the build stops (exit 1). Warnings,
such as a crowded view, are printed but do not stop the build.
"""

import json
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL / "assets" / "template.html"
ELK = SKILL / "assets" / "elk.bundled.js"
ELK_LICENCE = SKILL / "assets" / "ELK-LICENSE.md"
ELK_VERSION = "0.11.1"
KINDS = ("person", "process", "store", "external")
CROWDED = 9
DATA_BLOCK = re.compile(
    r'<script type="application/json" id="diagram-data">\s*(.*?)\s*</script>', re.DOTALL
)


def script_safe(text):
    # Stop embedded content from closing the <script> element early.
    return re.sub(r"</(script)", r"<\\/\1", text, flags=re.IGNORECASE)


def elk_with_licence():
    # Every built page passes on a copy of elkjs, so it carries the licence with it.
    notice = (
        f"elkjs {ELK_VERSION}: the Eclipse Layout Kernel (ELK) compiled to JavaScript,\n"
        "used by this page to lay out the diagram. It is licensed under the Eclipse\n"
        "Public License 2.0 (EPL-2.0), reproduced in full below. Source code:\n"
        f"https://github.com/kieler/elkjs, also published on npm as elkjs@{ELK_VERSION}.\n\n"
    )
    text = (notice + ELK_LICENCE.read_text(encoding="utf-8")).replace("*/", "* /")
    body = "\n".join(f" * {line}" if line else " *" for line in text.splitlines())
    return f"/*!\n{body}\n */\n" + ELK.read_text(encoding="utf-8")


def check(data):
    """Return (problems, warnings), mirroring the checks the page itself makes."""
    problems, warnings = [], []
    if not isinstance(data.get("title"), str) or not isinstance(data.get("view"), dict):
        return ["The data needs a \"title\" and a top-level \"view\"."], warnings

    def walk(view, trail, ancestors):
        where = " > ".join(trail)
        nodes = view.get("nodes") or []
        ids = set()
        for node in nodes:
            nid = node.get("id")
            if not nid or not node.get("label"):
                problems.append(f"{where}: a node is missing its id or label.")
                continue
            if nid.startswith("^"):
                problems.append(f"{where}: node id \"{nid}\" may not start with ^.")
            if nid in ids:
                problems.append(f"{where}: duplicate node id \"{nid}\".")
            ids.add(nid)
            if node.get("kind") not in KINDS:
                problems.append(f"{where}: node \"{nid}\" has kind \"{node.get('kind')}\"; expected one of {', '.join(KINDS)}.")
            if "issue" in node and not (isinstance(node["issue"], str) and node["issue"].strip()):
                problems.append(f"{where}: node \"{nid}\" has an empty or non-text issue.")
            if not node.get("description"):
                warnings.append(f"{where}: node \"{nid}\" has no description.")
        for edge in view.get("edges") or []:
            if "label" in edge and not str(edge["label"]).strip():
                warnings.append(f"{where}: the edge from \"{edge.get('from')}\" to \"{edge.get('to')}\" has an empty label; give it one or leave the label out.")
            for end in (edge.get("from"), edge.get("to")):
                if not isinstance(end, str):
                    problems.append(f"{where}: an edge is missing its from or to.")
                elif end.startswith("^"):
                    if not any(end[1:] in level for level in ancestors):
                        problems.append(f"{where}: edge end \"{end}\" matches no node in any enclosing view.")
                elif end not in ids:
                    problems.append(f"{where}: edge end \"{end}\" matches no node in this view.")
        if len(nodes) > CROWDED:
            warnings.append(f"{where}: {len(nodes)} boxes; consider grouping some of them.")
        for node in nodes:
            if isinstance(node.get("view"), dict):
                walk(node["view"], trail + [node.get("label", "?")], [ids] + ancestors)

    walk(data["view"], [data["title"]], [])
    return problems, warnings


def report(problems, warnings):
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    for p in problems:
        print(f"problem: {p}", file=sys.stderr)
    return not problems


def build(data_path, out_path):
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    if not report(*check(data)):
        sys.exit(1)
    template = TEMPLATE.read_text(encoding="utf-8")
    before_data, after_data = template.split("__DIAGRAM_DATA__")
    before_elk, after_elk = after_data.split("/*__ELK__*/")
    html = "".join([
        before_data,
        script_safe(json.dumps(data, indent=2, ensure_ascii=False)),
        before_elk,
        script_safe(elk_with_licence()),
        after_elk,
    ])
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"Wrote {out} ({out.stat().st_size // 1024} KB)")


def extract(page_path):
    match = DATA_BLOCK.search(Path(page_path).read_text(encoding="utf-8"))
    if not match:
        sys.exit(f"No diagram data found in {page_path}.")
    # "<\/" is a valid JSON escape for "</", so the block parses as it stands.
    print(json.dumps(json.loads(match.group(1)), indent=2, ensure_ascii=False))


def main(args):
    if len(args) == 2 and args[0] == "--check":
        data = json.loads(Path(args[1]).read_text(encoding="utf-8"))
        ok = report(*check(data))
        print("Data looks fine." if ok else "Fix the problems above.")
        sys.exit(0 if ok else 1)
    if len(args) == 2 and args[0] == "--extract":
        extract(args[1])
    elif len(args) == 2:
        build(*args)
    else:
        sys.exit(__doc__.strip())


if __name__ == "__main__":
    main(sys.argv[1:])
