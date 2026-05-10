"""Parse Stripe doc HTML into structured blocks for chunking."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bs4 import BeautifulSoup, Tag

RAW_DIR = Path("data/raw_html")
PARSED_DIR = Path("data/parsed")

HEADING_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


@dataclass
class Block:
    kind: str  # heading | paragraph | code | list | table
    text: str
    heading_path: list[str]
    level: int | None = None
    language: str | None = None


@dataclass
class ParsedDoc:
    source: str
    title: str
    blocks: list[Block] = field(default_factory=list)


def _table_to_text(table: Tag) -> str:
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows)


def _list_to_text(lst: Tag) -> str:
    items = [
        "- " + li.get_text(" ", strip=True)
        for li in lst.find_all("li", recursive=False)
        if li.get_text(strip=True)
    ]
    return "\n".join(items)


def _walk(node: Tag, heading_path: list[str], blocks: list[Block]) -> None:
    for child in node.children:
        if not isinstance(child, Tag):
            continue
        name = child.name
        if name in HEADING_TAGS:
            text = child.get_text(" ", strip=True)
            if not text:
                continue
            level = int(name[1])
            del heading_path[level - 1:]
            heading_path.append(text)
            blocks.append(Block("heading", text, list(heading_path), level=level))
        elif name == "p":
            text = child.get_text(" ", strip=True)
            if text:
                blocks.append(Block("paragraph", text, list(heading_path)))
        elif name == "pre":
            text = child.get_text()
            if text.strip():
                blocks.append(Block("code", text, list(heading_path)))
        elif name in {"ul", "ol"}:
            text = _list_to_text(child)
            if text:
                blocks.append(Block("list", text, list(heading_path)))
        elif name == "table":
            text = _table_to_text(child)
            if text:
                blocks.append(Block("table", text, list(heading_path)))
        else:
            _walk(child, heading_path, blocks)


def parse_html(html: str, source: str) -> ParsedDoc:
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("article") or soup.body or soup
    title = soup.title.get_text(strip=True) if soup.title else ""
    blocks: list[Block] = []
    _walk(root, [], blocks)
    return ParsedDoc(source=source, title=title, blocks=blocks)


def main() -> None:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    for html_path in sorted(RAW_DIR.glob("*.html")):
        html = html_path.read_text(encoding="utf-8")
        doc = parse_html(html, source=html_path.name)
        out = PARSED_DIR / f"{html_path.stem}.json"
        out.write_text(
            json.dumps(asdict(doc), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        counts: dict[str, int] = {}
        for b in doc.blocks:
            counts[b.kind] = counts.get(b.kind, 0) + 1
        print(f"{html_path.name} -> {out.name} ({len(doc.blocks)} blocks: {counts})")


if __name__ == "__main__":
    main()
