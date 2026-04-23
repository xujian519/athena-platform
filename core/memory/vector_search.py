#!/usr/bin/env python3
from __future__ import annotations
"""
向量搜索服务
Vector Search Service for Athena Memory System

提供混合检索（向量+关键词）和语义搜索功能

作者: Claude Code
创建时间: 2026-04-21
"""

import logging
from datetime import datetime
from typing import Any, Optional

from core.memory.unified_memory_system import MemoryEntry, MemoryCategory, MemoryType
from core.memory.embedding_store import EmbeddingStore, SearchResult

logger = logging.getLogger(__name__)


class VectorSearchService:
    """向量搜索服务

    核心功能：
    - 纯向量搜索
    - 混合检索（向量+关键词）
    - 自动索引记忆
    - 批量索引优化
    """

    def __init__(self, memory_system, embedding_store: EmbeddingStore) -> None:
        """初始化向量搜索服务

        Args:
            memory_system: 统一记忆系统实例
            embedding_store: 向量存储实例
        """
        self.memory_system = memory_system
        self.embedding_store = embedding_store

        logger.info("向量搜索服务初始化完成")

    async def search_by_vector(
        self,
        query: str,
        top_k: int = 10,
        memory_type: MemoryType | None = None,
        category: MemoryCategory | None = None,
    ) -> list[MemoryEntry]:
        """纯向量搜索

        Args:
            query: 查询文本
            top_k: 返回前K个结果
            memory_type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）

        Returns:
            匹配的记忆条目列表
        """
        try:
            # 1. 将查询文本向量化
            query_vector = await self.embedding_store.embed_text(query)

            # 2. 向量搜索
            search_results = await self.embedding_store.search_similar(
                query_vector=query_vector,
                top_k=top_k,
                threshold=0.6,  # 相似度阈值
                memory_type=memory_type.value if memory_type else None,
                category=category.value if category else None,
            )

            # 3. 转换为MemoryEntry
            results = []
            for result in search_results:
                # 从memory_id解析出type/category/key
                # 格式: "type/category/key"
                parts = result.memory_id.split("/")
                if len(parts) == 3:
                    entry_type, entry_category, key = parts

                    # 读取完整内容
                    content = self.memory_system.read(
                        type=MemoryType(entry_type),
                        category=MemoryCategory(entry_category),
                        key=key,
                    )

                    if content:
                        # 创建MemoryEntry
                        entry = MemoryEntry(
                            type=MemoryType(entry_type),
                            category=MemoryCategory(entry_category),
                            key=key,
                            content=content,
                            metadata={
                                **result.metadata,
                                "similarity": result.similarity,
                                "vector_search": True,
                            },
                            created_at=result.created_at,
                        )
                        results.append(entry)

            logger.info(f"向量搜索完成 - 查询: {query}, 结果数: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            # 降级到关键词搜索
            logger.warning("降级到关键词搜索")
            return self.memory_system.search(
                query=query,
                type=memory_type,
                category=category,
                limit=top_k,
            )

    async def search_hybrid(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.5,
        memory_type: MemoryType | None = None,
        category: MemoryCategory | None = None,
    ) -> list[MemoryEntry]:
        """混合检索（向量+关键词）

        Args:
            query: 查询文本
            top_k: 返回前K个结果
            alpha: 向量搜索权重（0.0-1.0）
                   0.0 = 纯关键词搜索
                   0.5 = 向量+关键词各占50%
                   1.0 = 纯向量搜索
            memory_type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）

        Returns:
            匹配的记忆条目列表
        """
        try:
            # 边界情况处理
            if alpha <= 0.0:
                # 纯关键词搜索
                return self.memory_system.search(
                    query=query, type=memory_type, category=category, limit=top_k
                )
            elif alpha >= 1.0:
                # 纯向量搜索
                return await self.search_by_vector(
                    query=query, top_k=top_k, memory_type=memory_type, category=category
                )

            # 1. 向量搜索
            vector_results = await self.search_by_vector(
                query=query, top_k=top_k * 2, memory_type=memory_type, category=category
            )

            # 2. 关键词搜索
            keyword_results = self.memory_system.search(
                query=query, type=memory_type, category=category, limit=top_k * 2
            )

            # 3. 合并结果（去重）
            combined_scores: dict[str, dict[str, Any]] = {}

            # 向量搜索得分（权重alpha）
            for i, entry in enumerate(vector_results):
                key = f"{entry.type.value}/{entry.category.value}/{entry.key}"
                # 位置越前得分越高
                vector_score = (1.0 - i / len(vector_results)) * alpha

                if key not in combined_scores:
                    combined_scores[key] = {
                        "entry": entry,
                        "vector_score": vector_score,
                        "keyword_score": 0.0,
                    }
                else:
                    combined_scores[key]["vector_score"] = vector_score

            # 关键词搜索得分（权重1-alpha）
            for i, entry in enumerate(keyword_results):
                key = f"{entry.type.value}/{entry.category.value}/{entry.key}"
                # 位置越前得分越高
                keyword_score = (1.0 - i / len(keyword_results)) * (1.0 - alpha)

                if key not in combined_scores:
                    combined_scores[key] = {
                        "entry": entry,
                        "vector_score": 0.0,
                        "keyword_score": keyword_score,
                    }
                else:
                    combined_scores[key]["keyword_score"] = keyword_score

            # 4. 计算综合得分并排序
            for key, data in combined_scores.items():
                data["combined_score"] = data["vector_score"] + data["keyword_score"]

            # 按综合得分排序
            sorted_results = sorted(
                combined_scores.items(), key=lambda x: x[1]["combined_score"], reverse=True
            )

            # 5. 提取top_k结果
            results = [data["entry"] for _, data in sorted_results[:top_k]]

            logger.info(f"混合检索完成 - 查询: {query}, alpha: {alpha}, 结果数: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            # 降级到关键词搜索
            logger.warning("降级到关键词搜索")
            return self.memory_system.search(
                query=query, type=memory_type, category=category, limit=top_k
            )

    async def index_memory(self, entry: MemoryEntry) -> None:
        """为记忆条目建立索引

        Args:
            entry: 记忆条目
        """
        try:
            # 生成memory_id
            memory_id = f"{entry.type.value}/{entry.category.value}/{entry.key}"

            # 检查是否已索引
            existing_vector = await self.embedding_store.get_vector(memory_id)

            # 如果内容未变化，跳过
            if existing_vector and entry.metadata.get("indexed"):
                return

            # 文本向量化
            # 组合标题和内容以提高检索质量
            text_to_embed = f"{entry.key}\n{entry.content[:2000]}"  # 限制长度
            vector = await self.embedding_store.embed_text(text_to_embed)

            # 存储向量
            await self.embedding_store.store_vector(
                memory_id=memory_id,
                vector=vector,
                memory_type=entry.type.value,
                category=entry.category.value,
                metadata={
                    "key": entry.key,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                },
            )

            logger.debug(f"记忆索引成功 - {memory_id}")

        except Exception as e:
            logger.error(f"记忆索引失败: {e}")
            # 不抛出异常，避免影响主流程

    async def batch_index_memories(
        self, entries: list[MemoryEntry], batch_size: int = 16
    ) -> dict[str, Any]:
        """批量索引记忆

        Args:
            entries: 记忆条目列表
            batch_size: 批处理大小

        Returns:
            索引统计信息
        """
        stats = {
            "total": len(entries),
            "success": 0,
            "failed": 0,
            "skipped": 0,
        }

        logger.info(f"开始批量索引 - {stats['total']}条记忆")

        for i in range(0, len(entries), batch_size):
            batch = entries[i : i + batch_size]

            for entry in batch:
                try:
                    # 检查是否需要重新索引
                    memory_id = f"{entry.type.value}/{entry.category.value}/{entry.key}"
                    existing_vector = await self.embedding_store.get_vector(memory_id)

                    # 如果已存在且内容未变化，跳过
                    if existing_vector and entry.metadata.get("indexed"):
                        stats["skipped"] += 1
                        continue

                    # 索引
                    await self.index_memory(entry)
                    stats["success"] += 1

                except Exception as e:
                    logger.error(f"索引失败 - {entry.key}: {e}")
                    stats["failed"] += 1

        logger.info(
            f"批量索引完成 - 成功: {stats['success']}, "
            f"跳过: {stats['skipped']}, 失败: {stats['failed']}"
        )

        return stats

    async def reindex_all(self) -> dict[str, Any]:
        """重新索引所有记忆

        Returns:
            索引统计信息
        """
        logger.info("开始重新索引所有记忆")

        # 1. 清空现有索引
        await self.embedding_store.clear_all()

        # 2. 收集所有记忆
        all_entries = []

        # 遍历记忆索引
        for unique_key, entry_data in self.memory_system.memory_index.items():
            try:
                # 重建MemoryEntry
                entry = MemoryEntry(
                    type=MemoryType(entry_data["type"]),
                    category=MemoryCategory(entry_data["category"]),
                    key=entry_data["key"],
                    content=entry_data["content"],
                    metadata=entry_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(entry_data["created_at"]),
                    updated_at=datetime.fromisoformat(entry_data["updated_at"]),
                )
                all_entries.append(entry)

            except Exception as e:
                logger.error(f"重建记忆条目失败 - {unique_key}: {e}")

        # 3. 批量索引
        stats = await self.batch_index_memories(all_entries, batch_size=32)

        logger.info(f"重新索引完成 - {stats}")

        return stats


# 便捷函数
async def get_vector_search_service(
    memory_system, embedding_store: EmbeddingStore | None = None
) -> VectorSearchService:
    """获取向量搜索服务实例

    Args:
        memory_system: 统一记忆系统实例
        embedding_store: 向量存储实例（可选）

    Returns:
        VectorSearchService实例
    """
    if embedding_store is None:
        from core.memory.embedding_store import get_embedding_store

        embedding_store = await get_embedding_store()

    return VectorSearchService(memory_system=memory_system, embedding_store=embedding_store)


# 导出
__all__ = ["VectorSearchService", "get_vector_search_service"]
