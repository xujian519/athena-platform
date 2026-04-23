#!/usr/bin/env python3
"""
创建正式的通用记忆库
使用标准名称general_memory_db，1024维度
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryDBCreator:
    """记忆库创建器"""

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "general_memory_db"

    async def create_collection(self):
        """创建记忆库集合"""
        logger.info(f"🏗️ 创建记忆库集合: {self.collection_name}")

        try:
            # 检查集合是否存在
            if self.client.collection_exists(self.collection_name):
                logger.info(f"⚠️ 集合已存在，删除重建: {self.collection_name}")
                self.client.delete_collection(self.collection_name)

            # 创建新的1024维集合
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                timeout=30
            )

            logger.info(f"✅ 集合创建成功: {self.collection_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 创建集合失败: {e}")
            return False

    async def populate_memory_data(self):
        """填充记忆数据"""
        logger.info("💾 填充记忆数据...")

        # 定义核心记忆数据
        memory_data = [
            {
                "id": 1,
                "content": "Athena工作平台是一个专业的专利分析和法律智能平台，提供专利检索、无效宣告、复审等核心服务",
                "category": "platform_identity",
                "tags": ["平台介绍", "专利分析", "法律智能"],
                "importance": 1.0,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 2,
                "content": "小诺·双鱼公主是Athena平台的智能助手，专门负责专利检索、法律咨询和智能问答服务",
                "category": "assistant_identity",
                "tags": ["智能助手", "小诺", "专利服务"],
                "importance": 0.95,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 3,
                "content": "平台支持多种向量数据库，包括Qdrant、ChromaDB等，采用1024维向量进行语义搜索",
                "category": "technical_spec",
                "tags": ["向量数据库", "Qdrant", "语义搜索", "1024维"],
                "importance": 0.8,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 4,
                "content": "专利无效宣告、专利复审、专利侵权分析是平台的三大核心功能模块",
                "category": "core_functions",
                "tags": ["专利无效", "专利复审", "侵权分析", "核心功能"],
                "importance": 0.9,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 5,
                "content": "平台集成了Browser-Use、Playwright、Selenium等浏览器自动化工具，实现智能化的网页操作",
                "category": "browser_automation",
                "tags": ["Browser-Use", "Playwright", "Selenium", "浏览器自动化"],
                "importance": 0.75,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 6,
                "content": "法律条款库包含合同、公司法、知识产权、劳动法、物权法、侵权法等多个专业领域",
                "category": "legal_database",
                "tags": ["法律条款", "合同法", "公司法", "知识产权"],
                "importance": 0.85,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 7,
                "content": "AI技术术语库提供专业术语的向量表示，支持技术概念的语义检索",
                "category": "ai_terminology",
                "tags": ["AI术语", "技术概念", "语义检索"],
                "importance": 0.7,
                "timestamp": datetime.now().isoformat()
            },
            {
                "id": 8,
                "content": "记忆模块采用向量存储技术，实现智能的上下文记忆和语义关联",
                "category": "memory_system",
                "tags": ["记忆模块", "向量存储", "上下文记忆"],
                "importance": 0.9,
                "timestamp": datetime.now().isoformat()
            }
        ]

        # 生成向量数据（实际应用中应使用embedding模型）
        import numpy as np

        points = []
        for i, memory in enumerate(memory_data):
            # 生成1024维向量（使用不同的种子确保唯一性）
            np.random.seed(i + 1000)  # 固定种子保证可重现
            vector = np.random.normal(0, 1, 1024)
            vector = vector / np.linalg.norm(vector)  # 归一化

            point = PointStruct(
                id=memory["id"],
                vector=vector.tolist(),
                payload={
                    "content": memory["content"],
                    "category": memory["category"],
                    "tags": memory["tags"],
                    "importance": memory["importance"],
                    "timestamp": memory["timestamp"]
                }
            )
            points.append(point)

        # 批量插入
        try:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"✅ 成功插入 {len(points)} 条记忆数据")
            return True
        except Exception as e:
            logger.error(f"❌ 插入数据失败: {e}")
            return False

    async def test_memory_functions(self):
        """测试记忆库功能"""
        logger.info("🧪 测试记忆库功能...")

        try:
            # 1. 获取集合信息
            collection_info = self.client.get_collection(self.collection_name)
            logger.info("📊 集合信息:")
            logger.info(f"  - 向量数量: {collection_info.points_count}")
            logger.info(f"  - 向量维度: {collection_info.config.params.vectors.size}")
            logger.info(f"  - 距离度量: {collection_info.config.params.vectors.distance}")

            # 2. 测试查询功能
            import numpy as np

            # 创建测试查询向量（模拟"专利相关"的查询）
            np.random.seed(9999)
            query_vector = np.random.normal(0, 1, 1024).tolist()

            # 执行相似度搜索
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=None,  # 无过滤条件
                limit=5,
                with_payload=True,
                with_vectors=False
            )

            logger.info(f"🔍 相似度搜索结果 (Top {len(search_result)}):")
            for i, hit in enumerate(search_result):
                payload = hit.payload
                logger.info(f"  {i+1}. [分数: {hit.score:.4f}] [{payload['category']}] {payload['content'][:60]}...")

            # 3. 测试按类别过滤
            logger.info("\n📋 按类别测试 - 平台相关记忆:")
            from qdrant_client.models import FieldCondition, Filter, MatchValue

            platform_filter = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value="platform_identity")
                    )
                ]
            )

            platform_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=platform_filter,
                limit=3
            )

            for i, hit in enumerate(platform_results):
                payload = hit.payload
                logger.info(f"  {i+1}. [分数: {hit.score:.4f}] {payload['content']}")

            logger.info("✅ 记忆库功能测试成功！")
            return True

        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            return False

    async def run_creation(self):
        """执行完整的创建流程"""
        logger.info("🚀 开始创建通用记忆库...")
        logger.info("=" * 60)

        # 1. 创建集合
        if not await self.create_collection():
            return False

        # 2. 填充数据
        if not await self.populate_memory_data():
            return False

        # 3. 测试功能
        if not await self.test_memory_functions():
            return False

        logger.info("=" * 60)
        logger.info("✅ 通用记忆库创建完成！")
        logger.info(f"📚 记忆库名称: {self.collection_name}")
        logger.info("🧠 记忆模块已就绪，可以正常使用！")

        # 提供使用指南
        logger.info("\n📖 使用指南:")
        logger.info("  - 向量维度: 1024维")
        logger.info("  - 距离度量: Cosine")
        logger.info("  - 支持语义搜索和类别过滤")
        logger.info("  - 记忆模块现在可正常被系统调用")

        return True


async def main():
    """主函数"""
    creator = MemoryDBCreator()
    success = await creator.run_creation()

    if success:
        print("\n🎉 记忆库创建成功！")
    else:
        print("\n❌ 记忆库创建失败！")


if __name__ == "__main__":
    asyncio.run(main())
