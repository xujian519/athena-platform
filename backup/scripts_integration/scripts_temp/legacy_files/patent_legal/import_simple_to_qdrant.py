#!/usr/bin/env python3
"""
将简化版向量数据导入Qdrant
Import Simple Vectors to Qdrant

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleQdrantImporter:
    """简化版Qdrant导入器"""

    def __init__(self):
        """初始化"""
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "patent_legal_vectors_simple"

    def create_collection(self):
        """创建集合"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name in collection_names:
                logger.info(f"集合 {self.collection_name} 已存在")
                return True

            # 创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=22, distance=Distance.COSINE)
            )
            logger.info(f"✅ 创建集合 {self.collection_name} 成功")
            return True

        except Exception as e:
            logger.error(f"创建集合失败: {e}")
            return False

    async def load_vectors(self, file_path: str) -> Dict[str, Any]:
        """加载向量数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"加载向量数据: {len(data['points'])} 个向量")
            return data
        except Exception as e:
            logger.error(f"加载向量数据失败: {e}")
            return {}

    def import_vectors(self, qdrant_data: Dict[str, Any], batch_size: int = 100):
        """批量导入向量"""
        try:
            points = qdrant_data.get('points', [])
            total = len(points)

            logger.info(f"开始导入 {total} 个向量...")

            # 分批导入
            for i in range(0, total, batch_size):
                batch = points[i:i+batch_size]

                # 转换为PointStruct对象
                point_structs = []
                for p in batch:
                    point = PointStruct(
                        id=p['id'],
                        vector=p['vector'],
                        payload=p['payload']
                    )
                    point_structs.append(point)

                # 执行导入
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=point_structs
                )

                logger.info(f"已导入 {i+len(batch)}/{total} 个向量")

            logger.info("✅ 向量导入完成！")
            return True

        except Exception as e:
            logger.error(f"导入向量失败: {e}")
            return False

    def verify_import(self):
        """验证导入结果"""
        try:
            # 获取集合信息
            info = self.client.get_collection(self.collection_name)
            logger.info(f"集合信息:")
            logger.info(f"  向量数量: {info.points_count}")
            logger.info(f"  向量维度: {info.config.params.vectors.size}")
            logger.info(f"  距离度量: {info.config.params.vectors.distance}")

            # 测试搜索
            if info.points_count > 0:
                # 随机搜索
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=[0.1] * 22,
                    limit=3
                )

                logger.info(f"\n测试搜索结果:")
                for i, hit in enumerate(search_result):
                    logger.info(f"  {i+1}. {hit.payload.get('file_name', 'Unknown')} (score: {hit.score:.4f})")

            return True

        except Exception as e:
            logger.error(f"验证导入失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("开始将简化版向量数据导入Qdrant...")

    # 创建导入器
    importer = SimpleQdrantImporter()

    # 创建集合
    if not importer.create_collection():
        logger.error("创建集合失败，退出")
        return

    # 加载向量数据
    qdrant_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_simple/qdrant_import.json"
    qdrant_data = await importer.load_vectors(qdrant_path)

    if not qdrant_data:
        logger.error("加载向量数据失败，退出")
        return

    # 导入向量
    if not importer.import_vectors(qdrant_data):
        logger.error("导入向量失败，退出")
        return

    # 验证导入
    importer.verify_import()

    logger.info("\n🎉 简化版向量数据导入Qdrant完成！")
    logger.info(f"\n可访问:")
    logger.info(f"- Qdrant: http://localhost:6333")
    logger.info(f"- 集合名称: {importer.collection_name}")

if __name__ == "__main__":
    asyncio.run(main())