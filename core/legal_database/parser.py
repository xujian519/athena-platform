#!/usr/bin/env python3
from __future__ import annotations
"""
法律文本解析器
Legal Text Parser

按照 ChatGLM 专家建议的"层次化递归切分 + 结构优先"策略
- 优先单元:款(一款一块)
- 例外:定义性条文、列举性条款保持整条
- 每个chunk带上 norm_id、article_id、clause_id 和层级信息
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ParsedArticle:
    """解析后的条款"""

    norm_id: str
    article_number: str  # 如"第12条"
    chapter_name: Optional[str] = None
    section_name: Optional[str] = None

    # 条款内容
    clauses: list[dict[str, Any]] = field(default_factory=list)  # 款列表
    items: list[dict[str, Any]] = field(default_factory=list)  # 项列表

    # 原始文本
    original_text: str = ""

    # 层级路径
    hierarchy_path: str = ""  # 如"第一章/第二节/第十二条"


@dataclass
class ParsedNorm:
    """解析后的法规"""

    id: str
    name: str
    file_path: str

    # 元数据
    document_number: Optional[str] = None
    issuing_authority: Optional[str] = None
    issue_date: Optional[str] = None
    effective_date: Optional[str] = None
    status: str = "现行有效"
    hierarchy: Optional[str] = None
    category: Optional[str] = None

    # 结构化内容
    chapters: dict[str, list[ParsedArticle]] = field(default_factory=dict)

    # 全文
    full_text: str = ""

    # 统计信息
    total_articles: int = 0
    total_clauses: int = 0


class LegalTextParser:
    """法律文本解析器"""

    # 标题层级模式
    TITLE_PATTERNS = {
        "book": r"^第[零一二三四五六七八九十百]+编\s+(.+)$",  # 第X编
        "chapter": r"^第[零一二三四五六七八九十百]+章\s+(.+)$",  # 第X章
        "section": r"^第[零一二三四五六七八九十百]+节\s+(.+)$",  # 第X节
    }

    # 条款模式
    ARTICLE_PATTERNS = [
        r"^第([一二三四五六七八九十百千万零\d]+)条\s*",  # 第XX条
        r"^Article\s+(\d+)",  # Article XX (英文)
    ]

    # 款项模式(自然段分割)
    CLAUSE_INDICATORS = [
        r"^([一二三四五六七八九十]+)",  # (一)(二)...
        r"^\d+\.",  # 1. 2. 3.....
        r"^[①②③④⑤⑥⑦⑧⑨⑩]",  # 圈码数字
    ]

    # 日期模式
    DATE_PATTERNS = [
        r"(\d{4})年(\d{1,2})月(\d{1,2})日",
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
    ]

    # 文号模式
    DOCUMENT_NUMBER_PATTERNS = [
        r"([^、。;;\s]{2,20}〔?\d{4}〕?[^、。;;\s]{0,10}号)",  # 国法〔2023〕X号
        r"([^、。;;\s]{2,30}令第[^、。;;\s]{1,10}号)",  # XX令第X号
    ]

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化解析器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.stats = {
            "parsed_files": 0,
            "total_articles": 0,
            "total_clauses": 0,
            "failed_files": 0,
        }

    def parse_file(self, file_path: Path, category: Optional[str] = None) -> ParsedNorm | None:
        """
        解析法律文件

        Args:
            file_path: 文件路径
            category: 类别

        Returns:
            解析后的法规对象
        """
        try:
            # 读取文件
            content = file_path.read_text(encoding="utf-8")

            # 提取元数据
            norm_id = file_path.stem
            norm_name = self._extract_title(content, file_path.name)

            # 提取日期和文号
            metadata = self._extract_metadata(content)

            # 解析结构
            parsed_norm = ParsedNorm(
                id=norm_id, name=norm_name, file_path=str(file_path), category=category, **metadata
            )

            # 解析条款
            articles = self._parse_articles(content, norm_id)
            parsed_norm.chapters = articles
            parsed_norm.total_articles = sum(
                len(chapter_articles) for chapter_articles in articles.values()
            )
            parsed_norm.total_clauses = sum(
                len(article.clauses)
                for chapter_articles in articles.values()
                for article in chapter_articles
            )
            parsed_norm.full_text = content

            self.stats["parsed_files"] += 1
            self.stats["total_articles"] += parsed_norm.total_articles
            self.stats["total_clauses"] += parsed_norm.total_clauses

            logger.info(f"✅ 解析成功: {norm_name} ({parsed_norm.total_articles}条)")
            return parsed_norm

        except Exception as e:
            logger.error(f"❌ 解析失败 {file_path.name}: {e}")
            self.stats["failed_files"] += 1
            return None

    def _extract_title(self, content: str, filename: str) -> str:
        """提取标题"""
        # 第一行通常是标题(去除#标记)
        lines = content.split("\n")
        for line in lines[:10]:
            line = line.strip()
            if line and not line.startswith("<!--"):
                # 移除Markdown标记
                title = re.sub(r"^#+\s*", "", line)
                if title and len(title) > 2 and len(title) < 100:
                    return title

        # 从文件名提取
        return filename.replace(".md", "")

    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """提取元数据"""
        metadata = {
            "document_number": None,
            "issuing_authority": None,
            "issue_date": None,
            "effective_date": None,
            "status": "现行有效",
            "hierarchy": None,
        }

        lines = content.split("\n")[:50]  # 只检查前50行

        for line in lines:
            line = line.strip()

            # 提取文号
            if not metadata["document_number"]:
                for pattern in self.DOCUMENT_NUMBER_PATTERNS:
                    match = re.search(pattern, line)
                    if match:
                        metadata["document_number"] = match.group(1)
                        break

            # 提取日期
            dates_found = []
            for pattern in self.DATE_PATTERNS:
                matches = re.findall(pattern, line)
                dates_found.extend(matches)

            if dates_found:
                # 第一个日期通常是发布日期,第二个是施行日期
                for i, date_tuple in enumerate(dates_found[:2]):
                    year, month, day = date_tuple
                    date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    if i == 0 and not metadata["issue_date"]:
                        metadata["issue_date"] = date_str
                    elif (i == 1 and not metadata["effective_date"]) or not metadata["effective_date"]:
                        metadata["effective_date"] = date_str

            # 提取发布机关
            if "发布" in line or "通过" in line:
                # 尝试提取机关名称
                if "全国人民代表大会" in line:
                    metadata["issuing_authority"] = "全国人民代表大会"
                elif "全国人民代表大会常务委员会" in line:
                    metadata["issuing_authority"] = "全国人民代表大会常务委员会"
                elif "国务院" in line:
                    metadata["issuing_authority"] = "国务院"

        # 判断层级
        if metadata["issuing_authority"]:
            if "全国人民代表大会" in metadata["issuing_authority"]:
                metadata["hierarchy"] = "法律"
            elif "国务院" in metadata["issuing_authority"]:
                metadata["hierarchy"] = "行政法规"

        return metadata

    def _parse_articles(self, content: str, norm_id: str) -> dict[str, list[ParsedArticle]]:
        """
        解析条款

        按照层次化递归切分 + 结构优先策略
        """
        # 保留<!-- INFO END -->后面的内容(正文),移除前面的元数据
        if "<!-- INFO END -->" in content:
            content = content.split("<!-- INFO END -->")[1]

        # 按行分割
        lines = content.split("\n")

        articles = {}
        current_chapter = "总则"
        current_section = None
        current_article = None
        article_number = 0

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查标题层级
            chapter_match = re.match(self.TITLE_PATTERNS["chapter"], line)
            if chapter_match:
                current_chapter = chapter_match.group(1)
                current_section = None
                continue

            section_match = re.match(self.TITLE_PATTERNS["section"], line)
            if section_match:
                current_section = section_match.group(1)
                continue

            # 检查条款
            article_match = None
            for pattern in self.ARTICLE_PATTERNS:
                match = re.match(pattern, line)
                if match:
                    article_match = match
                    break

            if article_match:
                # 保存上一条
                if current_article:
                    if current_chapter not in articles:
                        articles[current_chapter] = []
                    articles[current_chapter].append(current_article)

                # 创建新条款
                article_number += 1
                article_num = article_match.group(1)
                article_num_cn = (
                    self._to_chinese_number(article_num) if article_num.isdigit() else article_num
                )

                current_article = ParsedArticle(
                    norm_id=norm_id,
                    article_number=f"第{article_num_cn}条",
                    chapter_name=current_chapter,
                    section_name=current_section,
                    original_text=line,
                    hierarchy_path=(
                        f"{current_chapter}/{current_section}/第{article_num_cn}条"
                        if current_section
                        else f"{current_chapter}/第{article_num_cn}条"
                    ),
                )
                current_article.clauses = [{"text": line[len(article_match.group(0)) :].strip()}]

            elif current_article:
                # 检查是否是款(自然段)
                is_clause = False
                for pattern in self.CLAUSE_INDICATORS:
                    if re.match(pattern, line):
                        # 检查这一段是否属于当前条款
                        if line[0] in "((①②③④⑤":
                            # 新的一款
                            current_article.clauses.append({"text": line})
                        else:
                            # 可能是同一款的延续
                            if current_article.clauses:
                                current_article.clauses[-1]["text"] += " " + line
                        is_clause = True
                        break

                if not is_clause:
                    # 普通文本,添加到当前款或创建新款
                    if current_article.clauses and len(line) > 10:
                        # 检查是否是新的一段(不是句子的延续)
                        last_text = current_article.clauses[-1]["text"]
                        if last_text.endswith(("。", "!", "?", ";", ":", ":")):
                            # 新的一段
                            current_article.clauses.append({"text": line})
                        else:
                            # 延续上一段
                            current_article.clauses[-1]["text"] += " " + line
                    elif len(line) > 10:
                        current_article.clauses.append({"text": line})

                current_article.original_text += "\n" + line

        # 保存最后一条
        if current_article:
            if current_chapter not in articles:
                articles[current_chapter] = []
            articles[current_chapter].append(current_article)

        return articles

    def _to_chinese_number(self, num_str: str) -> str:
        """转中文数字"""
        num_map = {
            "0": "零",
            "1": "一",
            "2": "二",
            "3": "三",
            "4": "四",
            "5": "五",
            "6": "六",
            "7": "七",
            "8": "八",
            "9": "九",
            "10": "十",
            "100": "百",
            "1000": "千",
        }

        # 简单映射(只处理常见数字)
        if num_str in num_map:
            return num_map[num_str]

        # 对于更复杂的数字,返回原样
        return num_str

    def create_embedding_text(
        self, norm: ParsedNorm, article: ParsedArticle, clause_idx: int, clause_text: str
    ) -> str:
        """
        创建用于向量化的增强文本

        Args:
            norm: 法规对象
            article: 条款对象
            clause_idx: 款索引
            clause_text: 款文本

        Returns:
            增强的向量化文本
        """
        parts = [
            f"法规:{norm.name}",
            f"条款:{article.article_number}",
        ]

        # 添加层级信息
        if article.chapter_name:
            parts.append(f"章节:{article.chapter_name}")
        if article.section_name:
            parts.append(f"节:{article.section_name}")

        # 添加元数据
        if norm.document_number:
            parts.append(f"文号:{norm.document_number}")
        if norm.issuing_authority:
            parts.append(f"发布机关:{norm.issuing_authority}")

        # 添加条款内容(核心)
        parts.append(f"内容:{clause_text}")

        return " ".join(parts)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "parsed_files": self.stats["parsed_files"],
            "failed_files": self.stats["failed_files"],
            "total_articles": self.stats["total_articles"],
            "total_clauses": self.stats["total_clauses"],
            "success_rate": (
                self.stats["parsed_files"]
                / (self.stats["parsed_files"] + self.stats["failed_files"])
                if (self.stats["parsed_files"] + self.stats["failed_files"]) > 0
                else 0
            ),
        }

    def print_stats(self) -> Any:
        """打印统计信息"""
        stats = self.get_stats()
        logger.info("\n" + "=" * 60)
        logger.info("📊 法律文本解析统计")
        logger.info("=" * 60)
        logger.info(f"✅ 成功解析: {stats['parsed_files']}个文件")
        logger.info(f"❌ 解析失败: {stats['failed_files']}个文件")
        logger.info(f"📈 成功率: {stats['success_rate']*100:.1f}%")
        logger.info(f"📄 总条款数: {stats['total_articles']}条")
        logger.info(f"📝 总段落数: {stats['total_clauses']}段")
        logger.info("=" * 60 + "\n")
