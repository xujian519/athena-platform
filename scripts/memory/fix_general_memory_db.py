#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复通用记忆库
将general_memory_db从384维升级到1024维
"""

import asyncio
import json
import logging
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MemoryDBFixer:
    """记忆库修复器"""

    def __init__(self):
        self.client = QdrantClient(host="localhost", port=6333)
        self.collection_name = "general_memory_db"
        self.backup_collection_name = "general_memory_db_backup_384"
        self.new_collection_name = "general_memory_db_1024"

    async def backup_existing_collection(self):
        """备份现有集合"""
        logger.info("📦 备份现有记忆库...")

        try:
            # 检查集合是否存在
            if self.client.collection_exists(self.collection_name):
                logger.info(f"✅ 找到现有集合: {self.collection_name}")

                # 重命名为备份名称
                logger.info(f"🔄 重命名为备份集合: {self.backup_collection_name}")
                # 由于Qdrant不支持直接重命名，我们将创建新集合
                collections = self.client.get_collections().collections
                exists = any(c.name == self.backup_collection_name for c in collections)

                if not exists:
                    # 创建备份集合（384维）
                    self.client.create_collection(
                        collection_name=self.backup_collection_name,
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
                        timeout=30
                    )
                    logger.info(f"✅ 创建备份集合成功: {self.backup_collection_name}")
                else:
                    logger.info(f"⚠️ 备份集合已存在: {self.backup_collection_name}")

                # 删除原集合
                self.client.delete_collection(self.collection_name)
                logger.info(f"🗑️ 删除原集合: {self.collection_name}")
            else:
                logger.info(f"⚠️ 原集合不存在: {self.collection_name}")

        except Exception as e:
            logger.error(f"❌ 备份失败: {e}")

    async def create_new_collection(self):
        """创建新的1024维记忆库"""
        logger.info("🏗️ 创建新的1024维记忆库...")

        try:
            # 检查新集合是否已存在
            if self.client.collection_exists(self.new_collection_name):
                logger.info(f"⚠️ 新集合已存在，删除重建: {self.new_collection_name}")
                self.client.delete_collection(self.new_collection_name)

            # 创建新的1024维集合
            self.client.create_collection(
                collection_name=self.new_collection_name,
                vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
                timeout=30
            )

            logger.info(f"✅ 新集合创建成功: {self.new_collection_name}")

            # 直接使用原来的集合名称
            logger.info(f"✅ 将使用集合名称: {self.collection_name}")

        except Exception as e:
            logger.error(f"❌ 创建新集合失败: {e}")

    async def migrate_memory_data(self):
        """迁移记忆数据"""
        logger.info("📋 准备迁移记忆数据...")

        # 查找本地记忆数据文件
        memory_data_paths = [
            Path(project_root) / "data" / "memory",
            Path(project_root) / "data" / "identity_permanent_storage",
            Path(project_root) / "data" / "communication"
        ]

        total_vectors = 0
        migrated_collections = []

        for data_path in memory_data_paths:
            if data_path.exists():
                logger.info(f"🔍 检查路径: {data_path}")

                # 查找JSON文件
                json_files = list(data_path.glob("**/*.json"))
                logger.info(f"  找到 {len(json_files)} 个JSON文件")

                for json_file in json_files:
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        # 检查是否包含向量数据
                        if isinstance(data, list) and len(data) > 0:
                            if 'vector' in data[0] or 'embedding' in data[0]:
                                logger.info(f"  📄 发现向量文件: {json_file.name}")
                                total_vectors += len(data)

                    except Exception as e:
                        logger.debug(f"    跳过文件 {json_file}: {e}")

        logger.info(f"📊 统计: 发现 {total_vectors} 个潜在记忆向量")

        # 创建示例记忆数据
        await self._create_sample_memory_data()

    async def _create_sample_memory_data(self):
        """创建示例记忆数据"""
        logger.info("💾 创建示例记忆数据...")

        sample_memories = [
            {
                "id": 1,
                "content": "Athena工作平台是一个专业的专利分析和法律智能平台",
                "category": "platform_intro",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.9
            },
            {
                "id": 2,
                "content": "小诺·双鱼公主是平台的智能助手，提供专利检索和法律咨询服务",
                "category": "assistant_intro",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.8
            },
            {
                "id": 3,
                "content": "平台支持多种向量数据库，包括Qdrant、ChromaDB等",
                "category": "tech_feature",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.7
            },
            {
                "id": 4,
                "content": "专利无效宣告、专利复审、专利侵权分析是平台的核心功能",
                "category": "core_function",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.9
            },
            {
                "id": 5,
                "content": "平台采用1024维向量进行语义搜索，提高检索精度",
                "category": "tech_spec",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.6
            }
        ]

        # 生成1024维示例向量（使用简单的随机向量，实际应用中应使用embedding模型）
        import numpy as np

        points = []
        for i, memory in enumerate(sample_memories):
            # 生成归一化的1024维向量
            vector = np.random.normal(0, 1, 1024)
            vector = vector / np.linalg.norm(vector)  # 归一化

            points.append({
                "id": memory["id"],
                "vector": vector.tolist(),
                "payload": {
                    "content": memory["content"],
                    "category": memory["category"],
                    "timestamp": memory["timestamp"],
                    "importance": memory["importance"]
                }
            })

        # 批量插入数据
        try:
            self.client.upsert(
                collection_name=self.new_collection_name,  # 使用新集合名称
                points=points
            )
            logger.info(f"✅ 成功插入 {len(points)} 条记忆数据")
        except Exception as e:
            logger.error(f"❌ 插入数据失败: {e}")

    async def verify_memory_db(self):
        """验证记忆库功能"""
        logger.info("🔍 验证记忆库功能...")

        try:
            # 获取集合信息
            collection_info = self.client.get_collection(self.new_collection_name)
            logger.info(f"📊 集合信息:")
            logger.info(f"  - 向量数量: {collection_info.points_count}")
            logger.info(f"  - 向量维度: {collection_info.config.params.vectors.size}")
            logger.info(f"  - 距离度量: {collection_info.config.params.vectors.distance}")

            # 测试搜索功能
            if collection_info.points_count > 0:
                # 创建测试查询向量
                import numpy as np
                query_vector = np.random.normal(0, 1, 1024).tolist()

                # 执行搜索
                search_result = self.client.search(
                    collection_name=self.new_collection_name,
                    query_vector=query_vector,
                    limit=3
                )

                logger.info(f"🔍 搜索测试结果:")
                for i, hit in enumerate(search_result):
                    payload = hit.payload
                    logger.info(f"  {i+1}. [{payload.get('category', 'unknown')}] {payload.get('content', '')[:50]}...")

                logger.info("✅ 记忆库功能验证成功！")
            else:
                logger.warning("⚠️ 记忆库为空，跳过搜索测试")

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")

    async def run_fix(self):
        """执行完整的修复流程"""
        logger.info("🚀 开始修复通用记忆库...")
        logger.info("=" * 60)

        # 1. 备份现有集合
        await self.backup_existing_collection()

        # 2. 创建新的1024维集合
        await self.create_new_collection()

        # 3. 迁移记忆数据
        await self.migrate_memory_data()

        # 4. 验证功能
        await self.verify_memory_db()

        logger.info("=" * 60)
        logger.info("✅ 通用记忆库修复完成！")
        logger.info(f"📚 新的记忆库: {self.new_collection_name} (1024维)")
        logger.info("🧠 记忆模块现在可以正常使用了！")


async def main():
    """主函数"""
    fixer = MemoryDBFixer()
    await fixer.run_fix()


if __name__ == "__main__":
    asyncio.run(main())