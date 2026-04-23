#!/usr/bin/env python3
from __future__ import annotations
"""
增强的时间线记忆系统 - 集成向量存储
Timeline Memory System with Vector Integration

这是时间线记忆系统的增强版本,在原有三类记忆基础上:
1. 自动将记忆向量化存储到Qdrant
2. 支持语义搜索记忆
3. 双存储:JSONL(完整)+ 向量(语义检索)

作者: 小诺·双鱼公主
创建时间: 2025-12-23
版本: v2.0.0 "向量增强"
"""


import json
import logging
from datetime import datetime
from typing import Any

from core.nlp.bge_embedding_service import get_bge_service

# 导入向量库和BGE服务
from .family_memory_vector_db import FamilyMemoryVectorDB, MemoryVector, get_family_memory_db

# 导入基础时间线记忆系统
from .timeline_memory_system import TimelineMemory

logger = logging.getLogger(__name__)


class TimelineMemoryWithVector(TimelineMemory):
    """增强的时间线记忆系统 - 集成向量存储"""

    def __init__(self, base_path: str | None = None):
        """初始化记忆系统"""
        super().__init__(base_path)

        # 向量数据库
        self.vector_db: FamilyMemoryVectorDB | None = None
        self.bge_service = None

    async def initialize_vector(self):
        """初始化向量数据库"""
        if self.vector_db is None:
            self.vector_db = get_family_memory_db()
            await self.vector_db.initialize()

        # 初始化BGE服务
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    async def add_episodic_memory(
        self,
        title: str,
        content: str,
        event_date: str | None = None,
        participants: list[str] | None = None,
        tags: list[str] | None = None,
        emotional_weight: float = 0.5,
        key_event: bool = False,
        auto_vectorize: bool = True,
    ) -> str:
        """
        添加情节记忆(带向量化)

        Args:
            auto_vectorize: 是否自动向量化存储
        """
        # 先添加到JSONL
        memory_id = await super().add_episodic_memory(
            title=title,
            content=content,
            event_date=event_date,
            participants=participants,
            tags=tags,
            emotional_weight=emotional_weight,
            key_event=key_event,
        )

        # 如果启用向量化
        if auto_vectorize:
            await self._vectorize_memory(
                memory_id=memory_id,
                content=content,
                memory_type="episodic",
                title=title,
                agent="小诺",  # 默认记录者
                emotional_weight=emotional_weight,
                tags=tags or [],
                participants=participants or [],
                event_date=event_date,
            )

        return memory_id

    async def add_semantic_memory(
        self,
        category: str,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: str | None = None,
        tags: list[str] | None = None,
        auto_vectorize: bool = True,
    ) -> str:
        """
        添加语义记忆(带向量化)
        """
        # 构建内容描述用于向量化
        content = f"{category}: {key} = {value}"

        # 先添加到JSONL
        memory_id = await super().add_semantic_memory(
            category=category, key=key, value=value, confidence=confidence, source=source, tags=tags
        )

        # 如果启用向量化
        if auto_vectorize:
            await self._vectorize_memory(
                memory_id=memory_id,
                content=content,
                memory_type="semantic",
                title=key,
                agent="小诺",
                emotional_weight=0.5,
                tags=tags or [],
                participants=[],
                metadata={"category": category, "original_value": str(value)},
            )

        return memory_id

    async def add_procedural_memory(
        self,
        skill_name: str,
        steps: list[str],
        context: str | None = None,
        frequency: int = 1,
        proficiency: float = 0.5,
        tags: list[str] | None = None,
        auto_vectorize: bool = True,
    ) -> str:
        """
        添加程序记忆(带向量化)
        """
        # 构建内容描述用于向量化
        content = f"{skill_name}: {', '.join(steps[:3])}..."

        # 先添加到JSONL
        memory_id = await super().add_procedural_memory(
            skill_name=skill_name,
            steps=steps,
            context=context,
            frequency=frequency,
            proficiency=proficiency,
            tags=tags,
        )

        # 如果启用向量化
        if auto_vectorize:
            await self._vectorize_memory(
                memory_id=memory_id,
                content=content,
                memory_type="procedural",
                title=skill_name,
                agent="小诺",
                emotional_weight=0.5,
                tags=tags or [],
                participants=[],
                metadata={"steps_count": len(steps), "proficiency": proficiency},
            )

        return memory_id

    async def _vectorize_memory(
        self,
        memory_id: str,
        content: str,
        memory_type: str,
        title: str = "",
        agent: str = "小诺",
        emotional_weight: float = 0.5,
        tags: list[str] | None = None,
        participants: list[str] | None = None,
        event_date: str | None = None,
        metadata: dict | None = None,
    ):
        """将记忆向量化存储"""
        try:
            await self.initialize_vector()

            # 生成向量
            embedding_result = await self.bge_service.encode(content)
            embedding = embedding_result.embeddings

            # 创建记忆向量对象
            memory_vector = MemoryVector(
                memory_id=memory_id,
                content=content,
                memory_type=memory_type,
                agent=agent,
                timestamp=datetime.now().isoformat(),
                title=title,
                emotional_weight=emotional_weight,
                tags=tags or [],
                participants=participants or [],
                metadata=metadata or {},
            )

            # 添加到向量库
            await self.vector_db.add_memory(memory_vector, embedding)

        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    async def semantic_search(
        self, query: str, limit: int = 10, memory_type: str | None = None
    ) -> list[dict]:
        """
        语义搜索记忆

        Args:
            query: 查询文本
            limit: 返回数量
            memory_type: 记忆类型过滤
        """
        try:
            await self.initialize_vector()

            # 生成查询向量
            embedding_result = await self.bge_service.encode(query)
            query_embedding = embedding_result.embeddings

            # 执行搜索
            results = await self.vector_db.semantic_search(
                query_embedding=query_embedding, limit=limit, memory_type=memory_type
            )

            return results

        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    async def recall_memories(self, query: str, limit: int = 5) -> str:
        """
        回忆相关记忆(自然语言接口)

        Args:
            query: 查询文本,如"关于诗歌的记忆"
            limit: 返回数量

        Returns:
            格式化的回忆结果
        """
        results = await self.semantic_search(query, limit=limit)

        if not results:
            return f"🔍 没有找到关于'{query}'的记忆"

        output = f"🔍 关于'{query}'的记忆 ({len(results)} 条):\n\n"

        for i, result in enumerate(results, 1):
            payload = result.get("payload", {})
            score = result.get("score", 0)

            memory_type = payload.get("memory_type", "")
            title = payload.get("title", payload.get("memory_id", ""))
            content = payload.get("content", "")

            type_emoji = {"episodic": "📜", "semantic": "📚", "procedural": "🛠️"}.get(
                memory_type, "📝"
            )

            output += f"{i}. {type_emoji} {title}\n"
            output += f"   {content[:100]}{'...' if len(content) > 100 else ''}\n"
            output += f"   相似度: {score:.4f}\n\n"

        return output


