#!/usr/bin/env python3
"""
上下文压缩器

实现对话历史的智能压缩功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""

import logging
import time

from ..types import SessionMessage
from .scorer import MessageScorer
from .types import (
from typing import Optional
    CompressionConfig,
    CompressionLevel,
    CompressionResult,
    CompressionStrategy,
)

logger = logging.getLogger(__name__)


class ContextCompressor:
    """上下文压缩器

    根据配置的策略和级别压缩对话历史，保留关键信息。
    """

    # 压缩级别对应的保留比例
    LEVEL_RATIOS = {
        CompressionLevel.NONE: 1.0,
        CompressionLevel.LOW: 0.8,
        CompressionLevel.MEDIUM: 0.6,
        CompressionLevel.HIGH: 0.4,
        CompressionLevel.AGGRESSIVE: 0.2,
    }

    def __init__(
        self,
        config: Optional[CompressionConfig] = None,
        scorer: Optional[MessageScorer] = None,
    ):
        """初始化压缩器

        Args:
            config: 压缩配置
            scorer: 消息评分器
        """
        self.config = config or CompressionConfig()
        self.scorer = scorer or MessageScorer()
        logger.info(
            f"🗜️ 上下文压缩器已初始化 (策略: {self.config.strategy.value}, "
            f"级别: {self.config.level.value})"
        )

    def compress(self, messages: list[SessionMessage]) -> CompressionResult:
        """压缩消息列表

        Args:
            messages: 原始消息列表

        Returns:
            CompressionResult: 压缩结果
        """
        start_time = time.perf_counter()

        # 空列表处理
        if not messages:
            return CompressionResult(
                original_messages=[],
                compressed_messages=[],
                removed_messages=[],
                summaries=[],
                compression_ratio=0.0,
                tokens_saved=0,
                quality_score=1.0,
                execution_time_ms=0.0,
                strategy=self.config.strategy,
            )

        # 单条消息直接返回
        if len(messages) == 1:
            return self._create_result(
                messages=messages,
                kept_messages=messages,
                removed_messages=[],
                summaries=[],
                start_time=start_time,
            )

        # 根据策略选择压缩方法
        if self.config.strategy == CompressionStrategy.RECENT_FIRST:
            kept, removed, summaries = self._compress_recent_first(messages)
        elif self.config.strategy == CompressionStrategy.IMPORTANCE_BASED:
            kept, removed, summaries = self._compress_by_importance(messages)
        elif self.config.strategy == CompressionStrategy.SEMANTIC_CLUSTERING:
            kept, removed, summaries = self._compress_by_clustering(messages)
        else:  # HYBRID
            kept, removed, summaries = self._compress_hybrid(messages)

        return self._create_result(
            messages=messages,
            kept_messages=kept,
            removed_messages=removed,
            summaries=summaries,
            start_time=start_time,
        )

    def _compress_recent_first(
        self,
        messages: list[SessionMessage],
    ) -> tuple:
        """最近优先策略

        优先保留最近的消息，删除较早的消息。

        Args:
            messages: 原始消息

        Returns:
            tuple: (保留的消息, 删除的消息, 摘要列表)
        """
        target_count = self._calculate_target_count(messages)

        # 始终保留最近的N条
        preserve_count = self.config.preserve_recent_count
        recent_messages = messages[-preserve_count:] if preserve_count > 0 else []

        # 从剩余消息中选择最近的
        remaining = messages[:-preserve_count] if preserve_count > 0 else messages
        additional_keep = max(0, target_count - preserve_count)
        kept_remaining = remaining[-additional_keep:] if additional_keep > 0 else []

        kept_messages = kept_remaining + recent_messages
        removed_messages = [m for m in messages if m not in kept_messages]

        # 为删除的消息生成摘要
        summaries = self._generate_summaries(removed_messages)

        return kept_messages, removed_messages, summaries

    def _compress_by_importance(
        self,
        messages: list[SessionMessage],
    ) -> tuple:
        """基于重要性压缩

        根据消息重要性评分保留重要消息。

        Args:
            messages: 原始消息

        Returns:
            tuple: (保留的消息, 删除的消息, 摘要列表)
        """
        # 评分所有消息
        scores = self.scorer.score_messages(messages)
        score_map = {s.message_id: s for s in scores}

        # 按分数排序
        sorted_messages = sorted(
            messages,
            key=lambda m: score_map[m.message_id].score,
            reverse=True,
        )

        # 选择目标数量的消息
        target_count = self._calculate_target_count(messages)
        kept_set = set(sorted_messages[:target_count])

        # 确保最近的消息被保留
        preserve_count = self.config.preserve_recent_count
        if preserve_count > 0:
            for msg in messages[-preserve_count:]:
                kept_set.add(msg)

        kept_messages = [m for m in messages if m in kept_set]
        removed_messages = [m for m in messages if m not in kept_set]

        summaries = self._generate_summaries(removed_messages)

        return kept_messages, removed_messages, summaries

    def _compress_by_clustering(
        self,
        messages: list[SessionMessage],
    ) -> tuple:
        """语义聚类压缩

        将相似消息聚类，每个聚类保留代表。

        Args:
            messages: 原始消息

        Returns:
            tuple: (保留的消息, 删除的消息, 摘要列表)
        """
        # 简化的聚类实现：按对话轮次聚类
        # 在实际应用中，可以使用向量相似度进行聚类

        target_count = self._calculate_target_count(messages)

        # 将消息按轮次分组（每两条为一轮：用户+助手）
        clusters = []
        i = 0
        while i < len(messages):
            if i + 1 < len(messages):
                # 成对消息
                clusters.append([messages[i], messages[i + 1])
                i += 2
            else:
                # 单条消息
                clusters.append([messages[i])
                i += 1

        # 计算每个聚类的重要性
        cluster_scores = []
        for cluster in clusters:
            cluster_score = sum(len(m.content) for m in cluster)
            cluster_scores.append((cluster, cluster_score))

        # 按重要性排序并选择
        cluster_scores.sort(key=lambda x: x[1], reverse=True)
        target_clusters = max(1, target_count // 2)

        kept_clusters = [c for c, _ in cluster_scores[:target_clusters]

        # 确保保留最近的消息
        preserve_count = self.config.preserve_recent_count
        if preserve_count > 0:
            recent_messages = messages[-preserve_count:]
            for msg in recent_messages:
                for cluster in kept_clusters:
                    if msg in cluster:
                        break
                else:
                    # 如果最近消息不在已选聚类中，单独添加
                    kept_clusters.append([msg])

        kept_messages = []
        for cluster in kept_clusters:
            kept_messages.extend(cluster)

        # 去重
        seen = set()
        unique_kept = []
        for msg in kept_messages:
            if msg.message_id not in seen:
                seen.add(msg.message_id)
                unique_kept.append(msg)

        kept_messages = unique_kept
        removed_messages = [m for m in messages if m not in kept_messages]

        summaries = self._generate_summaries(removed_messages)

        return kept_messages, removed_messages, summaries

    def _compress_hybrid(
        self,
        messages: list[SessionMessage],
    ) -> tuple:
        """混合策略

        结合多种策略的优点：
        1. 始终保留最近N条消息
        2. 根据重要性评分选择其他消息
        3. 平衡时间和重要性

        Args:
            messages: 原始消息

        Returns:
            tuple: (保留的消息, 删除的消息, 摘要列表)
        """
        target_count = self._calculate_target_count(messages)

        # 1. 保留最近的消息
        preserve_count = min(self.config.preserve_recent_count, target_count)
        recent_messages = messages[-preserve_count:] if preserve_count > 0 else []
        remaining = messages[:-preserve_count] if preserve_count > 0 else messages

        # 2. 从剩余消息中根据重要性选择
        additional_count = max(0, target_count - preserve_count)

        if additional_count > 0 and remaining:
            scores = self.scorer.score_messages(remaining)
            score_map = {s.message_id: s for s in scores}

            # 按分数排序，同时考虑时间因素
            sorted_remaining = sorted(
                remaining,
                key=lambda m: (
                    score_map[m.message_id].score * 0.7
                    + (remaining.index(m) / len(remaining)) * 0.3
                ),
                reverse=True,
            )

            kept_remaining = sorted_remaining[:additional_count]
        else:
            kept_remaining = []

        kept_messages = kept_remaining + recent_messages

        # 去重（保持原始顺序）
        seen = set()
        ordered_kept = []
        for msg in messages:
            if msg in kept_messages and msg.message_id not in seen:
                seen.add(msg.message_id)
                ordered_kept.append(msg)

        removed_messages = [m for m in messages if m.message_id not in seen]
        summaries = self._generate_summaries(removed_messages)

        return ordered_kept, removed_messages, summaries

    def _calculate_target_count(self, messages: list[SessionMessage]) -> int:
        """计算目标保留数量

        Args:
            messages: 原始消息

        Returns:
            int: 目标数量
        """
        total_count = len(messages)

        # 根据级别确定保留比例
        ratio = self.LEVEL_RATIOS.get(self.config.level, 0.6)

        # 根据token数调整
        total_tokens = sum(m.token_count for m in messages)
        if total_tokens > self.config.max_tokens:
            ratio = min(ratio, self.config.max_tokens / total_tokens)

        # 计算目标数量
        target_count = max(
            int(total_count * ratio),
            int(total_count * self.config.min_keep_ratio),
        )

        # 至少保留最近的消息数
        target_count = max(target_count, self.config.preserve_recent_count)

        return target_count

    def _generate_summaries(
        self,
        messages: list[SessionMessage],
    ) -> list[str]:
        """为删除的消息生成摘要

        Args:
            messages: 被删除的消息

        Returns:
            list[str]: 摘要列表
        """
        if not messages:
            return []

        summaries = []

        # 按角色分组生成摘要
        user_msgs = [m for m in messages if m.role.value == "user"]
        assistant_msgs = [m for m in messages if m.role.value == "assistant"]

        if user_msgs:
            count = len(user_msgs)
            summaries.append(f"省略了{count}条用户消息")

        if assistant_msgs:
            count = len(assistant_msgs)
            summaries.append(f"省略了{count}条助手回复")

        # 如果有工具调用，单独记录
        tool_msgs = [m for m in messages if m.role.value == "tool"]
        if tool_msgs:
            summaries.append(f"省略了{len(tool_msgs)}条工具调用结果")

        return summaries

    def _create_result(
        self,
        messages: list[SessionMessage],
        kept_messages: list[SessionMessage],
        removed_messages: list[SessionMessage],
        summaries: list[str],
        start_time: float,
    ) -> CompressionResult:
        """创建压缩结果

        Args:
            messages: 原始消息
            kept_messages: 保留的消息
            removed_messages: 删除的消息
            summaries: 摘要
            start_time: 开始时间

        Returns:
            CompressionResult: 压缩结果
        """
        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000

        original_ids = [m.message_id for m in messages]
        compressed_ids = [m.message_id for m in kept_messages]
        removed_ids = [m.message_id for m in removed_messages]

        # 计算压缩率
        if len(messages) > 0:
            compression_ratio = 1.0 - (len(kept_messages) / len(messages))
        else:
            compression_ratio = 0.0

        # 计算节省的token
        original_tokens = sum(m.token_count for m in messages)
        compressed_tokens = sum(m.token_count for m in kept_messages)
        tokens_saved = original_tokens - compressed_tokens

        # 计算质量分数
        quality_score = self._calculate_quality_score(
            messages,
            kept_messages,
            removed_messages,
        )

        return CompressionResult(
            original_messages=original_ids,
            compressed_messages=compressed_ids,
            removed_messages=removed_ids,
            summaries=summaries,
            compression_ratio=round(compression_ratio, 3),
            tokens_saved=tokens_saved,
            quality_score=round(quality_score, 3),
            execution_time_ms=round(execution_time_ms, 2),
            strategy=self.config.strategy,
        )

    def _calculate_quality_score(
        self,
        original: list[SessionMessage],
        kept: list[SessionMessage],
        removed: list[SessionMessage],
    ) -> float:
        """计算压缩质量分数

        考虑因素：
        - 是否保留了系统消息
        - 是否保留了最近的消息
        - 删除的消息比例是否合理
        - 是否保留了重要的对话转折

        Args:
            original: 原始消息
            kept: 保留的消息
            removed: 删除的消息

        Returns:
            float: 质量分数 (0.0 - 1.0)
        """
        score = 1.0

        # 检查系统消息是否保留
        system_msgs = [m for m in original if m.role.value == "system"]
        if system_msgs:
            kept_system = [m for m in kept if m.role.value == "system"]
            if len(kept_system) < len(system_msgs):
                score -= 0.1

        # 检查最近消息是否保留
        preserve_count = self.config.preserve_recent_count
        if preserve_count > 0 and len(original) > preserve_count:
            recent = original[-preserve_count:]
            kept_recent = [m for m in kept if m in recent]
            if len(kept_recent) < len(recent):
                score -= 0.1

        # 检查压缩比例是否合理
        if len(original) > 0:
            remove_ratio = len(removed) / len(original)
            expected_ratio = 1.0 - self.LEVEL_RATIOS.get(self.config.level, 0.6)
            if abs(remove_ratio - expected_ratio) > 0.2:
                score -= 0.1

        return max(0.0, score)


__all__ = ["ContextCompressor"]

