#!/usr/bin/env python3
"""
大PDF文件分割处理器
Large PDF File Splitter

用于处理超大PDF文件（如80M+的商标审查指南），支持：
1. 分页分割处理
2. 内存优化
3. 断点续传
4. 进度跟踪

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LargePDFSplitter:
    """大PDF文件分割处理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化分割器

        Args:
            config: 配置字典，包含：
                - pdf_path: PDF文件路径
                - output_dir: 输出目录
                - chunk_size: 分块大小（页数，默认50页）
                - enable_ocr: 是否启用OCR（默认False）
                - progress_file: 进度文件路径
        """
        self.config = config or {}
        self.pdf_path = self.config.get('pdf_path')
        self.output_dir = Path(self.config.get('output_dir', './data/trademark_rules/temp'))
        self.chunk_size = self.config.get('chunk_size', 50)  # 每50页一块
        self.enable_ocr = self.config.get('enable_ocr', False)
        self.progress_file = self.config.get('progress_file')

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            'total_pages': 0,
            'processed_pages': 0,
            'total_chunks': 0,
            'failed_pages': 0,
            'start_time': None,
            'end_time': None
        }

        # 进度跟踪
        self.progress = self._load_progress()

    def _load_progress(self) -> dict[str, Any]:
        """加载进度信息"""
        if self.progress_file and os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载进度文件失败: {e}")
        return {
            'processed_chunks': [],
            'last_page': 0,
            'timestamp': None
        }

    def _save_progress(self, chunk_id: str, last_page: int) -> Any:
        """保存进度信息"""
        if self.progress_file:
            self.progress['processed_chunks'].append(chunk_id)
            self.progress['last_page'] = last_page
            self.progress['timestamp'] = datetime.now().isoformat()

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)

    def _get_page_hash(self, page_text: str) -> str:
        """获取页面文本哈希值"""
        return hashlib.sha256(page_text.encode('utf-8')).hexdigest()[:16]

    async def split_pdf(self) -> list[dict[str, Any]]:
        """
        分割大PDF文件

        Returns:
            分块信息列表
        """
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")

        logger.info(f"🔄 开始分割大PDF: {self.pdf_path}")
        self.stats['start_time'] = datetime.now().isoformat()

        # 打开PDF文件
        pdf_document = fitz.open(self.pdf_path)
        total_pages = len(pdf_document)
        self.stats['total_pages'] = total_pages

        logger.info(f"📖 PDF总页数: {total_pages}")
        logger.info(f"📦 分块大小: {self.chunk_size} 页/块")

        chunks = []
        start_page = self.progress.get('last_page', 0)

        # 从上次中断的位置继续
        for chunk_start in range(start_page, total_pages, self.chunk_size):
            chunk_end = min(chunk_start + self.chunk_size, total_pages)
            chunk_id = f"chunk_{chunk_start+1}_{chunk_end}"

            # 检查是否已处理
            if chunk_id in self.progress.get('processed_chunks', []):
                logger.info(f"⏭️  跳过已处理的块: {chunk_id}")
                continue

            logger.info(f"📦 处理第 {chunk_start+1}-{chunk_end} 页 (块 {len(chunks)+1})")

            # 提取分块内容
            chunk_data = await self._extract_chunk(
                pdf_document, chunk_start, chunk_end, chunk_id
            )

            if chunk_data:
                chunks.append(chunk_data)
                self._save_progress(chunk_id, chunk_end)

        pdf_document.close()
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['total_chunks'] = len(chunks)

        logger.info(f"✅ PDF分割完成！共 {len(chunks)} 个块")
        logger.info(f"📊 统计: {json.dumps(self.stats, ensure_ascii=False, indent=2)}")

        return chunks

    async def _extract_chunk(
        self,
        pdf_document: fitz.Document,
        start_page: int,
        end_page: int,
        chunk_id: str
    ) -> dict[str, Any | None]:
        """
        提取PDF分块内容

        Args:
            pdf_document: PyMuPDF文档对象
            start_page: 起始页索引
            end_page: 结束页索引
            chunk_id: 分块ID

        Returns:
            分块数据字典
        """
        try:
            pages_content = []
            full_text = ""

            for page_idx in range(start_page, end_page):
                page = pdf_document[page_idx]

                # 提取文本
                text = page.get_text("text")
                page_hash = self._get_page_hash(text)

                page_data = {
                    'page_num': page_idx + 1,
                    'text': text.strip(),
                    'hash': page_hash,
                    'char_count': len(text.strip())
                }

                pages_content.append(page_data)
                full_text += text + "\n\n"
                self.stats['processed_pages'] += 1

            # 保存分块内容
            chunk_file = self.output_dir / f"{chunk_id}.json"
            chunk_data = {
                'chunk_id': chunk_id,
                'start_page': start_page + 1,
                'end_page': end_page,
                'page_count': end_page - start_page,
                'pages': pages_content,
                'full_text': full_text.strip(),
                'char_count': len(full_text),
                'created_at': datetime.now().isoformat()
            }

            with open(chunk_file, 'w', encoding='utf-8') as f:
                json.dump(chunk_data, f, ensure_ascii=False, indent=2)

            logger.info(f"✅ 分块 {chunk_id} 已保存: {len(full_text)} 字符")

            return chunk_data

        except Exception as e:
            logger.error(f"❌ 提取分块 {chunk_id} 失败: {e}")
            self.stats['failed_pages'] += (end_page - start_page)
            return None

    async def process_single_pass(self) -> dict[str, Any]:
        """
        单次完整处理大PDF

        Returns:
            处理结果
        """
        logger.info("🚀 开始单次完整处理大PDF文件")

        # 分割PDF
        chunks = await self.split_pdf()

        # 合并所有文本
        merged_content = {
            'source_file': os.path.basename(self.pdf_path),
            'file_size': os.path.getsize(self.pdf_path),
            'total_pages': self.stats['total_pages'],
            'total_chunks': len(chunks),
            'chunks': chunks,
            'created_at': datetime.now().isoformat()
        }

        # 保存合并内容
        merged_file = self.output_dir / 'merged_content.json'
        with open(merged_file, 'w', encoding='utf-8') as f:
            json.dump(merged_content, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 合并内容已保存: {merged_file}")

        return {
            'status': 'success',
            'stats': self.stats,
            'chunks_count': len(chunks),
            'output_files': {
                'chunks_dir': str(self.output_dir),
                'merged_file': str(merged_file),
                'progress_file': self.progress_file
            }
        }


async def main():
    """主函数 - 使用示例"""
    # 配置分割器
    config = {
        'pdf_path': '/Users/xujian/Athena工作平台/data/商标/商标审查审理指南.pdf',
        'output_dir': './data/trademark_rules/temp',
        'chunk_size': 50,  # 每50页一块
        'enable_ocr': False,
        'progress_file': './data/trademark_rules/temp/progress.json'
    }

    # 创建并运行分割器
    splitter = LargePDFSplitter(config)
    result = await splitter.process_single_pass()

    print("\n" + "="*50)
    print("📊 处理完成！")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
