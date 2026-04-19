#!/usr/bin/env python3
"""
专利复审决定书全量处理管道
解析DOCX文件 -> 分块 -> BGE向量 -> Qdrant导入 -> NebulaGraph导出

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
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/decision_pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class DecisionPipeline:
    """决定书处理管道"""

    def __init__(self):
        self.base_dir = Path("/Users/xujian/Athena工作平台")
        self.data_dir = self.base_dir / "production/data/patent_decisions"

        # BGE服务
        self.bge_service = None
        # Qdrant客户端
        self.qdrant_client = None

        logger.info("决定书处理管道初始化完成")

    async def initialize_services(self):
        """初始化服务"""
        logger.info("=" * 60)
        logger.info("🚀 初始化服务")
        logger.info("=" * 60)

        # 1. BGE服务
        try:
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

            self.bge_service = BGEEmbeddingService(config)
            await self.bge_service.initialize()

            health = await self.bge_service.health_check()
            logger.info(f"✅ BGE服务: {health['status']}, 维度: {health['dimension']}")

        except Exception as e:
            logger.error(f"❌ BGE服务初始化失败: {e}")

        # 2. Qdrant客户端
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self.qdrant_client = QdrantClient(url="http://localhost:6333")

            # 创建集合
            collection_name = "patent_decisions"

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

        except Exception as e:
            logger.warning(f"⚠️ Qdrant初始化失败: {e}")

        logger.info("=" * 60)

    def load_processed_chunks(self, json_file: str = None) -> list[dict[str, Any]]:
        """加载已处理的数据块"""
        logger.info("📦 加载数据块...")

        processed_dir = self.data_dir / "processed"

        if json_file:
            file_path = processed_dir / json_file
        else:
            # 使用最新的文件
            files = sorted(processed_dir.glob("*_chunks_*.json"))
            if not files:
                logger.error("找不到处理后的数据文件")
                return []
            file_path = files[-1]

        logger.info(f"📄 加载文件: {file_path}")

        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        chunks = data.get('chunks', [])
        logger.info(f"✅ 加载了 {len(chunks)} 个块")

        return chunks

    async def generate_vectors_and_import(self, chunks: list[dict[str, Any]]):
        """生成向量并导入Qdrant"""
        logger.info("=" * 60)
        logger.info(f"📤 为 {len(chunks)} 个块生成向量并导入Qdrant")
        logger.info("=" * 60)

        if not self.bge_service or not self.qdrant_client:
            logger.error("服务未初始化")
            return

        # 准备文本
        texts = [chunk['text'] for chunk in chunks]
        chunk_ids = [chunk['chunk_id'] for chunk in chunks]

        batch_size = 32
        total_batches = (len(texts) + batch_size - 1) // batch_size

        # 准备Qdrant点
        points = []
        from qdrant_client.models import PointStruct

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(texts))

            batch_texts = texts[start_idx:end_idx]
            batch_ids = chunk_ids[start_idx:end_idx]
            batch_chunks = chunks[start_idx:end_idx]

            try:
                # 编码
                result = await self.bge_service.encode(batch_texts, task_type="patent_decision")

                # 创建Qdrant点
                for _i, (chunk_id, embedding, chunk) in enumerate(zip(batch_ids, result.embeddings, batch_chunks, strict=False)):
                    # 生成数值ID
                    hash_id = abs(hash(chunk_id)) % (10 ** 10)

                    points.append(PointStruct(
                        id=hash_id,
                        vector=embedding.tolist() if hasattr(embedding, 'tolist') else list(embedding),
                        payload={
                            'chunk_id': chunk_id,
                            'doc_id': chunk['doc_id'],
                            'block_type': chunk['block_type'],
                            'section_path': chunk['section_path'],
                            'text': chunk['text'][:500],  # 保存前500字符用于预览
                            'decision_date': chunk['metadata'].get('decision_date', ''),
                            'char_count': chunk['metadata'].get('char_count', 0),
                            'law_references': chunk['metadata'].get('law_references', []),
                            'evidence_references': chunk['metadata'].get('evidence_references', [])
                        }
                    ))

                # 每100个点上传一次
                if len(points) >= 100:
                    self.qdrant_client.upsert(
                        collection_name="patent_decisions",
                        points=points
                    )
                    logger.info(f"   📤 已上传 {len(points)} 个点到Qdrant")
                    points = []

                progress = (batch_idx + 1) / total_batches * 100
                logger.info(f"✅ 批次 {batch_idx + 1}/{total_batches} ({progress:.1f}%)")

            except Exception as e:
                logger.error(f"❌ 批次 {batch_idx} 失败: {e}")

        # 上传剩余的点
        if points:
            self.qdrant_client.upsert(
                collection_name="patent_decisions",
                points=points
            )
            logger.info(f"   📤 已上传 {len(points)} 个点到Qdrant")

        logger.info("✅ 向量生成和Qdrant导入完成")

        # 验证
        try:
            collection_info = self.qdrant_client.get_collection("patent_decisions")
            logger.info("📊 集合状态:")
            logger.info(f"   点数量: {collection_info.points_count}")
            logger.info(f"   配置: 向量维度={collection_info.config.params.vectors.size}")
        except Exception as e:
            logger.warning(f"验证失败: {e}")

    def export_to_nebula_graph(self, chunks: list[dict[str, Any]]) -> Any:
        """导出到NebulaGraph"""
        logger.info("=" * 60)
        logger.info("🌐 导出数据到NebulaGraph")
        logger.info("=" * 60)

        # 创建NebulaGraph导入脚本
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / "knowledge_graph" / f"nebula_decisions_{timestamp}.ngql"

        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write("# NebulaGraph 专利决定书导入脚本\n")
            f.write(f"# 生成时间: {datetime.now().isoformat()}\n\n")

            # 创建空间
            f.write("CREATE SPACE IF NOT EXISTS patent_decisions(partition_num=10, replica_factor=1, vid_type=FIXED_STRING(32));\n")
            f.write("USE patent_decisions;\n\n")

            # 创建标签
            f.write("# 创建节点类型\n")
            f.write("CREATE TAG IF NOT EXISTS decision(doc_id string, decision_date string, block_type string, char_count int);\n")
            f.write("CREATE TAG IF NOT EXISTS law_article(name string, text string);\n")
            f.write("CREATE TAG IF NOT EXISTS evidence(evidence_id string, content string);\n\n")

            # 创建边类型
            f.write("# 创建边类型\n")
            f.write("CREATE EDGE IF NOT EXISTS cites(weight int);\n")
            f.write("CREATE EDGE IF NOT EXISTS refers_to(weight int);\n\n")

            # 插入决定节点
            f.write("# 插入决定节点（示例）\n")
            unique_docs = {(c['doc_id'], c['metadata'].get('decision_date', '')) for c in chunks}
            for doc_id, decision_date in list(unique_docs)[:20]:  # 示例：只插入前20个
                f.write(f'INSERT VERTEX decision("{doc_id}", "{decision_date}", "decision", 0);\n')

            f.write("\n")

            # 插入块节点（示例）
            f.write("# 插入块节点（示例）\n")
            for chunk in chunks[:20]:  # 示例：只插入前20个
                escaped_text = chunk['text'][:100].replace('"', '\\"').replace('\n', '\\n')
                f.write(f'INSERT VERTEX decision("{chunk["chunk_id"]}", "", "{chunk["block_type"]}", {chunk["metadata"]["char_count"]});\n')

            f.write("\n")

            # 插入引用关系（示例）
            f.write("# 插入引用关系（示例）\n")
            for chunk in chunks[:20]:
                law_refs = chunk['metadata'].get('law_references', [])
                for law_ref in law_refs[:3]:  # 最多3个引用
                    law_id = f"law_{hash(law_ref) % 100000}"
                    f.write(f'INSERT EDGE cites() FROM "{chunk["chunk_id"]}" TO "{law_id}";\n')

        logger.info(f"📄 NebulaGraph脚本: {output_file}")
        logger.info("✅ NebulaGraph导出完成")

        return str(output_file)

    async def run_pipeline(self, chunks_json: str = None):
        """运行完整管道"""
        logger.info("=" * 60)
        logger.info("🚀 启动决定书处理管道")
        logger.info("=" * 60)

        try:
            # 初始化服务
            await self.initialize_services()

            # 加载数据块
            chunks = self.load_processed_chunks(chunks_json)
            if not chunks:
                logger.error("没有数据可处理")
                return

            # 生成向量并导入Qdrant
            await self.generate_vectors_and_import(chunks)

            # 导出到NebulaGraph
            self.export_to_nebula_graph(chunks)

            logger.info("=" * 60)
            logger.info("🎉 管道执行完成！")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 管道执行失败: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    pipeline = DecisionPipeline()
    await pipeline.run_pipeline()


if __name__ == "__main__":
    asyncio.run(main())
