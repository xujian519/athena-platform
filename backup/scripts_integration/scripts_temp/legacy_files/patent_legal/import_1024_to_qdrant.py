#!/usr/bin/env python3
"""
将1024维向量数据导入Qdrant
Import 1024-dim Vectors to Qdrant

作者: 小诺·双鱼公主
创建时间: 2024年12月15日
"""

# Numpy兼容性导入
from config.numpy_compatibility import array, zeros, ones, random, mean, sum, dot
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

class PatentLegal1024QdrantImporter:
    """专利法律法规1024维向量Qdrant导入器"""

    def __init__(self):
        """初始化"""
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "patent_legal_vectors_1024"
        self.vector_size = 1024

    def create_collection(self):
        """创建集合"""
        try:
            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.collection_name in collection_names:
                logger.info(f"集合 {self.collection_name} 已存在")
                # 删除旧集合以重新创建
                logger.info(f"删除旧集合 {self.collection_name}...")
                self.client.delete_collection(self.collection_name)

            # 创建新集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE)
            )
            logger.info(f"✅ 创建集合 {self.collection_name} 成功")
            logger.info(f"   向量维度: {self.vector_size}")
            logger.info(f"   距离度量: COSINE")
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

    def import_vectors(self, qdrant_data: Dict[str, Any], batch_size: int = 50):
        """批量导入向量"""
        try:
            points = qdrant_data.get('points', [])
            total = len(points)

            logger.info(f"开始导入 {total} 个1024维向量...")

            # 分批导入
            for i in range(0, total, batch_size):
                batch = points[i:i+batch_size]

                # 转换为PointStruct对象
                point_structs = []
                for p in batch:
                    # 确保向量维度正确
                    vector = p['vector']
                    if len(vector) != self.vector_size:
                        logger.warning(f"向量维度不匹配: {len(vector)} != {self.vector_size}")
                        continue

                    point = PointStruct(
                        id=p['id'],
                        vector=vector,
                        payload=p['payload']
                    )
                    point_structs.append(point)

                # 执行导入
                if point_structs:
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=point_structs
                    )

                    logger.info(f"已导入 {i+len(batch)}/{total} 个向量")

            logger.info("✅ 1024维向量导入完成！")
            return True

        except Exception as e:
            logger.error(f"导入向量失败: {e}")
            return False

    def verify_import(self):
        """验证导入结果"""
        try:
            # 获取集合信息
            info = self.client.get_collection(self.collection_name)
            logger.info(f"\n=== 1024维向量集合信息 ===")
            logger.info(f"集合名称: {self.collection_name}")
            logger.info(f"向量数量: {info.points_count}")
            logger.info(f"向量维度: {info.config.params.vectors.size}")
            logger.info(f"距离度量: {info.config.params.vectors.distance}")

            # 测试搜索
            if info.points_count > 0:
                # 使用示例向量进行搜索
                import numpy as np
                query_vector = random((self.vector_size)).tolist()

                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=3
                )

                logger.info(f"\n测试搜索结果 (随机向量):")
                for i, hit in enumerate(search_result):
                    payload = hit.payload
                    logger.info(f"  {i+1}. {payload.get('doc_name', 'Unknown')}")
                    logger.info(f"     块ID: {payload.get('chunk_id', 'N/A')}")
                    logger.info(f"     相似度: {hit.score:.4f}")
                    logger.info(f"     内容预览: {payload.get('content', 'N/A')[:100]}...")

            return True

        except Exception as e:
            logger.error(f"验证导入失败: {e}")
            return False

    def compare_collections(self):
        """比较不同维度的集合"""
        try:
            logger.info("\n=== 集合对比 ===")

            # 获取所有集合
            collections = self.client.get_collections().collections
            patent_collections = [c for c in collections if 'patent_legal' in c.name]

            for collection in patent_collections:
                info = self.client.get_collection(collection.name)
                logger.info(f"\n集合: {collection.name}")
                logger.info(f"  向量数量: {info.points_count}")
                logger.info(f"  向量维度: {info.config.params.vectors.size}")
                logger.info(f"  距离度量: {info.config.params.vectors.distance}")

        except Exception as e:
            logger.error(f"比较集合失败: {e}")

async def main():
    """主函数"""
    logger.info("开始将1024维专利法律法规向量导入Qdrant...")

    # 创建导入器
    importer = PatentLegal1024QdrantImporter()

    # 创建集合
    if not importer.create_collection():
        logger.error("创建集合失败，退出")
        return

    # 加载向量数据
    qdrant_path = "/Users/xujian/Athena工作平台/data/patent_legal_vectors_1024/qdrant_import.json"
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

    # 对比不同集合
    importer.compare_collections()

    logger.info("\n🎉 1024维专利法律法规向量导入Qdrant完成！")
    logger.info(f"\n可访问:")
    logger.info(f"- Qdrant: http://localhost:6333")
    logger.info(f"- 1024维集合: {importer.collection_name}")
    logger.info(f"\n使用方法:")
    logger.info(f"  1. 使用1024维向量进行更精确的语义搜索")
    logger.info(f"  2. 与原有22维向量进行效果对比")
    logger.info(f"  3. 根据搜索质量选择合适的向量维度")

if __name__ == "__main__":
    asyncio.run(main())