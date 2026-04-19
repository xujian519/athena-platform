#!/usr/bin/env python3
"""
增强记忆管理系统 (Memory Management Pattern)
基于《智能体设计》记忆管理模式的实现

功能：
- 短期记忆管理 (对话缓存)
- 长期记忆管理 (向量存储)
- 工作记忆管理 (当前任务上下文)
- 情节记忆管理 (重要事件记录)
- 记忆检索和匹配

应用场景：
- 小娜: 记忆用户专利偏好和搜索历史
- 小诺: 保存系统优化经验和教训
- 云熙: 追踪目标进展和状态变化
- 小宸: 记录内容创作灵感和素材

实施优先级: ⭐⭐⭐⭐ (高)
预期收益: 持续优化和个性化服务
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"      # 短期记忆 (对话缓存)
    LONG_TERM = "long_term"        # 长期记忆 (向量存储)
    WORKING = "working"            # 工作记忆 (当前上下文)
    EPISODIC = "episodic"          # 情节记忆 (事件记录)
    PROCEDURAL = "procedural"      # 程序记忆 (技能和流程)

class MemoryPriority(Enum):
    """记忆优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    type: MemoryType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    priority: MemoryPriority = MemoryPriority.MEDIUM
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    expiration: datetime | None = None
    embedding: list[float] | None = None  # 向量嵌入
    source: str = ""  # 来源
    related_items: list[str] = field(default_factory=list)

@dataclass
class ConversationContext:
    """对话上下文"""
    session_id: str
    user_id: str
    conversation_history: list[dict[str, Any]] = field(default_factory=list)
    current_context: dict[str, Any] = field(default_factory=dict)
    user_preferences: dict[str, Any] = field(default_factory=dict)
    last_activity: datetime = field(default_factory=datetime.now)
    total_interactions: int = 0

@dataclass
class EpisodicMemory:
    """情节记忆"""
    id: str
    event_type: str
    description: str
    timestamp: datetime = field(default_factory=datetime.now)
    entities: list[str] = field(default_factory=list)
    emotional_weight: float = 0.0  # 情感权重
    importance: float = 0.0  # 重要性评分
    resolved: bool = False
    related_memories: list[str] = field(default_factory=list)

