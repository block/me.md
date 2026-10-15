#!/usr/bin/env python3
"""Check the protocol documents for drift and broken links.

1. Shared blocks. Text that must be the same in more than one document is
   marked with <!-- shared:NAME --> and <!-- /shared:NAME -->. Every copy of
   a block must be identical.
2. Relative links. Every relative link must point to a file that exists,
   and every #anchor must match a heading in that file.

Run from the repository root: python3 scripts/check-docs.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHARED = re.compile(r"<!-- shared:([a-z0-9-]+) -->\n(.*?)\n<!-- /shared:\1 -->", re.S)
OPEN_MARK = re.compile(r"<!-- /?shared:([a-z0-9-]+) -->")
LINK = re.compile(r"\]\(([^)\s]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.*)$", re.M)
FENCE = re.compile(r"^```.*?^```", re.M | re.S)


def slug(heading):
    text = re.sub(r"[`*_]", "", heading).strip().lower()
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path):
    body = FENCE.sub("", path.read_text(encoding="utf-8"))
    return {slug(h) for h in HEADING.findall(body)}


def main():
    errors = []
    docs = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
    blocks = {}

    for doc in docs:
        rel = doc.relative_to(ROOT)
        text = doc.read_text(encoding="utf-8")

        found = SHARED.findall(text)
        if len(OPEN_MARK.findall(text)) != 2 * len(found):
            errors.append(f"{rel}: unmatched shared-block marker")
        for name, body in found:
            blocks.setdefault(name, []).append((rel, body))

        for target in LINK.findall(FENCE.sub("", text)):
            if re.match(r"^[a-z]+:", target):
                continue
            file_part, _, anchor = target.partition("#")
            dest = (doc.parent / file_part).resolve() if file_part else doc
            if not dest.exists():
                errors.append(f"{rel}: broken link {target}")
            elif anchor and dest.suffix == ".md" and anchor not in anchors(dest):
                errors.append(f"{rel}: missing anchor {target}")

    for name, copies in sorted(blocks.items()):
        first_file, first_body = copies[0]
        for other_file, other_body in copies[1:]:
            if other_body != first_body:
                errors.append(
                    f"shared:{name} differs between {first_file} and {other_file}"
                )

    for error in errors:
        print(f"error: {error}")
    if errors:
        return 1
    print(f"ok: {len(docs)} documents, {len(blocks)} shared blocks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
