#!/usr/bin/env python3
"""
Markdown文件处理器
Markdown File Processor for Trademark Rules

处理商标相关的Markdown格式法律法规文件：
1. 文件内容提取
2. 结构化解析（章、节、条）
3. 元数据提取
4. 文本分块

作者: Athena AI系统
创建时间: 2025-01-15
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MarkdownProcessor:
    """Markdown文件处理器"""

    def __init__(self, config: dict[str, Any] | None = None):
        """
        初始化处理器

        Args:
            config: 配置字典，包含：
                - data_dir: 数据目录路径
                - output_dir: 输出目录
                - chunk_size: 文本分块大小（默认1000字符）
                - chunk_overlap: 分块重叠大小（默认200字符）
        """
        self.config = config or {}
        self.data_dir = Path(self.config.get('data_dir', './data/商标'))
        self.output_dir = Path(self.config.get('output_dir', './data/trademark_rules/processed'))
        self.chunk_size = self.config.get('chunk_size', 1000)
        self.chunk_overlap = self.config.get('chunk_overlap', 200)

        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_chunks': 0,
            'total_articles': 0
        }

    async def process_directory(self) -> dict[str, Any]:
        """
        处理整个目录的Markdown文件

        Returns:
            处理结果字典
        """
        logger.info(f"🔄 开始处理目录: {self.data_dir}")

        # 获取所有MD文件
        md_files = list(self.data_dir.glob('*.md'))
        self.stats['total_files'] = len(md_files)

        logger.info(f"📁 找到 {len(md_files)} 个MD文件")

        all_documents = []

        for md_file in md_files:
            logger.info(f"📄 处理文件: {md_file.name}")
            try:
                doc_data = await self.process_single_file(md_file)
                if doc_data:
                    all_documents.append(doc_data)
                    self.stats['processed_files'] += 1
            except Exception as e:
                logger.error(f"❌ 处理文件失败 {md_file.name}: {e}")
                self.stats['failed_files'] += 1

        # 保存汇总结果
        summary_file = self.output_dir / 'documents_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump({
                'documents': all_documents,
                'stats': self.stats,
                'created_at': datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 汇总结果已保存: {summary_file}")
        logger.info(f"📊 处理完成: {self.stats['processed_files']}/{self.stats['total_files']} 成功")

        return {
            'status': 'success',
            'stats': self.stats,
            'documents': all_documents,  # 添加documents列表
            'documents_count': len(all_documents),
            'summary_file': str(summary_file)
        }

    async def process_single_file(self, file_path: Path) -> dict[str, Any | None]:
        """
        处理单个Markdown文件

        Args:
            file_path: 文件路径

        Returns:
            文档数据字典
        """
        try:
            # 读取文件内容
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # 提取元数据
            metadata = self._extract_metadata(file_path, content)

            # 解析结构（章、节、条）
            structure = self._parse_structure(content)

            # 文本分块
            chunks = self._chunk_content(content, metadata)

            # 构建文档数据
            doc_data = {
                'file_name': file_path.name,
                'file_path': str(file_path),
                'metadata': metadata,
                'structure': structure,
                'chunks': chunks,
                'total_chunks': len(chunks),
                'total_articles': len(structure.get('articles', [])),
                'created_at': datetime.now().isoformat()
            }

            self.stats['total_chunks'] += len(chunks)
            self.stats['total_articles'] += len(structure.get('articles', []))

            logger.info(f"✅ {file_path.name}: {len(chunks)} 块, {len(structure.get('articles', []))} 条")

            return doc_data

        except Exception as e:
            logger.error(f"❌ 处理文件失败 {file_path.name}: {e}")
            return None

    def _extract_metadata(self, file_path: Path, content: str) -> dict[str, Any]:
        """
        提取文件元数据

        Args:
            file_path: 文件路径
            content: 文件内容

        Returns:
            元数据字典
        """
        # 从文件名提取信息
        name_parts = file_path.stem.split('_')

        metadata = {
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'document_type': 'unknown',
            'issuing_authority': 'unknown',
            'issue_date': None,
            'effective_date': None
        }

        # 根据文件名判断类型
        if '商标法' in file_path.name:
            metadata['document_type'] = '法律'
            metadata['issuing_authority'] = '全国人民代表大会'
        elif '实施条例' in file_path.name:
            metadata['document_type'] = '行政法规'
            metadata['issuing_authority'] = '国务院'
        elif '审理指南' in file_path.name:
            metadata['document_type'] = '审理指南'
            if '北京' in file_path.name:
                metadata['issuing_authority'] = '北京市高级人民法院'
            else:
                metadata['issuing_authority'] = '国家知识产权局'
        elif '最高人民法院' in file_path.name:
            metadata['document_type'] = '司法解释'
            metadata['issuing_authority'] = '最高人民法院'

        # 提取日期
        date_match = re.search(r'(\d{8})', file_path.name)
        if date_match:
            date_str = date_match.group(1)
            try:
                metadata['issue_date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

        return metadata

    def _parse_structure(self, content: str) -> dict[str, Any]:
        """
        解析文档结构（章、节、条）

        Args:
            content: 文件内容

        Returns:
            结构化数据
        """
        structure = {
            'chapters': [],
            'articles': []
        }

        lines = content.split('\n')
        current_chapter = None
        current_section = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测章标题
            if line.startswith('# 第') and '章' in line:
                chapter_match = re.match(r'#+\s*(第[一二三四五六七八九十\d]+章)\s*(.*)', line)
                if chapter_match:
                    current_chapter = {
                        'number': chapter_match.group(1),
                        'title': chapter_match.group(2).strip(),
                        'sections': []
                    }
                    structure['chapters'].append(current_chapter)

            # 检测节标题
            elif line.startswith('##') and '节' in line:
                section_match = re.match(r'#+\s*(\S+节)\s*(.*)', line)
                if section_match and current_chapter:
                    current_section = {
                        'number': section_match.group(1),
                        'title': section_match.group(2).strip()
                    }
                    current_chapter['sections'].append(current_section)

            # 检测条（法律条款）
            elif re.match(r'^第[一二三四五六七八九十\d]+条[、\s]', line):
                article_match = re.match(r'(第[一二三四五六七八九十\d]+条)[、\s]*(.*)', line)
                if article_match:
                    article = {
                        'number': article_match.group(1),
                        'content': article_match.group(2).strip(),
                        'chapter': current_chapter['title'] if current_chapter else None
                    }
                    structure['articles'].append(article)

        return structure

    def _chunk_content(
        self,
        content: str,
        metadata: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """
        将内容分块

        Args:
            content: 文件内容
            metadata: 元数据

        Returns:
            文本块列表
        """
        chunks = []
        current_chunk = ""
        chunk_id = 0

        # 按段落分割
        paragraphs = content.split('\n\n')

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # 如果当前块加上新段落超过大小限制
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk:
                    chunk_data = self._create_chunk(
                        current_chunk, chunk_id, metadata
                    )
                    chunks.append(chunk_data)
                    chunk_id += 1

                    # 保留重叠部分
                    overlap_text = current_chunk[-self.chunk_overlap:] if self.chunk_overlap > 0 else ""
                    current_chunk = overlap_text + para
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        # 保存最后一个块
        if current_chunk:
            chunk_data = self._create_chunk(current_chunk, chunk_id, metadata)
            chunks.append(chunk_data)

        return chunks

    def _create_chunk(
        self,
        text: str,
        chunk_id: int,
        metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """
        创建文本块

        Args:
            text: 文本内容
            chunk_id: 块ID
            metadata: 元数据

        Returns:
            文本块字典
        """
        chunk_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]

        return {
            'chunk_id': chunk_id,
            'chunk_hash': chunk_hash,
            'text': text,
            'char_count': len(text),
            'metadata': {
                'document_type': metadata.get('document_type'),
                'issuing_authority': metadata.get('issuing_authority'),
                'issue_date': metadata.get('issue_date')
            }
        }


async def main():
    """主函数 - 使用示例"""
    # 配置处理器
    config = {
        'data_dir': './data/商标',
        'output_dir': './data/trademark_rules/processed',
        'chunk_size': 1000,
        'chunk_overlap': 200
    }

    # 创建并运行处理器
    processor = MarkdownProcessor(config)
    result = await processor.process_directory()

    print("\n" + "="*50)
    print("📊 处理完成！")
    print("="*50)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