class EnhancedMemoryManager:
    """增强记忆管理器"""

    def __init__(
        self,
        short_term_capacity: int = 1000,
        long_term_storage_path: str = "/tmp/memory_store",
        vector_dimension: int = 768,
        max_working_memory: int = 50
    ):
        # 存储配置
        self.short_term_capacity = short_term_capacity
        self.long_term_storage_path = Path(long_term_storage_path)
        self.vector_dimension = vector_dimension
        self.max_working_memory = max_working_memory

        # 确保存储目录存在
        self.long_term_storage_path.mkdir(parents=True, exist_ok=True)

        # 记忆存储
        self.short_term_memory: dict[str, MemoryItem] = {}
        self.working_memory: dict[str, Any] = {}
        self.episodic_memories: dict[str, EpisodicMemory] = {}
        self.procedural_memories: dict[str, Any] = {}

        # 对话上下文
        self.conversation_contexts: dict[str, ConversationContext] = {}

        # 统计信息
        self.stats = {
            "total_memory_items": 0,
            "short_term_items": 0,
            "long_term_items": 0,
            "episodic_items": 0,
            "retrieval_requests": 0,
            "total_retrievals": 0,
            "cache_hits": 0
        }

    async def store_memory(
        self,
        memory_id: str,
        content: Any,
        memory_type: MemoryType,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        expiration: datetime | None = None,
        embedding: list[float] | None = None,
        source: str = ""
    ) -> bool:
        """存储记忆项"""

        try:
            if tags is None:
                tags = []
            if metadata is None:
                metadata = {}

            memory_item = MemoryItem(
                id=memory_id,
                type=memory_type,
                content=content,
                priority=priority,
                tags=tags,
                metadata=metadata,
                expiration=expiration,
                embedding=embedding,
                source=source
            )

            # 根据类型存储到不同位置
            if memory_type == MemoryType.SHORT_TERM:
                await self._store_short_term(memory_item)
            elif memory_type == MemoryType.LONG_TERM:
                await self._store_long_term(memory_item)
            elif memory_type == MemoryType.WORKING:
                await self._store_working_memory(memory_id, content)
            elif memory_type == MemoryType.EPISODIC:
                # 转换为情节记忆格式
                episodic = EpisodicMemory(
                    id=memory_id,
                    event_type=metadata.get("event_type", "general"),
                    description=str(content),
                    entities=metadata.get("entities", []),
                    emotional_weight=metadata.get("emotional_weight", 0.0),
                    importance=metadata.get("importance", 0.0),
                    resolved=metadata.get("resolved", False)
                )
                self.episodic_memories[memory_id] = episodic
            elif memory_type == MemoryType.PROCEDURAL:
                self.procedural_memories[memory_id] = content

            self.stats["total_memory_items"] += 1
            logger.info(f"记忆项 {memory_id} 已存储到 {memory_type.value}")

            return True

        except Exception as e:
            logger.error(f"存储记忆失败: {e}")
            return False

    async def _store_short_term(self, memory_item: MemoryItem):
        """存储短期记忆"""
        # 检查容量限制
        if len(self.short_term_memory) >= self.short_term_capacity:
            await self._evict_lru_short_term()

        self.short_term_memory[memory_item.id] = memory_item
        self.stats["short_term_items"] += 1

    async def _store_long_term(self, memory_item: MemoryItem):
        """存储长期记忆"""
        file_path = self.long_term_storage_path / f"{memory_item.id}.json"

        memory_data = asdict(memory_item)
        # 转换datetime为字符串以便JSON序列化
        memory_data["timestamp"] = memory_item.timestamp.isoformat()
        if memory_item.expiration:
            memory_data["expiration"] = memory_item.expiration.isoformat()
        if memory_item.last_accessed:
            memory_data["last_accessed"] = memory_item.last_accessed.isoformat()

        # 添加向量嵌入到单独文件
        if memory_item.embedding:
            embedding_path = self.long_term_storage_path / f"{memory_item.id}.embedding"
            with open(embedding_path, 'w') as f:
                json.dump(memory_item.embedding, f)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)

        self.stats["long_term_items"] += 1

    async def _store_working_memory(self, key: str, value: Any):
        """存储工作记忆"""
        # 检查容量限制
        if len(self.working_memory) >= self.max_working_memory:
            await self._evict_lru_working_memory()

        self.working_memory[key] = value
        self.working_memory[f"timestamp_{key}"] = datetime.now()

    async def _evict_lru_short_term(self):
        """短期记忆LRU淘汰"""
        if not self.short_term_memory:
            return

        # 找到最久未访问的记忆项
        lru_item = min(
            self.short_term_memory.values(),
            key=lambda x: x.last_accessed
        )

        del self.short_term_memory[lru_item.id]
        self.stats["short_term_items"] -= 1
        logger.info(f"LRU淘汰短期记忆项: {lru_item.id}")

    async def _evict_lru_working_memory(self):
        """工作记忆LRU淘汰"""
        if not self.working_memory:
            return

        timestamp_keys = [k for k in self.working_memory if k.startswith("timestamp_")]
        if not timestamp_keys:
            return

        lru_timestamp_key = min(timestamp_keys)
        lru_key = lru_timestamp_key.replace("timestamp_", "")

        del self.working_memory[lru_key]
        del self.working_memory[lru_timestamp_key]
        logger.info(f"LRU淘汰工作记忆项: {lru_key}")

    async def retrieve_memory(
        self,
        memory_id: str,
        memory_type: MemoryType | None = None
    ) -> MemoryItem | None:
        """检索记忆项"""
        self.stats["retrieval_requests"] += 1

        try:
            memory_item = None

            # 从指定类型检索
            if memory_type:
                if memory_type == MemoryType.SHORT_TERM:
                    memory_item = self.short_term_memory.get(memory_id)
                elif memory_type == MemoryType.LONG_TERM:
                    memory_item = await self._retrieve_long_term(memory_id)
                elif memory_type == MemoryType.EPISODIC:
                    episodic = self.episodic_memories.get(memory_id)
                    if episodic:
                        # 转换回MemoryItem格式
                        memory_item = MemoryItem(
                            id=episodic.id,
                            type=MemoryType.EPISODIC,
                            content=episodic.description,
                            metadata={
                                "event_type": episodic.event_type,
                                "entities": episodic.entities,
                                "emotional_weight": episodic.emotional_weight,
                                "importance": episodic.importance,
                                "resolved": episodic.resolved
                            }
                        )

                if memory_item:
                    self.stats["cache_hits"] += 1
            else:
                # 从所有存储中检索
                memory_item = (
                    self.short_term_memory.get(memory_id) or
                    await self._retrieve_long_term(memory_id) or
                    self.episodic_memories.get(memory_id)
                )

                if memory_item:
                    self.stats["cache_hits"] += 1
                    # 更新访问信息
                    memory_item.access_count += 1
                    memory_item.last_accessed = datetime.now()
                    if memory_item.type == MemoryType.SHORT_TERM:
                        self.short_term_memory[memory_item.id] = memory_item

            return memory_item

        except Exception as e:
            logger.error(f"检索记忆失败: {e}")
            return None

    async def _retrieve_long_term(self, memory_id: str) -> MemoryItem | None:
        """检索长期记忆"""
        file_path = self.long_term_storage_path / f"{memory_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, encoding='utf-8') as f:
                memory_data = json.load(f)

            # 转换字符串为datetime
            memory_data["timestamp"] = datetime.fromisoformat(memory_data["timestamp"])
            if memory_data.get("expiration"):
                memory_data["expiration"] = datetime.fromisoformat(memory_data["expiration"])
            if memory_data.get("last_accessed"):
                memory_data["last_accessed"] = datetime.fromisoformat(memory_data["last_accessed"])

            # 检查是否过期
            if memory_data.get("expiration") and memory_data["expiration"] < datetime.now():
                logger.info(f"记忆项 {memory_id} 已过期，删除")
                file_path.unlink()  # 删除过期文件
                return None

            # 加载向量嵌入
            embedding_path = self.long_term_storage_path / f"{memory_id}.embedding"
            if embedding_path.exists():
                with open(embedding_path) as f:
                    memory_data["embedding"] = json.load(f)

            # 重建MemoryItem对象
            memory_item = MemoryItem(**memory_data)
            return memory_item

        except Exception as e:
            logger.error(f"检索长期记忆失败: {e}")
            return None

    async def search_memories(
        self,
        query: str,
        memory_type: MemoryType | None = None,
        limit: int = 10,
        tags: list[str] | None = None
    ) -> list[MemoryItem]:
        """搜索记忆"""
        try:
            results = []

            # 构建查询嵌入（这里使用简化版本，实际应用中需要调用嵌入模型）
            query_embedding = await self._generate_embedding(query)

            # 搜索范围
            search_scope = []
            if memory_type is None or memory_type == MemoryType.SHORT_TERM:
                search_scope.extend(self.short_term_memory.values())
            if memory_type is None or memory_type == MemoryType.LONG_TERM:
                # 简化实现：只搜索短期记忆中的文件名作为示例
                long_term_files = list(self.long_term_storage_path.glob("*.json"))
                for file_path in long_term_files:
                    memory_id = file_path.stem
                    if memory_id not in [f"{f.id}.embedding" for f in search_scope]:
                        item = await self._retrieve_long_term(memory_id)
                        if item:
                            search_scope.append(item)

            if memory_type is None or memory_type == MemoryType.EPISODIC:
                search_scope.extend(
                    [MemoryItem(
                        id=episodic.id,
                        type=MemoryType.EPISODIC,
                        content=episodic.description,
                        metadata={
                            "event_type": episodic.event_type,
                            "importance": episodic.importance
                        },
                        tags=episodic.entities
                    ) for episodic in self.episodic_memories.values()]
                )

            # 计算相似度并排序
            scored_results = []
            for item in search_scope:
                if tags and not any(tag in item.tags for tag in tags):
                    continue

                similarity = self._calculate_similarity(query_embedding, item.embedding)
                scored_results.append((similarity, item))

            # 按相似度排序并返回top结果
            scored_results.sort(key=lambda x: x[0], reverse=True)

            results = [item for _, item in scored_results[:limit]]
            return results

        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            return []

    async def retrieve_memories(
        self,
        query: str,
        memory_types: list[MemoryType] | None = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> list[MemoryItem]:
        """检索记忆"""
        retrieved_memories = []
        query_lower = query.lower()

        # 设置默认记忆类型
        if memory_types is None:
            memory_types = [MemoryType.SHORT_TERM, MemoryType.LONG_TERM, MemoryType.WORKING]

        # 搜索短期记忆
        if MemoryType.SHORT_TERM in memory_types:
            for memory_item in self.short_term_memory.values():
                if query_lower in str(memory_item.content).lower():
                    memory_item.last_accessed = datetime.now()
                    retrieved_memories.append(memory_item)

        # 搜索工作记忆
        if MemoryType.WORKING in memory_types:
            for key, value in self.working_memory.items():
                if not key.startswith("timestamp_"):
                    if query_lower in str(value).lower():
                        # 创建临时记忆项
                        temp_item = MemoryItem(
                            id=f"working_{key}",
                            content=value,
                            memory_type=MemoryType.WORKING,
                            timestamp=self.working_memory.get(f"timestamp_{key}", datetime.now())
                        )
                        retrieved_memories.append(temp_item)

        # 搜索情景记忆
        if MemoryType.EPISODIC in memory_types:
            for memory_item in self.episodic_memory.values():
                if query_lower in str(memory_item.content).lower():
                    memory_item.last_accessed = datetime.now()
                    retrieved_memories.append(memory_item)

        # 搜索长期记忆（简化版本，实际应该实现更复杂的搜索）
        if MemoryType.LONG_TERM in memory_types:
            try:
                for file_path in self.long_term_storage_path.glob("*.json"):
                    if len(retrieved_memories) >= limit:
                        break

                    with open(file_path, encoding='utf-8') as f:
                        memory_data = json.load(f)

                    if query_lower in str(memory_data.get("content", "")).lower():
                        # 重建记忆项
                        memory_item = MemoryItem(
                            id=memory_data["id"],
                            content=memory_data["content"],
                            memory_type=MemoryType.LONG_TERM,
                            timestamp=datetime.fromisoformat(memory_data["timestamp"]),
                            metadata=memory_data.get("metadata", {})
                        )
                        if "tags" in memory_data:
                            memory_item.tags = memory_data["tags"]

                        memory_item.last_accessed = datetime.now()
                        retrieved_memories.append(memory_item)

            except Exception as e:
                logger.error(f"搜索长期记忆时出错: {e}")

        # 按相关性和时间排序
        retrieved_memories.sort(key=lambda x: x.last_accessed, reverse=True)

        # 限制返回数量
        self.stats["total_retrievals"] += 1
        return retrieved_memories[:limit]

    def _generate_embedding(self, text: str) -> list[float]:
        """生成文本嵌入向量"""
        # 简化实现：使用文本哈希模拟向量嵌入
        # 实际应用中应该调用真实的嵌入模型
        text_bytes = text.encode('utf-8')
        hash_obj = hashlib.sha256(text_bytes)

        # 将哈希值转换为向量
        embedding = []
        for i in range(0, min(len(hash_obj.digest()), self.vector_dimension), 4):
            byte_val = hash_obj.digest()[i]
            for j in range(4):
                embedding.append((byte_val >> (j * 8)) & 255 / 255.0)

        # 补齐到指定维度
        while len(embedding) < self.vector_dimension:
            embedding.append(0.0)

        return embedding

    def _calculate_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """计算向量相似度"""
        if not embedding1 or not embedding2:
            return 0.0

        if len(embedding1) != len(embedding2):
            return 0.0

        # 计算余弦相似度
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2, strict=False))
        norm1 = sum(a * a for a in embedding1) ** 0.5
        norm2 = sum(b * b for b in embedding2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def store_conversation_context(self, session_id: str, user_id: str, context: dict[str, Any]):
        """存储对话上下文"""
        context_obj = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            user_preferences=context.get("preferences", {}),
            current_context=context.get("current_context", {})
        )

        self.conversation_contexts[session_id] = context_obj

    async def get_conversation_context(self, session_id: str) -> ConversationContext | None:
        """获取对话上下文"""
        return self.conversation_contexts.get(session_id)

    async def update_conversation_history(
        self,
        session_id: str,
        message: dict[str, Any]
    ):
        """更新对话历史"""
        context = await self.get_conversation_context(session_id)
        if context:
            context.conversation_history.append(message)
            context.total_interactions += 1
            context.last_activity = datetime.now()

    async def cleanup_expired_memories(self):
        """清理过期记忆"""
        try:
            # 清理短期记忆
            expired_short_term = []
            for memory_id, memory_item in self.short_term_memory.items():
                if (memory_item.expiration and
                    memory_item.expiration < datetime.now()):
                    expired_short_term.append(memory_id)

            for memory_id in expired_short_term:
                del self.short_term_memory[memory_id]
                self.stats["short_term_items"] -= 1

            # 清理长期记忆
            expired_files = 0
            for file_path in self.long_term_storage_path.glob("*.json"):
                try:
                    with open(file_path) as f:
                        memory_data = json.load(f)

                    if memory_data.get("expiration"):
                        expiration = datetime.fromisoformat(memory_data["expiration"])
                        if expiration < datetime.now():
                            file_path.unlink()
                            embedding_path = file_path.with_suffix('.embedding')
                            if embedding_path.exists():
                                embedding_path.unlink()
                            expired_files += 1
                except Exception:
                    continue

            self.stats["long_term_items"] -= expired_files
            logger.info(f"清理了 {len(expired_short_term)} 个短期记忆和 {expired_files} 个长期记忆")

        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")

    def get_memory_statistics(self) -> dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "storage_stats": {
                "short_term_capacity": self.short_term_capacity,
                "short_term_used": len(self.short_term_memory),
                "working_memory_used": len(self.working_memory),
                "long_term_storage": str(self.long_term_storage_path)
            },
            "memory_stats": self.stats,
            "memory_distribution": {
                "short_term": len(self.short_term_memory),
                "working_memory": len(self.working_memory),
                "episodic": len(self.episodic_memories),
                "procedural": len(self.procedural_memories),
                "conversations": len(self.conversation_contexts)
            },
            "performance_metrics": {
                "hit_rate": (
                    self.stats["cache_hits"] / max(1, self.stats["retrieval_requests"])
                ),
                "storage_efficiency": (
                    self.stats["short_term_items"] / max(1, self.short_term_capacity)
                )
            }
        }

    def export_memory_data(self, export_path: str) -> bool:
        """导出记忆数据"""
        try:
            export_data = {
                "export_time": datetime.now().isoformat(),
                "memory_stats": self.get_memory_statistics(),
                "short_term_memories": {
                    id: asdict(item) for id, item in self.short_term_memory.items()
                },
                "episodic_memories": {
                    id: asdict(episodic) for id, episodic in self.episodic_memories.items()
                },
                "procedural_memories": self.procedural_memories
            }

            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            logger.info(f"记忆数据已导出到: {export_path}")
            return True

        except Exception as e:
            logger.error(f"导出记忆数据失败: {e}")
            return False


