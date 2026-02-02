#!/usr/bin/env python3
"""
Athena工作平台 - 向量数据库管理器
Vector Database Manager for Athena Platform

提供统一的向量数据库管理、检索和访问接口
支持共用向量库和专业向量库
"""

# Numpy兼容性导入
import logging
from enum import Enum
from typing import Any

import requests

from config.numpy_compatibility import random
from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class VectorDBType(Enum):
    """向量库类型枚举"""

    GENERAL = "general"  # 共用向量库
    PATENT_RULES = "patent_rules"  # 专利规则库
    LEGAL = "legal"  # 法律库
    TECHNICAL_TERMS = "technical_terms"  # 技术术语库
    PATENT_INVALID = "patent_invalid"  # 专利无效库
    PATENT_REVIEW = "patent_review"  # 专利复审库
    PATENT_JUDGMENT = "patent_judgment"  # 专利判决库


class VectorQuery:
    """向量查询对象"""

    def __init__(
        self,
        vector: list[float],
        text: str | None = None,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
        with_payload: bool = True,
        with_vectors: bool = False,
    ):
        self.vector = vector
        self.text = text
        self.filters = filters or {}
        self.limit = limit
        self.with_payload = with_payload
        self.with_vectors = with_vectors


class VectorResult:
    """向量检索结果对象"""

    def __init__(
        self, id: str, score: float, payload: dict[str, Any], vector: list[float] | None = None
    ):
        self.id = id
        self.score = score
        self.payload = payload
        self.vector = vector


