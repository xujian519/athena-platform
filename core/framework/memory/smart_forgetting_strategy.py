
"""
智能遗忘策略
基于重要性、时效性和访问频率的智能记忆管理
"""

import logging
import math
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np

logger = logging.getLogger(__name__)

class ForgettingReason(Enum):
    """遗忘原因"""
    TIME_DECAY = 'time_decay'            # 时间衰减
    LOW_IMPORTANCE = 'low_importance'    # 重要性低
    RARELY_ACCESSED = 'rarely_accessed'  # 很少访问
    CAPACITY_PRESSURE = 'capacity_pressure'  # 容量压力
    CONFLICT_RESOLUTION = 'conflict_resolution'  # 冲突解决
    CONSOLIDATION = 'consolidation'      # 记忆整合

class MemoryPriority(Enum):
    """记忆优先级"""
    CRITICAL = 5    # 关键记忆，永不遗忘
    HIGH = 4        # 高优先级
    MEDIUM = 3      # 中等优先级
    LOW = 2         # 低优先级
    EPHEMERAL = 1   # 短暂记忆

@dataclass
class MemoryItem:
    """记忆项"""
    memory_id: str
    content: Any
    memory_type: str
    importance: float  # 0-1
    priority: MemoryPriority
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    access_frequency: float = 0.0  # 访问频率（次/天）
    decay_rate: float = 0.1  # 衰减率
    associations: list[str] = field(default_factory=list)  # 关联记忆ID
    tags: list[str] = field(default_factory=list)
    embedding: np.Optional[ndarray] = None
    consolidated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_access(self):
        """更新访问信息"""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # 计算访问频率
        days_active = (self.last_accessed - self.created_at).days + 1
        self.access_frequency = self.access_count / days_active

@dataclass
class ForgettingEvent:
    """遗忘事件"""
    memory_id: str
    forgetting_reason: ForgettingReason
    forgetting_time: datetime
    importance_before_forget: float
    access_count_before_forget: int
    summary: str  # 遗忘内容的摘要
    backup_location: Optional[str] = None

