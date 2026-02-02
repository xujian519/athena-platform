#!/usr/bin/env python3
"""
上下文管理器
Context Manager

智能检索和注入相关上下文,为Agent提供历史记忆和背景信息

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器 - 智能检索和注入相关上下文"""

    def __init__(self, agent_id: str, config: dict | None = None):
        self.agent_id = agent_id
        self.config = config or {}
        self.vector_memory = None
        self.initialized = False

        # 上下文缓存
        self.context_cache = {}
        self.cache_ttl = self.config.get("cache_ttl", 300)  # 5分钟缓存

        # 检索配置
        self.max_context_items = self.config.get("max_context_items", 5)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.3)
        self.context_categories = self.config.get(
            "context_categories", ["identity", "family", "conversation", "knowledge"]
        )

    async def initialize(self):
        """初始化上下文管理器"""
        logger.info(f"🔄 初始化上下文管理器: {self.agent_id}")

        try:
            # 获取向量记忆实例
            from ..memory.vector_memory import get_vector_memory_instance

            self.vector_memory = await get_vector_memory_instance(
                self.agent_id, self.config.get("vector_memory", {})
            )

            self.initialized = True
            logger.info(f"✅ 上下文管理器初始化完成: {self.agent_id}")

        except Exception as e:
            logger.error(f"❌ 上下文管理器初始化失败: {e}")
            raise

    async def get_relevant_context(
        self, query: str, context_type: str = "general"
    ) -> dict[str, Any]:
        """获取相关上下文"""
        if not self.initialized:
            await self.initialize()

        # 检查缓存
        cache_key = f"{hash(query)}_{context_type}"
        if cache_key in self.context_cache:
            cached_time, cached_result = self.context_cache[cache_key]
            if (datetime.now().timestamp() - cached_time) < self.cache_ttl:
                logger.debug(f"使用缓存的上下文: {query[:50]}...")
                return cached_result

        try:
            # 并行检索不同类别的上下文
            context_tasks = []

            # 身份上下文 - 优先级最高
            context_tasks.append(self._search_context(query, "identity", importance_threshold=8))

            # 家族关系上下文
            context_tasks.append(self._search_context(query, "family", importance_threshold=7))

            # 对话历史上下文
            context_tasks.append(
                self._search_context(query, "conversation", importance_threshold=6)
            )

            # 知识点上下文
            context_tasks.append(self._search_context(query, "knowledge", importance_threshold=5))

            # 等待所有检索完成
            results = await asyncio.gather(*context_tasks, return_exceptions=True)

            # 合并和排序结果
            all_contexts = []
            for result in results:
                if isinstance(result, dict) and "memories" in result:
                    all_contexts.extend(result["memories"])

            # 按重要性排序
            all_contexts.sort(key=lambda x: x.get("importance", 0), reverse=True)

            # 构建上下文响应
            context_response = {
                "query": query,
                "context_type": context_type,
                "total_found": len(all_contexts),
                "contexts": all_contexts[: self.max_context_items],
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
            }

            # 缓存结果
            self.context_cache[cache_key] = (datetime.now().timestamp(), context_response)

            # 清理过期缓存
            await self._cleanup_cache()

            return context_response

        except Exception as e:
            logger.error(f"❌ 获取上下文失败: {e}")
            return {
                "query": query,
                "context_type": context_type,
                "total_found": 0,
                "contexts": [],
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
            }

    async def _search_context(
        self, query: str, category: str, importance_threshold: int = 0
    ) -> dict[str, Any]:
        """搜索特定类别的上下文"""
        try:
            result = await self.vector_memory.search_memories(
                query=query,
                category=category,
                k=self.max_context_items,
                threshold=self.similarity_threshold,
            )

            # 过滤重要性
            if "memories" in result:
                result["memories"] = [
                    m for m in result["memories"] if m.get("importance", 0) >= importance_threshold
                ]

            return result

        except Exception as e:
            logger.debug(f"搜索{category}上下文失败: {e}")
            return {"memories": []}

    async def inject_context(self, query: str) -> tuple[str, list[dict]]:
        """将上下文注入到查询中"""
        context_response = await self.get_relevant_context(query)

        # 构建上下文提示
        context_prompt = self._build_context_prompt(context_response.get("contexts", []))

        # 构建增强查询
        if context_prompt:
            enhanced_query = f"""
# 相关上下文
{context_prompt}

# 当前查询
{query}

# 请基于以上上下文回答当前查询
"""
        else:
            enhanced_query = query

        return enhanced_query, context_response.get("contexts", [])

    def _build_context_prompt(self, contexts: list[dict]) -> str:
        """构建上下文提示"""
        if not contexts:
            return ""

        prompt_lines = []

        # 按类别组织上下文
        categorized = defaultdict(list)
        for ctx in contexts:
            category = ctx.get("category", "unknown")
            categorized[category].append(ctx)

        # 为每个类别构建提示
        for category, items in categorized.items():
            if category == "identity":
                prompt_lines.append("## 身份信息")
                for item in items[:2]:  # 限制每个类别的项目数
                    content = item.get("content", "")
                    prompt_lines.append(f"- {content}")

            elif category == "family":
                prompt_lines.append("\n## 家庭关系")
                for item in items[:2]:
                    content = item.get("content", "")
                    prompt_lines.append(f"- {content}")

            elif category == "conversation":
                prompt_lines.append("\n## 相关对话")
                for item in items[:3]:
                    content = item.get("content", "")
                    date = item.get("date", "")
                    prompt_lines.append(f"- ({date}) {content}")

            elif category == "knowledge":
                prompt_lines.append("\n## 相关知识")
                for item in items[:2]:
                    content = item.get("content", "")
                    prompt_lines.append(f"- {content}")

        return "\n".join(prompt_lines)

    async def store_conversation(self, text: str, context_info: dict[str, Any] | None = None):
        """存储对话到上下文库"""
        if not self.initialized:
            await self.initialize()

        metadata = {
            "type": "conversation",
            "timestamp": datetime.now().isoformat(),
            **(context_info or {}),
        }

        await self.vector_memory.store_memory(
            content=text, category="conversation", metadata=metadata
        )

        # 清除相关缓存
        await self._clear_cache_for_query(text)

    async def store_memory(self, text: str, category: str, metadata: dict[str, Any] | None = None):
        """存储记忆到上下文库"""
        if not self.initialized:
            await self.initialize()

        final_metadata = {
            "type": "memory",
            "timestamp": datetime.now().isoformat(),
            **(metadata or {}),
        }

        await self.vector_memory.store_memory(
            content=text, category=category, metadata=final_metadata
        )

    async def _cleanup_cache(self):
        """清理过期缓存"""
        current_time = datetime.now().timestamp()
        expired_keys = [
            key
            for key, (timestamp, _) in self.context_cache.items()
            if (current_time - timestamp) > self.cache_ttl
        ]

        for key in expired_keys:
            del self.context_cache[key]

    async def _clear_cache_for_query(self, query: str):
        """清除查询相关的缓存"""
        # 简单的模糊匹配清除
        query_hash = str(hash(query))
        keys_to_remove = []

        for cache_key in self.context_cache:
            if query_hash in str(cache_key):
                keys_to_remove.append(cache_key)

        for key in keys_to_remove:
            del self.context_cache[key]

    async def get_context_stats(self) -> dict[str, Any]:
        """获取上下文统计信息"""
        if not self.initialized:
            await self.initialize()

        # 获取向量库统计
        memory_stats = await self.vector_memory.get_memory_stats()

        # 添加上下文管理器统计
        context_stats = {
            "cache_size": len(self.context_cache),
            "cache_ttl": self.cache_ttl,
            "max_context_items": self.max_context_items,
            "similarity_threshold": self.similarity_threshold,
        }

        return {**memory_stats, "context_manager": context_stats, "agent_id": self.agent_id}

    async def search_memories(self, query: str, **kwargs) -> list[dict]:
        """搜索记忆(兼容接口)"""
        context_response = await self.get_relevant_context(query)
        return context_response.get("contexts", [])

    async def shutdown(self):
        """关闭上下文管理器"""
        logger.info(f"🔄 关闭上下文管理器: {self.agent_id}")
        self.context_cache.clear()
        self.initialized = False


# 全局上下文管理器实例
_context_managers = {}


async def get_context_manager(agent_id: str, config: dict | None = None) -> ContextManager:
    """获取上下文管理器实例"""
    if agent_id not in _context_managers:
        manager = ContextManager(agent_id, config)
        await manager.initialize()
        _context_managers[agent_id] = manager

    return _context_managers[agent_id]


async def shutdown_all_context_managers():
    """关闭所有上下文管理器"""
    for manager in _context_managers.values():
        await manager.shutdown()
    _context_managers.clear()
