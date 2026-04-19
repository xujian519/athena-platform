#!/usr/bin/env python3
"""
记忆系统 (Memory System)
统一的三层记忆管理接口

整合三层记忆:
1. 工作记忆 (WorkingMemory) - Redis - 短期快速访问
2. 语义记忆 (SemanticMemory) - Neo4j+Qdrant - 长期知识
3. 情景记忆 (EpisodicMemory) - PostgreSQL - 经历事件

作者: Athena平台团队
创建时间: 2026-01-22
版本: v2.0.0
"""

from __future__ import annotations
import asyncio
import logging
from enum import Enum
from typing import Any

from core.xiaonuo_agent.memory.episodic_memory import (
    EpisodicMemory,
    EpisodicMemoryItem,
    ExperienceType,
    get_episodic_memory,
)
from core.xiaonuo_agent.memory.semantic_memory import (
    KnowledgeType,
    SemanticMemory,
    SemanticMemoryItem,
    get_semantic_memory,
)
from core.xiaonuo_agent.memory.working_memory import MemoryItem, WorkingMemory, get_working_memory

logger = logging.getLogger(__name__)

# 常量定义
MAX_INFO_SIZE = 10_000_000  # 10MB - 单条信息最大大小
MAX_CONTEXT_SIZE = 1000  # 最大上下文条目数


class MemoryType(Enum):
    """记忆类型"""

    WORKING = "working"  # 工作记忆(短期)
    SEMANTIC = "semantic"  # 语义记忆(知识)
    EPISODIC = "episodic"  # 情景记忆(经历)


