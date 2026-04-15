#!/usr/bin/env python3
"""
导入processed patent rules数据到Qdrant
将processed目录的2,694个chunks全量导入到patent_rules_complete集合

作者: 小诺·双鱼公主
创建时间: 2025-12-26
"""

from __future__ import annotations
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/import_patent_rules_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class PatentRulesImporter:
    """专利规则导入器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.processed_dir = self.base_dir / "production/data/patent_rules/processed"
        self.qdrant_client = None

    def initialize_qdrant(self) -> Any:
        """初始化Qdrant客户端"""
        logger.info("🚀 初始化Qdrant客户端...")

        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams

        self.qdrant_client = QdrantClient(url="http://localhost:6333")

        # 确保集合存在
        collection_name = "patent_rules_complete"
        collections = self.qdrant_client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            logger.info(f"创建集合: {collection_name}")
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
            )
        else:
            logger.info(f"集合已存在: {collection_name}")

        return True

    def load_processed_chunks(self) -> list:
        """加载所有processed chunks"""
        logger.info("📦 加载processed chunks...")

        all_chunks = []

        for json_file in sorted(self.processed_dir.glob('legal_chunks_*.json')):
            try:
                logger.info(f"  读取: {json_file.name}")
                with open(json_file) as f:
                    data = json.load(f)

                chunks = data.get('chunks', [])
                # 为每个chunk添加JSON文件名标识以避免ID冲突
                json_file_name = json_file.stem  # 去掉.json后缀
                for chunk in chunks:
                    chunk['_json_file'] = json_file_name

                all_chunks.extend(chunks)
                logger.info(f"    ✓ {len(chunks)} chunks")

            except Exception as e:
                logger.error(f"    ✗ 错误: {e}")

        logger.info(f"✅ 总共加载 {len(all_chunks)} 个chunks")
        return all_chunks

    async def import_to_qdrant(self, chunks: list):
        """导入到Qdrant"""
        logger.info("=" * 60)
        logger.info(f"📤 开始导入 {len(chunks)} 个chunks到Qdrant")
        logger.info("=" * 60)

        # 初始化BGE服务
        from core.nlp.bge_embedding_service import BGEEmbeddingService

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
            "preload": True
        }

        bge_service = BGEEmbeddingService(config)
        await bge_service.initialize()

        # 批量处理
        batch_size = 32
        total_batches = (len(chunks) + batch_size - 1) // batch_size

        from qdrant_client.models import PointStruct

        points = []
        imported_count = 0

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(chunks))

            batch_chunks = chunks[start_idx:end_idx]
            texts = [chunk['content'] for chunk in batch_chunks]

            try:
                # 生成向量
                result = await bge_service.encode(texts, task_type="patent_rule")

                # 创建点 - 使用JSON文件名确保唯一性
                for _i, (chunk, embedding) in enumerate(zip(batch_chunks, result.embeddings, strict=False)):
                    chunk_id = chunk['chunk_id']
                    json_file = chunk.get('_json_file', 'unknown')
                    # 使用JSON文件名+chunk_id确保唯一性
                    unique_id = f"{json_file}_{chunk_id}"
                    # 使用安全哈希避免冲突
                    hash_id = int(short_hash(unique_id.encode('utf-8'), 8), 16)

                    points.append(PointStruct(
                        id=hash_id,
                        vector=embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                        payload={
                            'chunk_id': chunk_id,
                            'doc_id': chunk.get('doc_id', ''),
                            'doc_type': chunk.get('doc_type', ''),
                            'title': chunk.get('title', '')[:200],
                            'content': chunk['content'][:500],
                            'chunk_index': chunk.get('chunk_index', 0),
                            'source_file': chunk.get('metadata', {}).get('source_file', '')
                        }
                    ))

                # 每100个点上传一次
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name="patent_rules_complete",
                        points=points
                    )
                    imported_count += len(points)
                    logger.info(f"  已上传 {len(points)} 个点，总计 {imported_count}/{len(chunks)}")
                    points = []

                progress = (batch_idx + 1) / total_batches * 100
                if (batch_idx + 1) % 10 == 0:
                    logger.info(f"✅ 批次 {batch_idx + 1}/{total_batches} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx} 失败: {e}")

        # 上传剩余的点
        if points:
            self.qdrant_client.upsert(
                collection_name="patent_rules_complete",
                points=points
            )
            imported_count += len(points)
            logger.info(f"  已上传 {len(points)} 个点，总计 {imported_count}/{len(chunks)}")

        logger.info("✅ 导入完成")

        # 验证
        collection_info = self.qdrant_client.get_collection("patent_rules_complete")
        logger.info("📊 集合状态:")
        logger.info(f"   点数量: {collection_info.points_count}")
        logger.info(f"   向量维度: {collection_info.config.params.vectors.size}")

    async def run(self):
        """运行导入流程"""
        logger.info("=" * 60)
        logger.info("🚀 启动专利规则导入器")
        logger.info("=" * 60)

        try:
            # 初始化Qdrant
            self.initialize_qdrant()

            # 加载数据
            chunks = self.load_processed_chunks()

            if not chunks:
                logger.error("❌ 没有数据可导入")
                return

            # 导入到Qdrant
            await self.import_to_qdrant(chunks)

            logger.info("=" * 60)
            logger.info("🎉 导入完成！")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    importer = PatentRulesImporter()
    await importer.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
