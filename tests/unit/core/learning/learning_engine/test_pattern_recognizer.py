#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模式识别器单元测试
Pattern Recognizer Unit Tests

测试PatternRecognizer的功能：
1. 模式识别
2. 关键词提取
3. 边界条件处理
4. 空数据处理

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-27
"""

import pytest
from core.learning.learning_engine import PatternRecognizer


class TestPatternRecognizer:
    """模式识别器测试类"""

    @pytest.fixture
    def recognizer(self):
        """创建模式识别器实例"""
        return PatternRecognizer()

    @pytest.fixture
    def sample_data(self):
        """创建示例数据"""
        return [
            {"text": "专利搜索功能很好用", "content": "positive feedback"},
            {"text": "专利检索速度快", "content": "positive feedback"},
            {"text": "搜索结果准确", "content": "positive feedback"},
            {"text": "界面操作简单", "content": "neutral feedback"},
            {"text": "需要更多筛选条件", "content": "negative feedback"},
        ]

    @pytest.mark.asyncio
    async def test_recognize_patterns(self, recognizer, sample_data):
        """测试模式识别"""
        # 识别模式
        patterns = await recognizer.recognize_patterns(sample_data, "feedback")

        # 验证返回了模式
        assert len(patterns) > 0

        # 验证模式结构
        pattern = patterns[0]
        assert "pattern_id" in pattern
        assert "type" in pattern
        assert "cluster_id" in pattern
        assert "texts" in pattern
        assert "count" in pattern
        assert "keywords" in pattern
        assert "confidence" in pattern

    @pytest.mark.asyncio
    async def test_recognize_patterns_with_insufficient_data(self, recognizer):
        """测试数据不足时的模式识别"""
        # 只有1条数据
        single_data = [{"text": "单条数据", "content": "test"}]

        patterns = await recognizer.recognize_patterns(single_data, "test")

        # 应该返回空列表
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_recognize_patterns_with_empty_data(self, recognizer):
        """测试空数据的模式识别"""
        patterns = await recognizer.recognize_patterns([], "test")

        # 应该返回空列表
        assert len(patterns) == 0

    @pytest.mark.asyncio
    async def test_recognize_patterns_saves_history(self, recognizer, sample_data):
        """测试模式识别保存历史"""
        initial_history_len = len(recognizer.pattern_history)

        # 识别模式
        await recognizer.recognize_patterns(sample_data, "feedback")

        # 验证历史被保存
        assert len(recognizer.pattern_history) == initial_history_len + 1

        # 验证历史记录结构
        history_entry = recognizer.pattern_history[-1]
        assert "timestamp" in history_entry
        assert "context_type" in history_entry
        assert "patterns" in history_entry
        assert history_entry["context_type"] == "feedback"

    @pytest.mark.asyncio
    async def test_pattern_history_multiple_calls(self, recognizer, sample_data):
        """测试多次调用累积历史"""
        # 多次识别模式
        for i in range(3):
            await recognizer.recognize_patterns(sample_data, f"context_{i}")

        # 验证历史累积
        assert len(recognizer.pattern_history) == 3

    def test_extract_keywords(self, recognizer):
        """测试关键词提取"""
        texts = [
            "专利搜索功能很好用",
            "专利检索速度快",
            "搜索结果准确",
        ]

        keywords = recognizer._extract_keywords(texts, top_k=5)

        # 验证返回关键词
        assert len(keywords) > 0
        assert isinstance(keywords, list)
        assert all(isinstance(k, str) for k in keywords)

    def test_extract_keywords_with_empty_text(self, recognizer):
        """测试空文本的关键词提取"""
        keywords = recognizer._extract_keywords([], top_k=5)

        # 应该返回空列表
        assert keywords == []

    def test_extract_keywords_top_k(self, recognizer):
        """测试关键词数量限制"""
        texts = [
            "专利 搜索 功能 很 好用",
            "专利 检索 速度 快",
            "搜索 结果 准确 无误",
        ]

        # 请求前3个关键词
        keywords = recognizer._extract_keywords(texts, top_k=3)

        # 验证只返回指定数量
        assert len(keywords) <= 3

    @pytest.mark.asyncio
    async def test_pattern_confidence_calculation(self, recognizer, sample_data):
        """测试模式置信度计算"""
        patterns = await recognizer.recognize_patterns(sample_data, "feedback")

        # 验证置信度在合理范围内
        for pattern in patterns:
            assert 0 < pattern["confidence"] <= 1

            # 验证置信度等于该聚类在总数据中的比例
            expected_confidence = pattern["count"] / len(sample_data)
            assert abs(pattern["confidence"] - expected_confidence) < 0.01

    @pytest.mark.asyncio
    async def test_pattern_with_mixed_content(self, recognizer):
        """测试混合内容的模式识别"""
        mixed_data = [
            {"text": "专利搜索", "content": "A"},
            {"text": "patent search", "content": "B"},
            {"text": "专利检索", "content": "C"},
            {"text": "商标查询", "content": "D"},
            {"text": "trademark search", "content": "E"},
        ]

        patterns = await recognizer.recognize_patterns(mixed_data, "mixed")

        # 验证能够识别出不同主题的模式
        assert len(patterns) > 0

        # 验证每个模式至少有一条文本
        for pattern in patterns:
            assert len(pattern["texts"]) > 0

    @pytest.mark.asyncio
    async def test_recognize_patterns_with_dict_content(self, recognizer):
        """测试包含字典内容的模式识别"""
        # 包含字典而非简单字符串的数据
        dict_data = [
            {"content": {"query": "专利", "action": "search"}},
            {"content": {"query": "专利", "action": "analyze"}},
            {"content": {"query": "商标", "action": "search"}},
        ]

        patterns = await recognizer.recognize_patterns(dict_data, "dict_test")

        # 验证能够处理字典内容（转换为字符串）
        # 即使无法识别模式，也不应该抛出异常
        assert isinstance(patterns, list)


class TestPatternRecognizerIntegration:
    """模式识别器集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_pattern_workflow(self):
        """测试端到端模式识别工作流"""
        recognizer = PatternRecognizer()

        # 1. 准备数据
        data = [
            {"text": "专利搜索很好", "outcome": "success"},
            {"text": "检索快速", "outcome": "success"},
            {"text": "结果准确", "outcome": "success"},
            {"text": "界面友好", "outcome": "success"},
            {"text": "功能完善", "outcome": "success"},
        ]

        # 2. 识别模式
        patterns = await recognizer.recognize_patterns(data, "positive")

        # 3. 验证结果
        assert len(patterns) > 0
        assert len(recognizer.pattern_history) == 1

        # 4. 获取历史中的模式
        history_patterns = recognizer.pattern_history[0]["patterns"]
        assert len(history_patterns) == len(patterns)
