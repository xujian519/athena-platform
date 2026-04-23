#!/usr/bin/env python3
from __future__ import annotations
"""
向量存储服务
Embedding Store for Athena Memory System

提供基于SQLite的向量存储和检索功能，集成BGE-M3嵌入模型

作者: Claude Code
创建时间: 2026-04-21
"""

import json
import logging
import pickle
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import numpy as np

from core.embedding.unified_embedding_service import ModuleType, get_unified_embedding_service

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """搜索结果"""
    memory_id: str  # 记忆ID
    similarity: float  # 相似度分数 (0-1)
    memory_type: str  # 记忆类型
    category: str  # 记忆分类
    metadata: dict[str, Any]  # 元数据
    created_at: datetime  # 创建时间


class EmbeddingStore:
    """向量存储服务

    核心功能：
    - 文本向量化（集成BGE-M3）
    - 向量存储（SQLite BLOB）
    - 相似度搜索（余弦相似度）
    - 批量处理优化
    """

    def __init__(self, db_path: str) -> None:
        """初始化向量存储

        Args:
            db_path: SQLite数据库路径
        """
        self.db_path = Path(db_path).expanduser()
        self.embedding_service: Optional[Any] = None

        # 创建数据库目录
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

        logger.info(f"向量存储初始化完成 - {self.db_path}")

    def _init_db(self) -> None:
        """初始化数据库Schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # 创建向量表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_vectors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id TEXT UNIQUE NOT NULL,
                vector BLOB NOT NULL,
                memory_type TEXT NOT NULL,
                category TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建索引
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_vectors(memory_type)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_category ON memory_vectors(category)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_memory_id ON memory_vectors(memory_id)"
        )

        conn.commit()
        conn.close()

    async def _ensure_embedding_service(self) -> None:
        """确保嵌入服务已初始化"""
        if self.embedding_service is None:
            self.embedding_service = await get_unified_embedding_service()
            await self.embedding_service.initialize()

    async def embed_text(self, text: str) -> list[float]:
        """文本向量化

        Args:
            text: 待嵌入的文本

        Returns:
            向量列表（1024维，BGE-M3）
        """
        await self._ensure_embedding_service()

        try:
            result = await self.embedding_service.encode(
                texts=text, module_type=ModuleType.MEMORY
            )

            # 提取向量
            if isinstance(result["embeddings"], list):
                if len(result["embeddings"]) > 0 and isinstance(
                    result["embeddings"][0], list
                ):
                    return result["embeddings"][0]
                return result["embeddings"]
            return [result["embeddings"]]

        except Exception as e:
            logger.error(f"文本嵌入失败: {e}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本向量化

        Args:
            texts: 待嵌入的文本列表

        Returns:
            向量列表
        """
        await self._ensure_embedding_service()

        try:
            result = await self.embedding_service.encode(
                texts=texts, module_type=ModuleType.MEMORY
            )

            embeddings = result["embeddings"]

            # 标准化为列表格式
            if isinstance(embeddings, list) and len(embeddings) > 0:
                if isinstance(embeddings[0], list):
                    return embeddings
                else:
                    # 单个向量
                    return [embeddings]

            return []

        except Exception as e:
            logger.error(f"批量嵌入失败: {e}")
            raise

    async def store_vector(
        self,
        memory_id: str,
        vector: list[float],
        memory_type: str,
        category: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """存储向量

        Args:
            memory_id: 记忆唯一标识
            vector: 向量数据
            memory_type: 记忆类型（global/project）
            category: 记忆分类
            metadata: 元数据
        """
        try:
            # 序列化向量
            vector_array = np.array(vector, dtype=np.float32)
            vector_blob = pickle.dumps(vector_array)

            # 序列化元数据
            metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 检查是否已存在
            cursor.execute("SELECT id FROM memory_vectors WHERE memory_id = ?", (memory_id,))
            exists = cursor.fetchone()

            if exists:
                # 更新
                cursor.execute(
                    """
                    UPDATE memory_vectors
                    SET vector = ?, memory_type = ?, category = ?,
                        metadata = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE memory_id = ?
                    """,
                    (vector_blob, memory_type, category, metadata_json, memory_id),
                )
            else:
                # 插入
                cursor.execute(
                    """
                    INSERT INTO memory_vectors
                    (memory_id, vector, memory_type, category, metadata)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (memory_id, vector_blob, memory_type, category, metadata_json),
                )

            conn.commit()
            conn.close()

            logger.debug(f"向量存储成功 - {memory_id}")

        except Exception as e:
            logger.error(f"向量存储失败: {e}")
            raise

    async def get_vector(self, memory_id: str) -> Optional[list[float]]:
        """获取向量

        Args:
            memory_id: 记忆ID

        Returns:
            向量数据，不存在则返回None
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("SELECT vector FROM memory_vectors WHERE memory_id = ?", (memory_id,))
            result = cursor.fetchone()

            conn.close()

            if result:
                vector = pickle.loads(result[0])
                return vector.tolist()

            return None

        except Exception as e:
            logger.error(f"获取向量失败: {e}")
            return None

    async def delete_vector(self, memory_id: str) -> None:
        """删除向量

        Args:
            memory_id: 记忆ID
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memory_vectors WHERE memory_id = ?", (memory_id,))

            conn.commit()
            conn.close()

            logger.debug(f"向量删除成功 - {memory_id}")

        except Exception as e:
            logger.error(f"向量删除失败: {e}")
            raise

    async def search_similar(
        self,
        query_vector: list[float],
        top_k: int = 10,
        threshold: float = 0.7,
        memory_type: Optional[str] = None,
        category: Optional[str] = None,
    ) -> list[SearchResult]:
        """相似度搜索

        Args:
            query_vector: 查询向量
            top_k: 返回前K个结果
            threshold: 相似度阈值（0-1）
            memory_type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）

        Returns:
            搜索结果列表
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 构建查询
            query = "SELECT memory_id, vector, memory_type, category, metadata, created_at FROM memory_vectors"
            params: list[Any] = []

            conditions = []
            if memory_type:
                conditions.append("memory_type = ?")
                params.append(memory_type)
            if category:
                conditions.append("category = ?")
                params.append(category)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            cursor.execute(query, params)

            results: list[SearchResult] = []

            for memory_id, vector_blob, mem_type, cat, metadata_json, created_at_str in cursor.fetchall():
                # 反序列化向量
                vector = pickle.loads(vector_blob)

                # 计算余弦相似度
                similarity = self._cosine_similarity(query_vector, vector)

                # 过滤低相似度结果
                if similarity >= threshold:
                    # 解析元数据
                    metadata = json.loads(metadata_json) if metadata_json else {}

                    # 解析时间
                    created_at = datetime.fromisoformat(created_at_str)

                    results.append(
                        SearchResult(
                            memory_id=memory_id,
                            similarity=similarity,
                            memory_type=mem_type,
                            category=cat,
                            metadata=metadata,
                            created_at=created_at,
                        )
                    )

            conn.close()

            # 按相似度排序
            results.sort(key=lambda x: x.similarity, reverse=True)

            # 限制返回数量
            return results[:top_k]

        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []

    @staticmethod
    def _cosine_similarity(vec1: list[float] | np.ndarray, vec2: list[float] | np.ndarray) -> float:
        """计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度分数（0-1）
        """
        # 转换为numpy数组
        arr1 = np.array(vec1, dtype=np.float32)
        arr2 = np.array(vec2, dtype=np.float32)

        # 计算点积和模长
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        # 避免除零
        if norm1 == 0 or norm2 == 0:
            return 0.0

        # 返回余弦相似度
        return float(dot_product / (norm1 * norm2))

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息

        Returns:
            统计信息字典
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 总向量数
            cursor.execute("SELECT COUNT(*) FROM memory_vectors")
            total_vectors = cursor.fetchone()[0]

            # 按类型统计
            cursor.execute(
                "SELECT memory_type, COUNT(*) FROM memory_vectors GROUP BY memory_type"
            )
            type_stats = dict(cursor.fetchall())

            # 按分类统计
            cursor.execute(
                "SELECT category, COUNT(*) FROM memory_vectors GROUP BY category"
            )
            category_stats = dict(cursor.fetchall())

            conn.close()

            return {
                "total_vectors": total_vectors,
                "by_type": type_stats,
                "by_category": category_stats,
                "db_path": str(self.db_path),
            }

        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "total_vectors": 0,
                "by_type": {},
                "by_category": {},
                "db_path": str(self.db_path),
            }

    async def clear_all(self) -> None:
        """清空所有向量"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute("DELETE FROM memory_vectors")

            conn.commit()
            conn.close()

            logger.info("所有向量已清空")

        except Exception as e:
            logger.error(f"清空向量失败: {e}")
            raise


# 便捷函数
async def get_embedding_store(db_path: str = "~/.athena/memory/memory_vectors.db") -> EmbeddingStore:
    """获取向量存储实例

    Args:
        db_path: 数据库路径

    Returns:
        EmbeddingStore实例
    """
    return EmbeddingStore(db_path=db_path)


# 导出
__all__ = ["EmbeddingStore", "SearchResult", "get_embedding_store"]
