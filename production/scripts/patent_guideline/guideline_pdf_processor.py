#!/usr/bin/env python3
"""
专利审查指南PDF处理器
解析专利审查指南PDF并生成小节级分块

作者: Athena平台团队
创建时间: 2025-12-23
基于: 国家知识产权局局令第84号（2025版）
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
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
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/guideline_pdf_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class GuidelineChunk:
    """指南块数据结构"""
    chunk_id: str
    level: str  # part, chapter, section, subsection
    level_number: int  # 1-4
    title: str
    content: str
    parent_path: str  # 完整层级路径
    metadata: dict[str, Any] = field(default_factory=dict)

    # 统计信息
    word_count: int = field(default=0)
    char_count: int = field(default=0)

    def __post_init__(self):
        self.char_count = len(self.content)
        self.word_count = len([w for w in self.content if w.strip()])


class PatentGuidelinePDFProcessor:
    """专利审查指南PDF处理器"""

    def __init__(self):
        # 层级模式
        self.patterns = {
            'part': re.compile(r'^第([一二三四五六七八九十\d]+)部分\s*(.*)'),
            'chapter': re.compile(r'^第([一二三四五六七八九十\d]+)章\s*(.*)'),
            'section': re.compile(r'^(\d+\.\d+)\s+(.+)'),
            'subsection': re.compile(r'^(\d+\.\d+\.\d+)\s+(.+)'),
            'example': re.compile(r'^【例(\d+)】\s*(.*)'),
        }

        # 2025版新增内容标记
        self.new_content_markers = {
            'AI伦理': ['人工智能', 'AI伦理', '算法歧视'],
            '比特流': ['比特流', 'bit stream', '数字信号'],
            '大数据': ['大数据', '数据挖掘', '机器学习'],
        }

        logger.info("专利审查指南PDF处理器初始化完成")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF中提取文本"""
        logger.info(f"📖 开始解析PDF: {pdf_path}")

        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
        except Exception as e:
            logger.error(f"❌ 无法打开PDF文件 {pdf_path}: {e}")
            return ""

        logger.info(f"📄 总页数: {total_pages}")

        all_text = []
        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            all_text.append(f"[第{page_num+1}页]\n{text}")

        doc.close()

        full_text = "\n".join(all_text)
        logger.info(f"✅ 提取完成，总字符数: {len(full_text)}")

        return full_text

    def parse_structure(self, text: str) -> list[GuidelineChunk]:
        """解析指南结构"""
        logger.info("🔍 开始解析结构...")

        # 按行分割
        lines = text.split('\n')
        lines = [line.strip() for line in lines if line.strip()]

        chunks = []
        stack = []  # 层级栈

        for line_num, line in enumerate(lines):
            # 检测行类型
            level_info = self._detect_line_level(line)

            if level_info:
                # 确定父级
                while stack and stack[-1].level_number >= level_info['level_number']:
                    stack.pop()

                parent_path = " > ".join([c.title for c in stack]) if stack else ""

                # 创建块
                chunk = GuidelineChunk(
                    chunk_id=self._generate_chunk_id(level_info['level'], line_num),
                    level=level_info['level'],
                    level_number=level_info['level_number'],
                    title=level_info['title'],
                    content=line,
                    parent_path=parent_path,
                    metadata={
                        'line_number': line_num,
                        'confidence': level_info.get('confidence', 1.0),
                        'is_new_content': self._check_new_content(line)
                    }
                )

                chunks.append(chunk)
                stack.append(chunk)

                logger.debug(f"[{level_info['level']}] {level_info['title']}")

        logger.info(f"✅ 解析完成，共 {len(chunks)} 个块")
        return chunks

    def _detect_line_level(self, line: str) -> dict[str, Any | None]:
        """检测行所属层级"""
        # 按优先级检查
        checks = [
            ('part', self.patterns['part'], 1),
            ('chapter', self.patterns['chapter'], 2),
            ('section', self.patterns['section'], 3),
            ('subsection', self.patterns['subsection'], 4),
        ]

        for level_name, pattern, level_num in checks:
            match = pattern.match(line)
            if match:
                return {
                    'level': level_name,
                    'level_number': level_num,
                    'title': match.group(2) if len(match.groups()) >= 2 else match.group(1),
                    'confidence': 1.0
                }

        return None

    def _generate_chunk_id(self, level: str, line_num: int) -> str:
        """生成块ID"""
        id_string = f"{level}_{line_num}"
        return f"chunk_{short_hash(id_string.encode(), 12)}"

    def _check_new_content(self, text: str) -> bool:
        """检查是否为2025新增内容"""
        for _category, keywords in self.new_content_markers.items():
            if any(kw in text for kw in keywords):
                return True
        return False

    def extract_subsections(self, chunks: list[GuidelineChunk]) -> list[dict[str, Any]]:
        """提取小节级块"""
        logger.info("🎯 提取小节级块...")

        subsections = []
        current_part = None
        current_chapter = None
        current_section = None
        current_subsection = None
        content_buffer = []

        for chunk in chunks:
            if chunk.level == 'part':
                current_part = chunk.title
            elif chunk.level == 'chapter':
                current_chapter = chunk.title
            elif chunk.level == 'section':
                current_section = chunk.title
                # 重置
                current_subsection = None
                content_buffer = []
            elif chunk.level == 'subsection':
                # 保存前一个小节
                if current_subsection and content_buffer:
                    subsections.append({
                        'part': current_part or '',
                        'chapter': current_chapter or '',
                        'section': current_section or '',
                        'subsection': current_subsection,
                        'title': content_buffer[0] if content_buffer else '',
                        'content': '\n'.join(content_buffer[1:]) if len(content_buffer) > 1 else '',
                        'metadata': {
                            'level': 'subsection',
                            'word_count': sum(len(c.split()) for c in content_buffer)
                        }
                    })

                # 开始新小节
                current_subsection = chunk.title
                content_buffer = [chunk.title]
            else:
                # 累积内容
                if current_subsection:
                    content_buffer.append(chunk.content)

        # 保存最后一个小节
        if current_subsection and content_buffer:
            subsections.append({
                'part': current_part or '',
                'chapter': current_chapter or '',
                'section': current_section or '',
                'subsection': current_subsection,
                'title': content_buffer[0] if content_buffer else '',
                'content': '\n'.join(content_buffer[1:]) if len(content_buffer) > 1 else '',
                'metadata': {
                    'level': 'subsection',
                    'word_count': sum(len(c.split()) for c in content_buffer)
                }
            })

        logger.info(f"✅ 提取完成，共 {len(subsections)} 个小节")
        return subsections

    def save_results(self, subsections: list[dict[str, Any]], output_dir: str) -> None:
        """保存结果"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存小节数据
        chunks_file = output_path / f"guideline_subsections_{timestamp}.json"

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'version': '2025',
                'total_subsections': len(subsections),
                'subsections': subsections
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 已保存: {chunks_file}")

        # 生成统计报告
        stats = self._generate_statistics(subsections)
        stats_file = output_path / f"guideline_stats_{timestamp}.json"

        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info(f"📊 统计报告: {stats_file}")

        return str(chunks_file), str(stats_file)

    def _generate_statistics(self, subsections: list[dict[str, Any]]) -> dict[str, Any]:
        """生成统计信息"""
        stats = {
            'total_subsections': len(subsections),
            'avg_word_count': 0,
            'by_part': defaultdict(int),
            'by_chapter': defaultdict(int),
        }

        word_counts = []
        for sub in subsections:
            wc = sub.get('metadata', {}).get('word_count', 0)
            word_counts.append(wc)
            stats['by_part'][sub.get('part', '未知')] += 1
            stats['by_chapter'][sub.get('chapter', '未知')] += 1

        if word_counts:
            stats['avg_word_count'] = sum(word_counts) / len(word_counts)

        stats['by_part'] = dict(stats['by_part'])
        stats['by_chapter'] = dict(stats['by_chapter'])

        return stats


async def main():
    """主函数"""
    pdf_path = "/Volumes/AthenaData/语料/专利/专利法律法规/专利审查指南（最新版）.pdf"
    output_dir = "/Users/xujian/Athena工作平台/production/data/patent_rules/legal_documents"

    logger.info("=" * 60)
    logger.info("🚀 启动专利审查指南PDF处理器")
    logger.info("=" * 60)

    processor = PatentGuidelinePDFProcessor()

    # 1. 提取PDF文本
    text = processor.extract_text_from_pdf(pdf_path)

    # 2. 解析结构
    chunks = processor.parse_structure(text)

    # 3. 提取小节
    subsections = processor.extract_subsections(chunks)

    # 4. 保存结果
    chunks_file, stats_file = processor.save_results(subsections, output_dir)

    logger.info("=" * 60)
    logger.info("✅ 处理完成！")
    logger.info(f"📄 小节数据: {chunks_file}")
    logger.info(f"📊 统计报告: {stats_file}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
