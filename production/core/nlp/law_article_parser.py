#!/usr/bin/env python3
from __future__ import annotations
"""
法律条文精确解析器
Legal Article Precise Parser

将法律文档精确拆分为:条-款-项
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ArticleLevel(Enum):
    """条文层级"""

    CHAPTER = "chapter"  # 章
    SECTION = "section"  # 节
    ARTICLE = "article"  # 条
    PARAGRAPH = "paragraph"  # 款
    ITEM = "item"  # 项


@dataclass
class LawArticle:
    """法律条文"""

    id: str  # 如 "26-1-0" 表示第26条第1款
    full_path: str  # 如 "第一章 > 第二十六条 > 第1款"
    level: ArticleLevel
    article_number: str  # 如 "26"
    paragraph_number: int | None  # 如 1, 2, 3
    item_number: str | None  # 如 "(一)", "1"
    title: str  # 如 "第1款" 或 "(一)"
    content: str  # 条文内容
    parent_id: str | None = None  # 父级ID

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "full_path": self.full_path,
            "level": self.level.value,
            "article_number": self.article_number,
            "paragraph_number": self.paragraph_number,
            "item_number": self.item_number,
            "title": self.title,
            "content": self.content,
            "parent_id": self.parent_id,
        }


class LawArticleParser:
    """法律条文精确解析器"""

    # 条号模式:第X条
    ARTICLE_PATTERN = re.compile(r"^([第第][一二三四五六七八九十百零\d]+条)[\s\u3000]*(.*)")

    # 项模式:(一)(二)或 1. 2. 或 (1)(1)
    # 注意:去掉^,因为项可能在段落中间而不是行首
    # 分组说明:group(1)是项号,group(2)是内容
    ITEM_PATTERN_CHINESE = re.compile(r"(([一二三四五六七八九十]+))\s*(.*)")
    ITEM_PATTERN_NUMBER = re.compile(r"(\d+)[.、．]\s*(.*)")
    ITEM_PATTERN_PAREN = re.compile(r"((\d+))\s*(.*)")
    ITEM_PATTERN_EN_PAREN = re.compile(r"\((\d+)\)\s*(.*)")

    # 章节模式
    CHAPTER_PATTERN = re.compile(r"^第[一二三四五六七八九十百零\d]+章\s*(.*)")

    def __init__(self):
        self.articles = []
        self.current_chapter = ""
        self.current_section = ""

    def parse_law_document(self, content: str, document_type: str = "law") -> list[LawArticle]:
        """
        解析法律文档

        Args:
            content: 文档内容
            document_type: 文档类型 (law/rule/guideline)

        Returns:
            条文列表
        """
        self.articles = []
        lines = content.split("\n")

        current_article_num = None
        current_paragraphs = []
        article_start_line = 0

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 检测章节
            if self.CHAPTER_PATTERN.match(line):
                # 保存上一条
                if current_article_num and current_paragraphs:
                    self._process_article(
                        current_article_num, current_paragraphs, article_start_line, document_type
                    )
                    current_paragraphs = []

                match = self.CHAPTER_PATTERN.match(line)
                self.current_chapter = match.group(1)
                self.current_section = ""
                current_article_num = None
                continue

            # 检测条文
            article_match = self.ARTICLE_PATTERN.match(line)
            if article_match:
                # 保存上一条
                if current_article_num and current_paragraphs:
                    self._process_article(
                        current_article_num, current_paragraphs, article_start_line, document_type
                    )
                    current_paragraphs = []

                current_article_num = self._extract_article_number(article_match.group(1))
                article_start_line = i
                current_paragraphs = []
                # 第一款可能紧接在条号后面
                content_after = article_match.group(2).strip()
                if content_after:
                    current_paragraphs.append(content_after)
                continue

            # 累积段落
            if current_article_num:
                current_paragraphs.append(line)

        # 保存最后一条
        if current_article_num and current_paragraphs:
            self._process_article(
                current_article_num, current_paragraphs, article_start_line, document_type
            )

        logger.info(f"📊 解析完成: {len(self.articles)} 个条文单元")
        return self.articles

    def _extract_article_number(self, article_text: str) -> str:
        """提取条号"""
        # "第二十六条" -> "26"
        chinese_nums = {
            "一": "1",
            "二": "2",
            "三": "3",
            "四": "4",
            "五": "5",
            "六": "6",
            "七": "7",
            "八": "8",
            "九": "9",
            "十": "10",
            "十一": "11",
            "十二": "12",
            "十三": "13",
            "十四": "14",
            "十五": "15",
            "十六": "16",
            "十七": "17",
            "十八": "18",
            "十九": "19",
            "二十": "20",
            "二十一": "21",
            "二十二": "22",
            "二十三": "23",
            "二十四": "24",
            "二十五": "25",
            "二十六": "26",
            "二十七": "27",
            "二十八": "28",
            "二十九": "29",
            "三十": "30",
            "三十一": "31",
            "三十二": "32",
            "三十三": "33",
            "三十四": "34",
            "三十五": "35",
            "三十六": "36",
            "三十七": "37",
            "三十八": "38",
            "三十九": "39",
            "四十": "40",
            "四十一": "41",
            "四十二": "42",
            "四十三": "43",
            "四十四": "44",
            "四十五": "45",
            "四十六": "46",
            "四十七": "47",
            "四十八": "48",
            "四十九": "49",
            "五十": "50",
            "五十一": "51",
            "五十二": "52",
            "五十三": "53",
            "五十四": "54",
            "五十五": "55",
            "五十六": "56",
            "五十七": "57",
            "五十八": "58",
            "五十九": "59",
            "六十": "60",
            "六十一": "61",
            "六十二": "62",
            "六十三": "63",
            "六十四": "64",
            "六十五": "65",
            "六十六": "66",
            "六十七": "67",
            "六十八": "68",
            "六十九": "69",
            "七十": "70",
            "七十一": "71",
            "七十二": "72",
            "七十三": "73",
            "七十四": "74",
            "七十五": "75",
        }

        article_clean = article_text.replace("第", "").replace("条", "")

        # 处理中文数字
        for cn, num in chinese_nums.items():
            article_clean = article_clean.replace(cn, num)

        # 提取数字
        match = re.search(r"(\d+)", article_clean)
        if match:
            return match.group(1)

        return article_clean

    def _process_article(
        self, article_number: str, paragraphs: list[str], start_line: int, document_type: str
    ):
        """处理一条法律条文"""
        article_full_path = f"{self.current_chapter} > 第{article_number}条"

        # 如果只有一个段落且不包含项,整条作为一个单元
        if len(paragraphs) == 1 and not self._has_items(paragraphs[0]):
            article = LawArticle(
                id=f"{article_number}-0",
                full_path=article_full_path,
                level=ArticleLevel.ARTICLE,
                article_number=article_number,
                paragraph_number=0,
                item_number=None,
                title=f"第{article_number}条",
                content=paragraphs[0],
                parent_id=None,
            )
            self.articles.append(article)
            return

        # 多个段落,分别处理每个款
        for para_idx, paragraph in enumerate(paragraphs, start=1):
            para_full_path = f"{article_full_path} > 第{para_idx}款"

            # 检查是否包含项
            items = self._extract_items(paragraph)

            if not items:
                # 没有项,整个段落作为一款
                article = LawArticle(
                    id=f"{article_number}-{para_idx}-0",
                    full_path=para_full_path,
                    level=ArticleLevel.PARAGRAPH,
                    article_number=article_number,
                    paragraph_number=para_idx,
                    item_number=None,
                    title=f"第{article_number}条第{para_idx}款",
                    content=paragraph,
                    parent_id=f"{article_number}-0",
                )
                self.articles.append(article)
            else:
                # 有项,拆分每一项
                for item_idx, (item_num, item_content) in enumerate(items):
                    item_full_path = f"{para_full_path} > 第{item_idx + 1}项"
                    item_id = f"{article_number}-{para_idx}-{item_num or item_idx + 1}"

                    article = LawArticle(
                        id=item_id,
                        full_path=item_full_path,
                        level=ArticleLevel.ITEM,
                        article_number=article_number,
                        paragraph_number=para_idx,
                        item_number=item_num,
                        title=f"第{article_number}条第{para_idx}款第{item_idx + 1}项",
                        content=item_content,
                        parent_id=f"{article_number}-{para_idx}-0",
                    )
                    self.articles.append(article)

    def _has_items(self, text: str) -> bool:
        """检查文本是否包含项"""
        return bool(
            self.ITEM_PATTERN_CHINESE.search(text)
            or self.ITEM_PATTERN_NUMBER.search(text)
            or self.ITEM_PATTERN_PAREN.search(text)
            or self.ITEM_PATTERN_EN_PAREN.search(text)
        )

    def _extract_items(self, text: str) -> list[tuple]:
        """
        提取项

        Returns:
            [(item_number, item_content), ...]
        """
        items = []

        # 尝试中文项 - 使用finditer获取完整匹配
        chinese_matches = self.ITEM_PATTERN_CHINESE.finditer(text)
        chinese_items = [(m.group(1), m.group(2)) for m in chinese_matches]
        if chinese_items:
            return chinese_items

        # 尝试数字项
        number_matches = self.ITEM_PATTERN_NUMBER.finditer(text)
        number_items = [(m.group(1), m.group(2)) for m in number_matches]
        if number_items:
            return number_items

        # 尝试括号项
        paren_matches = self.ITEM_PATTERN_PAREN.finditer(text)
        paren_items = [(m.group(1), m.group(2)) for m in paren_matches]
        if paren_items:
            return paren_items

        en_paren_matches = self.ITEM_PATTERN_EN_PAREN.finditer(text)
        en_paren_items = [(m.group(1), m.group(2)) for m in en_paren_matches]
        if en_paren_items:
            return en_paren_items

        return items


def parse_law_file(file_path: str, document_type: str = "law") -> list[LawArticle]:
    """
    解析法律文件

    Args:
        file_path: 文件路径
        document_type: 文档类型

    Returns:
        条文列表
    """
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    parser = LawArticleParser()
    return parser.parse_law_document(content, document_type)


if __name__ == "__main__":
    # 测试
    articles = parse_law_file("/Users/xujian/语料/专利/中华人民共和国专利法_20201017.md")

    print(f"📊 共解析 {len(articles)} 个条文单元")
    print("\n示例条文:")

    for article in articles[:10]:
        print(f"\n[{article.title}]")
        print(f"  ID: {article.id}")
        print(f"  路径: {article.full_path}")
        print(f"  内容: {article.content[:80]}...")
