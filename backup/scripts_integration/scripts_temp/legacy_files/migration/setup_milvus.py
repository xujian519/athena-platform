#!/usr/bin/env python3
"""
Milvus向量数据库设置脚本
Setup script for Milvus vector database
"""

import asyncio
import logging
from typing import Dict, List, Any
from pymilvus import (
    connections, Collection, FieldSchema, CollectionSchema,
    DataType, utility
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MilvusSetup:
    def __init__(self, host: str = "localhost", port: int = 19530):
        self.host = host
        self.port = port
        self.alias = "default"

    async def connect(self):
        """连接到Milvus"""
        try:
            connections.connect(
                alias=self.alias,
                host=self.host,
                port=self.port
            )
            logger.info("✅ 成功连接到Milvus")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False

    async def create_collections(self):
        """创建向量集合"""
        collections_config = [
            {
                "name": "patent_vectors",
                "description": "专利向量集合",
                "dimension": 768,  # BERT向量维度
                "index_params": {
                    "metric_type": "IP",  # 内积
                    "index_type": "HNSW",  # 层次导航小世界图
                    "params": {
                        "M": 16,
                        "efConstruction": 200
                    }
                },
                "fields": [
                    {"name": "id", "type": DataType.INT64, "is_primary": True, "auto_id": True},
                    {"name": "patent_id", "type": DataType.VARCHAR, "max_length": 100},
                    {"name": "vector", "type": DataType.FLOAT_VECTOR, "dim": 768},
                    {"name": "title", "type": DataType.VARCHAR, "max_length": 1000},
                    {"name": "abstract", "type": DataType.VARCHAR, "max_length": 5000},
                    {"name": "ipc_codes", "type": DataType.VARCHAR, "max_length": 500},
                    {"name": "publication_date", "type": DataType.VARCHAR, "max_length": 20}
                ]
            },
            {
                "name": "document_vectors",
                "description": "文档向量集合",
                "dimension": 1024,  # OpenAI向量维度
                "index_params": {
                    "metric_type": "COSINE",
                    "index_type": "IVF_PQ",
                    "params": {
                        "nlist": 1024,
                        "m": 16,
                        "nbits": 8
                    }
                },
                "fields": [
                    {"name": "id", "type": DataType.INT64, "is_primary": True, "auto_id": True},
                    {"name": "doc_id", "type": DataType.VARCHAR, "max_length": 100},
                    {"name": "vector", "type": DataType.FLOAT_VECTOR, "dim": 1024},
                    {"name": "content", "type": DataType.VARCHAR, "max_length": 65535},
                    {"name": "doc_type", "type": DataType.VARCHAR, "max_length": 50},
                    {"name": "created_at", "type": DataType.INT64}
                ]
            },
            {
                "name": "knowledge_vectors",
                "description": "知识图谱实体向量集合",
                "dimension": 768,
                "index_params": {
                    "metric_type": "L2",
                    "index_type": "HNSW",
                    "params": {
                        "M": 32,
                        "efConstruction": 400
                    }
                },
                "fields": [
                    {"name": "id", "type": DataType.INT64, "is_primary": True, "auto_id": True},
                    {"name": "entity_id", "type": DataType.VARCHAR, "max_length": 100},
                    {"name": "entity_type", "type": DataType.VARCHAR, "max_length": 50},
                    {"name": "vector", "type": DataType.FLOAT_VECTOR, "dim": 768},
                    {"name": "name", "type": DataType.VARCHAR, "max_length": 500},
                    {"name": "description", "type": DataType.VARCHAR, "max_length": 2000},
                    {"name": "domain", "type": DataType.VARCHAR, "max_length": 100}
                ]
            }
        ]

        for config in collections_config:
            await self.create_collection(config)

    async def create_collection(self, config: Dict[str, Any]):
        """创建单个集合"""
        collection_name = config["name"]

        # 检查集合是否已存在
        if utility.has_collection(collection_name):
            logger.info(f"⚠️ 集合 {collection_name} 已存在")
            collection = Collection(collection_name)
        else:
            # 创建字段
            fields = []
            for field_config in config["fields"]:
                field = FieldSchema(
                    name=field_config["name"],
                    dtype=field_config["type"],
                    is_primary=field_config.get("is_primary", False),
                    auto_id=field_config.get("auto_id", False),
                    max_length=field_config.get("max_length", 65535),
                    dim=field_config.get("dim")
                )
                fields.append(field)

            # 创建集合schema
            schema = CollectionSchema(
                fields=fields,
                description=config["description"]
            )

            # 创建集合
            collection = Collection(
                name=collection_name,
                schema=schema
            )
            logger.info(f"✅ 创建集合: {collection_name}")

        # 创建索引
        await self.create_index(collection, config["index_params"])

    async def create_index(self, collection: Collection, index_params: Dict[str, Any]):
        """为向量字段创建索引"""
        try:
            # 为vector字段创建索引
            index_name = f"vector_index"
            if not collection.has_index(index_name):
                collection.create_index(
                    field_name="vector",
                    index_params=index_params,
                    index_name=index_name
                )
                logger.info(f"✅ 创建向量索引: {collection.name}")

            # 为其他字段创建索引
            other_fields = ["patent_id", "doc_id", "entity_id"]
            for field_name in other_fields:
                if collection.has_field(field_name):
                    if not collection.has_index(f"{field_name}_index"):
                        collection.create_index(
                            field_name=field_name,
                            index_name=f"{field_name}_index"
                        )
                        logger.info(f"✅ 创建{field_name}字段索引")

        except Exception as e:
            logger.warning(f"⚠️ 创建索引失败: {e}")

    async def load_collections(self):
        """加载集合到内存"""
        collections = ["patent_vectors", "document_vectors", "knowledge_vectors"]

        for collection_name in collections:
            if utility.has_collection(collection_name):
                collection = Collection(collection_name)
                collection.load()
                logger.info(f"✅ 加载集合到内存: {collection_name}")

    async def verify_setup(self):
        """验证设置"""
        logger.info("\n🔍 验证Milvus设置...")

        # 获取所有集合
        collections = utility.list_collections()
        logger.info(f"\n📊 集合数量: {len(collections)}")

        for collection_name in collections:
            if not collection_name.startswith("__"):
                collection = Collection(collection_name)
                stats = collection.get_stats()
                logger.info(f"\n📂 {collection_name}:")
                logger.info(f"  - 描述: {collection.description}")
                logger.info(f"  - 文档数: {stats.get('row_count', 0):,}")
                logger.info(f"  - 向量维度: {get_vector_dimension(collection)}")


def get_vector_dimension(collection: Collection) -> int:
    """获取集合的向量维度"""
    schema = collection.schema
    for field in schema.fields:
        if field.dtype == DataType.FLOAT_VECTOR:
            return field.dim
    return 0


async def main():
    """主函数"""
    setup = MilvusSetup(
        host="localhost",
        port=19530
    )

    if await setup.connect():
        await setup.create_collections()
        await setup.load_collections()
        await setup.verify_setup()
        logger.info("\n🎉 Milvus设置完成！")
    else:
        logger.error("❌ 设置失败")


if __name__ == "__main__":
    asyncio.run(main())