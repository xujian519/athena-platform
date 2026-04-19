#!/usr/bin/env python3
"""
专利审查指南PDF处理器 - 改进版
正确解析小节并累积完整内容

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/guideline_processor_v2_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class SubsectionData:
    """小节数据结构"""
    chunk_id: str
    part: str
    chapter: str
    section: str
    subsection: str
    title: str
    content: str
    full_path: str
    word_count: int
    char_count: int
    has_example: bool
    references: list[str]
    metadata: dict[str, Any]


class ImprovedGuidelineProcessor:
    """改进的专利审查指南处理器"""

    def __init__(self):
        # 匹配模式
        self.patterns = {
            'part': re.compile(r'^第([一二三四五六七八九十\d]+)部分[：\s]*(.*)'),
            'chapter': re.compile(r'^第([一二三四五六七八九十\d]+)章[：\s]*(.*)'),
            'section': re.compile(r'^(\d+\.\d+)[：\s]+(.+)'),
            'subsection': re.compile(r'^(\d+\.\d+\.\d+)[：\s]+(.+)'),
        }

        # 示例模式
        self.example_pattern = re.compile(r'^【例(\d+)】')

        # 法律引用模式
        self.law_ref_pattern = re.compile(r'(专利法|实施细则|审查指南)[\s\u3000]*(第[一二三四五六七八九十百千万零\d]+条)')

        # 2025新增内容
        self.new_2025_content = {
            '6.1.1': 'AI伦理审查',
            '7.1': '比特流相关规定',
            '7.1.1': '比特流审查',
        }

    def extract_pdf_pages(self, pdf_path: str) -> list[dict[str, Any]]:
        """提取PDF页面，保留页码信息"""
        logger.info(f"📖 解析PDF: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
        except Exception as e:
            logger.error(f"❌ 无法打开PDF文件 {pdf_path}: {e}")
            return []

        pages_data = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            pages_data.append({
                'page_number': page_num + 1,
                'text': text
            })

        doc.close()
        logger.info(f"✅ 提取完成，共 {len(pages_data)} 页")
        return pages_data

    def parse_hierarchical_structure(self, pages_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """解析层级结构"""
        logger.info("🏗️ 解析层级结构...")

        # 合并所有文本
        all_lines = []
        for page in pages_data:
            lines = page['text'].split('\n')
            for line in lines:
                line = line.strip()
                if line:
                    all_lines.append({
                        'text': line,
                        'page': page['page_number']
                    })

        # 解析结构
        hierarchy = []
        current_part = None
        current_chapter = None
        current_section = None
        current_subsection = None
        content_lines = []

        for item in all_lines:
            line = item['text']
            page = item['page']

            # 检测部分
            match = self.patterns['part'].match(line)
            if match:
                if current_subsection:
                    hierarchy.append(self._create_subsection(
                        current_part, current_chapter, current_section,
                        current_subsection, content_lines
                    ))
                current_part = f"第{match.group(1)}部分"
                current_chapter = None
                current_section = None
                current_subsection = None
                content_lines = []
                continue

            # 检测章
            match = self.patterns['chapter'].match(line)
            if match:
                if current_subsection:
                    hierarchy.append(self._create_subsection(
                        current_part, current_chapter, current_section,
                        current_subsection, content_lines
                    ))
                current_chapter = f"第{match.group(1)}章"
                current_section = None
                current_subsection = None
                content_lines = []
                continue

            # 检测节
            match = self.patterns['section'].match(line)
            if match:
                if current_subsection:
                    hierarchy.append(self._create_subsection(
                        current_part, current_chapter, current_section,
                        current_subsection, content_lines
                    ))
                current_section = match.group(1)
                current_subsection = None
                content_lines = [line]  # 节标题
                continue

            # 检测小节
            match = self.patterns['subsection'].match(line)
            if match:
                # 保存前一个小节
                if current_subsection and content_lines:
                    hierarchy.append(self._create_subsection(
                        current_part, current_chapter, current_section,
                        current_subsection, content_lines
                    ))

                # 开始新小节
                current_subsection = match.group(1)
                subsection_title = match.group(2)
                content_lines = [subsection_title]

                # 检查是否为2025新增
                is_new = current_subsection in self.new_2025_content
                if is_new:
                    logger.info(f"🆕 2025新增: {current_subsection} - {subsection_title}")

                continue

            # 累积内容
            if current_subsection:
                content_lines.append(line)

        # 保存最后一个小节
        if current_subsection and content_lines:
            hierarchy.append(self._create_subsection(
                current_part, current_chapter, current_section,
                current_subsection, content_lines
            ))

        logger.info(f"✅ 解析完成，共 {len(hierarchy)} 个小节")
        return hierarchy

    def _create_subsection(self, part: str, chapter: str, section: str,
                          subsection: str, content_lines: list[str]) -> dict[str, Any]:
        """创建小节数据"""
        title = content_lines[0] if content_lines else ""
        content = "\n".join(content_lines[1:]) if len(content_lines) > 1 else ""

        # 生成ID
        chunk_id = self._generate_id(part or "", chapter or "", subsection)

        # 完整路径
        full_path = " > ".join(filter(None, [part, chapter, section, subsection]))

        # 统计
        char_count = len(content)
        word_count = len([w for w in content if w.strip() and w.strip() not in '，。；：、！？""''（）【】《》\n\r\t'])

        # 检查示例
        has_example = bool(self.example_pattern.search(content))

        # 提取引用
        references = self.law_ref_pattern.findall(content)
        references = [f"{law} {article}" for law, article in references]

        # 检查2025更新
        update_type = None
        if subsection in self.new_2025_content:
            update_type = "新增"

        return {
            'chunk_id': chunk_id,
            'part': part or "",
            'chapter': chapter or "",
            'section': section or "",
            'subsection': subsection,
            'title': title,
            'content': content,
            'full_path': full_path,
            'word_count': word_count,
            'char_count': char_count,
            'has_example': has_example,
            'references': references,
            'update_type': update_type,
            'metadata': {
                'level': 'subsection',
                'version': '2025'
            }
        }

    def _generate_id(self, part: str, chapter: str, subsection: str) -> str:
        """生成唯一ID"""
        id_string = f"{part}_{chapter}_{subsection}".replace(" ", "_")
        return f"subsec_{short_hash(id_string.encode(), 12)}"

    def save_results(self, hierarchy: list[dict[str, Any]], output_dir: str) -> None:
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存小节数据
        chunks_file = output_path / f"guideline_subsections_v2_{timestamp}.json"

        # 只保存有内容的小节
        valid_subsections = [s for s in hierarchy if s['content']]

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '2025',
                'source_pdf': '专利审查指南（最新版）.pdf',
                'total_subsections': len(hierarchy),
                'valid_subsections_with_content': len(valid_subsections),
                'subsections': valid_subsections
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 已保存: {chunks_file}")

        # 生成统计
        stats = self._generate_stats(valid_subsections)
        stats_file = output_path / f"guideline_stats_v2_{timestamp}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 统计报告: {stats_file}")

        # 生成用于向量化的简化数据
        vector_data = []
        for sub in valid_subsections:
            vector_data.append({
                'chunk_id': sub['chunk_id'],
                'text': f"{sub['full_path']}\n{sub['title']}\n{sub['content']}",
                'metadata': {
                    'part': sub['part'],
                    'chapter': sub['chapter'],
                    'section': sub['section'],
                    'subsection': sub['subsection'],
                    'title': sub['title'],
                    'full_path': sub['full_path'],
                    'word_count': sub['word_count'],
                    'update_type': sub.get('update_type')
                }
            })

        vector_file = output_path / f"guideline_vectors_input_{timestamp}.json"

        with open(vector_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_chunks': len(vector_data),
                'chunks': vector_data
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📦 向量输入数据: {vector_file}")

        return str(chunks_file), str(stats_file), str(vector_file)

    def _generate_stats(self, subsections: list[dict[str, Any]]) -> dict[str, Any]:
        """生成统计信息"""
        stats = {
            'total_subsections': len(subsections),
            'total_words': sum(s['word_count'] for s in subsections),
            'total_chars': sum(s['char_count'] for s in subsections),
            'avg_words_per_subsection': 0,
            'avg_chars_per_subsection': 0,
            'with_examples': sum(1 for s in subsections if s['has_example']),
            'new_in_2025': sum(1 for s in subsections if s.get('update_type') == '新增'),
            'by_part': defaultdict(int),
            'by_chapter': defaultdict(int),
            'word_count_distribution': {
                'min': float('inf'),
                'max': 0,
                'avg': 0
            }
        }

        word_counts = []
        for sub in subsections:
            wc = sub['word_count']
            word_counts.append(wc)
            stats['by_part'][sub['part'] or '未分类'] += 1
            stats['by_chapter'][sub['chapter'] or '未分类'] += 1

        if word_counts:
            stats['avg_words_per_subsection'] = sum(word_counts) / len(word_counts)
            stats['avg_chars_per_subsection'] = sum(s['char_count'] for s in subsections) / len(subsections)
            stats['word_count_distribution']['min'] = min(word_counts)
            stats['word_count_distribution']['max'] = max(word_counts)
            stats['word_count_distribution']['avg'] = sum(word_counts) / len(word_counts)

        # 转换defaultdict
        stats['by_part'] = dict(sorted(stats['by_part'].items(), key=lambda x: x[1], reverse=True))
        stats['by_chapter'] = dict(sorted(stats['by_chapter'].items(), key=lambda x: x[1], reverse=True))

        return stats


def main() -> None:
    """主函数"""
    pdf_path = "/Volumes/AthenaData/语料/专利/专利法律法规/专利审查指南（最新版）.pdf"
    output_dir = "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents"

    logger.info("=" * 60)
    logger.info("🚀 专利审查指南处理器 V2")
    logger.info("=" * 60)

    processor = ImprovedGuidelineProcessor()

    # 1. 提取PDF页面
    pages_data = processor.extract_pdf_pages(pdf_path)

    # 2. 解析层级结构
    hierarchy = processor.parse_hierarchical_structure(pages_data)

    # 3. 保存结果
    chunks_file, stats_file, vector_file = processor.save_results(hierarchy, output_dir)

    logger.info("=" * 60)
    logger.info("✅ 处理完成！")
    logger.info(f"📄 小节数据: {chunks_file}")
    logger.info(f"📊 统计报告: {stats_file}")
    logger.info(f"📦 向量输入: {vector_file}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