# 便捷函数
_memory_with_vector = None


async def get_timeline_memory_with_vector() -> TimelineMemoryWithVector:
    """获取增强的时间线记忆系统单例"""
    global _memory_with_vector
    if _memory_with_vector is None:
        _memory_with_vector = TimelineMemoryWithVector()
        await _memory_with_vector.initialize_vector()
    return _memory_with_vector


# 批量导入历史记忆
async def import_historical_memories():
    """将历史记忆批量导入向量库"""

    print("\n" + "=" * 60)
    print("📦 批量导入历史记忆到向量库")
    print("=" * 60 + "\n")

    # 获取增强的记忆系统
    memory = TimelineMemoryWithVector()
    await memory.initialize_vector()

    # 读取所有历史记忆
    memories_file = memory.base_path / "complete_timeline.jsonl"

    if not memories_file.exists():
        print("❌ 没有找到历史记忆文件")
        return

    memories = []
    with open(memories_file, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                memories.append(json.loads(line))

    print(f"📋 找到 {len(memories)} 条历史记忆\n")

    # 统计各类记忆数量
    episodic_count = sum(1 for m in memories if m["type"] == "episodic")
    semantic_count = sum(1 for m in memories if m["type"] == "semantic")
    procedural_count = sum(1 for m in memories if m["type"] == "procedural")

    print(f"   情节记忆: {episodic_count} 条")
    print(f"   语义记忆: {semantic_count} 条")
    print(f"   程序记忆: {procedural_count} 条\n")

    # 批量向量化
    print("⏳ 开始向量化...")

    success_count = 0
    fail_count = 0

    for i, memory_data in enumerate(memories, 1):
        memory_id = memory_data["id"]
        memory_type = memory_data["type"]

        try:
            if memory_type == "episodic":
                # 情节记忆
                await memory._vectorize_memory(
                    memory_id=memory_id,
                    content=memory_data.get("content", ""),
                    memory_type="episodic",
                    title=memory_data.get("title", ""),
                    agent="小诺",
                    emotional_weight=memory_data.get("emotional_weight", 0.5),
                    tags=memory_data.get("tags", []),
                    participants=memory_data.get("participants", []),
                    event_date=memory_data.get("event_date"),
                )

            elif memory_type == "semantic":
                # 语义记忆
                content = f"{memory_data.get('category', '')}: {memory_data.get('key', '')} = {memory_data.get('value', '')}"
                await memory._vectorize_memory(
                    memory_id=memory_id,
                    content=content,
                    memory_type="semantic",
                    title=memory_data.get("key", ""),
                    agent="小诺",
                    emotional_weight=0.5,
                    tags=memory_data.get("tags", []),
                    participants=[],
                    metadata={
                        "category": memory_data.get("category", ""),
                        "original_value": str(memory_data.get("value", "")),
                    },
                )

            elif memory_type == "procedural":
                # 程序记忆
                steps = memory_data.get("steps", [])
                content = f"{memory_data.get('skill_name', '')}: {', '.join(steps[:3])}..."
                await memory._vectorize_memory(
                    memory_id=memory_id,
                    content=content,
                    memory_type="procedural",
                    title=memory_data.get("skill_name", ""),
                    agent="小诺",
                    emotional_weight=0.5,
                    tags=memory_data.get("tags", []),
                    participants=[],
                    metadata={
                        "steps_count": len(steps),
                        "proficiency": memory_data.get("proficiency", 0.5),
                    },
                )

            success_count += 1

            # 显示进度
            if i % 5 == 0:
                print(f"   进度: {i}/{len(memories)} ({i / len(memories) * 100:.1f}%)")

        except Exception as e:
            logger.error(f"操作失败: {e}", exc_info=True)
            raise

    print("\n✅ 批量导入完成!")
    print(f"   成功: {success_count} 条")
    print(f"   失败: {fail_count} 条")

    # 显示统计
    stats = await memory.vector_db.get_statistics()
    print("\n📊 向量库统计:")
    print(f"   总向量数: {stats['points_count']}")
    print(f"   索引向量: {stats['indexed_vectors']}")
    print(f"   状态: {stats['status']}")


# 测试代码
async def main():
    """测试代码"""

    # 1. 批量导入历史记忆
    await import_historical_memories()

    # 2. 测试语义搜索
    print("\n" + "=" * 60)
    print("🔍 测试语义搜索")
    print("=" * 60 + "\n")

    memory = await get_timeline_memory_with_vector()

    # 测试查询
    test_queries = ["关于诗歌的记忆", "爸爸的邮箱", "专利工作流程", "小诺的角色"]

    for query in test_queries:
        print(f"\n查询: {query}")
        result = await memory.recall_memories(query, limit=3)
        print(result)


# 入口点: @async_main装饰器已添加到main函数
