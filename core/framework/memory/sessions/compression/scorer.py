#!/usr/bin/env python3
"""
消息重要性评分器

根据多个因素评估消息的重要性，为压缩提供依据。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import logging
import re
from datetime import datetime

from ..types import MessageRole, SessionMessage
from .types import ImportanceScore, MessageImportance

logger = logging.getLogger(__name__)


class MessageScorer:
    """消息重要性评分器

    根据多个维度评估消息的重要性：
    - 角色权重（系统消息 > 助手消息 > 用户消息 > 工具消息）
    - 内容特征（包含代码、实体、关键信息）
    - 时间因素（最近的消息权重更高）
    - 对话结构（是否为对话转折点）
    - 内容长度（更详细的内容可能更重要）
    """

    # 角色基础权重
    ROLE_WEIGHTS: dict[MessageRole, float] = {
        MessageRole.SYSTEM: 1.0,  # 系统消息最关键
        MessageRole.ASSISTANT: 0.9,  # 助手回复重要
        MessageRole.USER: 0.8,  # 用户询问重要
        MessageRole.TOOL: 0.5,  # 工具调用结果较次要
    }

    # 关键词模式（用于检测重要内容）
    CRITICAL_PATTERNS = [
        r"\b重要\b",
        r"\b关键\b",
        r"\b必须\b",
        r"\b注意\b",
        r"\b结论\b",
        r"\b因此\b",
        r"\b总结\b",
    ]

    def __init__(
        self,
        recency_weight: float = 0.2,
        role_weight: float = 0.3,
        content_weight: float = 0.3,
        structure_weight: float = 0.2,
    ):
        """初始化评分器

        Args:
            recency_weight: 时间权重
            role_weight: 角色权重
            content_weight: 内容权重
            structure_weight: 结构权重
        """
        self.recency_weight = recency_weight
        self.role_weight = role_weight
        self.content_weight = content_weight
        self.structure_weight = structure_weight

        # 编译正则表达式
        self._critical_pattern = re.compile(
            "|".join(self.CRITICAL_PATTERNS), re.IGNORECASE
        )

    def score_messages(self, messages: list[SessionMessage]) -> list[ImportanceScore]:
        """批量评分消息

        Args:
            messages: 消息列表

        Returns:
            list[ImportanceScore]: 评分结果列表
        """
        if not messages:
            return []

        # 计算时间范围（用于归一化）
        timestamps = [m.timestamp for m in messages]
        min_time = min(timestamps)
        max_time = max(timestamps)
        time_range = (max_time - min_time).total_seconds() or 1

        # 计算内容长度范围
        lengths = [len(m.content) for m in messages]
        max_length = max(lengths) or 1

        scores = []

        for i, message in enumerate(messages):
            # 计算各维度分数
            recency_score = self._score_recency(message, min_time, time_range)
            role_score = self._score_role(message)
            content_score = self._score_content(message, max_length)
            structure_score = self._score_structure(message, i, len(messages))

            # 加权总分
            total_score = (
                recency_score * self.recency_weight
                + role_score * self.role_weight
                + content_score * self.content_weight
                + structure_score * self.structure_weight
            )

            # 记录评分因子
            factors = {
                "recency": recency_score,
                "role": role_score,
                "content": content_score,
                "structure": structure_score,
            }

            scores.append(
                ImportanceScore(
                    message_id=message.message_id,
                    score=round(total_score, 3),
                    level=MessageImportance.MEDIUM,  # 会被自动调整
                    factors=factors,
                )
            )

        logger.debug(f"📊 评分了 {len(scores)} 条消息")
        return scores

    def _score_recency(
        self,
        message: SessionMessage,
        min_time: datetime,
        time_range: float,
    ) -> float:
        """计算时间分数

        最近的消息分数更高。

        Args:
            message: 消息
            min_time: 最早时间
            time_range: 时间范围（秒）

        Returns:
            float: 时间分数 (0.0 - 1.0)
        """
        delta = (message.timestamp - min_time).total_seconds()
        return min(delta / time_range, 1.0)

    def _score_role(self, message: SessionMessage) -> float:
        """计算角色分数

        Args:
            message: 消息

        Returns:
            float: 角色分数 (0.0 - 1.0)
        """
        return self.ROLE_WEIGHTS.get(message.role, 0.5)

    def _score_content(self, message: SessionMessage, max_length: int) -> float:
        """计算内容分数

        考虑：
        - 内容长度（更详细可能更重要）
        - 是否包含代码
        - 是否包含关键信息

        Args:
            message: 消息
            max_length: 最大长度

        Returns:
            float: 内容分数 (0.0 - 1.0)
        """
        score = 0.3  # 基础分数

        # 长度分数（0.0 - 0.3）
        if max_length > 0:
            length_ratio = len(message.content) / max_length
            score += min(length_ratio * 0.3, 0.3)

        # 代码检测（+0.2）
        if self._contains_code(message.content):
            score += 0.2

        # 关键信息检测（+0.2）
        if self._contains_critical_info(message.content):
            score += 0.2

        return min(score, 1.0)

    def _score_structure(
        self,
        message: SessionMessage,
        index: int,
        total: int,
    ) -> float:
        """计算结构分数

        考虑消息在对话中的位置和作用。

        Args:
            message: 消息
            index: 索引
            total: 总数

        Returns:
            float: 结构分数 (0.0 - 1.0)
        """
        score = 0.5  # 基础分数

        # 系统消息在开头，非常重要
        if message.role == MessageRole.SYSTEM:
            score = 1.0
            return score

        # 首尾消息更重要
        if index == 0 or index == total - 1:
            score += 0.3

        # 对话轮次的开头
        if index % 2 == 0:  # 假设偶数索引是用户消息
            score += 0.2

        return min(score, 1.0)

    def _contains_code(self, content: str) -> bool:
        """检测是否包含代码

        Args:
            content: 内容

        Returns:
            bool: 是否包含代码
        """
        code_indicators = [
            "```",
            "`",
            "def ",
            "class ",
            "function ",
            "import ",
            "from ",
            "=>",
            "{",
            "};",
        ]
        return any(indicator in content for indicator in code_indicators)

    def _contains_critical_info(self, content: str) -> bool:
        """检测是否包含关键信息

        Args:
            content: 内容

        Returns:
            bool: 是否包含关键信息
        """
        return bool(self._critical_pattern.search(content))


__all__ = ["MessageScorer"]

