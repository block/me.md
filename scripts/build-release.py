#!/usr/bin/env python3
"""Build the release files for one tag.

Writes two files to dist/:
  me.md-protocol-X.Y.Z.md  all normative drafts in one file, with links
                           pinned to the tag
  release-notes.md         the CHANGELOG.md section for X.Y.Z, plus links

Usage: python3 scripts/build-release.py vX.Y.Z
"""

import pathlib
import re
import sys

REPO = "https://github.com/block/me.md"
ROOT = pathlib.Path(__file__).resolve().parent.parent
NORMATIVE = ["PROTOCOL.md", "SOVEREIGNTY.md", "HOST.md", "BRIEFING.md"]
MARKER = re.compile(r"^<!-- /?shared:[a-z0-9-]+ -->\n", re.M)
LINK = re.compile(r"\]\(\./([^)\s]+)\)")


def pin_links(text, tag):
    return LINK.sub(lambda m: f"]({REPO}/blob/{tag}/{m.group(1)})", text)


def changelog_section(version):
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(
        rf"^## {re.escape(version)}\b.*?\n(.*?)(?=^## |\Z)", text, re.M | re.S
    )
    if not match:
        sys.exit(f"error: CHANGELOG.md has no section for {version}")
    return match.group(1).strip()


def main():
    if len(sys.argv) != 2 or not re.fullmatch(r"v\d+\.\d+\.\d+", sys.argv[1]):
        sys.exit("usage: build-release.py vX.Y.Z")
    tag = sys.argv[1]
    version = tag[1:]
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)

    combined = dist / f"me.md-protocol-{version}.md"
    parts = [
        f"# me.md protocol {version}\n\n"
        f"All normative drafts at tag `{tag}`, in one file. "
        f"Source: {REPO}/tree/{tag}\n"
    ]
    for name in NORMATIVE:
        body = MARKER.sub("", (ROOT / name).read_text(encoding="utf-8"))
        parts.append(f"<!-- {name} -->\n\n{body.strip()}\n")
    combined.write_text(pin_links("\n---\n\n".join(parts), tag), encoding="utf-8")

    notes = pin_links(changelog_section(version), tag)
    notes += (
        f"\n\n---\n\n"
        f"- Read the protocol at this release: {REPO}/blob/{tag}/PROTOCOL.md\n"
        f"- All normative drafts in one file: `{combined.name}` (attached below)\n"
        f"- Full changelog: {REPO}/blob/{tag}/CHANGELOG.md\n"
    )
    (dist / "release-notes.md").write_text(notes, encoding="utf-8")
    print(f"wrote {combined.relative_to(ROOT)} and dist/release-notes.md")


if __name__ == "__main__":
    main()