class MemorySystem:
    """
    记忆系统 - 三层记忆统一管理

    核心功能:
    1. 自动分类记忆
    2. 智能检索(三层并行+合并)
    3. 记忆重要性评分
    4. 记忆关联
    5. 遗忘管理
    """

    def __init__(self):
        """初始化记忆系统"""
        self._working: WorkingMemory | None = None
        self._semantic: SemanticMemory | None = None
        self._episodic: EpisodicMemory | None = None

        self._initialized = False

    async def initialize(self) -> bool:
        """
        初始化记忆系统

        Returns:
            是否成功
        """
        try:
            logger.info("🧠 初始化记忆系统...")

            # 初始化各层记忆
            self._working = await get_working_memory()
            self._semantic = await get_semantic_memory()
            self._episodic = await get_episodic_memory()

            # 健康检查
            health_checks = await asyncio.gather(
                self._working.health_check(),
                self._semantic.health_check(),
                self._episodic.health_check(),
                return_exceptions=True,
            )

            if all(health_checks):
                self._initialized = True
                logger.info("✅ 记忆系统初始化完成")
                return True
            else:
                logger.error("❌ 部分记忆系统初始化失败")
                return False

        except Exception as e:
            logger.error(f"❌ 记忆系统初始化异常: {e}")
            return False

    async def remember(
        self,
        information: Any,
        context: dict[str, Any] | None = None,
        memory_type: MemoryType | None = None,
        **kwargs,
    ) -> dict[str, str]:
        """
        存储记忆(自动分类)

        Args:
            information: 信息内容
            context: 上下文信息
            memory_type: 指定记忆类型(可选,自动判断)
            **kwargs: 其他参数

        Returns:
            存储结果 {记忆层: ID}

        Raises:
            ValueError: 输入无效时
            TypeError: 类型错误时
        """
        # 输入验证
        self._validate_input(information, context)

        if not self._initialized:
            await self.initialize()

        context = context or {}
        results = {}

        # 自动分类记忆类型
        if memory_type is None:
            memory_type = self._classify_memory(information, context)

        # 根据类型存储
        if memory_type == MemoryType.WORKING:
            # 工作记忆:临时、快速访问的信息
            key = await self._working.store(
                value=information,
                importance=kwargs.get("importance", 0.5),
                tags=kwargs.get("tags"),
                ttl=kwargs.get("ttl"),
            )
            results["working"] = key

        elif memory_type == MemoryType.SEMANTIC:
            # 语义记忆:长期知识
            knowledge_id = await self._semantic.store(
                content=str(information),
                knowledge_type=kwargs.get("knowledge_type", KnowledgeType.CONCEPT),
                entities=kwargs.get("entities"),
                relations=kwargs.get("relations"),
                metadata=context,
                confidence=kwargs.get("confidence", 1.0),
            )
            results["semantic"] = knowledge_id

        elif memory_type == MemoryType.EPISODIC:
            # 情景记忆:经历事件
            episode_id = await self._episodic.store(
                content=str(information),
                experience_type=kwargs.get("experience_type", ExperienceType.INTERACTION),
                context=context,
                participants=kwargs.get("participants"),
                emotional_tag=kwargs.get("emotional_tag"),
                importance=kwargs.get("importance", 0.5),
                metadata=kwargs.get("metadata"),
            )
            results["episodic"] = episode_id

        logger.info(f"💾 记忆存储完成: {memory_type.value} -> {results}")
        return results

    async def recall(
        self,
        query: str,
        memory_types: list[MemoryType] | None = None,
        top_k: int = 10,
        context: dict[str, Any] | None = None,
    ) -> dict[MemoryType, list[Any]]:
        """
        检索记忆(并行搜索三层)

        Args:
            query: 查询内容
            memory_types: 指定搜索的记忆类型(可选,默认全部)
            top_k: 每层返回数量
            context: 查询上下文

        Returns:
            检索结果 {记忆层: [记忆项]}
        """
        if not self._initialized:
            await self.initialize()

        if memory_types is None:
            memory_types = [MemoryType.WORKING, MemoryType.SEMANTIC, MemoryType.EPISODIC]

        results = {}
        tasks = []

        # 并行搜索各层记忆
        if MemoryType.WORKING in memory_types:
            tasks.append(self._search_working(query, top_k, context))

        if MemoryType.SEMANTIC in memory_types:
            tasks.append(self._search_semantic(query, top_k, context))

        if MemoryType.EPISODIC in memory_types:
            tasks.append(self._search_episodic(query, top_k, context))

        # 等待所有搜索完成
        search_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for i, memory_type in enumerate(memory_types):
            if i < len(search_results) and not isinstance(search_results[i], Exception):
                results[memory_type] = search_results[i]

        logger.debug(
            f"🔍 记忆检索完成: {len(results)}层, 总计{sum(len(v) for v in results.values())}条"
        )
        return results

    async def _search_working(
        self, query: str, top_k: int, context: dict[str, Any]
    ) -> list[MemoryItem]:
        """搜索工作记忆"""
        tags = context.get("tags") if context else None
        return await self._working.search(query, top_k=top_k, tags=tags)

    async def _search_semantic(
        self, query: str, top_k: int, context: dict[str, Any]
    ) -> list[SemanticMemoryItem]:
        """搜索语义记忆"""
        knowledge_type = context.get("knowledge_type") if context else None
        if isinstance(knowledge_type, str):
            knowledge_type = KnowledgeType(knowledge_type)

        return await self._semantic.search(
            query,
            top_k=top_k,
            knowledge_type=knowledge_type,
            min_confidence=context.get("min_confidence", 0.0) if context else 0.0,
        )

    async def _search_episodic(
        self, query: str, top_k: int, context: dict[str, Any]
    ) -> list[EpisodicMemoryItem]:
        """搜索情景记忆"""
        # 默认按内容搜索
        return await self._episodic.search_by_content(query, top_k=top_k)

    async def forget(self, memory_type: MemoryType, id: str) -> bool:
        """
        遗忘记忆(删除)

        Args:
            memory_type: 记忆类型
            id: 记忆ID

        Returns:
            是否成功
        """
        if not self._initialized:
            await self.initialize()

        success = False

        if memory_type == MemoryType.WORKING:
            success = await self._working.delete(id)
        elif memory_type == MemoryType.SEMANTIC:
            success = await self._semantic.delete(id)
        elif memory_type == MemoryType.EPISODIC:
            success = await self._episodic.delete(id)

        if success:
            logger.info(f"🗑️  记忆删除: {memory_type.value} -> {id}")

        return success

    async def consolidate(self) -> dict[str, Any]:
        """
        巩固记忆(将工作记忆转移到长期记忆)

        Returns:
            巩固结果统计
        """
        logger.info("🔄 开始记忆巩固...")

        # 获取工作记忆中的重要记忆
        recent_memories = await self._working.get_recent(n=50)

        consolidated = {"to_semantic": 0, "to_episodic": 0, "errors": []}

        for memory in recent_memories:
            try:
                if memory.importance > 0.7:
                    # 高重要性:转移到语义记忆
                    await self._semantic.store(
                        content=str(memory.value),
                        knowledge_type=KnowledgeType.FACT,
                        entities=memory.tags,
                        confidence=memory.importance,
                    )
                    consolidated["to_semantic"] += 1

                    # 从工作记忆删除
                    await self._working.delete(memory.key)

            except Exception as e:
                consolidated["errors"].append(str(e))

        logger.info(f"✅ 记忆巩固完成: {consolidated}")
        return consolidated

    async def get_timeline(
        self, days: int = 7, participant: str | None = None
    ) -> dict[str, list[EpisodicMemoryItem]]:
        """
        获取记忆时间线

        Args:
            days: 天数
            participant: 参与者过滤

        Returns:
            时间线 {日期: [经历]}
        """
        if not self._initialized:
            await self.initialize()

        return await self._episodic.get_timeline(participant=participant, days=days)

    async def get_stats(self) -> dict[str, Any]:
        """
        获取记忆系统统计信息

        Returns:
            统计信息
        """
        if not self._initialized:
            await self.initialize()

        stats = await asyncio.gather(
            self._working.get_stats(),
            self._semantic.get_stats(),
            self._episodic.get_stats(),
            return_exceptions=True,
        )

        return {
            "working_memory": stats[0] if not isinstance(stats[0], Exception) else {},
            "semantic_memory": stats[1] if not isinstance(stats[1], Exception) else {},
            "episodic_memory": stats[2] if not isinstance(stats[2], Exception) else {},
            "system_initialized": self._initialized,
        }

    def _validate_input(self, information: Any, context: dict[str, Any] | None = None) -> None:
        """
        验证输入参数

        Args:
            information: 信息内容
            context: 上下文信息

        Raises:
            ValueError: 输入无效时
            TypeError: 类型错误时
        """
        # 检查information不为None
        if information is None:
            raise ValueError("information cannot be None")

        # 检查信息大小
        info_str = str(information)
        info_size = len(info_str.encode("utf-8"))
        if info_size > MAX_INFO_SIZE:
            raise ValueError(
                f"information size ({info_size} bytes) " f"exceeds maximum ({MAX_INFO_SIZE} bytes)"
            )

        # 检查context大小
        if context:
            if not isinstance(context, dict):
                raise TypeError("context must be a dictionary")

            if len(context) > MAX_CONTEXT_SIZE:
                raise ValueError(
                    f"context size ({len(context)}) " f"exceeds maximum ({MAX_CONTEXT_SIZE})"
                )

    def _classify_memory(self, information: Any, context: dict[str, Any]) -> MemoryType:
        """
        自动分类记忆类型

        分类规则:
        1. 工作记忆:临时、对话、低重要性
        2. 语义记忆:知识、概念、规则
        3. 情景记忆:经历、事件、情感

        Args:
            information: 信息内容
            context: 上下文

        Returns:
            记忆类型
        """
        info_str = str(information).lower()

        # 情景记忆关键词
        episode_keywords = ["经历", "事件", "昨天", "上周", "讨论", "对话", "完成", "失败", "成功"]
        if any(kw in info_str for kw in episode_keywords):
            return MemoryType.EPISODIC

        # 语义记忆关键词
        semantic_keywords = ["定义", "规则", "概念", "事实", "知识", "方法", "专利", "法律"]
        if any(kw in info_str for kw in semantic_keywords):
            return MemoryType.SEMANTIC

        # 根据重要性判断
        importance = context.get("importance", 0.5)
        if importance > 0.7:
            return MemoryType.SEMANTIC
        elif importance < 0.3:
            return MemoryType.WORKING

        # 默认:工作记忆
        return MemoryType.WORKING

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            是否健康
        """
        if not self._initialized:
            return False

        checks = await asyncio.gather(
            self._working.health_check(),
            self._semantic.health_check(),
            self._episodic.health_check(),
            return_exceptions=True,
        )

        return all(checks)

    async def close(self):
        """关闭记忆系统"""
        # 关闭工作记忆
        if self._working:
            await self._working.close()
            self._working = None

        # 关闭情景记忆连接池
        if self._episodic and self._episodic._pool:
            await self._episodic._pool.close()
            self._episodic._pool = None

        # 语义记忆的Neo4j和Qdrant客户端通常由连接池管理
        # 这里可以添加额外的清理逻辑

        self._initialized = False
        logger.info("🔌 记忆系统已关闭")


# 全局记忆系统实例
_memory_system: MemorySystem | None = None


async def get_memory_system() -> MemorySystem:
    """获取全局记忆系统实例"""
    global _memory_system
    if _memory_system is None:
        _memory_system = MemorySystem()
        await _memory_system.initialize()
    return _memory_system
