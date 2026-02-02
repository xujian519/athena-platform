#!/usr/bin/env python3
"""
上下文压缩器 - Token Sprawl防护机制
Context Compressor - Token Sprawl Prevention

基于行业最佳实践,实现智能的上下文压缩策略:
- 历史对话摘要
- 信息重要性排序
- 动态上下文窗口调整
- 不相关信息的主动清理

目标: 防止上下文随对话轮次指数增长,保持响应速度

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.0.0
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class MessageRole(Enum):
    """消息角色"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


class MessageImportance(Enum):
    """消息重要性"""

    CRITICAL = "critical"  # 关键: 不能移除
    HIGH = "high"  # 高: 优先保留
    MEDIUM = "medium"  # 中: 可考虑摘要
    LOW = "low"  # 低: 可移除或超短摘要


@dataclass
class Message:
    """消息"""

    role: MessageRole
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    importance: MessageImportance = MessageImportance.MEDIUM
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """估算Token数量"""
        if self.token_count == 0:
            self.token_count = len(self.content) // 3  # 粗略估算: 1 Token ≈ 3 字符


@dataclass
class SummaryLevel:
    """摘要级别"""

    level: int  # 0=原文, 1=50%压缩, 2=90%压缩
    name: str
    compression_ratio: float  # 压缩比例
    content: str
    original_tokens: int
    compressed_tokens: int


@dataclass
class CompressionStrategy:
    """压缩策略"""

    target_token_ratio: float  # 目标Token比例 (相对于当前)
    preserve_critical: bool = True  # 是否保留关键信息
    create_summary: bool = True  # 是否创建摘要
    remove_irrelevant: bool = True  # 是否移除不相关信息


