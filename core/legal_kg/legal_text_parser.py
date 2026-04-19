#!/usr/bin/env python3
from __future__ import annotations
"""
法律文本解析器 - 精细化解析法律条、款、项
用于法律文档的深度处理和知识图谱构建
"""

import json
import logging
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LawLevel(Enum):
    """法律层级"""
    ARTICLE = "article"      # 条
    PARAGRAPH = "paragraph"  # 款
    ITEM = "item"           # 项
    SUBITEM = "subitem"     # 目(子项)


class LawImportance(Enum):
    """法律重要程度"""
    HIGH = "high"           # 高:民法典等基本法律
    MEDIUM = "medium"       # 中:重要法律
    NORMAL = "normal"       # 普通:地方法规等


@dataclass
class LawArticle:
    """法律条"""
    id: str
    article_number: int
    title: str
    content: str
    law_id: str
    level: LawLevel
    parent_id: str | None = None
    order: int = 0


@dataclass
class LawParagraph:
    """法律款"""
    id: str
    article_id: str
    paragraph_number: int
    content: str
    order: int


@dataclass
class LawItem:
    """法律项"""
    id: str
    parent_id: str  # 可以是article_id或paragraph_id
    item_number: str  # (1), (2) 等
    content: str
    order: int


class LegalTextParser:
    """法律文本解析器"""

    # 重要法律列表(需要精细化处理)
    IMPORTANT_LAWS = [
        "民法典",
        "宪法",
        "刑法",
        "刑事诉讼法",
        "民事诉讼法",
        "行政诉讼法",
        "合同法",
        "物权法",
        "侵权责任法",
        "公司法",
        "专利法",
        "商标法",
        "著作权法",
    ]

    # 正则表达式模式
    PATTERNS = {
        # 条:第X条(支持全角空格和普通空格)
        'article': re.compile(r'^第([一二三四五六七八九十百千\d]+)[条章]\s*(.*)$', re.MULTILINE),

        # 款:通常是一段独立的文字,没有编号,紧跟在条后面
        # 款的识别需要在上下文中判断

        # 项:(1)、(2)、(3) 或 一、二、三、
        'item_arabic': re.compile(r'^(\([一二三四五六七八九十\d]+\))\s*(.*)$', re.MULTILINE),
        'item_chinese': re.compile(r'^([一二三四五六七八九十]+)[、,．\.]\s*(.*)$', re.MULTILINE),

        # 目:1. 2. 3. 或 (1) (2)
        'subitem': re.compile(r'^(\d+)[、．\.]\s*(.*)$', re.MULTILINE),
    }

    def __init__(self):
        self.articles = []
        self.paragraphs = []
        self.items = []

    def determine_importance(self, title: str) -> LawImportance:
        """判断法律重要程度"""
        for important_law in self.IMPORTANT_LAWS:
            if important_law in title:
                return LawImportance.HIGH

        # 中等重要法律
        medium_keywords = ["法", "解释"]
        if any(kw in title for kw in medium_keywords):
            return LawImportance.MEDIUM

        # 普通:地方性法规、规章等
        return LawImportance.NORMAL

    def parse_law_text(self, content: str, law_id: str, title: str) -> dict:
        """解析法律文本"""
        importance = self.determine_importance(title)

        # 根据重要程度决定解析深度
        if importance == LawImportance.HIGH:
            return self._parse_high_quality(content, law_id, title)
        elif importance == LawImportance.MEDIUM:
            return self._parse_medium_quality(content, law_id, title)
        else:
            return self._parse_normal_quality(content, law_id, title)

    def _parse_high_quality(self, content: str, law_id: str, title: str) -> dict:
        """
        高质量解析:拆分到条、款、项
        用于民法典等重要法律
        """
        result = {
            'law_id': law_id,
            'title': title,
            'importance': 'high',
            'articles': [],
            'paragraphs': [],
            'items': []
        }

        lines = content.split('\n')
        current_article = None
        article_order = 0

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # 检测是否是条
            article_match = self.PATTERNS['article'].match(line)
            if article_match:
                article_num = self._chinese_to_int(article_match.group(1))
                article_title = article_match.group(2).strip()
                article_order += 1

                article_id = f"{law_id}_article_{article_num}"
                current_article = {
                    'id': article_id,
                    'article_number': article_num,
                    'title': article_title if article_title else f"第{article_num}条",
                    'content': '',
                    'order': article_order
                }

                # 收集整条的内容
                content_lines = [line]
                i += 1

                # 收集属于该条的所有内容(直到下一条或文件结束)
                while i < len(lines):
                    next_line = lines[i].strip()

                    # 检查是否是新的一条
                    if self.PATTERNS['article'].match(next_line):
                        break

                    content_lines.append(next_line)
                    i += 1

                # 合并内容
                full_content = '\n'.join(content_lines)
                current_article['content'] = full_content

                # 解析款和项
                paragraphs, items = self._parse_paragraphs_and_items(
                    full_content, article_id, law_id
                )

                current_article['paragraphs'] = paragraphs
                result['articles'].append(current_article)
                result['paragraphs'].extend(paragraphs)
                result['items'].extend(items)

            else:
                i += 1

        return result

    def _parse_medium_quality(self, content: str, law_id: str, title: str) -> dict:
        """
        中等质量解析:拆分到条和主要项
        用于普通法律
        """
        result = {
            'law_id': law_id,
            'title': title,
            'importance': 'medium',
            'articles': [],
            'items': []
        }

        # 按条分割
        article_splits = self.PATTERNS['article'].split(content)

        article_order = 0
        for i in range(1, len(article_splits), 2):
            if i + 1 >= len(article_splits):
                break

            article_num_str = article_splits[i]
            article_content = article_splits[i + 1]

            try:
                article_num = self._chinese_to_int(article_num_str)
                article_order += 1

                article = {
                    'id': f"{law_id}_article_{article_num}",
                    'article_number': article_num,
                    'title': f"第{article_num_str}条",
                    'content': article_content.strip(),
                    'order': article_order
                }

                result['articles'].append(article)

            except (ValueError, KeyError, AttributeError) as e:
                # 解析失败时跳过该条目
                logger.debug(f"文章解析跳过: {e}")
                continue

        return result

    def _parse_normal_quality(self, content: str, law_id: str, title: str) -> dict:
        """
        普通解析:按段落分割
        用于地方法规等
        """
        # 简单按段落分割
        paragraphs = []
        for i, para in enumerate(content.split('\n\n')):
            if para.strip():
                paragraphs.append({
                    'id': f"{law_id}_para_{i}",
                    'content': para.strip(),
                    'order': i
                })

        return {
            'law_id': law_id,
            'title': title,
            'importance': 'normal',
            'paragraphs': paragraphs
        }

    def _parse_paragraphs_and_items(self, content: str, article_id: str, law_id: str) -> tuple[list, list]:
        """解析款和项"""
        paragraphs = []
        items = []

        # 按行分割
        lines = content.split('\n')
        current_paragraph = []
        current_paragraph_num = 0
        item_order = 0

        for line in lines:
            line = line.strip()

            # 检测项:(1) 或 一、
            item_match = self.PATTERNS['item_arabic'].match(line)
            if not item_match:
                item_match = self.PATTERNS['item_chinese'].match(line)

            if item_match:
                # 保存当前段落
                if current_paragraph:
                    para_text = '\n'.join(current_paragraph).strip()
                    if para_text:
                        current_paragraph_num += 1
                        para_id = f"{article_id}_para_{current_paragraph_num}"
                        paragraphs.append({
                            'id': para_id,
                            'article_id': article_id,
                            'paragraph_number': current_paragraph_num,
                            'content': para_text,
                            'order': current_paragraph_num
                        })
                    current_paragraph = []

                # 添加项
                item_order += 1
                item_id = f"{article_id}_item_{item_order}"
                items.append({
                    'id': item_id,
                    'parent_id': article_id,
                    'item_number': item_match.group(1),
                    'content': item_match.group(2).strip(),
                    'order': item_order
                })
            else:
                if line:
                    current_paragraph.append(line)

        # 保存最后一个段落
        if current_paragraph:
            para_text = '\n'.join(current_paragraph).strip()
            if para_text:
                current_paragraph_num += 1
                para_id = f"{article_id}_para_{current_paragraph_num}"
                paragraphs.append({
                    'id': para_id,
                    'article_id': article_id,
                    'paragraph_number': current_paragraph_num,
                    'content': para_text,
                    'order': current_paragraph_num
                })

        return paragraphs, items

    def _chinese_to_int(self, chinese_num: str) -> int:
        """将中文数字转换为阿拉伯数字"""
        # 如果是阿拉伯数字,直接返回
        if chinese_num.isdigit():
            return int(chinese_num)

        # 中文数字映射
        chinese_map = {
            '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
            '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
            '百': 100, '千': 1000
        }

        result = 0
        temp = 0
        for char in chinese_num:
            if char in chinese_map:
                val = chinese_map[char]
                if val >= 10:
                    if temp == 0:
                        temp = 1
                    result += temp * val
                    temp = 0
                else:
                    temp = val

        result += temp
        return result


# 使用示例
if __name__ == '__main__':
    parser = LegalTextParser()

    # 示例:解析一段法律文本
    sample_text = """
    第一条  为了保护民事主体的合法权益,调整民事关系,维护社会和经济秩序,
    适应中国特色社会主义发展要求,弘扬社会主义核心价值观,根据宪法,制定本法。

    第二条  民事主体从事民事活动,应当遵循自愿原则,按照自己的意思设立、变更、终止民事法律关系。
    (1) 自愿原则是指民事主体有权根据自己的意愿设立、变更、终止民事法律关系。
    (2) 民事主体的意思表示应当真实。
    """

    result = parser.parse_law_text(
        content=sample_text,
        law_id="test_law",
        title="中华人民共和国民法典"
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))