# 使用示例
async def example_memory_usage():
    """记忆管理使用示例"""

    memory_manager = EnhancedMemoryManager()

    # 存储不同类型的记忆
    await memory_manager.store_memory(
        "user_pref_001",
        {"theme": "dark", "language": "zh-CN"},
        MemoryType.SHORT_TERM,
        priority=MemoryPriority.HIGH,
        tags=["preference", "user_settings"]
    )

    await memory_manager.store_memory(
        "patent_knowledge_001",
        "AI技术在专利分析中的应用",
        MemoryType.LONG_TERM,
        priority=MemoryPriority.MEDIUM,
        tags=["patent", "AI", "knowledge"],
        expiration=datetime.now() + timedelta(days=365)
    )

    await memory_manager.store_memory(
        "conversation_001",
        {"user_query": "如何进行专利检索", "bot_response": "可以使用向量搜索技术"},
        MemoryType.EPISODIC,
        priority=MemoryPriority.MEDIUM,
        metadata={"event_type": "conversation", "importance": 0.8}
    )

    # 搜索记忆
    search_results = await memory_manager.search_memories(
        "专利",
        limit=5,
        tags=["AI"]
    )

    print(f"搜索结果: {len(search_results)} 个记忆项")
    for result in search_results:
        print(f"  - {result.id}: {result.content}")

    # 获取统计信息
    stats = memory_manager.get_memory_statistics()
    print(f"记忆统计: {json.dumps(stats, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    asyncio.run(example_memory_usage())
