#!/usr/bin/env python3
"""
上下文压缩系统 - 数据类型定义

定义上下文压缩系统的核心数据结构。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CompressionLevel(Enum):
    """压缩级别"""

    NONE = "none"  # 不压缩
    LOW = "low"  # 轻度压缩（保留80%）
    MEDIUM = "medium"  # 中度压缩（保留60%）
    HIGH = "high"  # 高度压缩（保留40%）
    AGGRESSIVE = "aggressive"  # 激进压缩（保留20%）


class MessageImportance(Enum):
    """消息重要性等级"""

    CRITICAL = "critical"  # 关键信息（必须保留）
    HIGH = "high"  # 高重要性
    MEDIUM = "medium"  # 中等重要性
    LOW = "low"  # 低重要性
    TRIVIAL = "trivial"  # 微不足道（可删除）


class CompressionStrategy(Enum):
    """压缩策略"""

    RECENT_FIRST = "recent_first"  # 优先保留最近消息
    IMPORTANCE_BASED = "importance_based"  # 基于重要性评分
    SEMANTIC_CLUSTERING = "semantic_clustering"  # 语义聚类压缩
    HYBRID = "hybrid"  # 混合策略


@dataclass
class ImportanceScore:
    """消息重要性评分"""

    message_id: str
    score: float  # 0.0 - 1.0
    level: MessageImportance
    factors: dict[str, float] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理，根据分数确定重要性等级"""
        if self.level == MessageImportance.MEDIUM:  # 默认值，根据分数调整
            if self.score >= 0.85:
                self.level = MessageImportance.CRITICAL
            elif self.score >= 0.65:
                self.level = MessageImportance.HIGH
            elif self.score >= 0.4:
                self.level = MessageImportance.MEDIUM
            elif self.score >= 0.2:
                self.level = MessageImportance.LOW
            else:
                self.level = MessageImportance.TRIVIAL


@dataclass
class CompressionResult:
    """压缩结果"""

    original_messages: list[str]  # 原始消息ID列表
    compressed_messages: list[str]  # 压缩后保留的消息ID列表
    removed_messages: list[str]  # 删除的消息ID列表
    summaries: list[str]  # 生成的摘要列表
    compression_ratio: float  # 压缩率 (0.0 - 1.0)
    tokens_saved: int  # 节省的token数
    quality_score: float  # 压缩质量评分 (0.0 - 1.0)
    execution_time_ms: float  # 执行时间（毫秒）
    strategy: CompressionStrategy  # 使用的压缩策略
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TokenBudget:
    """Token预算管理"""

    total_budget: int  # 总预算
    reserved: int = 0  # 已预留
    used: int = 0  # 已使用
    compression_threshold: float = 0.8  # 触发压缩的阈值（使用率）

    @property
    def available(self) -> int:
        """可用预算"""
        return self.total_budget - self.reserved - self.used

    @property
    def usage_rate(self) -> float:
        """使用率"""
        if self.total_budget == 0:
            return 1.0
        return self.used / self.total_budget

    def needs_compression(self) -> bool:
        """是否需要压缩"""
        return self.usage_rate >= self.compression_threshold

    def reserve(self, amount: int) -> bool:
        """预留预算"""
        if self.available >= amount:
            self.reserved += amount
            return True
        return False

    def release(self, amount: int) -> None:
        """释放预留"""
        self.reserved = max(0, self.reserved - amount)

    def consume(self, amount: int) -> bool:
        """消耗预算"""
        if self.available >= amount:
            self.reserved -= amount
            self.used += amount
            return True
        return False


@dataclass
class CompressionConfig:
    """压缩配置"""

    level: CompressionLevel = CompressionLevel.MEDIUM
    strategy: CompressionStrategy = CompressionStrategy.HYBRID
    max_tokens: int = 8000  # 最大token数
    min_keep_ratio: float = 0.2  # 最小保留比例
    preserve_recent_count: int = 10  # 始终保留的最近消息数
    summary_length: int = 100  # 摘要长度限制
    quality_threshold: float = 0.7  # 质量阈值


@dataclass
class MessageMetadata:
    """消息元数据（用于压缩）"""

    message_id: str
    is_system: bool = False  # 是否为系统消息
    is_tool_call: bool = False  # 是否为工具调用
    has_code: bool = False  # 是否包含代码
    has_entity: bool = False  # 是否包含实体
    conversation_turn: int = 0  # 对话轮次
    references: list[str] = field(default_factory=list)  # 引用的消息ID
    referenced_by: list[str] = field(default_factory=list)  # 被引用的消息ID


__all__ = [
    "CompressionLevel",
    "MessageImportance",
    "CompressionStrategy",
    "ImportanceScore",
    "CompressionResult",
    "TokenBudget",
    "CompressionConfig",
    "MessageMetadata",
]

