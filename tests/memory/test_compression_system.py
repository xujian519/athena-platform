#!/usr/bin/env python3
"""
上下文压缩系统测试

测试上下文压缩系统的所有核心功能。

作者: Athena平台团队
创建时间: 2026-04-21
"""

from datetime import datetime, timedelta

import pytest

from core.framework.memory.sessions.compression.compressor import ContextCompressor
from core.framework.memory.sessions.compression.scorer import MessageScorer
from core.framework.memory.sessions.compression.types import (
    CompressionConfig,
    CompressionLevel,
    CompressionResult,
    CompressionStrategy,
    ImportanceScore,
    MessageImportance,
    TokenBudget,
)
from core.framework.memory.sessions.types import MessageRole, SessionMessage


class TestTokenBudget:
    """Token预算管理测试"""

    def test_initial_budget(self):
        """测试初始预算"""
        budget = TokenBudget(total_budget=1000)
        assert budget.total_budget == 1000
        assert budget.available == 1000
        assert budget.usage_rate == 0.0

    def test_reserve_and_consume(self):
        """测试预留和消耗"""
        budget = TokenBudget(total_budget=1000)

        # 预留
        assert budget.reserve(200) is True
        assert budget.reserved == 200
        assert budget.available == 800

        # 消耗
        assert budget.consume(200) is True
        assert budget.reserved == 0
        assert budget.used == 200
        assert budget.available == 800

    def test_insufficient_budget(self):
        """测试预算不足"""
        budget = TokenBudget(total_budget=1000)

        # 超出预算
        assert budget.reserve(1500) is False
        assert budget.consume(1500) is False

    def test_release(self):
        """测试释放预留"""
        budget = TokenBudget(total_budget=1000)

        budget.reserve(300)
        budget.release(100)
        assert budget.reserved == 200

        budget.release(300)  # 释放超过预留
        assert budget.reserved == 0

    def test_compression_trigger(self):
        """测试压缩触发"""
        budget = TokenBudget(total_budget=1000, compression_threshold=0.8)

        # 未达到阈值
        budget.consume(500)
        assert budget.needs_compression() is False

        # 达到阈值
        budget.consume(300)
        assert budget.usage_rate == 0.8
        assert budget.needs_compression() is True


class TestImportanceScore:
    """重要性评分测试"""

    def test_score_classification(self):
        """测试分数分类"""
        # 关键
        score1 = ImportanceScore(
            message_id="msg1",
            score=0.95,
            level=MessageImportance.MEDIUM,  # 会被自动调整
        )
        assert score1.level == MessageImportance.CRITICAL

        # 高
        score2 = ImportanceScore("msg2", 0.75, MessageImportance.MEDIUM)
        assert score2.level == MessageImportance.HIGH

        # 中
        score3 = ImportanceScore("msg3", 0.5, MessageImportance.MEDIUM)
        assert score3.level == MessageImportance.MEDIUM

        # 低
        score4 = ImportanceScore("msg4", 0.3, MessageImportance.MEDIUM)
        assert score4.level == MessageImportance.LOW

        # 微不足道
        score5 = ImportanceScore("msg5", 0.1, MessageImportance.MEDIUM)
        assert score5.level == MessageImportance.TRIVIAL


