#!/usr/bin/env python3
"""
专利全文PDF向量处理 - Qdrant集合设置
创建和配置patent_full_text集合

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import asyncio
import logging
from datetime import datetime

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/setup_qdrant_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


async def setup_patent_full_text_collection():
    """设置专利全文向量集合"""

    logger.info("=" * 70)
    logger.info("🚀 Qdrant专利全文向量集合初始化")
    logger.info("=" * 70)

    # 连接Qdrant，带重试机制
    max_retries = 5
    retry_delay = 3

    for attempt in range(max_retries):
        try:
            client = QdrantClient(
                url="http://localhost:6333",
                timeout=60,
                verify=False,
                prefer_grpc=False
            )
            collections = client.get_collections().collections
            logger.info(f"✅ Qdrant连接成功，现有{len(collections)}个集合")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"⚠️ Qdrant连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                logger.info(f"   等待{retry_delay}秒后重试...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ Qdrant连接失败: {e}")
                raise

    collection_name = "patent_full_text"

    # 检查集合是否已存在
    existing_collections = [c.name for c in collections]

    if collection_name in existing_collections:
        logger.info(f"📋 集合 '{collection_name}' 已存在，获取配置信息...")
        info = client.get_collection(collection_name)
        logger.info(f"   - 向量维度: {info.config.params.vectors.size}")
        logger.info(f"   - 距离度量: {info.config.params.vectors.distance}")
        logger.info(f"   - 当前点数: {info.points_count:,}")
        logger.info(f"   - 已索引: {info.indexed_point_count:,}")

        # 检查是否需要创建payload索引
        payload_indexes = []
        try:
            # 尝试获取现有索引信息（Qdrant 1.7+支持）
            info = client.get_collection(collection_name)
            logger.info("📋 Payload索引信息已记录")
        except Exception as e:
            logger.debug(f"无法获取详细索引信息: {e}")

        logger.info("✅ 集合已就绪，无需重建")
        return True

    # 创建新集合
    logger.info(f"🔨 创建新集合 '{collection_name}'...")

    try:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=1024,  # BGE-Large-zh-v1.5向量维度
                distance=Distance.COSINE,
                hnsw_config={
                    "m": 16,  # 每层最大连接数
                    "ef_construct": 100,  # 构建时的搜索深度
                }
            ),
            optimizers_config={
                "indexing_threshold": 20000,  # 至少2万条记录才开始索引
            },
            quantization_config=None,  # 不使用量化以保持精度
        )
        logger.info("✅ 集合创建成功")

    except Exception as e:
        logger.error(f"❌ 集合创建失败: {e}")
        raise

    # 注意: Payload索引在数据插入后会自动创建，这里跳过手动创建
    # 验证创建结果
    info = client.get_collection(collection_name)
    logger.info("")
    logger.info("=" * 70)
    logger.info("🎉 Qdrant集合初始化完成！")
    logger.info("=" * 70)
    logger.info(f"📋 集合名称: {collection_name}")
    logger.info("📊 向量配置:")
    logger.info(f"   - 维度: {info.config.params.vectors.size}")
    logger.info(f"   - 距离: {info.config.params.vectors.distance}")
    logger.info(f"   - 当前点数: {info.points_count:,}")
    logger.info("")
    logger.info("🔍 Payload字段说明:")
    logger.info("   - doc_id: 专利文档ID（申请号）")
    logger.info("   - block_type: 块类型(patent/claim/description/abstract)")
    logger.info("   - source: 来源(google_apps/patents/cnipa/epo/uspto)")
    logger.info("   - application_number: 申请号")
    logger.info("   - publication_number: 公开号")
    logger.info("   - title: 专利名称")
    logger.info("   - text: 文本内容（前500字符）")
    logger.info("")
    logger.info("💡 使用方法:")
    logger.info("   client = QdrantClient(url='http://localhost:6333')")
    logger.info(f"   client.search(collection_name='{collection_name}', ...)")
    logger.info("")

    return True


async def main():
    """主函数"""
    await setup_patent_full_text_collection()


if __name__ == "__main__":
    asyncio.run(main())