class ContextCompressor:
    """
    上下文压缩器

    核心功能:
    1. 历史对话摘要
    2. 信息重要性评分
    3. 动态上下文窗口调整
    4. 不相关信息清理
    """

    def __init__(self, max_context_tokens: int = 8000, summary_threshold: float = 0.7):
        """
        初始化上下文压缩器

        Args:
            max_context_tokens: 最大上下文Token数
            summary_threshold: 触发摘要的阈值(相对于max)
        """
        self.max_context_tokens = max_context_tokens
        self.summary_threshold = summary_threshold

        # 消息历史 (用于测试,实际应从外部传入)
        self.message_history: deque = deque(maxlen=1000)

        # 摘要缓存
        self.summary_cache: dict[str, list[SummaryLevel]] = {}

        logger.info(f"上下文压缩器初始化完成 (max_tokens={max_context_tokens})")

    async def compress_context(
        self,
        messages: list[Message],
        target_tokens: int | None = None,
        strategy: CompressionStrategy | None = None,
    ) -> list[Message]:
        """
        智能压缩上下文到目标Token数

        Args:
            messages: 当前消息列表
            target_tokens: 目标Token数 (None表示使用max_context_tokens)
            strategy: 压缩策略

        Returns:
            list[Message]: 压缩后的消息列表
        """
        target = target_tokens or self.max_context_tokens
        strat = strategy or CompressionStrategy(target_token_ratio=target / self.max_context_tokens)

        # 计算当前Token数
        current_tokens = sum(msg.token_count for msg in messages)

        logger.info(f"压缩上下文: {current_tokens} -> {target} tokens")

        if current_tokens <= target:
            # 不需要压缩
            return messages

        # 1. 评估消息重要性
        messages_with_importance = await self._assess_message_importance(messages)

        # 2. 按重要性排序
        messages_with_importance.sort(
            key=lambda x: (-x.importance.value, x.timestamp)  # 重要性降序  # 时间戳升序(保留最新的)
        )

        # 3. 选择保留的消息
        preserved_messages = []
        current_count = 0

        for msg in messages_with_importance:
            # 关键消息必须保留
            if msg.importance == MessageImportance.CRITICAL:
                preserved_messages.append(msg)
                current_count += msg.token_count
                continue

            # 检查是否超出目标
            if current_count + msg.token_count > target:
                # 尝试摘要
                if strat.create_summary and msg.importance in [
                    MessageImportance.HIGH,
                    MessageImportance.MEDIUM,
                ]:
                    summary_msg = await self._create_summary_message(msg, target - current_count)
                    if summary_msg:
                        preserved_messages.append(summary_msg)
                        current_count += summary_msg.token_count
                # 跳过此消息
                continue

            preserved_messages.append(msg)
            current_count += msg.token_count

        # 4. 移除不相关信息
        if strat.remove_irrelevant:
            preserved_messages = await self._remove_irrelevant_info(preserved_messages)

        # 5. 按时间排序恢复顺序
        preserved_messages.sort(key=lambda x: x.timestamp)

        final_tokens = sum(msg.token_count for msg in preserved_messages)
        logger.info(
            f"压缩完成: {current_tokens} -> {final_tokens} tokens ({final_tokens/current_tokens:.1%})"
        )

        return preserved_messages

    async def _assess_message_importance(self, messages: list[Message]) -> list[Message]:
        """
        评估消息重要性

        评估维度:
        1. 消息角色 (SYSTEM > ASSISTANT > USER)
        2. 消息内容 (关键词、长度、结构)
        3. 时间新旧 (越新越重要)
        4. 对话轮次位置 (开头和结尾更重要)
        """
        total = len(messages)

        for idx, msg in enumerate(messages):
            # 基础分数
            score = 0.0

            # 1. 角色评分
            if msg.role == MessageRole.SYSTEM:
                score += 50  # 系统消息很重要
            elif msg.role == MessageRole.ASSISTANT:
                score += 30  # AI回复较重要
            else:  # USER
                score += 20  # 用户消息

            # 2. 位置评分 (开头和结尾更重要)
            if idx == 0:
                score += 30  # 第一条消息
            elif idx == total - 1:
                score += 20  # 最新消息
            elif idx < 3:
                score += 10  # 前几条
            elif idx > total - 3:
                score += 10  # 最后几条

            # 3. 时间评分 (越新越重要)
            age_hours = (datetime.now().timestamp() - msg.timestamp) / 3600
            if age_hours < 1:
                score += 15  # 1小时内
            elif age_hours < 6:
                score += 10  # 6小时内
            elif age_hours < 24:
                score += 5  # 24小时内

            # 4. 内容评分 (关键词、长度)
            if self._contains_critical_info(msg.content):
                score += 20
            elif self._contains_task_info(msg.content):
                score += 10
            elif self._contains_greeting(msg.content):
                score -= 10  # 问候可以移除

            # 5. 长度评分 (中等长度最重要)
            length = len(msg.content)
            if 50 <= length <= 500:
                score += 10  # 中等长度
            elif length > 500:
                score += 5  # 长消息可能重要

            # 转换为Importance枚举
            if score >= 80:
                msg.importance = MessageImportance.CRITICAL
            elif score >= 60:
                msg.importance = MessageImportance.HIGH
            elif score >= 40:
                msg.importance = MessageImportance.MEDIUM
            else:
                msg.importance = MessageImportance.LOW

        return messages

    def _contains_critical_info(self, content: str) -> bool:
        """检查是否包含关键信息"""
        critical_keywords = [
            "重要",
            "关键",
            "必须",
            "禁止",
            "警告",
            "错误",
            "失败",
            "配置",
            "密钥",
            "密码",
            "结论",
            "决定",
            "确认",
        ]
        return any(kw in content for kw in critical_keywords)

    def _contains_task_info(self, content: str) -> bool:
        """检查是否包含任务信息"""
        task_keywords = ["任务", "步骤", "执行", "完成", "结果", "分析", "处理", "操作", "行动"]
        return any(kw in content for kw in task_keywords)

    def _contains_greeting(self, content: str) -> bool:
        """检查是否为问候"""
        greetings = ["你好", "hi", "hello", "您好", "早上好", "下午好", "晚上好"]
        content_lower = content.lower()
        return any(greeting in content_lower for greeting in greetings)

    async def _create_summary_message(
        self, original_msg: Message, max_tokens: int
    ) -> Message | None:
        """
        创建摘要消息

        Args:
            original_msg: 原始消息
            max_tokens: 最大Token数

        Returns:
            Optional[Message]: 摘要消息
        """
        original_content = original_msg.content
        original_tokens = original_msg.token_count

        if original_tokens <= max_tokens:
            # 不需要摘要
            return original_msg

        # 简单的摘要策略: 保留开头和结尾
        content_lines = original_content.split("\n")

        # 保留比例
        keep_ratio = max_tokens / original_tokens

        # 保留开头
        keep_start = int(len(content_lines) * keep_ratio * 0.6)
        # 保留结尾
        keep_end = int(len(content_lines) * keep_ratio * 0.4)

        summary_lines = content_lines[:keep_start]
        if keep_end > 0:
            summary_lines.append("\n... [摘要省略] ...\n")
            summary_lines.extend(content_lines[-keep_end:])

        summary_content = "\n".join(summary_lines)

        return Message(
            role=original_msg.role,
            content=summary_content,
            timestamp=original_msg.timestamp,
            importance=MessageImportance.MEDIUM,
            metadata={
                "summary_of": original_msg.content[:100],
                "compression_ratio": len(summary_content) / len(original_content),
            },
        )

    async def _remove_irrelevant_info(self, messages: list[Message]) -> list[Message]:
        """
        移除不相关信息

        移除策略:
        1. 连续的问候
        2. 重复的确认消息
        3. 空或极短的消息
        """
        filtered = []
        last_was_greeting = False

        for msg in messages:
            # 跳过空消息
            if not msg.content or len(msg.content.strip()) < 10:
                continue

            # 跳过连续的问候
            is_greeting = self._contains_greeting(msg.content)
            if is_greeting and last_was_greeting:
                continue
            last_was_greeting = is_greeting

            # 保留其他消息
            filtered.append(msg)

        return filtered

    def create_hierarchical_summary(self, long_context: str) -> dict[str, SummaryLevel]:
        """
        创建分层摘要

        层级:
        - L0: 原始上下文
        - L1: 关键信息摘要 (50%压缩)
        - L2: 超短摘要 (90%压缩)

        Args:
            long_context: 长文本

        Returns:
            dict[str, SummaryLevel]: 各层级的摘要
        """
        original_tokens = len(long_context) // 3

        # L0: 原始
        l0 = SummaryLevel(
            level=0,
            name="原始",
            compression_ratio=1.0,
            content=long_context,
            original_tokens=original_tokens,
            compressed_tokens=original_tokens,
        )

        # L1: 50%压缩
        l1_content = self._create_summary_level1(long_context)
        l1 = SummaryLevel(
            level=1,
            name="关键信息",
            compression_ratio=0.5,
            content=l1_content,
            original_tokens=original_tokens,
            compressed_tokens=len(l1_content) // 3,
        )

        # L2: 90%压缩
        l2_content = self._create_summary_level2(long_context)
        l2 = SummaryLevel(
            level=2,
            name="超短摘要",
            compression_ratio=0.1,
            content=l2_content,
            original_tokens=original_tokens,
            compressed_tokens=len(l2_content) // 3,
        )

        return {"L0": l0, "L1": l1, "L2": l2}

    def _create_summary_level1(self, content: str) -> str:
        """创建L1摘要 (50%压缩)"""
        lines = content.split("\n")

        # 保留策略:
        # 1. 保留标题行 (以#开头的)
        # 2. 保留关键信息行
        # 3. 每隔一行保留一行

        summary_lines = []
        for i, line in enumerate(lines):
            # 保留标题
            if line.strip().startswith("#"):
                summary_lines.append(line)
                continue

            # 保留关键信息
            if self._contains_critical_info(line):
                summary_lines.append(line)
                continue

            # 隔行保留
            if i % 2 == 0:
                summary_lines.append(line)

        return "\n".join(summary_lines)

    def _create_summary_level2(self, content: str) -> str:
        """创建L2摘要 (90%压缩)"""
        lines = content.split("\n")

        # 只保留:
        # 1. 所有标题
        # 2. 包含关键信息的行

        summary_lines = []
        for line in lines:
            # 保留标题
            if line.strip().startswith("#"):
                summary_lines.append(line)
                continue

            # 保留关键信息
            if self._contains_critical_info(line):
                summary_lines.append(line)

        return "\n".join(summary_lines)

    async def monitor_context_size(self, messages: list[Message]) -> dict[str, Any]:
        """
        监控上下文大小

        Returns:
            Dict: 监控指标
        """
        total_tokens = sum(msg.token_count for msg in messages)
        token_ratio = total_tokens / self.max_context_tokens

        # 统计各类消息
        by_importance = {}
        for imp in MessageImportance:
            count = sum(1 for msg in messages if msg.importance == imp)
            tokens = sum(msg.token_count for msg in messages if msg.importance == imp)
            by_importance[imp.value] = {
                "count": count,
                "tokens": tokens,
                "percentage": tokens / total_tokens if total_tokens > 0 else 0,
            }

        # 检查是否需要压缩
        needs_compression = token_ratio > self.summary_threshold

        return {
            "total_messages": len(messages),
            "total_tokens": total_tokens,
            "max_tokens": self.max_context_tokens,
            "token_ratio": token_ratio,
            "by_importance": by_importance,
            "needs_compression": needs_compression,
            "recommendation": "建议压缩上下文" if needs_compression else "上下文大小正常",
        }

    def adjust_context_window(self, current_tokens: int, max_tokens: int) -> int:
        """
        动态调整上下文窗口大小

        策略:
        - 超过80%: 触发摘要
        - 超过90%: 强制压缩
        - 超过95%: 紧急压缩
        """
        ratio = current_tokens / max_tokens

        if ratio >= 0.95:
            # 紧急压缩到50%
            return int(max_tokens * 0.5)
        elif ratio >= 0.90:
            # 强制压缩到70%
            return int(max_tokens * 0.7)
        elif ratio >= 0.80:
            # 触发摘要,压缩到85%
            return int(max_tokens * 0.85)
        else:
            # 不调整
            return max_tokens

    async def summarize_history(
        self, messages: list[Message], target_ratio: float = 0.5
    ) -> list[Message]:
        """
        摘要历史消息

        Args:
            messages: 消息列表
            target_ratio: 目标压缩比例

        Returns:
            list[Message]: 摘要后的消息列表
        """
        target_tokens = int(sum(msg.token_count for msg in messages) * target_ratio)

        return await self.compress_context(
            messages,
            target_tokens=target_tokens,
            strategy=CompressionStrategy(
                target_token_ratio=target_ratio,
                preserve_critical=True,
                create_summary=True,
                remove_irrelevant=True,
            ),
        )


# ============================================================================
# 便捷函数
# ============================================================================

_compressor_instance: ContextCompressor | None = None


async def get_context_compressor() -> ContextCompressor:
    """获取上下文压缩器单例(异步版本)"""
    global _compressor_instance
    if _compressor_instance is None:
        _compressor_instance = ContextCompressor()
    return _compressor_instance


def get_context_compressor_sync() -> ContextCompressor:
    """获取上下文压缩器单例(同步版本,用于向后兼容)"""
    global _compressor_instance
    if _compressor_instance is None:
        _compressor_instance = ContextCompressor()
    return _compressor_instance


# ============================================================================
# 导出
# ============================================================================

__all__ = [
    "CompressionStrategy",
    "ContextCompressor",
    "Message",
    "MessageImportance",
    "MessageRole",
    "SummaryLevel",
    "get_context_compressor",
]
