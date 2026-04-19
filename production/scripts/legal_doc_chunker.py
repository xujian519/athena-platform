#!/usr/bin/env python3
"""
法律文档条款分块器
作者: 小诺·双鱼公主 v4.0.0
日期: 2025-12-28

功能:
1. 解析DOCX法律文档
2. 条款级别智能分块
3. 结构化数据提取
4. 向量化准备
"""

from __future__ import annotations
import json
import logging
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class LegalArticle:
    """法律条款数据结构"""
    law_id: str                    # 条款唯一标识
    law_name: str                  # 法律名称
    article_number: str            # 条号
    paragraph_number: str | None  # 款号（可选）
    content: str                   # 条款内容
    chapter: str | None         # 所属章
    section: str | None         # 所属节
    level: str                     # 效力层级（法律/行政法规/部门规章/司法解释）
    effective_date: str            # 生效日期
    source_file: str               # 来源文件
    metadata: dict[str, Any]       # 额外元数据

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    def to_payload(self) -> dict:
        """转换为Qdrant payload格式"""
        return {
            "law_id": self.law_id,
            "law_name": self.law_name,
            "article_number": self.article_number,
            "paragraph_number": self.paragraph_number,
            "content": self.content,
            "chapter": self.chapter,
            "section": self.section,
            "level": self.level,
            "effective_date": self.effective_date,
            "source_file": self.source_file,
            **self.metadata
        }


class LegalDocParser:
    """法律文档解析器"""

    # 条款正则模式
    ARTICLE_PATTERNS = [
        r'^第[一二三四五六七八九十百千万]+[条条款]',  # 中文数字
        r'^第\d+[条条款]',                           # 阿拉伯数字
        r'^附\s*则',                                  # 附则
    ]

    # 章节正则模式
    CHAPTER_PATTERN = r'^第[一二三四五六七八九十百千万]+[章节篇]'
    SECTION_PATTERN = r'^第[一二三四五六七八九十百千万]+[章节篇]'

    def __init__(self):
        self.current_law_name = ""
        self.current_chapter = ""
        self.current_section = ""
        self.articles = []

    def parse_file(self, file_path: str) -> list[LegalArticle]:
        """解析单个法律文件"""
        logger.info(f"📄 开始解析: {os.path.basename(file_path)}")

        try:
            doc = Document(file_path)
            self.articles = []

            # 提取文件元信息
            file_name = os.path.basename(file_path)
            law_name, level, effective_date = self._extract_file_metadata(file_name)

            self.current_law_name = law_name

            # 解析段落
            current_article = None
            current_content = []

            for para in doc.paragraphs:
                text = para.text.strip()
                if not text:
                    continue

                # 检测章节
                if self._is_chapter(text):
                    self.current_chapter = text
                    logger.debug(f"📑 章节: {text}")
                    continue

                # 检测条款
                if self._is_article(text):
                    # 保存上一条
                    if current_article:
                        current_article['content'] = '\n'.join(current_content).strip()
                        if current_article['content']:
                            self.articles.append(self._create_article(
                                current_article, file_path, level, effective_date
                            ))

                    # 开始新条款
                    current_article = {
                        'article_number': text,
                        'content_paragraphs': []
                    }
                    current_content = []

                    # 检查是否有款
                    if '\n' in text:
                        parts = text.split('\n', 1)
                        current_article['article_number'] = parts[0]
                        current_content.append(parts[1] if len(parts) > 1 else '')

                elif current_article:
                    # 累积条款内容
                    current_content.append(text)

            # 保存最后一条
            if current_article:
                current_article['content'] = '\n'.join(current_content).strip()
                if current_article['content']:
                    self.articles.append(self._create_article(
                        current_article, file_path, level, effective_date
                    ))

            logger.info(f"✅ 解析完成: 提取 {len(self.articles)} 个条款")
            return self.articles

        except Exception as e:
            logger.error(f"❌ 解析失败 {file_path}: {e}")
            return []

    def _extract_file_metadata(self, file_name: str) -> tuple:
        """从文件名提取元信息"""
        # 提取生效日期
        date_match = re.search(r'(\d{8})', file_name)
        effective_date = date_match.group(1) if date_match else "未知"
        if effective_date != "未知":
            effective_date = f"{effective_date[:4]}-{effective_date[4:6]}-{effective_date[6:8]}"

        # 确定效力层级
        if "专利法" in file_name and "实施细则" not in file_name:
            level = "法律"
        elif "实施细则" in file_name:
            level = "行政法规"
        elif "条例" in file_name:
            level = "行政法规"
        elif "最高法院" in file_name or "最高人民法院" in file_name:
            level = "司法解释"
        elif "审查指南" in file_name:
            level = "部门规章"
        else:
            level = "未知"

        # 提取法律名称
        name = file_name.replace('_', ' ').replace('.docx', '')
        name = re.sub(r'\s+\d{8}', '', name)  # 移除日期
        law_name = name.strip()

        return law_name, level, effective_date

    def _is_chapter(self, text: str) -> bool:
        """判断是否为章节"""
        return bool(re.match(self.CHAPTER_PATTERN, text.strip()))

    def _is_article(self, text: str) -> bool:
        """判断是否为条款"""
        text_stripped = text.strip().split('\n')[0]
        return any(re.match(pattern, text_stripped) for pattern in self.ARTICLE_PATTERNS)

    def _create_article(self, article_data: dict, file_path: str,
                       level: str, effective_date: str) -> LegalArticle:
        """创建条款对象"""
        article_number = article_data['article_number']
        content = article_data.get('content', '')

        # 生成唯一ID
        law_id = f"{self.current_law_name}_{article_number}"
        law_id = re.sub(r'[^\w\u4e00-\u9fff]', '_', law_id)

        # 提取款号（如果有）
        paragraph_number = None
        if '第' in content[:20] and '款' in content[:20]:
            match = re.search(r'第([一二三四五六七八九十]|[0-9]+)款', content[:30])
            if match:
                paragraph_number = match.group(0)

        return LegalArticle(
            law_id=law_id,
            law_name=self.current_law_name,
            article_number=article_number,
            paragraph_number=paragraph_number,
            content=content,
            chapter=self.current_chapter,
            section=self.current_section,
            level=level,
            effective_date=effective_date,
            source_file=os.path.basename(file_path),
            metadata={
                'word_count': len(content),
                'char_count': len(content.replace(' ', '')),
                'parsed_at': datetime.now().isoformat()
            }
        )