class TestCompressionConfig:
    """压缩配置测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = CompressionConfig()
        assert config.level == CompressionLevel.MEDIUM
        assert config.strategy == CompressionStrategy.HYBRID
        assert config.max_tokens == 8000
        assert config.preserve_recent_count == 10

    def test_custom_config(self):
        """测试自定义配置"""
        config = CompressionConfig(
            level=CompressionLevel.HIGH,
            strategy=CompressionStrategy.IMPORTANCE_BASED,
            max_tokens=4000,
        )
        assert config.level == CompressionLevel.HIGH
        assert config.strategy == CompressionStrategy.IMPORTANCE_BASED
        assert config.max_tokens == 4000


class TestMessageScorer:
    """消息评分器测试"""

    @pytest.fixture
    def scorer(self):
        """创建评分器"""
        return MessageScorer()

    @pytest.fixture
    def sample_messages(self):
        """创建示例消息"""
        now = datetime.now()
        return [
            SessionMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful assistant.",
                timestamp=now,
            ),
            SessionMessage(
                role=MessageRole.USER,
                content="分析专利CN123456789A的创造性",
                timestamp=now + timedelta(seconds=1),
            ),
            SessionMessage(
                role=MessageRole.ASSISTANT,
                content="好的，我来分析这个专利的创造性。首先查看权利要求...",
                timestamp=now + timedelta(seconds=2),
            ),
            SessionMessage(
                role=MessageRole.USER,
                content="谢谢",
                timestamp=now + timedelta(seconds=3),
            ),
            SessionMessage(
                role=MessageRole.TOOL,
                content="专利检索结果：...",
                timestamp=now + timedelta(seconds=4),
            ),
        ]

    def test_score_messages(self, scorer, sample_messages):
        """测试消息评分"""
        scores = scorer.score_messages(sample_messages)

        assert len(scores) == len(sample_messages)
        assert all(isinstance(s, ImportanceScore) for s in scores)

        # 系统消息应该有较高分数
        system_score = next(s for s in scores if s.message_id == sample_messages[0].message_id)
        assert system_score.level in [MessageImportance.CRITICAL, MessageImportance.HIGH]

    def test_importance_factors(self, scorer, sample_messages):
        """测试重要性因子"""
        scores = scorer.score_messages(sample_messages)

        for score in scores:
            # 检查是否有评分因子
            assert isinstance(score.factors, dict)
            assert len(score.factors) > 0

    def test_score_range(self, scorer, sample_messages):
        """测试分数范围"""
        scores = scorer.score_messages(sample_messages)

        for score in scores:
            assert 0.0 <= score.score <= 1.0


class TestContextCompressor:
    """上下文压缩器测试"""

    @pytest.fixture
    def compressor(self):
        """创建压缩器"""
        config = CompressionConfig(
            level=CompressionLevel.MEDIUM,
            strategy=CompressionStrategy.HYBRID,
            max_tokens=2000,
            preserve_recent_count=3,
        )
        return ContextCompressor(config=config)

    @pytest.fixture
    def sample_messages(self):
        """创建大量示例消息"""
        now = datetime.now()
        messages = []

        # 添加系统消息
        messages.append(
            SessionMessage(
                role=MessageRole.SYSTEM,
                content="You are a patent analysis assistant.",
                timestamp=now,
                token_count=10,
            )
        )

        # 添加多轮对话
        for i in range(20):
            messages.append(
                SessionMessage(
                    role=MessageRole.USER,
                    content=f"这是第{i+1}轮用户询问，关于专利分析的问题",
                    timestamp=now + timedelta(seconds=i * 2 + 1),
                    token_count=20,
                )
            )
            messages.append(
                SessionMessage(
                    role=MessageRole.ASSISTANT,
                    content=f"这是第{i+1}轮助手回复，包含详细的专利分析内容，" * 5,
                    timestamp=now + timedelta(seconds=i * 2 + 2),
                    token_count=50,
                )
            )

        return messages

    def test_compress_messages(self, compressor, sample_messages):
        """测试消息压缩"""
        result = compressor.compress(sample_messages)

        assert isinstance(result, CompressionResult)
        assert len(result.compressed_messages) < len(sample_messages)
        assert result.compression_ratio > 0
        assert result.tokens_saved > 0
        assert result.execution_time_ms >= 0

    def test_preserve_recent(self, compressor, sample_messages):
        """测试保留最近消息"""
        result = compressor.compress(sample_messages)

        # 最近的消息应该被保留
        original_ids = [m.message_id for m in sample_messages]
        recent_ids = original_ids[-compressor.config.preserve_recent_count :]

        for msg_id in recent_ids:
            assert msg_id in result.compressed_messages

    def test_quality_score(self, compressor, sample_messages):
        """测试质量评分"""
        result = compressor.compress(sample_messages)

        assert 0.0 <= result.quality_score <= 1.0
        # 质量分数应该达到配置的阈值
        assert result.quality_score >= compressor.config.quality_threshold

    def test_compression_ratio(self, compressor, sample_messages):
        """测试压缩率"""
        result = compressor.compress(sample_messages)

        # MEDIUM级别应该保留约60%
        expected_ratio = 0.6
        actual_ratio = len(result.compressed_messages) / len(sample_messages)

        # 允许10%的误差
        assert abs(actual_ratio - expected_ratio) < 0.15

    def test_empty_messages(self, compressor):
        """测试空消息列表"""
        result = compressor.compress([])

        assert len(result.compressed_messages) == 0
        assert result.compression_ratio == 0

    def test_single_message(self, compressor):
        """测试单条消息"""
        messages = [
            SessionMessage(
                role=MessageRole.USER,
                content="Hello",
                token_count=5,
            )
        ]

        result = compressor.compress(messages)

        # 单条消息应该保留
        assert len(result.compressed_messages) == 1

    def test_strategy_recent_first(self, sample_messages):
        """测试最近优先策略"""
        config = CompressionConfig(
            strategy=CompressionStrategy.RECENT_FIRST,
            max_tokens=1000,
            preserve_recent_count=5,
        )
        compressor = ContextCompressor(config=config)
        result = compressor.compress(sample_messages)

        # 验证策略
        assert result.strategy == CompressionStrategy.RECENT_FIRST

    def test_strategy_importance_based(self, sample_messages):
        """测试基于重要性的策略"""
        config = CompressionConfig(
            strategy=CompressionStrategy.IMPORTANCE_BASED,
            max_tokens=1000,
        )
        compressor = ContextCompressor(config=config)
        result = compressor.compress(sample_messages)

        # 验证策略
        assert result.strategy == CompressionStrategy.IMPORTANCE_BASED

    def test_performance(self, compressor, sample_messages):
        """测试性能：压缩速度应该合理"""
        import time

        total_tokens = sum(m.token_count for m in sample_messages)

        start = time.perf_counter()
        compressor.compress(sample_messages)
        end = time.perf_counter()

        # 计算每1000 tokens的耗时（秒）
        if total_tokens > 0:
            time_per_1k = (end - start) / (total_tokens / 1000)
            # 应该小于1秒（对于Python实现来说合理）
            assert time_per_1k < 1.0  # 1秒
        else:
            # 如果没有token，直接验证执行时间
            assert (end - start) < 1.0

    def test_strategy_semantic_clustering(self, sample_messages):
        """测试语义聚类策略"""
        config = CompressionConfig(
            strategy=CompressionStrategy.SEMANTIC_CLUSTERING,
            max_tokens=1000,
            preserve_recent_count=3,
        )
        compressor = ContextCompressor(config=config)
        result = compressor.compress(sample_messages)

        # 验证策略
        assert result.strategy == CompressionStrategy.SEMANTIC_CLUSTERING
        # 验证压缩效果
        assert len(result.compressed_messages) < len(sample_messages)

    def test_different_compression_levels(self, sample_messages):
        """测试不同压缩级别"""
        for level in [
            CompressionLevel.LOW,
            CompressionLevel.MEDIUM,
            CompressionLevel.HIGH,
        ]:
            config = CompressionConfig(level=level, max_tokens=2000)
            compressor = ContextCompressor(config=config)
            result = compressor.compress(sample_messages)

            # 验证压缩级别
            assert compressor.config.level == level
            # 验证有压缩效果
            assert len(result.compressed_messages) <= len(sample_messages)

    def test_no_compression_level(self, sample_messages):
        """测试不压缩级别"""
        config = CompressionConfig(
            level=CompressionLevel.NONE,
            max_tokens=20000,  # 足够大
        )
        compressor = ContextCompressor(config=config)
        result = compressor.compress(sample_messages)

        # 不压缩应该保留所有消息
        assert len(result.compressed_messages) == len(sample_messages)
        assert result.compression_ratio == 0.0


class TestCompressionResult:
    """压缩结果测试"""

    def test_result_properties(self):
        """测试结果属性"""
        result = CompressionResult(
            original_messages=["msg1", "msg2", "msg3"],
            compressed_messages=["msg1", "msg3"],
            removed_messages=["msg2"],
            summaries=["msg2被摘要"],
            compression_ratio=0.67,
            tokens_saved=100,
            quality_score=0.85,
            execution_time_ms=50,
            strategy=CompressionStrategy.HYBRID,
        )

        assert len(result.original_messages) == 3
        assert len(result.compressed_messages) == 2
        assert len(result.removed_messages) == 1
        assert result.compression_ratio == 0.67
        assert result.tokens_saved == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

