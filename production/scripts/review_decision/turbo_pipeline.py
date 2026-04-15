#!/usr/bin/env python3
"""
高速批处理管道 - 优化版本
目标: 在Claude Code窗口内完成6万份文档处理

优化策略:
1. 增大批次大小 (500 -> 2000)
2. 向量批次优化 (32 -> 128)
3. Qdrant上传批次优化 (100 -> 500)
4. 减少日志输出
5. 预加载模型

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
import subprocess

# 添加项目路径
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any

from docx import Document

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# 导入项目现有服务
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from core.nlp.bge_embedding_service import BGEEmbeddingService

# 简化日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/turbo_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class TurboDecisionPipeline:
    """高速批处理管道"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.review_dir = Path("/Volumes/AthenaData/语料/专利/专利复审决定原文")
        self.invalid_dir = Path("/Volumes/AthenaData/语料/专利/专利无效宣告原文")
        self.output_dir = self.base_dir / "production/data/patent_decisions"
        self.checkpoint_dir = self.output_dir / "checkpoints"

        # 服务
        self.bge_service = None
        self.qdrant_client = None
        self.executor = ThreadPoolExecutor(max_workers=4)  # 并行文件提取

        # 正则模式
        self.patterns = {
            'decision_number': re.compile(r'第(\d+)号'),
            'decision_date': re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日'),
            'law_reference': re.compile(r'(专利法|实施细则)[\s\u3000]*第?([\d一二三四五六七八九十]+)[条条款款]'),
        }

        # 检查点
        self.checkpoint = self._load_checkpoint()

        # 性能统计
        self.stats = {
            'files_processed': 0,
            'chunks_created': 0,
            'vectors_generated': 0,
            'start_time': time.time()
        }

        logger.info("🚀 高速批处理管道初始化完成")

    def _load_checkpoint(self) -> dict[str, Any]:
        """加载检查点"""
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = self.checkpoint_dir / "progress.json"

        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                return json.load(f)
        return {
            'processed_files': [],
            'total_chunks': 0,
            'total_vectors': 0,
            'qdrant_uploaded': 0
        }

    def _save_checkpoint(self) -> Any:
        """保存检查点"""
        checkpoint_file = self.checkpoint_dir / "progress.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    async def initialize_services(self):
        """初始化服务"""
        logger.info("初始化服务...")

        # BGE服务 - 预加载
        try:
            model_path = self.base_dir / "models/converted/bge-large-zh-v1.5"
            if not model_path.exists():
                model_path = self.base_dir / "models/bge-large-zh-v1.5"

            config = {
                "model_path": str(model_path),
                "device": "cpu",
                "batch_size": 128,  # 增大批次
                "max_length": 512,
                "normalize_embeddings": True,
                "cache_enabled": True,
                "preload": True  # 预加载
            }

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务就绪: {health['dimension']}维")

        except Exception as e:
            logger.error(f"❌ BGE初始化失败: {e}")
            raise

        # Qdrant客户端
        try:
            self.qdrant_client = QdrantClient(url="http://localhost:6333", timeout=60)
            collection_name = "patent_decisions"

            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info("✅ 创建Qdrant集合")
            else:
                info = self.qdrant_client.get_collection(collection_name)
                logger.info(f"✅ Qdrant集合: {info.points_count}点")

        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            raise

    def extract_from_docx(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOCX提取文本"""
        try:
            doc = Document(str(file_path))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            full_text = "\n".join(paragraphs)

            metadata = {
                'filename': file_path.name,
                'doc_id': file_path.stem,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs)
            }

            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception:
            return "", {}

    def extract_from_doc(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """从DOC文件提取"""
        try:
            result = subprocess.run([
                'textutil', '-convert', 'txt', '-stdout', str(file_path)
            ], capture_output=True, text=True, timeout=20)

            full_text = result.stdout

            if not full_text or not full_text.strip():
                return "", {}

            # 清理
            full_text = re.sub(r'FORMTEXT\s*', '', full_text)
            full_text = re.sub(r'FORMCHECKBOX\s*', '', full_text)
            full_text = re.sub(r'\n\s*\n\s*\n', '\n\n', full_text)
            full_text = re.sub(r'\t+', ' ', full_text)
            full_text = re.sub(r' +', ' ', full_text)

            paragraphs = [line.strip() for line in full_text.split('\n') if line.strip() and len(line.strip()) > 1]
            full_text = "\n".join(paragraphs)

            metadata = {
                'filename': file_path.name,
                'doc_id': file_path.stem,
                'file_size': file_path.stat().st_size,
                'paragraph_count': len(paragraphs),
                'file_format': 'doc'
            }

            match = self.patterns['decision_number'].search(full_text)
            if match:
                metadata['decision_number'] = match.group(1)

            match = self.patterns['decision_date'].search(full_text)
            if match:
                metadata['decision_date'] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"

            return full_text, metadata

        except Exception:
            return "", {}

    def chunk_decision_text(self, text: str, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        """将决定书分块"""
        if not text:
            return []

        doc_id = metadata.get('doc_id', 'unknown')
        lines = text.split('\n')

        chunks = []
        current_section = "未分类"
        current_content = []

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

            current_content.append(line)

        if current_content:
            chunks.append(self._create_chunk(doc_id, current_section, current_content, metadata))

        return chunks

    def _create_chunk(self, doc_id: str, section: str, content: list[str],
                     metadata: dict[str, Any]) -> dict[str, Any]:
        """创建数据块"""
        content_text = "\n".join(content)

        block_type_map = {
            '决定要点': 'keypoints',
            '案由': 'background',
            '决定的理由': 'reasoning',
            '理由': 'reasoning',
            '决定': 'decision'
        }
        block_type = block_type_map.get(section, 'other')

        chunk_hash = short_hash(f"{doc_id}_{section}_{len(content_text)}".encode())[:8]
        chunk_id = f"dec_{doc_id}_{chunk_hash}"

        law_refs = self.patterns['law_reference'].findall(content_text)
        law_refs_cleaned = [f"{law} {art}" for law, art in law_refs]

        return {
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
                'law_references': law_refs_cleaned,
                'related_laws': [ref for ref in law_refs_cleaned if '专利法' in ref or '实施细则' in ref]
            }
        }

    def _extract_file(self, file_path: Path) -> tuple[str, dict[str, Any]]:
        """提取单个文件（用于并行处理）"""
        if file_path.suffix.lower() == '.docx':
            return self.extract_from_docx(file_path)
        elif file_path.suffix.lower() == '.doc':
            return self.extract_from_doc(file_path)
        return "", {}

    async def _extract_files_parallel(self, file_paths: list[Path]) -> list[tuple[str, dict[str, Any]]]:
        """并行提取文件"""
        loop = asyncio.get_event_loop()
        tasks = [loop.run_in_executor(self.executor, self._extract_file, f) for f in file_paths]
        return await asyncio.gather(*tasks)

    async def process_batch(self, file_paths: list[Path], batch_index: int, total_batches: int) -> dict[str, Any]:
        """处理一个批次"""
        batch_start = time.time()

        # 过滤已处理
        processed_set = set(self.checkpoint['processed_files'])
        files_to_process = [f for f in file_paths if str(f) not in processed_set]

        if not files_to_process:
            return {'skipped': True}

        logger.info(f"[{batch_index+1}/{total_batches}] 处理 {len(files_to_process)} 文件...")

        all_chunks = []
        failed_count = 0

        # 并行提取
        extract_results = await self._extract_files_parallel(files_to_process)

        for file_path, (text, metadata) in zip(files_to_process, extract_results, strict=False):
            if not text:
                failed_count += 1
                continue

            chunks = self.chunk_decision_text(text, metadata)
            all_chunks.extend(chunks)

        extract_time = time.time() - batch_start

        if not all_chunks:
            return {'skipped': True}

        # 生成向量
        texts = [chunk['text'] for chunk in all_chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in all_chunks]

        vector_batch_size = 128  # 增大批次
        vectors = []

        for i in range(0, len(texts), vector_batch_size):
            batch_texts = texts[i:i + vector_batch_size]
            batch_ids = chunk_ids[i:i + vector_batch_size]

            response = await self.bge_service.encode(batch_texts, task_type="patent_decision")

            for chunk_id, embedding in zip(batch_ids, response.embeddings, strict=False):
                vectors.append({
                    'chunk_id': chunk_id,
                    'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding)
                })

        vector_time = time.time() - batch_start - extract_time

        # 上传Qdrant
        points = []
        for chunk, vec in zip(all_chunks, vectors, strict=False):
            hash_id = abs(hash(vec['chunk_id'])) % (10 ** 10)
            payload = {
                'chunk_id': vec['chunk_id'],
                'doc_id': chunk['doc_id'],
                'block_type': chunk['block_type'],
                'section': chunk['section'],
                'text': chunk['text'][:500],
                'decision_date': chunk['metadata'].get('decision_date', ''),
                'decision_number': chunk['metadata'].get('decision_number', ''),
                'char_count': chunk['metadata'].get('char_count', 0),
                'law_references': chunk['metadata'].get('law_references', []),
                'source': 'patent_decision',
                'related_laws': chunk['metadata'].get('related_laws', [])
            }
            points.append(PointStruct(id=hash_id, vector=vec['embedding'], payload=payload))

        # 批量上传
        upsert_batch_size = 500  # 增大批次
        for i in range(0, len(points), upsert_batch_size):
            batch_points = points[i:i + upsert_batch_size]
            self.qdrant_client.upsert(collection_name="patent_decisions", points=batch_points)

        upload_time = time.time() - batch_start - extract_time - vector_time

        # 更新检查点
        for file_path in files_to_process:
            self.checkpoint['processed_files'].append(str(file_path))

        self.checkpoint['total_chunks'] += len(all_chunks)
        self.checkpoint['total_vectors'] += len(vectors)
        self.checkpoint['qdrant_uploaded'] += len(points)
        self._save_checkpoint()

        # 更新统计
        self.stats['files_processed'] += len(files_to_process)
        self.stats['chunks_created'] += len(all_chunks)
        self.stats['vectors_generated'] += len(vectors)

        batch_time = time.time() - batch_start
        speed = len(files_to_process) / batch_time if batch_time > 0 else 0

        logger.info(f"  完成: {len(all_chunks)}块, {len(vectors)}向量 | "
                   f"速度: {speed:.1f}文件/秒 | "
                   f"累计: {self.stats['files_processed']}文件, {self.stats['vectors_generated']}向量")

        return {
            'files_processed': len(files_to_process),
            'chunks_created': len(all_chunks),
            'vectors_generated': len(vectors),
            'batch_time': batch_time
        }

    async def run_full_pipeline(self, batch_size: int = 2000):
        """运行完整管道"""
        logger.info("=" * 70)
        logger.info("🚀 高速批处理管道启动")
        logger.info("=" * 70)

        await self.initialize_services()

        # 获取所有文件
        review_docx = list(self.review_dir.glob("*.docx"))
        review_doc = list(self.review_dir.glob("*.doc"))
        invalid_docx = list(self.invalid_dir.glob("*.docx"))
        invalid_doc = list(self.invalid_dir.glob("*.doc"))

        all_files = review_docx + review_doc + invalid_docx + invalid_doc

        logger.info("📊 文件统计:")
        logger.info(f"   复审决定 .docx: {len(review_docx)}")
        logger.info(f"   复审决定 .doc: {len(review_doc)}")
        logger.info(f"   无效宣告 .docx: {len(invalid_docx)}")
        logger.info(f"   无效宣告 .doc: {len(invalid_doc)}")
        logger.info(f"   总计: {len(all_files)}")

        total_batches = (len(all_files) + batch_size - 1) // batch_size
        logger.info(f"   批次数: {total_batches} (批次大小: {batch_size})")
        logger.info("")

        results = []
        start_time = time.time()

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(all_files))
            batch_files = all_files[start_idx:end_idx]

            try:
                result = await self.process_batch(batch_files, batch_idx, total_batches)
                if not result.get('skipped'):
                    results.append(result)

                # 进度报告
                elapsed = time.time() - start_time
                progress = (batch_idx + 1) / total_batches * 100
                avg_speed = self.stats['files_processed'] / elapsed if elapsed > 0 else 0
                remaining_files = len(all_files) - self.stats['files_processed']
                eta = remaining_files / avg_speed if avg_speed > 0 else 0

                logger.info(f"  进度: {progress:.1f}% | 已用: {elapsed/60:.1f}分钟 | "
                           f"预计剩余: {eta/60:.1f}分钟")
                logger.info("")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx + 1} 失败: {e}")
                continue

        # 最终报告
        total_time = time.time() - start_time
        logger.info("=" * 70)
        logger.info("🎉 处理完成！")
        logger.info("=" * 70)
        logger.info(f"📊 处理文件: {self.stats['files_processed']}/{len(all_files)}")
        logger.info(f"📦 生成块: {self.stats['chunks_created']}")
        logger.info(f"🔢 生成向量: {self.stats['vectors_generated']}")
        logger.info(f"⏱️  总耗时: {total_time/60:.1f}分钟 ({total_time/3600:.2f}小时)")
        logger.info(f"⚡ 平均速度: {self.stats['files_processed']/total_time:.1f} 文件/秒")

        # 验证Qdrant
        try:
            info = self.qdrant_client.get_collection("patent_decisions")
            logger.info(f"✅ Qdrant集合: {info.points_count}点")
        except Exception as e:
            logger.warning(f"验证失败: {e}")


async def main():
    """主函数"""
    pipeline = TurboDecisionPipeline()
    await pipeline.run_full_pipeline(batch_size=2000)


if __name__ == "__main__":
    asyncio.run(main())