class LegalDocChunker:
    """法律文档分块处理主类"""

    def __init__(self, source_dir: str):
        self.source_dir = Path(source_dir)
        self.parser = LegalDocParser()
        self.all_articles = []

    def process_all(self) -> list[LegalArticle]:
        """处理所有法律文档"""
        logger.info(f"🚀 开始处理目录: {self.source_dir}")

        # 查找所有DOCX文件
        docx_files = list(self.source_dir.glob("*.docx"))
        logger.info(f"📊 找到 {len(docx_files)} 个法律文档")

        for file_path in docx_files:
            articles = self.parser.parse_file(str(file_path))
            self.all_articles.extend(articles)

        logger.info(f"✅ 总共提取 {len(self.all_articles)} 个条款")
        return self.all_articles

    def save_json(self, output_file: str) -> None:
        """保存为JSON"""
        logger.info(f"💾 保存JSON: {output_file}")

        data = {
            'total_articles': len(self.all_articles),
            'parsed_at': datetime.now().isoformat(),
            'articles': [article.to_dict() for article in self.all_articles]
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info("✅ JSON保存完成")

    def get_statistics(self) -> dict:
        """获取统计信息"""
        if not self.all_articles:
            return {}

        laws = {}
        levels = {}
        total_chars = 0

        for article in self.all_articles:
            # 统计法律文件
            if article.law_name not in laws:
                laws[article.law_name] = 0
            laws[article.law_name] += 1

            # 统计效力层级
            if article.level not in levels:
                levels[article.level] = 0
            levels[article.level] += 1

            total_chars += article.metadata['char_count']

        return {
            'total_articles': len(self.all_articles),
            'total_laws': len(laws),
            'laws': laws,
            'levels': levels,
            'total_characters': total_chars,
            'avg_chars_per_article': total_chars // len(self.all_articles) if self.all_articles else 0
        }


def main() -> None:
    """主函数"""

    source_dir = "/Volumes/AthenaData/语料/专利/专利法律法规"
    output_dir = "/Users/xujian/Athena工作平台/production/data/legal_articles"

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 处理文档
    chunker = LegalDocChunker(source_dir)
    articles = chunker.process_all()

    # 保存JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join(output_dir, f"legal_articles_{timestamp}.json")
    chunker.save_json(json_file)

    # 输出统计
    stats = chunker.get_statistics()
    print("\n" + "="*60)
    print("📊 处理统计:")
    print("="*60)
    print(f"总条款数: {stats['total_articles']}")
    print(f"法律文件数: {stats['total_laws']}")
    print(f"总字符数: {stats['total_characters']:,}")
    print(f"平均条款长度: {stats['avg_chars_per_article']} 字符")
    print("\n效力层级分布:")
    for level, count in stats['levels'].items():
        print(f"  {level}: {count} 条")

    print("\n各法律文件条款数:")
    for law, count in stats['laws'].items():
        print(f"  {law}: {count} 条")

    print(f"\n💾 数据已保存: {json_file}")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
