#!/usr/bin/env python3

"""
Markdown 分块处理器
Chunk Processor for Bao Chen Knowledge Base

移植自 patent_agent/build_index.py，增加 wiki-link 提取和扩展元数据。
将宝宸知识库的 Markdown 文件按 ## 标题分块，提取 [[wiki-links]，
生成带完整元数据的 chunk 数据。
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 不参与分块的文件名
SKIP_FILE_NAMES = {"CLAUDE.md", "log.md", "index.md"}


@dataclass
class BaoChenChunk:
    """宝宸知识库的一个分块"""

    text: str  # 分块文本内容
    source_file: str  # 相对路径，如 "专利实务/创造性/创造性-概述.md"
    kb_category: str  # 7 大分类之一，如 "专利实务"
    kb_subcategory: str  # 子目录，如 "创造性"
    page_title: str  # 页面标题（来自 # 标题）
    section_title: str  # 章节标题（来自 ## 标题，前言为 "摘要"）
    chunk_index: int  # 页面内的块序号
    char_count: int  # 字符数
    wiki_links: list[str] = field(default_factory=list)  # [[link] 提取结果
    source_book: Optional[str] = None  # 来源教材（以案说法/崔国斌/尹新天等）
    source_prefix: Optional[str] = None  # 命名前缀（原理-/法条- 或 None）
    content_hash: str = ""  # 文本 SHA-256 哈希


# wiki-link 正则: [[page-name] 或 [[path/page|显示名]
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]+?)?\]\]")

# 法律条文引用正则: 专利法第X条、实施细则第X条等
LEGAL_ARTICLE_PATTERN = re.compile(
    r"(?:《[^》]*》)?(?:专利法|实施细则|侵权解释|授权确权规定)" r"第[一二三四五六七八九十百千万\d]+条"
)


class ChunkProcessor:
    """Markdown 分块处理器"""

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: 最大分块字符数
            chunk_overlap: 分块重叠字符数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def process_file(self, file_path: Path, wiki_root: Path) -> list[BaoChenChunk]:
        """处理单个 Markdown 文件，返回分块列表"""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"跳过文件 {file_path}: {e}")
            return []

        if not content.strip():
            return []

        # 计算相对路径和分类
        rel_path = str(file_path.relative_to(wiki_root))
        parts = Path(rel_path).parts
        kb_category = parts[0] if len(parts) > 1 else "根目录"
        kb_subcategory = parts[1] if len(parts) > 2 else ""

        # 推断来源教材（根据专利实务的命名前缀）
        source_book, source_prefix = self._infer_source(rel_path, kb_category)

        # 提取页面标题
        page_title = self._extract_page_title(content)

        # 按 ## 标题分块
        sections = self._split_by_sections(content)

        # 生成 chunk
        chunks: list[BaoChenChunk] = []
        chunk_idx = 0

        for section_title, section_text in sections:
            if not section_text.strip():
                continue

            if len(section_text) <= self.chunk_size:
                chunks.append(
                    self._make_chunk(
                        text=section_text.strip(),
                        source_file=rel_path,
                        kb_category=kb_category,
                        kb_subcategory=kb_subcategory,
                        page_title=page_title,
                        section_title=section_title,
                        chunk_index=chunk_idx,
                        source_book=source_book,
                        source_prefix=source_prefix,
                    )
                )
                chunk_idx += 1
            else:
                # 按段落拆分超长章节
                sub_chunks = self._split_by_paragraphs(section_text)
                for sub_text in sub_chunks:
                    if not sub_text.strip():
                        continue
                    chunks.append(
                        self._make_chunk(
                            text=sub_text.strip(),
                            source_file=rel_path,
                            kb_category=kb_category,
                            kb_subcategory=kb_subcategory,
                            page_title=page_title,
                            section_title=section_title,
                            chunk_index=chunk_idx,
                            source_book=source_book,
                            source_prefix=source_prefix,
                        )
                    )
                    chunk_idx += 1

        return chunks

    def collect_files(self, wiki_root: Path) -> list[tuple[Path, str]]:
        """
        收集 Wiki 目录下所有 .md 文件

        Returns:
            [(文件路径, 知识库分类名), ...]
        """
        if not wiki_root.is_dir():
            raise FileNotFoundError(f"Wiki 目录不存在: {wiki_root}")

        files: list[tuple[Path, str]] = []
        for md_file in sorted(wiki_root.rglob("*.md")):
            if md_file.name in SKIP_FILE_NAMES:
                continue
            rel_path = md_file.relative_to(wiki_root)
            kb_name = rel_path.parts[0] if len(rel_path.parts) > 1 else "根目录"
            files.append((md_file, kb_name))

        return files

    def _make_chunk(
        self,
        text: str,
        source_file: str,
        kb_category: str,
        kb_subcategory: str,
        page_title: str,
        section_title: str,
        chunk_index: int,
        source_book: Optional[str],
        source_prefix: Optional[str],
    ) -> BaoChenChunk:
        """构建 BaoChenChunk 实例"""
        wiki_links = list(set(WIKI_LINK_PATTERN.findall(text)))
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

        return BaoChenChunk(
            text=text,
            source_file=source_file,
            kb_category=kb_category,
            kb_subcategory=kb_subcategory,
            page_title=page_title,
            section_title=section_title,
            chunk_index=chunk_index,
            char_count=len(text),
            wiki_links=wiki_links,
            source_book=source_book,
            source_prefix=source_prefix,
            content_hash=f"sha256:{content_hash[:16]}",
        )

    def _extract_page_title(self, content: str) -> str:
        """提取页面标题（第一个 # 标题）"""
        for line in content.split("\n"):
            if line.startswith("# ") and not line.startswith("## "):
                return line.lstrip("# ").strip()
        return ""

    def _split_by_sections(self, content: str) -> list[tuple[str, str]]:
        """按 ## 标题分割为 (章节标题, 章节文本) 列表"""
        lines = content.split("\n")
        sections: list[tuple[str, str]] = []
        current_title = "摘要"
        current_lines: list[str] = []

        for line in lines:
            if line.startswith("## ") and not line.startswith("### "):
                if current_lines:
                    sections.append((current_title, "\n".join(current_lines)))
                current_title = line.lstrip("# ").strip()
                current_lines = [line]
            else:
                current_lines.append(line)

        if current_lines:
            sections.append((current_title, "\n".join(current_lines)))

        return sections

    def _split_by_paragraphs(self, text: str) -> list[str]:
        """将超长文本按段落边界拆分"""
        paragraphs = text.split("\n\n")
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 > self.chunk_size and current:
                chunks.append(current.strip())
                # 重叠：保留最后 chunk_overlap 字符
                if self.chunk_overlap > 0 and len(current) > self.chunk_overlap:
                    current = current[-self.chunk_overlap :] + "\n\n" + para
                else:
                    current = para
            else:
                current = current + "\n\n" + para if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks

    def _infer_source(self, rel_path: str, kb_category: str) -> tuple[Optional[str], Optional[str]]:
        """
        从文件路径推断来源教材

        专利实务板块有三种来源，通过命名前缀区分:
        - 无前缀: 《以案说法》
        - 原理- 前缀: 崔国斌《专利法》
        - 法条- 前缀: 尹新天《中国专利法详解》
        """
        if kb_category != "专利实务":
            # 其他板块的来源标注
            source_map = {
                "审查指南": "审查指南(2023版)",
                "专利侵权": "北高院侵权判定指南",
                "专利判决": "法院判决汇编",
                "复审无效": "复审无效决定汇编",
                "法律法规": "法律法规汇编",
                "书籍": "参考书籍",
            }
            return source_map.get(kb_category), None

        # 专利实务板块：从文件名提取来源
        filename = Path(rel_path).stem
        parts = filename.split("-", 2)

        if len(parts) >= 2:
            prefix = parts[1]
            if prefix == "原理":
                return "崔国斌《专利法》", "原理-"
            elif prefix == "法条":
                return "尹新天《中国专利法详解》", "法条-"

        return "《以案说法》", None

    def extract_legal_articles(self, text: str) -> list[str]:
        """从文本中提取引用的法律条文"""
        matches = LEGAL_ARTICLE_PATTERN.findall(text)
        return list(set(matches))

    def chunk_to_payload(self, chunk: BaoChenChunk, sync_version: int = 1) -> dict[str, Any]:
        """将 chunk 转换为 Qdrant payload 格式"""
        from datetime import datetime

        return {
            "source_file": chunk.source_file,
            "kb_category": chunk.kb_category,
            "kb_subcategory": chunk.kb_subcategory,
            "page_title": chunk.page_title,
            "section_title": chunk.section_title,
            "chunk_index": chunk.chunk_index,
            "chunk_text": chunk.text,
            "char_count": chunk.char_count,
            "wiki_links": chunk.wiki_links,
            "source_book": chunk.source_book,
            "source_prefix": chunk.source_prefix,
            "content_hash": chunk.content_hash,
            "sync_version": sync_version,
            "ingested_at": datetime.now(UTC).isoformat(),
        }

