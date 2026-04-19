#!/usr/bin/env python3
"""
专利复审决定书处理器
解析DOCX格式的复审决定书，提取结构化数据，分块并生成向量

作者: Athena平台团队
创建时间: 2025-12-23
参考: 构建专利复审决定书的向量库和知识图谱
"""

from __future__ import annotations
import json
import logging
import re

# 添加项目路径
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/decision_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DecisionMetadata:
    """决定书元数据"""
    decision_number: str  # 决定号
    decision_date: str  # 决定日
    patent_number: str  # 专利号
    invention_title: str  # 发明名称
    requester: str  # 请求人
    patentee: str  # 专利权人
    law_basis: list[str]  # 法律依据
    ipc: str  # 国际分类号
    decision_type: str  # 决定类型（无效/复审）
    outcome: str  # 决定结果


@dataclass
class DecisionChunk:
    """决定书分块"""
    chunk_id: str
    doc_id: str
    block_type: str  # metadata, keypoints, background, evidence, analysis, decision
    section_path: str  # e.g., "决定理由 > 1、关于新颖性"
    text: str
    metadata: dict[str, Any]


class ReviewDecisionProcessor:
    """专利复审决定书处理器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.source_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")
        self.invalid_dir = Path("/Volumes/AthenaData/语料/专利/专利无效宣告原文")
        self.output_dir = self.base_dir / "production/data/patent_decisions"

        # 正则模式
        self.patterns = {
            # 决定号: 第XXXXX号
            'decision_number': re.compile(r'第(\d+)号'),
            # 决定日: 20XX年X月X日
            'decision_date': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            # 专利号: CNXXXXXXXXX.X
            'patent_number': re.compile(r'(CN\d{9}\.\d|[0-9X]{10})'),
            # 法律引用: 专利法第XX条第X款
            'law_reference': re.compile(r'(专利法|实施细则)[\s\u3000]*(?:第)?([\d一二三四五六七八九十百千万]+)[条条款款](?:第([\d一二三四五六七八九十]+)[款项])?'),
            # 段落标题: 一、二、三、或 1、2、3、
            'section_title_cn': re.compile(r'^([一二三四五六七八九十]+)、([^。]{2,30}?)[：:]\s*$'),
            'section_title_num': re.compile(r'^(\d+)、([^。]{2,30}?)[：:]\s*$'),
            # 证据引用: 附件1/2/3、证据1/2/3、对比文件1/2/3
            'evidence': re.compile(r'(附件|证据|对比文件)\s*(\d+)'),
        }

        logger.info("专利复审决定书处理器初始化完成")

    def scan_source_directory(self) -> tuple[list[Path], list[Path]]:
        """扫描源目录，返回复审决定和无效宣告文件"""
        logger.info("=" * 60)
        logger.info("📂 扫描源目录")
        logger.info("=" * 60)

        # 复审决定
        review_files = list(self.source_dir.glob("*.docx"))
        logger.info(f"📄 专利复审决定: {len(review_files)} 个文件")

        # 无效宣告
        invalid_files = list(self.invalid_dir.glob("*.docx"))
        logger.info(f"📄 专利无效宣告: {len(invalid_files)} 个文件")

        logger.info(f"📊 总计: {len(review_files) + len(invalid_files)} 个文件")

        return review_files, invalid_files

    def extract_from_docx(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOCX文件提取文本和基本元数据"""
        try:
            doc = Document(str(file_path))

            # 提取所有段落文本
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            full_text = "\n".join(paragraphs)

            # 提取基本元数据
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs),
            }

            # 从文件名提取决定号
            filename_stem = file_path.stem
            if re.match(r'\d{9}', filename_stem):
                metadata['decision_number'] = filename_stem

            # 从文本提取决定号
            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            # 提取决定日期
            match = self.patterns['decision_date'].search(full_text)
            if match:
                year, month, day = match.groups()
                metadata['decision_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"

            return full_text, metadata

        except Exception as e:
            logger.error(f"❌ DOCX提取失败 {file_path.name}: {e}")
            return "", {}

    def parse_decision_structure(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """解析决定书的结构化内容"""
        if not text:
            return []

        doc_id = metadata.get('decision_number', metadata.get('filename', 'unknown'))

        # 分割文本为行
        lines = text.split('\n')

        chunks = []
        current_section = "未分类"
        current_subsection = ""
        current_content = []
        section_counter = defaultdict(int)

        # 定义主要章节标题模式
        main_sections = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '决定': 'decision',
            '理由': 'reasoning'
        }

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # 检测主章节
            matched_main = None
            for section_name, block_type in main_sections.items():
                if section_name in line:
                    # 保存当前章节
                    if current_content:
                        chunks.append(self._create_chunk(
                            doc_id, current_section, current_subsection,
                            current_content, metadata, i
                        ))

                    matched_main = (section_name, block_type)
                    break

            if matched_main:
                current_section = matched_main[0]
                block_type = matched_main[1]
                current_subsection = ""
                current_content = []
                section_counter[block_type] += 1
                continue

            # 检测子章节 (1、2、3、或 一、二、三、)
            match_cn = self.patterns['section_title_cn'].match(line)
            match_num = self.patterns['section_title_num'].match(line)

            if match_cn or match_num:
                # 保存当前子章节
                if current_content:
                    chunks.append(self._create_chunk(
                        doc_id, current_section, current_subsection,
                        current_content, metadata, i
                    ))

                # 开始新子章节
                if match_cn:
                    current_subsection = match_cn.group(2)
                else:
                    current_subsection = match_num.group(2)

                current_content = []
                continue

            # 累积内容
            current_content.append(line)

        # 保存最后一个块
        if current_content:
            chunks.append(self._create_chunk(
                doc_id, current_section, current_subsection,
                current_content, metadata, len(lines)
            ))

        return chunks

    def _create_chunk(self, doc_id: str, section: str, subsection: str,
                     content_lines: list[str], metadata: dict[str, Any],
                     line_num: int) -> dict[str, Any]:
        """创建数据块"""
        content = "\n".join(content_lines)

        # 确定块类型
        block_type_map = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }
        block_type = block_type_map.get(section, 'other')

        # 构建路径
        section_path = f"{section}"
        if subsection:
            section_path += f" > {subsection}"

        # 生成chunk_id
        chunk_id_suffix = short_hash(f"{doc_id}_{section_path}_{line_num}".encode())[:8]
        chunk_id = f"dec_{doc_id}_{chunk_id_suffix}"

        # 提取法律引用
        law_refs = self.patterns['law_reference'].findall(content)

        # 提取证据引用
        evidence_refs = self.patterns['evidence'].findall(content)

        chunk = {
            'chunk_id': chunk_id,
            'doc_id': doc_id,
            'block_type': block_type,
            'section_path': section_path,
            'text': content,
            'metadata': {
                'filename': metadata.get('filename', ''),
                'decision_date': metadata.get('decision_date', ''),
                'char_count': len(content),
                'line_number': line_num,
                'law_references': [f"{law} {art}" for law, art, _ in law_refs if art],
                'evidence_references': [f"{evid} {num}" for evid, num in evidence_refs]
            }
        }

        return chunk

    def process_batch_files(self, file_paths: list[Path], batch_name: str,
                           max_files: int = None) -> dict[str, Any]:
        """批量处理文件"""
        logger.info("=" * 60)
        logger.info(f"📦 批量处理: {batch_name}")
        logger.info("=" * 60)

        if max_files:
            file_paths = file_paths[:max_files]

        all_chunks = []
        failed_files = []

        for i, file_path in enumerate(file_paths):
            if (i + 1) % 100 == 0:
                logger.info(f"   进度: {i + 1}/{len(file_paths)}")

            try:
                # 提取文本
                text, metadata = self.extract_from_docx(file_path)
                if not text:
                    failed_files.append((file_path.name, "empty_text"))
                    continue

                # 解析结构
                chunks = self.parse_decision_structure(text, metadata)
                if chunks:
                    all_chunks.extend(chunks)

            except Exception as e:
                failed_files.append((file_path.name, str(e)))

        logger.info("✅ 处理完成:")
        logger.info(f"   处理文件: {len(file_paths) - len(failed_files)}")
        logger.info(f"   生成块: {len(all_chunks)}")
        logger.info(f"   失败: {len(failed_files)}")

        # 保存结果
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.output_dir / "processed" / f"{batch_name}_chunks_{timestamp}.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'batch_name': batch_name,
                'processed_at': datetime.now().isoformat(),
                'total_files': len(file_paths),
                'successful_files': len(file_paths) - len(failed_files),
                'total_chunks': len(all_chunks),
                'failed_files': failed_files,
                'chunks': all_chunks
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 已保存: {output_file}")

        # 统计块类型分布
        block_type_counts = defaultdict(int)
        for chunk in all_chunks:
            block_type_counts[chunk['block_type']] += 1

        logger.info("📊 块类型分布:")
        for block_type, count in sorted(block_type_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"   {block_type}: {count}")

        return {
            'total_files': len(file_paths),
            'successful_files': len(file_paths) - len(failed_files),
            'total_chunks': len(all_chunks),
            'failed_files': failed_files,
            'output_file': str(output_file)
        }

    def process_sample(self, num_files: int = 10) -> dict[str, Any]:
        """处理样本文件用于测试"""
        logger.info("=" * 60)
        logger.info("🧪 样本处理模式")
        logger.info("=" * 60)

        review_files, invalid_files = self.scan_source_directory()

        # 取前N个复审决定文件
        sample_files = review_files[:num_files]

        logger.info(f"📋 处理样本: {len(sample_files)} 个复审决定文件")

        return self.process_batch_files(sample_files, f"sample_{num_files}")


def main() -> None:
    """主函数"""
    processor = ReviewDecisionProcessor()

    # 处理样本（测试用）
    result = processor.process_sample(num_files=10)

    logger.info("=" * 60)
    logger.info("🎉 样本处理完成！")
    logger.info(f"📊 处理文件: {result['successful_files']}/{result['total_files']}")
    logger.info(f"📦 生成块: {result['total_chunks']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