class SmartForgettingStrategy:
    """智能遗忘策略管理器"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {
            'max_memory_items': 10000,
            'time_decay_half_life': 30,  # 天
            'importance_threshold': 0.1,
            'access_frequency_threshold': 0.1,  # 次/天
            'consolidation_interval': 7,  # 天
            'backup_enabled': True,
            'forgetting_batch_size': 100
        }

        self.memory_store = {}
        self.forgetting_history = deque(maxlen=1000)
        self.importance_weights = {}
        self.forgetting_rules = {}
        self.last_consolidation = datetime.now()
        self.statistics = {
            'total_forgettings': 0,
            'forgettings_by_reason': defaultdict(int),
            'avg_memory_lifetime': 0.0,
            'consolidation_count': 0
        }

    async def add_memory(self, memory: MemoryItem):
        """添加记忆项"""
        # 计算初始重要性
        if memory.importance == 0:
            memory.importance = await self._calculate_importance(memory)

        # 设置初始衰减率
        memory.decay_rate = self._calculate_decay_rate(memory)

        self.memory_store[memory.memory_id] = memory

        # 检查是否需要遗忘
        await self._check_forgetting_needs()

    async def _calculate_importance(self, memory: MemoryItem) -> float:
        """计算记忆重要性"""
        importance = 0.5  # 基础重要性

        # 基于优先级
        priority_scores = {
            MemoryPriority.CRITICAL: 1.0,
            MemoryPriority.HIGH: 0.8,
            MemoryPriority.MEDIUM: 0.6,
            MemoryPriority.LOW: 0.4,
            MemoryPriority.EPHEMERAL: 0.2
        }
        importance += priority_scores.get(memory.priority, 0.5) * 0.3

        # 基于内容特征
        if isinstance(memory.content, str):
            content_importance = await self._analyze_content_importance(memory.content)
            importance += content_importance * 0.3

        # 基于关联数量
        min(len(memory.associations) / 10.0, 1.0) * 0.2

        # 基于标签
        min(len(memory.tags) / 5.0, 1.0) * 0.2

        return min(importance, 1.0)

    async def _analyze_content_importance(self, content: str) -> float:
        """分析内容重要性"""
        # 关键词权重
        important_keywords = [
            '错误', '失败', '成功', '关键', '重要', '核心',
            '问题', '解决方案', '优化', '突破', '创新'
        ]

        keyword_score = sum(1 for keyword in important_keywords
                          if keyword in content) / len(important_keywords)

        # 长度评分（适中长度更重要）
        length_score = 1.0 - abs(len(content) - 500) / 1000
        length_score = max(0, length_score)

        # 情感强度
        emotional_words = ['非常', '极其', '特别', '严重', '紧急']
        emotional_score = sum(1 for word in emotional_words
                            if word in content) / len(emotional_words)

        return (keyword_score + length_score + emotional_score) / 3

    def _calculate_decay_rate(self, memory: MemoryItem) -> float:
        """计算衰减率"""
        base_rate = 0.1

        # 基于优先级调整
        if memory.priority == MemoryPriority.CRITICAL:
            base_rate = 0.0
        elif memory.priority == MemoryPriority.HIGH:
            base_rate = 0.05
        elif memory.priority == MemoryPriority.EPHEMERAL:
            base_rate = 0.5

        # 基于记忆类型调整
        type_rates = {
            'error': 0.05,      # 错误记忆衰减慢
            'success': 0.1,     # 成功记忆正常衰减
            'routine': 0.2,     # 常规记忆衰减快
            'temp': 0.8         # 临时记忆快速衰减
        }

        return min(base_rate + type_rates.get(memory.memory_type, 0), 1.0)

    async def access_memory(self, memory_id: str) -> Optional[MemoryItem]:
        """访问记忆"""
        memory = self.memory_store.get(memory_id)
        if memory:
            memory.update_access()
            # 更新重要性（访问可以增强重要性）
            memory.importance = min(memory.importance * 1.05, 1.0)
        return memory

    async def _check_forgetting_needs(self):
        """检查是否需要执行遗忘"""
        # 检查容量压力
        if len(self.memory_store) > self.config['max_memory_items']:
            await self._forget_by_capacity_pressure()

        # 检查时间衰减
        await self._apply_time_decay()

        # 检查低重要性记忆
        await self._forget_low_importance()

        # 检查很少访问的记忆
        await self._forget_rarely_accessed()

        # 检查是否需要整合
        await self._check_consolidation_needs()

    async def _forget_by_capacity_pressure(self):
        """基于容量压力进行遗忘"""
        excess_count = len(self.memory_store) - self.config['max_memory_items']
        if excess_count <= 0:
            return

        # 按优先级和重要性排序
        memories = sorted(
            self.memory_store.values(),
            key=lambda m: (m.priority.value, m.importance),
            reverse=True
        )

        # 保留重要记忆，遗忘次要记忆
        to_forget = memories[-excess_count:]
        for memory in to_forget:
            if memory.priority != MemoryPriority.CRITICAL:
                await self._forget_memory(memory, ForgettingReason.CAPACITY_PRESSURE)

    async def _apply_time_decay(self):
        """应用时间衰减"""
        current_time = datetime.now()
        half_life_days = self.config['time_decay_half_life']

        for memory in list(self.memory_store.values()):
            if memory.priority == MemoryPriority.CRITICAL:
                continue  # 关键记忆不衰减

            days_elapsed = (current_time - memory.created_at).days
            if days_elapsed > 0:
                # 指数衰减
                decay_factor = math.exp(-days_elapsed / half_life_days)
                memory.importance *= decay_factor

                # 检查是否低于阈值
                if memory.importance < self.config['importance_threshold']:
                    await self._forget_memory(memory, ForgettingReason.TIME_DECAY)

    async def _forget_low_importance(self):
        """遗忘低重要性记忆"""
        threshold = self.config['importance_threshold']

        for memory in list(self.memory_store.values()):
            if (memory.importance < threshold and
                memory.priority not in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]):
                await self._forget_memory(memory, ForgettingReason.LOW_IMPORTANCE)

    async def _forget_rarely_accessed(self):
        """遗忘很少访问的记忆"""
        threshold = self.config['access_frequency_threshold']
        min_age_days = 7  # 至少存在7天

        current_time = datetime.now()

        for memory in list(self.memory_store.values()):
            age_days = (current_time - memory.created_at).days
            if (age_days > min_age_days and
                memory.access_frequency < threshold and
                memory.priority not in [MemoryPriority.CRITICAL, MemoryPriority.HIGH]):
                await self._forget_memory(memory, ForgettingReason.RARELY_ACCESSED)

    async def _check_consolidation_needs(self):
        """检查整合需求"""
        current_time = datetime.now()
        days_since_last = (current_time - self.last_consolidation).days

        if days_since_last >= self.config['consolidation_interval']:
            await self._consolidate_memories()
            self.last_consolidation = current_time

    async def _consolidate_memories(self):
        """整合记忆"""
        logger.info('开始记忆整合...')

        # 按类型分组
        memories_by_type = defaultdict(list)
        for memory in self.memory_store.values():
            if not memory.consolidated:
                memories_by_type[memory.memory_type].append(memory)

        consolidated_count = 0

        # 对每种类型的记忆进行整合
        for _memory_type, memories in memories_by_type.items():
            if len(memories) < 2:
                continue

            # 查找相似记忆
            for i, mem1 in enumerate(memories):
                for mem2 in memories[i+1:]:
                    similarity = await self._calculate_similarity(mem1, mem2)
                    if similarity > 0.8:  # 高相似度
                        # 整合记忆
                        await self._merge_memories(mem1, mem2)
                        consolidated_count += 1

        self.statistics['consolidation_count'] += 1
        logger.info(f"记忆整合完成，整合了 {consolidated_count} 个记忆")

    async def _calculate_similarity(self, mem1: MemoryItem, mem2: MemoryItem) -> float:
        """计算记忆相似度"""
        # 简单的基于内容的相似度计算
        if isinstance(mem1.content, str) and isinstance(mem2.content, str):
            # 使用Jaccard相似度
            words1 = set(mem1.content.split())
            words2 = set(mem2.content.split())
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            return intersection / union if union > 0 else 0.0

        # 其他类型的相似度计算
        return 0.0

    async def _merge_memories(self, mem1: MemoryItem, mem2: MemoryItem):
        """合并两个记忆"""
        # 保留更重要的记忆
        primary, secondary = (mem1, mem2) if mem1.importance >= mem2.importance else (mem2, mem1)

        # 合并内容
        if isinstance(primary.content, str) and isinstance(secondary.content, str):
            primary.content = f"{primary.content}\n[相关] {secondary.content}"

        # 合并关联和标签
        primary.associations.extend([a for a in secondary.associations if a not in primary.associations])
        primary.tags.extend([t for t in secondary.tags if t not in primary.tags])

        # 更新重要性
        primary.importance = min(primary.importance + secondary.importance * 0.3, 1.0)

        # 标记为已整合
        primary.consolidated = True

        # 删除次要记忆
        await self._forget_memory(secondary, ForgettingReason.CONSOLIDATION)

    async def _forget_memory(self, memory: MemoryItem, reason: ForgettingReason):
        """执行遗忘操作"""
        # 创建遗忘事件
        forgetting_event = ForgettingEvent(
            memory_id=memory.memory_id,
            forgetting_reason=reason,
            forgetting_time=datetime.now(),
            importance_before_forget=memory.importance,
            access_count_before_forget=memory.access_count,
            summary=str(memory.content)[:200] if memory.content else '',
            backup_location=await self._backup_memory(memory) if self.config['backup_enabled'] else None
        )

        # 记录遗忘事件
        self.forgetting_history.append(forgetting_event)

        # 更新统计
        self.statistics['total_forgettings'] += 1
        self.statistics['forgettings_by_reason'][reason.value] += 1

        # 计算记忆生命周期
        lifetime = (datetime.now() - memory.created_at).days
        if self.statistics['total_forgettings'] > 0:
            self.statistics['avg_memory_lifetime'] = (
                (self.statistics['avg_memory_lifetime'] * (self.statistics['total_forgettings'] - 1) + lifetime) /
                self.statistics['total_forgettings']
            )

        # 从记忆存储中删除
        if memory.memory_id in self.memory_store:
            del self.memory_store[memory.memory_id]

        logger.info(f"遗忘记忆 {memory.memory_id}，原因: {reason.value}")

    async def _backup_memory(self, memory: MemoryItem) -> str:
        """备份记忆"""
        backup_path = f"backups/memory_{memory.memory_id}_{int(time.time())}.json"

        {
            'memory_id': memory.memory_id,
            'content': memory.content,
            'memory_type': memory.memory_type,
            'importance': memory.importance,
            'priority': memory.priority.value,
            'created_at': memory.created_at.isoformat(),
            'last_accessed': memory.last_accessed.isoformat(),
            'access_count': memory.access_count,
            'metadata': memory.metadata
        }

        # 这里应该实际写入文件或数据库
        # await self._save_backup(backup_path, backup_data)

        return backup_path

    async def add_forgetting_rule(self, rule_name: str, rule_func: Callable[[MemoryItem], bool]):
        """添加自定义遗忘规则"""
        self.forgetting_rules[rule_name] = rule_func

    async def apply_custom_rules(self):
        """应用自定义遗忘规则"""
        for _rule_name, rule_func in self.forgetting_rules.items():
            for memory in list(self.memory_store.values()):
                if await rule_func(memory):
                    await self._forget_memory(memory, ForgettingReason.CONFLICT_RESOLUTION)

    def get_memory_statistics(self) -> dict[str, Any]:
        """获取记忆统计信息"""
        return {
            'total_memories': len(self.memory_store),
            'total_forgettings': self.statistics['total_forgettings'],
            'forgettings_by_reason': dict(self.statistics['forgettings_by_reason']),
            'avg_memory_lifetime': self.statistics['avg_memory_lifetime'],
            'consolidation_count': self.statistics['consolidation_count'],
            'memory_distribution': self._get_memory_distribution(),
            'recent_forgettings': list(self.forgetting_history)[-10:]
        }

    def _get_memory_distribution(self) -> dict[str, int]:
        """获取记忆分布"""
        distribution = defaultdict(int)

        for memory in self.memory_store.values():
            distribution[memory.memory_type] += 1

        return dict(distribution)

    async def search_memories(self, query: str, limit: int = 10) -> list[MemoryItem]:
        """搜索记忆"""
        query_words = set(query.lower().split())
        results = []

        for memory in self.memory_store.values():
            if isinstance(memory.content, str):
                content_words = set(memory.content.lower().split())
                # 计算匹配度
                match_count = len(query_words.intersection(content_words))
                if match_count > 0:
                    score = match_count / len(query_words)
                    results.append((memory, score))

        # 按分数排序
        results.sort(key=lambda x: x[1], reverse=True)

        return [memory for memory, _ in results[:limit]

    async def get_similar_memories(self, memory_id: str, limit: int = 5) -> list[tuple[MemoryItem, float]]:
        """获取相似记忆"""
        target_memory = self.memory_store.get(memory_id)
        if not target_memory:
            return []

        similarities = []
        for mem_id, memory in self.memory_store.items():
            if mem_id != memory_id:
                similarity = await self._calculate_similarity(target_memory, memory)
                if similarity > 0:
                    similarities.append((memory, similarity))

        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:limit]

# 创建全局智能遗忘策略管理器
smart_forgetting_strategy = SmartForgettingStrategy()

# 便捷函数
async def add_memory_with_forgetting(memory_id: str, content: Any, memory_type: str,
                                  priority: MemoryPriority = MemoryPriority.MEDIUM,
                                  tags: Optional[list[str]] = None):
    """添加带遗忘策略的记忆"""
    memory = MemoryItem(
        memory_id=memory_id,
        content=content,
        memory_type=memory_type,
        importance=0.0,  # 将自动计算
        priority=priority,
        created_at=datetime.now(),
        last_accessed=datetime.now(),
        tags=tags or []
    )
    await smart_forgetting_strategy.add_memory(memory)

async def access_and_protect_memory(memory_id: str) -> Optional[MemoryItem]:
    """访问并保护记忆"""
    return await smart_forgetting_strategy.access_memory(memory_id)

async def get_memory_insights() -> dict[str, Any]:
    """获取记忆洞察"""
    return smart_forgetting_strategy.get_memory_statistics()

