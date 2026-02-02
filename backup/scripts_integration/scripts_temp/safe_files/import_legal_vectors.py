#!/usr/bin/env python3
"""
导入法律向量库和知识图谱数据
Import Legal Vectors and Knowledge Graph Data

将本地存储的法律数据重新导入到运行中的Qdrant和知识图谱服务中
"""

import os
import sys
import json
import sqlite3
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegalDataImporter:
    """法律数据导入器"""

    def __init__(self):
        # Qdrant客户端
        self.qdrant_client = QdrantClient(host="localhost", port=6333)

        # 数据路径
        self.legal_db_path = "/Users/xujian/Athena工作平台/data/support_data/databases/legal_laws_database.db"
        self.vector_data_path = "/Users/xujian/Athena工作平台/data/vectors_qdrant/collections"

        # 集合配置
        self.collections = {
            "legal_laws_comprehensive": {
                "vector_size": 1024,
                "description": "综合法律向量库"
            },
            "legal_laws_1024": {
                "vector_size": 1024,
                "description": "1024维法律向量"
            },
            "legal_documents": {
                "vector_size": 768,
                "description": "法律文档向量"
            },
            "legal_clauses": {
                "vector_size": 768,
                "description": "法律条款向量"
            },
            "legal_patent_vectors": {
                "vector_size": 1024,
                "description": "专利法律向量"
            }
        }

    async def import_from_database(self):
        """从SQLite数据库导入法律文档"""
        logger.info("开始从数据库导入法律文档...")

        try:
            conn = sqlite3.connect(self.legal_db_path)
            cursor = conn.cursor()

            # 查看表结构
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            logger.info(f"数据库中的表: {[t[0] for t in tables]}")

            # 获取法律文档数据
            cursor.execute("SELECT COUNT(*) FROM legal_documents LIMIT 1")
            count = cursor.fetchone()

            if count:
                logger.info(f"找到 {count[0]} 条法律文档记录")

                # 创建并导入到legal_laws_comprehensive集合
                await self.create_collection_if_not_exists("legal_laws_comprehensive", 1024)

                # 分批导入数据
                batch_size = 100
                offset = 0
                total_imported = 0

                while True:
                    cursor.execute(f"""
                        SELECT id, title, content, category, vector
                        FROM legal_documents
                        LIMIT {batch_size} OFFSET {offset}
                    """)
                    batch = cursor.fetchall()

                    if not batch:
                        break

                    points = []
                    for doc_id, title, content, category, vector in batch:
                        if vector:
                            # 解析向量数据
                            try:
                                vector_data = json.loads(vector)
                                points.append(PointStruct(
                                    id=str(doc_id),
                                    vector=vector_data,
                                    payload={
                                        "title": title,
                                        "content": content[:500],  # 截取前500字符
                                        "category": category,
                                        "source": "legal_laws_database"
                                    }
                                ))
                            except json.JSONDecodeError:
                                logger.warning(f"无法解析文档 {doc_id} 的向量数据")

                    # 上传批量数据
                    if points:
                        self.qdrant_client.upsert(
                            collection_name="legal_laws_comprehensive",
                            points=points
                        )
                        total_imported += len(points)
                        logger.info(f"已导入 {total_imported} 条法律文档向量")

                    offset += batch_size

                logger.info(f"✅ 成功导入 {total_imported} 条法律文档向量到 legal_laws_comprehensive")

            conn.close()

        except Exception as e:
            logger.error(f"从数据库导入失败: {e}")

    async def import_from_vector_files(self):
        """从本地向量文件导入"""
        logger.info("开始从向量文件导入...")

        for collection_name, config in self.collections.items():
            collection_path = os.path.join(self.vector_data_path, collection_name)

            if os.path.exists(collection_path):
                logger.info(f"处理集合: {collection_name}")

                # 创建集合
                await self.create_collection_if_not_exists(
                    collection_name,
                    config["vector_size"]
                )

                # 查找向量数据文件
                vector_files = []
                for root, dirs, files in os.walk(collection_path):
                    for file in files:
                        if file.endswith('.json') and 'vector' in file.lower():
                            vector_files.append(os.path.join(root, file))

                logger.info(f"找到 {len(vector_files)} 个向量文件")

                # 导入每个文件
                total_points = 0
                for vector_file in vector_files:
                    try:
                        with open(vector_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)

                        if isinstance(data, list):
                            points = []
                            for item in data:
                                if 'vector' in item and 'id' in item:
                                    points.append(PointStruct(
                                        id=str(item['id']),
                                        vector=item['vector'],
                                        payload=item.get('payload', {})
                                    ))

                            if points:
                                self.qdrant_client.upsert(
                                    collection_name=collection_name,
                                    points=points
                                )
                                total_points += len(points)
                                logger.info(f"从 {os.path.basename(vector_file)} 导入 {len(points)} 个向量")

                    except Exception as e:
                        logger.error(f"导入文件 {vector_file} 失败: {e}")

                logger.info(f"✅ 集合 {collection_name} 总计导入 {total_points} 个向量")

    async def create_collection_if_not_exists(self, collection_name: str, vector_size: int):
        """创建集合（如果不存在）"""
        try:
            collections = self.qdrant_client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name not in collection_names:
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"✅ 创建集合 {collection_name}")
            else:
                logger.info(f"集合 {collection_name} 已存在")
        except Exception as e:
            logger.error(f"创建集合 {collection_name} 失败: {e}")

    async def verify_import(self):
        """验证导入结果"""
        logger.info("验证导入结果...")

        for collection_name in self.collections.keys():
            try:
                collection_info = self.qdrant_client.get_collection(collection_name)
                points_count = collection_info.points_count
                logger.info(f"集合 {collection_name}: {points_count} 个向量")
            except Exception as e:
                logger.error(f"获取集合 {collection_name} 信息失败: {e}")

    async def run(self):
        """执行导入流程"""
        logger.info("=" * 50)
        logger.info("开始导入法律向量库和知识图谱数据")
        logger.info("=" * 50)

        # 1. 从数据库导入
        await self.import_from_database()

        # 2. 从向量文件导入
        await self.import_from_vector_files()

        # 3. 验证导入
        await self.verify_import()

        logger.info("=" * 50)
        logger.info("法律向量库导入完成！")
        logger.info("=" * 50)

async def main():
    """主函数"""
    importer = LegalDataImporter()
    await importer.run()

if __name__ == "__main__":
    asyncio.run(main())