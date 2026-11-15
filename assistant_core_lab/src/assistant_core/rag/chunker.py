"""Split Markdown knowledge documents into chunks with source metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    """A numbered knowledge-base section and its provenance."""

    id: str
    doc_id: str
    title: str
    text: str
    version: str
    owner: str


def _front_matter(raw: str) -> tuple[dict[str, str], str]:
    match = re.match(r"^---\n(.*?)\n---\n", raw, flags=re.S)
    if not match:
        return {}, raw

    metadata = dict(line.split(":", 1) for line in match.group(1).splitlines() if ":" in line)
    return {key.strip(): value.strip() for key, value in metadata.items()}, raw[match.end() :]


def chunk_markdown(path: Path) -> list[Chunk]:
    """Create one chunk per level-one numbered section in a Markdown file."""
    metadata, body = _front_matter(path.read_text(encoding="utf-8"))
    doc_id = metadata.get("doc_id", path.stem)
    chunks: list[Chunk] = []

    for part in re.split(r"^# ", body, flags=re.M)[1:]:
        heading, _, text = part.partition("\n")
        number = heading.split()[0]
        chunks.append(
            Chunk(
                id=f"{doc_id}#{number}",
                doc_id=doc_id,
                title=heading.strip(),
                text=" ".join(text.split()),
                version=metadata.get("version", "?"),
                owner=metadata.get("owner", "?"),
            )
        )

    return chunks


def load_folder(folder: Path) -> list[Chunk]:
    """Load all Markdown files in filename order."""
    return [chunk for path in sorted(folder.glob("*.md")) for chunk in chunk_markdown(path)]
