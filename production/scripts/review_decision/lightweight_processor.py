#!/usr/bin/env python3
"""
轻量级复审决定书处理器
使用项目现有NLP服务，无需下载新模型

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import json
import logging
import re

# 添加项目路径
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 导入项目现有NLP服务
from core.nlp.bge_embedding_service import BGEEmbeddingService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/lightweight_processor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class LightweightDecisionProcessor:
    """轻量级决定书处理器 - 使用现有BGE服务"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.review_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")
        self.invalid_dir = Path("/Volumes/AthenaData/语料/专利/专利无效宣告原文")
        self.output_dir = self.base_dir / "production/data/patent_decisions"

        # BGE服务（复用现有）
        self.bge_service = None

        # 正则模式（简化版）
        self.patterns = {
            'decision_number': re.compile(r'第(\d+)号'),
            'decision_date': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            'law_reference': re.compile(r'(专利法|实施细则)[\s\u3000]*第?([\d一二三四五六七八九十]+)[条条款款]'),
            'section_cn': re.compile(r'^([一二三四五六七八九十]+)、([^。]{2,30}?)[：:]\s*$'),
            'section_num': re.compile(r'^(\d+)、([^。]{2,30}?)[：:]\s*$'),
        }

        logger.info("轻量级决定书处理器初始化完成")

    async def initialize_bge(self):
        """初始化BGE服务（复用现有模型）"""
        logger.info("🔄 初始化BGE嵌入服务...")

        try:
            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 32,
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": False  # 快速启动
            }

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            logger.info("✅ BGE服务已就绪")
            return True

        except Exception as e:
            logger.warning(f"BGE初始化失败: {e}")
            return False

    def extract_text_from_docx(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOCX提取文本和元数据"""
        try:
            doc = Document(str(file_path))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

            full_text = "\n".join(paragraphs)

            # 提取元数据
            metadata = {
                'filename': file_path.name,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs),
                'doc_id': file_path.stem
            }

            # 提取决定号和日期
            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception as e:
            logger.error(f"DOCX提取失败 {file_path.name}: {e}")
            return "", {}

    def chunk_decision_text(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """将决定书文本分块"""
        if not text:
            return []

        doc_id = metadata.get('doc_id', 'unknown')
        lines = text.split('\n')

        chunks = []
        current_section = "未分类"
        current_content = []

        # 主章节识别
        main_sections = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检测主章节
            matched = False
            for section_name, _block_type in main_sections.items():
                if section_name in line:
                    if current_content:
                        chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))
                    current_section = section_name
                    current_content = []
                    matched = True
                    break

            if matched:
                continue

            # 累积内容
            current_content.append(line)

        # 保存最后一块
        if current_content:
            chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))

        return chunks

    def _create_chunk(self, doc_id: str, section: str, content: list[str],
                     metadata: dict[str, Any]) -> dict[str, Any]:
        """创建数据块"""
        content_text = "\n".join(content)

        # 确定块类型
        block_type_map = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }
        block_type = block_type_map.get(section, 'other')

        # 生成ID
        chunk_id_suffix = short_hash(f"{doc_id}_{section}_{len(content_text)}".encode())[:8]
        chunk_id = f"dec_{doc_id}_{chunk_id_suffix}"

        # 提取法律引用
        law_refs = self.patterns['law_reference'].findall(content_text)

        chunk = {
            'chunk_id': chunk_id,
            'doc_id': doc_id,
            'block_type': block_type,
            'section': section,
            'text': content_text,
            'metadata': {
                'filename': metadata.get('filename', ''),
                'decision_date': metadata.get('decision_date', ''),
                'decision_number': metadata.get('decision_number', ''),
                'char_count': len(content_text),
                'law_references': [f"{law} {art}" for law, art in law_refs]
            }
        }

        return chunk

    async def process_files(self, file_paths: list[Path], batch_name: str,
                           generate_vectors: bool = True) -> dict[str, Any]:
        """批量处理文件"""
        logger.info("=" * 60)
        logger.info(f"📦 处理批次: {batch_name}")
        logger.info(f"   文件数: {len(file_paths)}")
        logger.info("=" * 60)

        all_chunks = []
        failed_files = []

        # 提取所有块
        for i, file_path in enumerate(file_paths):
            if (i + 1) % 500 == 0:
                logger.info(f"   进度: {i + 1}/{len(file_paths)}")

            try:
                text, metadata = self.extract_text_from_docx(file_path)
                if not text:
                    failed_files.append((file_path.name, "empty"))
                    continue

                chunks = self.chunk_decision_text(text, metadata)
                all_chunks.extend(chunks)

            except Exception as e:
                failed_files.append((file_path.name, str(e)))

        logger.info(f"✅ 提取完成: {len(file_paths) - len(failed_files)} 个文件, {len(all_chunks)} 个块")

        # 保存块数据
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunks_file = self.output_dir / "processed" / f"{batch_name}_chunks_{timestamp}.json"
        chunks_file.parent.mkdir(parents=True, exist_ok=True)

        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({
                'batch_name': batch_name,
                'processed_at': datetime.now().isoformat(),
                'total_files': len(file_paths),
                'successful_files': len(file_paths) - len(failed_files),
                'total_chunks': len(all_chunks),
                'failed_files': failed_files,
                'chunks': all_chunks
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"📄 块数据: {chunks_file}")

        # 生成向量（可选）
        if generate_vectors and self.bge_service:
            vectors = await self._generate_vectors(all_chunks)
            logger.info(f"📊 生成向量: {len(vectors)} 个")

            # 保存向量数据
            vectors_file = self.output_dir / "vectors" / f"{batch_name}_vectors_{timestamp}.json"
            vectors_file.parent.mkdir(parents=True, exist_ok=True)

            with open(vectors_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'generated_at': datetime.now().isoformat(),
                    'total_chunks': len(all_chunks),
                    'vectors_generated': len(vectors),
                    'vectors': vectors
                }, f, ensure_ascii=False, indent=2)

            logger.info(f"📄 向量数据: {vectors_file}")

        return {
            'total_files': len(file_paths),
            'successful_files': len(file_paths) - len(failed_files),
            'total_chunks': len(all_chunks),
            'failed_files': failed_files,
            'chunks_file': str(chunks_file)
        }

    async def _generate_vectors(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """生成向量（使用现有BGE服务）"""
        texts = [chunk['text'] for chunk in chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in chunks]

        batch_size = 32
        results = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_ids = chunk_ids[i:i + batch_size]

            try:
                response = await self.bge_service.encode(batch_texts, task_type="patent_decision")

                for chunk_id, embedding in zip(batch_ids, response.embeddings, strict=False):
                    results.append({
                        'chunk_id': chunk_id,
                        'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                    })

            except Exception as e:
                logger.warning(f"批次向量生成失败: {e}")

        return results


async def main():
    """主函数 - 处理样本"""
    processor = LightweightDecisionProcessor()

    # 初始化BGE
    await processor.initialize_bge()

    # 获取样本文件
    review_files = list(processor.review_dir.glob("*.docx"))[:100]  # 处理100个样本

    logger.info(f"📋 处理样本: {len(review_files)} 个复审决定文件")

    result = await processor.process_files(
        review_files,
        "review_sample_100",
        generate_vectors=True
    )

    logger.info("=" * 60)
    logger.info("🎉 处理完成！")
    logger.info(f"📊 成功: {result['successful_files']}/{result['total_files']}")
    logger.info(f"📦 块数: {result['total_chunks']}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
