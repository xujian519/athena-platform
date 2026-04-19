#!/usr/bin/env python3
"""
Athena工作平台 - 混合存储管理器
Hybrid Storage Manager for Athena Platform

实现SQLite+Qdrant混合存储架构,提供智能数据路由和同步功能

作者: 小诺 (AI助手)
创建时间: 2025-12-11
"""

# Numpy兼容性导入
from __future__ import annotations
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np

from config.numpy_compatibility import random
from core.logging_config import setup_logging

# 添加项目路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from core.vector_db.vector_db_manager import (
    VectorQuery,
)

try:
    from services.agent_services.vector_db.optimized_qdrant_client import OptimizedQdrantClient
except ImportError:
    OptimizedQdrantClient = None

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class StorageType(Enum):
    """存储类型枚举"""

    SQLITE = "sqlite"
    QDRANT = "qdrant"


class DataAge(Enum):
    """数据年龄枚举"""

    HOT = "hot"  # 热数据 (< 30天)
    WARM = "warm"  # 温数据 (30-90天)
    COLD = "cold"  # 冷数据 (> 90天)


@dataclass
class StorageDecision:
    """存储决策结果"""

    storage_type: StorageType
    collection_name: str
    reason: str
    priority: int


class HybridStorageManager:
    """混合存储管理器"""

    def __init__(self):
        self.project_root = project_root

        self.qdrant_manager = OptimizedQdrantClient() if OptimizedQdrantClient else None

        # SQLite数据库路径
        self.memory_db_path = os.path.join(
            project_root, "data/support_data/databases/databases/memory_system/athena_memory.db"
        )
        self.metadata_db_path = os.path.join(
        )

        # 存储策略配置
        self.storage_config = self._load_storage_config()

        # 路由规则
        self.routing_rules = self._initialize_routing_rules()

    def _load_storage_config(self) -> dict[str, Any]:
        """加载存储配置"""
        return {
            "hot_storage": {
                "type": StorageType.QDRANT,
                "retention_days": 30,
                "collections": list(self.qdrant_manager.existing_collections),
            },
            "cold_storage": {
                "type": StorageType.SQLITE,
                "databases": [self.memory_db_path, self.metadata_db_path],
            },
            "sync_schedule": "daily",
            "cleanup_schedule": "weekly",
        }

    def _initialize_routing_rules(self) -> list[dict[str, Any]]:
        """初始化路由规则"""
        return [
            {
                "name": "hot_data_rule",
                "condition": lambda data: self._is_hot_data(data),
                "action": StorageType.QDRANT,
                "priority": 1,
            },
            {
                "name": "cold_data_rule",
                "condition": lambda data: self._is_cold_data(data),
                "action": StorageType.SQLITE,
                "priority": 2,
            },
            {
                "name": "metadata_rule",
                "condition": lambda data: self._is_metadata(data),
                "action": StorageType.SQLITE,
                "priority": 3,
            },
            {
                "name": "default_rule",
                "condition": lambda data: True,
                "action": StorageType.QDRANT,
                "priority": 4,
            },
        ]

    def _is_hot_data(self, data: dict[str, Any]) -> bool:
        """判断是否为热数据"""
        # 检查数据年龄
        if "created_at" in data:
            created_at = datetime.fromisoformat(data["created_at"])
            if (datetime.now() - created_at).days < 30:
                return True

        # 检查访问频率
        return bool("access_count" in data and data["access_count"] > 10)

    def _is_cold_data(self, data: dict[str, Any]) -> bool:
        """判断是否为冷数据"""
        if "created_at" in data:
            created_at = datetime.fromisoformat(data["created_at"])
            if (datetime.now() - created_at).days > 90:
                return True
        return False

    def _is_metadata(self, data: dict[str, Any]) -> bool:
        """判断是否为元数据"""
        metadata_keys = ["vector_id", "document_id", "tags", "confidence"]
        return any(key in data for key in metadata_keys)

    def decide_storage_location(self, data: dict[str, Any]) -> StorageDecision:
        """决定数据存储位置"""
        for rule in sorted(self.routing_rules, key=lambda x: x["priority"]):
            if rule["condition"](data):
                return StorageDecision(
                    storage_type=rule["action"],
                    collection_name=self._get_target_collection(rule["action"], data),
                    reason=rule["name"],
                    priority=rule["priority"],
                )

        # 默认存储到Qdrant
        return StorageDecision(
            storage_type=StorageType.QDRANT,
            collection_name="general_memory_db",
            reason="default_rule",
            priority=4,
        )

    def _get_target_collection(self, storage_type: StorageType, data: dict[str, Any]) -> str:
        """获取目标集合名称"""
        if storage_type == StorageType.QDRANT:
            # 根据数据类型选择Qdrant集合
            if "category" in data:
                category = data["category"]
                if category == "patent":
                    return "patent_rules_unified_1024"
                elif category == "legal":
                    return "legal_vector_db"
                elif category == "technical":
                    return "ai_technical_terms_vector_db"
            return "general_memory_db"
        else:
            # SQLite数据库表名
            if "vector_id" in data:
                return "vector_metadata_enhanced"
            elif "content" in data:
                return "athena_memories"
            else:
                return "vector_embeddings"

    def store_vector(
        self, vector_id: str, vector: list[float], payload: dict[str, Any]
    ) -> dict[str, Any]:
        """存储向量数据到合适的位置"""
        # 决定存储位置
        decision = self.decide_storage_location(payload)

        if decision.storage_type == StorageType.QDRANT:
            return self._store_to_qdrant(vector_id, vector, payload, decision)
        else:
            return self._store_to_sqlite(vector_id, vector, payload, decision)

    def _store_to_qdrant(
        self,
        vector_id: str,
        vector: list[float],
        payload: dict[str, Any],        decision: StorageDecision,
    ) -> dict[str, Any]:
        """存储到Qdrant"""
        try:
            # 添加存储时间戳
            payload["stored_at"] = datetime.now().isoformat()
            payload["storage_location"] = "qdrant"

            success = self.qdrant_manager.insert_vector(
                decision.collection_name, vector_id, vector, payload
            )

            return {
                "status": "success" if success else "failed",
                "storage_type": "qdrant",
                "collection": decision.collection_name,
                "vector_id": vector_id,
                "reason": decision.reason,
            }

        except Exception as e:
            logger.error(f"❌ 存储到Qdrant失败: {e}")
            return {"status": "error", "error": str(e), "storage_type": "qdrant"}

    def _store_to_sqlite(
        self,
        vector_id: str,
        vector: list[float],
        payload: dict[str, Any],        decision: StorageDecision,
    ) -> dict[str, Any]:
        """存储到SQLite"""
        try:
            # 选择合适的SQLite数据库
            if "vector_id" in payload:
                db_path = self.metadata_db_path
                table_name = "vector_metadata_enhanced"
            else:
                db_path = self.memory_db_path
                table_name = "athena_memories"

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 准备数据
            vector_blob = np.array(vector, dtype=np.float32).tobytes()

            # 添加存储时间戳
            payload["stored_at"] = datetime.now().isoformat()
            payload["storage_location"] = "sqlite"

            # 根据表类型插入数据
            if table_name == "athena_memories":
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO athena_memories
                    (id, content, embedding_data, embedding_dim, category,
                     importance_score, tags, created_at, stored_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        vector_id,
                        payload.get("content", ""),
                        vector_blob,
                        len(vector),
                        payload.get("category", "general"),
                        payload.get("importance_score", 0.5),
                        payload.get("tags", ""),
                        payload.get("created_at", datetime.now().isoformat()),
                        payload["stored_at"],
                    ),
                )
            else:  # vector_metadata_enhanced
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO vector_metadata_enhanced
                    (vector_id, document_id, collection_name, tags, confidence,
                     vector_dim, created_at, stored_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        vector_id,
                        payload.get("document_id", ""),
                        payload.get("collection_name", ""),
                        payload.get("tags", ""),
                        payload.get("confidence", 0.0),
                        len(vector),
                        payload.get("created_at", datetime.now().isoformat()),
                        payload["stored_at"],
                        "active",
                    ),
                )

            conn.commit()
            conn.close()

            return {
                "status": "success",
                "storage_type": "sqlite",
                "table": table_name,
                "vector_id": vector_id,
                "reason": decision.reason,
            }

        except Exception as e:
            logger.error(f"❌ 存储到SQLite失败: {e}")
            return {"status": "error", "error": str(e), "storage_type": "sqlite"}

    def search_vectors(
        self, query_vector: list[float], limit: int = 10, filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """跨存储系统搜索向量"""
        results = {"qdrant_results": [], "sqlite_results": [], "total_results": 0, "search_time": 0}

        start_time = datetime.now()

        # 并行搜索Qdrant和SQLite
        try:
            # 搜索Qdrant
            qdrant_results = self._search_qdrant(query_vector, limit, filters)
            results["qdrant_results"] = qdrant_results
        except Exception as e:
            logger.warning(f"⚠️ Qdrant搜索失败: {e}")

        try:
            # 搜索SQLite
            sqlite_results = self._search_sqlite(query_vector, limit, filters)
            results["sqlite_results"] = sqlite_results
        except Exception as e:
            logger.warning(f"⚠️ SQLite搜索失败: {e}")

        # 计算搜索时间
        end_time = datetime.now()
        results["search_time"] = (end_time - start_time).total_seconds()
        results["total_results"] = len(results["qdrant_results"]) + len(results["sqlite_results"])

        return results

    def _search_qdrant(
        self, query_vector: list[float], limit: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """搜索Qdrant"""
        query = VectorQuery(
            vector=query_vector, filters=filters or {}, limit=limit, with_payload=True
        )

        all_results = []

        # 在所有可用的Qdrant集合中搜索
        for collection_name in self.qdrant_manager.existing_collections:
            try:
                results = self.qdrant_manager.search_in_collection(collection_name, query)
                for result in results:
                    all_results.append(
                        {
                            "id": result.id,
                            "score": result.score,
                            "payload": result.payload,
                            "collection": collection_name,
                            "storage_type": "qdrant",
                        }
                    )
            except Exception as e:
                logger.warning(f"⚠️ 搜索集合 {collection_name} 失败: {e}")

        # 按分数排序并限制结果数量
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:limit]

    def _search_sqlite(
        self, query_vector: list[float], limit: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """搜索SQLite"""
        results = []

        # 搜索记忆数据库
        try:
            memory_results = self._search_memory_db(query_vector, limit // 2, filters)
            results.extend(memory_results)
        except Exception as e:
            logger.warning(f"⚠️ 记忆数据库搜索失败: {e}")

        # 搜索元数据库
        try:
            metadata_results = self._search_metadata_db(query_vector, limit // 2, filters)
            results.extend(metadata_results)
        except Exception as e:
            logger.warning(f"⚠️ 元数据库搜索失败: {e}")

        return results

    def _search_memory_db(
        self, query_vector: list[float], limit: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """搜索记忆数据库"""
        conn = sqlite3.connect(self.memory_db_path)
        cursor = conn.cursor()

        # 简单的相似度搜索(实际应用中可以使用更复杂的算法)
        cursor.execute(
            """
            SELECT id, content, embedding_data, created_at, category, importance_score
            FROM athena_memories
            WHERE embedding_data IS NOT NULL
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            memory_id, content, embedding_blob, created_at, category, importance_score = row

            # 计算余弦相似度
            if embedding_blob:
                stored_vector = np.frombuffer(embedding_blob, dtype=np.float32)
                similarity = self._cosine_similarity(query_vector, stored_vector.tolist())

                results.append(
                    {
                        "id": memory_id,
                        "score": similarity,
                        "payload": {
                            "content": content,
                            "created_at": created_at,
                            "category": category,
                            "importance_score": importance_score,
                        },
                        "storage_type": "sqlite",
                        "table": "athena_memories",
                    }
                )

        conn.close()
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _search_metadata_db(
        self, query_vector: list[float], limit: int, filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """搜索元数据库"""
        conn = sqlite3.connect(self.metadata_db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT vector_id, document_id, collection_name, tags, confidence, created_at
            FROM vector_metadata_enhanced
            WHERE status = 'active'
            LIMIT ?
        """,
            (limit,),
        )

        results = []
        for row in cursor.fetchall():
            vector_id, document_id, collection_name, tags, confidence, created_at = row

            # 元数据搜索主要基于标签和文本匹配,这里使用置信度作为分数
            results.append(
                {
                    "id": vector_id,
                    "score": confidence,
                    "payload": {
                        "document_id": document_id,
                        "collection_name": collection_name,
                        "tags": tags,
                        "confidence": confidence,
                        "created_at": created_at,
                    },
                    "storage_type": "sqlite",
                    "table": "vector_metadata_enhanced",
                }
            )

        conn.close()
        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """计算余弦相似度"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)

        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    def sync_data(self, direction: str = "qdrant_to_sqlite") -> dict[str, Any]:
        """数据同步"""
        if direction == "qdrant_to_sqlite":
            return self._archive_old_data()
        else:
            return self._restore_hot_data()

    def _archive_old_data(self) -> dict[str, Any]:
        """将旧数据从Qdrant归档到SQLite"""
        logger.info("📦 开始归档旧数据...")

        archived_count = 0

        # 这里应该实现具体的数据归档逻辑
        # 遍历Qdrant中的旧数据,移动到SQLite

        return {
            "status": "success",
            "archived_count": archived_count,
            "message": f"成功归档 {archived_count} 条数据",
        }

    def _restore_hot_data(self) -> dict[str, Any]:
        """将热数据从SQLite恢复到Qdrant"""
        logger.info("🔥 开始恢复热数据...")

        restored_count = 0

        # 这里应该实现具体的数据恢复逻辑
        # 遍历SQLite中的热数据,移动到Qdrant

        return {
            "status": "success",
            "restored_count": restored_count,
            "message": f"成功恢复 {restored_count} 条数据",
        }

    def get_storage_statistics(self) -> dict[str, Any]:
        """获取存储统计信息"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "qdrant": {},
            "sqlite": {},
            "routing_stats": {},
        }

        # Qdrant统计
        for collection_name in self.qdrant_manager.existing_collections:
            try:
                info = self.qdrant_manager.get_collection_info(collection_name)
                if info:
                    stats["qdrant"][collection_name] = {
                        "points_count": info.get("points_count", 0),
                        "vector_size": info.get("config", {})
                        .get("params", {})
                        .get("vectors", {})
                        .get("size", 0),
                        "status": info.get("status", "unknown"),
                    }
            except Exception as e:
                logger.warning(f"⚠️ 获取Qdrant统计失败 {collection_name}: {e}")

        # SQLite统计
        try:
            # 记忆数据库统计
            if os.path.exists(self.memory_db_path):
                conn = sqlite3.connect(self.memory_db_path)
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT COUNT(*) FROM athena_memories WHERE embedding_data IS NOT NULL"
                )
                memory_vectors = cursor.fetchone()[0]

                stats["sqlite"]["athena_memories"] = {
                    "vectors_count": memory_vectors,
                    "database_size": os.path.getsize(self.memory_db_path),
                }

                conn.close()

            # 元数据库统计
            if os.path.exists(self.metadata_db_path):
                conn = sqlite3.connect(self.metadata_db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT COUNT(*) FROM vector_metadata_enhanced")
                metadata_count = cursor.fetchone()[0]

                stats["sqlite"]["vector_metadata"] = {
                    "records_count": metadata_count,
                    "database_size": os.path.getsize(self.metadata_db_path),
                }

                conn.close()

        except Exception as e:
            logger.warning(f"⚠️ 获取SQLite统计失败: {e}")

        return stats


def main() -> None:
    """主函数 - 测试混合存储管理器"""
    logger.info("🏗️ 混合存储管理器测试")
    logger.info(str("=" * 60))

    manager = HybridStorageManager()

    # 显示配置
    logger.info("📊 存储配置:")
    logger.info(f"  - 热存储: {manager.storage_config['hot_storage']['type'].value}")
    logger.info(f"  - 冷存储: {manager.storage_config['cold_storage']['type'].value}")
    logger.info(f"  - Qdrant集合数: {len(manager.qdrant_manager.existing_collections)}")
    print()

    # 测试存储决策
    test_data = [
        {
            "name": "热数据测试",
            "data": {
                "content": "最近创建的重要记忆",
                "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                "access_count": 20,
                "category": "general",
            },
        },
        {
            "name": "冷数据测试",
            "data": {
                "content": "很久以前的历史记录",
                "created_at": (datetime.now() - timedelta(days=100)).isoformat(),
                "access_count": 2,
                "category": "general",
            },
        },
        {
            "name": "元数据测试",
            "data": {
                "vector_id": "test_vec_001",
                "document_id": "doc_001",
                "tags": "测试,向量",
                "confidence": 0.95,
            },
        },
    ]

    logger.info("🧠 存储决策测试:")
    for test in test_data:
        decision = manager.decide_storage_location(test["data"])
        logger.info(f"  {test['name']}:")
        logger.info(f"    - 存储位置: {decision.storage_type.value}")
        logger.info(f"    - 目标集合: {decision.collection_name}")
        logger.info(f"    - 决策原因: {decision.reason}")
        print()

    # 测试向量存储
    logger.info("💾 向量存储测试:")
    test_vector = random(1024).tolist()

    store_result = manager.store_vector(
        "test_vector_001",
        test_vector,
        {
            "content": "测试向量存储",
            "category": "test",
            "created_at": datetime.now().isoformat(),
            "access_count": 15,
        },
    )

    logger.info(f"  存储结果: {store_result['status']}")
    logger.info(f"  存储位置: {store_result['storage_type']}")
    print()

    # 测试向量搜索
    logger.info("🔍 向量搜索测试:")
    search_results = manager.search_vectors(test_vector, limit=5)

    logger.info(f"  搜索时间: {search_results['search_time']:.3f}秒")
    logger.info(f"  总结果数: {search_results['total_results']}")
    logger.info(f"  Qdrant结果: {len(search_results['qdrant_results'])}")
    logger.info(f"  SQLite结果: {len(search_results['sqlite_results'])}")
    print()

    # 获取统计信息
    logger.info("📊 存储统计:")
    stats = manager.get_storage_statistics()

    logger.info(f"  Qdrant集合数: {len(stats['qdrant'])}")
    logger.info(f"  SQLite数据库数: {len(stats['sqlite'])}")

    logger.info("\n✅ 混合存储管理器测试完成")

    return manager


if __name__ == "__main__":
    manager = main()