class VectorDBManager:
    """向量数据库管理器"""

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.qdrant_url = qdrant_url
        self.session = requests.Session()
        self._initialize_collections()

    def _initialize_collections(self) -> Any:
        """初始化已知的集合"""
        self.collections = {
            VectorDBType.GENERAL: "general_memory_db",
            VectorDBType.PATENT_RULES: "patent_rules_unified_1024",
            VectorDBType.LEGAL: "legal_vector_db",
            VectorDBType.TECHNICAL_TERMS: "ai_technical_terms_vector_db",
            VectorDBType.PATENT_INVALID: "patent_invalid_db",
            VectorDBType.PATENT_REVIEW: "patent_review_db",
            VectorDBType.PATENT_JUDGMENT: "patent_judgment_db",
        }

        # 检查并记录实际存在的集合
        self.existing_collections = set()
        for _db_type, collection_name in self.collections.items():
            if self.collection_exists(collection_name):
                self.existing_collections.add(collection_name)
                logger.info(f"✅ 集合可用: {collection_name}")

        logger.info(f"📊 实际可用集合: {len(self.existing_collections)} 个")

    def collection_exists(self, collection_name: str) -> bool:
        """检查集合是否存在"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️ 检查集合 {collection_name} 时出错: {e}")
            return False

    def create_collection(
        self, collection_name: str, vector_size: int = 1024, distance: str = "Cosine"
    ) -> bool:
        """创建新的集合"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"

            # 先检查是否已存在
            if self.collection_exists(collection_name):
                logger.info(f"⚠️ 集合 {collection_name} 已存在")
                return True

            # 创建集合配置
            collection_config = {
                "vectors": {"size": vector_size, "distance": distance},
                "optimizers_config": {
                    "default_segment_number": 2,
                    "indexing_threshold": 20000,
                    "flush_interval_sec": 5,
                },
                "hnsw_config": {"m": 16, "ef_construct": 100},
            }

            response = self.session.put(url, json=collection_config, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ 成功创建集合: {collection_name}")
                self.existing_collections.add(collection_name)
                return True
            else:
                logger.error(f"❌ 创建集合失败: {response.text}")
                return False

        except Exception as e:
            logger.error(f"❌ 创建集合异常: {e}")
            return False

    def search_in_collection(self, collection_name: str, query: VectorQuery) -> list[VectorResult]:
        """在指定集合中搜索向量"""
        try:
            if collection_name not in self.existing_collections:
                logger.warning(f"⚠️ 集合 {collection_name} 不存在或不可用")
                return []

            url = f"{self.qdrant_url}/collections/{collection_name}/points/search"

            search_payload = {
                "vector": query.vector,
                "limit": query.limit,
                "with_payload": query.with_payload,
                "with_vector": query.with_vectors,
            }

            # 添加过滤条件
            if query.filters:
                search_payload["filter"] = {"must": []}
                for key, value in query.filters.items():
                    search_payload["filter"]["must"].append({"key": key, "match": {"value": value}})

            response = self.session.post(url, json=search_payload, timeout=10)

            if response.status_code == 200:
                results = []
                search_results = response.json().get("result", [])

                for item in search_results:
                    result = VectorResult(
                        id=str(item.get("id", "")),
                        score=item.get("score", 0.0),
                        payload=item.get("payload", {}),
                        vector=item.get("vector") if query.with_vectors else None,
                    )
                    results.append(result)

                logger.info(f"🔍 在 {collection_name} 中找到 {len(results)} 个结果")
                return results
            else:
                logger.error(f"❌ 搜索失败: {response.text}")
                return []

        except Exception as e:
            logger.error(f"❌ 搜索异常: {e}")
            return []

    def batch_search(
        self, collection_names: list[str], query: VectorQuery
    ) -> dict[str, list[VectorResult]]:
        """在多个集合中批量搜索"""
        results = {}

        for collection_name in collection_names:
            results[collection_name] = self.search_in_collection(collection_name, query)

        return results

    def smart_search(
        self, query: VectorQuery, db_types: list[VectorDBType] | None = None
    ) -> dict[str, list[VectorResult]]:
        """智能搜索 - 根据查询内容自动选择合适的向量库"""
        if db_types is None:
            # 默认搜索所有可用的集合
            collection_names = list(self.existing_collections)
        else:
            # 只搜索指定类型的集合
            collection_names = [
                self.collections[db_type]
                for db_type in db_types
                if self.collections[db_type] in self.existing_collections
            ]

        return self.batch_search(collection_names, query)

    def get_collection_info(self, collection_name: str) -> dict[str, Any] | None:
        """获取集合信息"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                return response.json().get("result", {})
            else:
                logger.error(f"❌ 获取集合信息失败: {response.text}")
                return None
        except Exception as e:
            logger.error(f"❌ 获取集合信息异常: {e}")
            return None

    def insert_vector(
        self, collection_name: str, vector_id: str, vector: list[float], payload: dict[str, Any]
    ) -> bool:
        """插入单个向量"""
        try:
            if collection_name not in self.existing_collections:
                logger.error(f"❌ 集合 {collection_name} 不存在")
                return False

            url = f"{self.qdrant_url}/collections/{collection_name}/points"

            payload_data = {"points": [{"id": vector_id, "vector": vector, "payload": payload}]}

            response = self.session.put(url, json=payload_data, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ 向量插入成功: {collection_name}/{vector_id}")
                return True
            else:
                logger.error(f"❌ 向量插入失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 向量插入异常: {e}")
            return False

    def batch_insert(self, collection_name: str, vectors_data: list[dict[str, Any]]) -> bool:
        """批量插入向量"""
        try:
            if collection_name not in self.existing_collections:
                logger.error(f"❌ 集合 {collection_name} 不存在")
                return False

            url = f"{self.qdrant_url}/collections/{collection_name}/points"

            points = []
            for item in vectors_data:
                point = {
                    "id": item["id"],
                    "vector": item["vector"],
                    "payload": item.get("payload", {}),
                }
                points.append(point)

            payload_data = {"points": points}

            response = self.session.put(url, json=payload_data, timeout=60)

            if response.status_code == 200:
                logger.info(f"✅ 批量插入成功: {len(points)} 个向量到 {collection_name}")
                return True
            else:
                logger.error(f"❌ 批量插入失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 批量插入异常: {e}")
            return False

    def delete_collection(self, collection_name: str) -> bool:
        """删除集合"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            response = self.session.delete(url, timeout=30)

            if response.status_code == 200:
                logger.info(f"✅ 删除集合成功: {collection_name}")
                self.existing_collections.discard(collection_name)
                return True
            else:
                logger.error(f"❌ 删除集合失败: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ 删除集合异常: {e}")
            return False


def main() -> None:
    """主函数 - 测试向量数据库管理器"""
    logger.info("🏗️  初始化向量数据库管理器...")

    # 创建管理器实例
    vector_db_manager = VectorDBManager()

    # 显示当前状态
    logger.info(str("=" * 70))
    logger.info("📊 向量数据库管理器状态")
    logger.info(str("=" * 70))
    logger.info(f"📍 Qdrant服务: {vector_db_manager.qdrant_url}")
    logger.info(f"📚 可用集合数量: {len(vector_db_manager.existing_collections)}")
    logger.info(f"📋 可用集合: {', '.join(vector_db_manager.existing_collections)}")
    logger.info(str("=" * 70))

    # 测试搜索功能
    if vector_db_manager.existing_collections:
        # 创建一个随机测试向量
        test_vector = random(1024).tolist()  # 使用1024维测试
        test_query = VectorQuery(vector=test_vector, limit=2, with_payload=True)

        # 在所有可用集合中测试搜索
        logger.info("🧪 测试向量搜索功能...")
        for collection_name in vector_db_manager.existing_collections:
            if collection_name in [
                "patent_rules_unified_1024",
                "legal_vector_db",
            ]:  # 只测试已知维度的集合
                results = vector_db_manager.search_in_collection(collection_name, test_query)
                logger.info(f"🔍 {collection_name}: 找到 {len(results)} 个结果")

    logger.info("✅ 向量数据库管理器初始化完成")
    return vector_db_manager


if __name__ == "__main__":
    manager = main()
