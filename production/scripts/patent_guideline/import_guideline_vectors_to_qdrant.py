#!/usr/bin/env python3
"""
将专利审查指南396个小节向量导入Qdrant

作者: Athena平台团队
创建时间: 2025-12-23
"""

from __future__ import annotations
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/qdrant_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class GuidelineQdrantImporter:
    """专利审查指南Qdrant导入器"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.base_dir / "production/data/patent_rules"
        self.qdrant_client = None

        logger.info("专利审查指南Qdrant导入器初始化完成")

    async def initialize_qdrant(self):
        """初始化Qdrant客户端"""
        logger.info("=" * 60)
        logger.info("🚀 初始化Qdrant客户端")
        logger.info("=" * 60)

        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self.qdrant_client = QdrantClient(url="http://localhost:6333")

            # 创建集合
            collection_name = "patent_guidelines"

            # 检查集合是否存在
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
                )
                logger.info(f"✅ Qdrant集合已创建: {collection_name}")
            else:
                logger.info(f"✅ Qdrant集合已存在: {collection_name}")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ Qdrant初始化失败: {e}")
            raise

    def load_vectors(self) -> list[dict[str, Any]]:
        """加载生成的向量"""
        logger.info("📦 加载BGE向量...")

        vectors_dir = self.data_dir / "vectors"
        vector_files = sorted(vectors_dir.glob("guideline_bge_vectors_*.json"))

        if not vector_files:
            logger.error("找不到向量文件")
            return []

        # 使用最新的向量文件
        latest_file = vector_files[-1]
        logger.info(f"📄 加载文件: {latest_file}")

        with open(latest_file, encoding='utf-8') as f:
            data = json.load(f)

        vectors = data.get('vectors', [])
        logger.info(f"✅ 加载了 {len(vectors)} 个向量")

        return vectors

    def load_chunks(self) -> list[dict[str, Any]]:
        """加载小节数据"""
        logger.info("📦 加载小节数据...")

        legal_docs_dir = self.data_dir / "legal_documents"
        vector_files = sorted(legal_docs_dir.glob("guideline_vectors_input_*.json"))

        if not vector_files:
            logger.error("找不到小节数据文件")
            return []

        # 使用最新的文件
        latest_file = vector_files[-1]
        logger.info(f"📄 加载文件: {latest_file}")

        with open(latest_file, encoding='utf-8') as f:
            data = json.load(f)

        chunks = data.get('chunks', [])
        logger.info(f"✅ 加载了 {len(chunks)} 个小节")

        return chunks

    async def import_to_qdrant(self, vectors: list[dict], chunks: list[dict]):
        """导入到Qdrant"""
        logger.info("=" * 60)
        logger.info(f"📤 导入 {len(vectors)} 个向量到Qdrant")
        logger.info("=" * 60)

        # 创建chunk_id到chunk的映射
        chunk_map = {chunk['chunk_id']: chunk for chunk in chunks}

        # 准备Qdrant点
        points = []
        for vec in vectors:
            chunk_id = vec['chunk_id']
            chunk = chunk_map.get(chunk_id)

            if not chunk:
                logger.warning(f"⚠️ 找不到小节数据: {chunk_id}")
                continue

            # 生成数值ID
            hash_id = abs(hash(chunk_id)) % (10 ** 10)

            points.append({
                'id': hash_id,
                'vector': vec['embedding'],
                'payload': {
                    'chunk_id': chunk_id,
                    'text': chunk['text'][:1000],  # 保存前1000字符
                    'part': chunk['metadata'].get('part', ''),
                    'chapter': chunk['metadata'].get('chapter', ''),
                    'section': chunk['metadata'].get('section', ''),
                    'subsection': chunk['metadata'].get('subsection', ''),
                    'title': chunk['metadata'].get('title', ''),
                    'word_count': chunk['metadata'].get('word_count', 0)
                }
            })

        logger.info(f"📊 准备导入 {len(points)} 个点")

        # 批量上传
        batch_size = 100
        total_batches = (len(points) + batch_size - 1) // batch_size

        from qdrant_client.models import PointStruct

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(points))

            batch_points = points[start_idx:end_idx]

            qdrant_points = [
                PointStruct(
                    id=p['id'],
                    vector=p['vector'],
                    payload=p['payload']
                )
                for p in batch_points
            ]

            try:
                self.qdrant_client.upsert(
                    collection_name="patent_guidelines",
                    points=qdrant_points
                )

                progress = (batch_idx + 1) / total_batches * 100
                logger.info(f"✅ 批次 {batch_idx + 1}/{total_batches} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx} 失败: {e}")

        logger.info("=" * 60)
        logger.info("✅ Qdrant导入完成")
        logger.info("=" * 60)

        # 验证导入
        collection_info = self.qdrant_client.get_collection("patent_guidelines")
        logger.info("📊 集合状态:")
        logger.info(f"   状态: {collection_info.status}")
        logger.info(f"   点数量: {collection_info.points_count}")
        logger.info(f"   配置: 向量维度={collection_info.config.params.vectors.size}, 距离={collection_info.config.params.vectors.distance}")

    async def run(self):
        """运行导入流程"""
        try:
            # 初始化Qdrant
            await self.initialize_qdrant()

            # 加载数据
            vectors = self.load_vectors()
            chunks = self.load_chunks()

            if not vectors or not chunks:
                logger.error("数据加载失败")
                return

            # 导入Qdrant
            await self.import_to_qdrant(vectors, chunks)

            logger.info("=" * 60)
            logger.info("🎉 导入流程完成！")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 导入流程失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    importer = GuidelineQdrantImporter()
    await importer.run()


if __name__ == "__main__":
    asyncio.run(main())
