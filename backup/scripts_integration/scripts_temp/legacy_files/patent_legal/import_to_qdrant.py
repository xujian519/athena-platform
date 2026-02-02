#!/usr/bin/env python3
"""
将专利法律法规向量导入Qdrant
Import Patent Legal Vectors to Qdrant

作者: 小诺·双鱼公主
创建时间: 2024年12月14日
"""

import os
import json
import asyncio
import logging
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PatentLegalQdrantImporter:
    """专利法律法规Qdrant导入器"""

    def __init__(self, host: str = "localhost", port: int = 6333):
        """初始化Qdrant客户端"""
        self.client = QdrantClient(host=host, port=port)
        self.collection_name = "patent_legal_vectors"

    async def create_collection(self, vector_size: int = 1024):
        """创建集合"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"集合 {self.collection_name} 创建成功")
            else:
                logger.info(f"集合 {self.collection_name} 已存在")
        except Exception as e:
            logger.error(f"创建集合失败: {e}")

    async def load_vectors(self, file_path: str) -> Dict[str, Any]:
        """加载向量数据"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"加载了 {len(data['points'])} 个向量")
        return data

    async def import_vectors(self, data: Dict[str, Any], batch_size: int = 100):
        """批量导入向量"""
        points = data['points']

        # 分批导入
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]

            # 转换为PointStruct
            point_structs = [
                PointStruct(
                    id=point['id'],
                    vector=point['vector'],
                    payload=point['payload']
                )
                for point in batch
            ]

            try:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=point_structs
                )
                logger.info(f"已导入 {min(i + batch_size, len(points))}/{len(points)} 个向量")
            except Exception as e:
                logger.error(f"导入批次失败: {e}")

        logger.info("所有向量导入完成！")

    async def verify_import(self):
        """验证导入结果"""
        try:
            count = self.client.count(self.collection_name)
            logger.info(f"集合中向量总数: {count.count}")

            # 获取一些示例点
            sample_points = self.client.scroll(
                collection_name=self.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=True
            )

            logger.info("导入验证完成！")
            return True
        except Exception as e:
            logger.error(f"验证失败: {e}")
            return False

async def main():
    """主函数"""
    logger.info("开始导入专利法律法规向量到Qdrant...")

    # 创建导入器
    importer = PatentLegalQdrantImporter()

    # 创建集合
    await importer.create_collection()

    # 加载数据
    data_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors/patent_legal_vectors.json"
    if not os.path.exists(data_path):
        logger.error(f"向量数据文件不存在: {data_path}")
        return

    data = await importer.load_vectors(data_path)

    # 导入向量
    await importer.import_vectors(data)

    # 验证导入
    await importer.verify_import()

if __name__ == "__main__":
    asyncio.run(main())