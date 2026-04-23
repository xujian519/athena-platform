
"""
Obsidian Wiki 索引与变更感知。
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import WikiConfig
from .models import RetrievalEvidence, SourceType


HEADING_PATTERN = re.compile(r"^(#+)\s+(.*)$", re.MULTILINE)
TAG_PATTERN = re.compile(r"[#＃]([A-Za-z0-9_\-\u4e00-\u9fff]+)")


@dataclass
class WikiDocument:
    path: str
    title: str
    content: str
    modified_ts: float
    version_hash: str
    headings: list[str]
    tags: list[str]


class ObsidianWikiIndexer:
    """对本地 Obsidian wiki 做轻量索引。"""

    def __init__(self, config: WikiConfig):
        self.config = config
        self.root = Path(config.root_path)

    def scan(self) -> list[WikiDocument]:
        if not self.root.exists():
            return []

        documents: list[WikiDocument] = []
        for path in self._iter_markdown_files():
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            stat = path.stat()
            title = self._title_for(path, text)
            version_hash = self._hash_text(path.as_posix(), stat.st_mtime, text)
            headings = [match.group(2).strip() for match in HEADING_PATTERN.finditer(text)]
            tags = TAG_PATTERN.findall(text)
            documents.append(
                WikiDocument(
                    path=str(path),
                    title=title,
                    content=text,
                    modified_ts=stat.st_mtime,
                    version_hash=version_hash,
                    headings=headings[:20],
                    tags=tags[:20],
                )
            )
        return documents

    def compute_revision(self, documents: Iterable[WikiDocument]) -> str:
        digest = hashlib.sha256()
        for document in sorted(documents, key=lambda item: item.path):
            digest.update(document.path.encode("utf-8"))
            digest.update(document.version_hash.encode("utf-8"))
        return digest.hexdigest()[:16]

    def search(self, query: str, limit: int = 5) -> list[RetrievalEvidence]:
        query_terms = [term for term in re.split(r"\s+", query.strip()) if term]
        if not query_terms:
            return []

        scored: list[tuple[float, WikiDocument, str]] = []
        for doc in self.scan():
            score = 0.0
            for term in query_terms:
                occurrences = doc.content.lower().count(term.lower())
                score += occurrences * 1.5
                if term.lower() in doc.title.lower():
                    score += 4.0
                if any(term.lower() in heading.lower() for heading in doc.headings):
                    score += 2.0
            if score <= 0:
                continue
            snippet = self._extract_snippet(doc.content, query_terms)
            scored.append((score, doc, snippet))

        scored.sort(key=lambda item: item[0], reverse=True)
        evidence: list[RetrievalEvidence] = []
        for score, doc, snippet in scored[:limit]:
            evidence.append(
                RetrievalEvidence(
                    source_type=SourceType.WIKI,
                    source_id=doc.path,
                    title=doc.title,
                    content=snippet,
                    score=score,
                    metadata={
                        "version_hash": doc.version_hash,
                        "modified_ts": doc.modified_ts,
                        "headings": doc.headings[:5],
                        "tags": doc.tags[:5],
                    },
                )
            )
        return evidence

    def _iter_markdown_files(self) -> Iterable[Path]:
        for ext in self.config.include_extensions:
            for path in self.root.rglob(f"*{ext}"):
                if not path.is_file():
                    continue
                try:
                    if path.stat().st_size > self.config.max_file_size_bytes:
                        continue
                except OSError:
                    continue
                yield path

    @staticmethod
    def _title_for(path: Path, text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return path.stem

    def _extract_snippet(self, content: str, query_terms: list[str]) -> str:
        lowered = content.lower()
        best_index = -1
        for term in query_terms:
            idx = lowered.find(term.lower())
            if idx != -1:
                best_index = idx
                break
        if best_index == -1:
            return content[: self.config.snippet_char_limit]
        start = max(0, best_index - 180)
        end = min(len(content), start + self.config.snippet_char_limit)
        return content[start:end].strip()

    @staticmethod
    def _hash_text(path: str, modified_ts: float, text: str) -> str:
        digest = hashlib.sha256()
        digest.update(path.encode("utf-8"))
        digest.update(str(modified_ts).encode("utf-8"))
        digest.update(text[:4000].encode("utf-8"))
        return digest.hexdigest()[:16]
