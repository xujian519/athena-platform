#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经验存储器单元测试
Experience Store Unit Tests

测试ExperienceStore的功能：
1. 添加经验
2. 获取相似经验
3. 上下文键生成
4. 边界条件处理

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-27
"""

import pytest
from datetime import datetime
from core.learning.learning_engine import ExperienceStore


class TestExperienceStore:
    """经验存储器测试类"""

    @pytest.fixture
    def store(self):
        """创建经验存储器实例"""
        return ExperienceStore(max_experiences=100)

    @pytest.fixture
    def sample_experience(self):
        """创建示例经验"""
        return {
            "type": "test",
            "context": {"task_type": "search", "domain": "patent"},
            "content": {"query": "test query"},
            "outcome": {"success": True},
        }

    def test_add_experience(self, store, sample_experience):
        """测试添加经验"""
        # 添加经验
        store.add_experience(sample_experience)

        # 验证经验被添加
        assert len(store.experiences) == 1

        # 验证经验有ID和时间戳
        exp = store.experiences[0]
        assert "id" in exp
        assert "timestamp" in exp
        assert isinstance(exp["timestamp"], datetime)

    def test_add_multiple_experiences(self, store):
        """测试添加多个经验"""
        # 添加多个经验
        for i in range(5):
            exp = {
                "type": "test",
                "context": {"index": i},
                "content": {},
                "outcome": {},
            }
            store.add_experience(exp)

        # 验证所有经验被添加
        assert len(store.experiences) == 5

        # 验证ID是唯一的
        ids = [exp["id"] for exp in store.experiences]
        assert len(ids) == len(set(ids))

    def test_max_experiences_limit(self, store):
        """测试最大经验数量限制"""
        # 设置较小的最大值
        small_store = ExperienceStore(max_experiences=3)

        # 添加超过最大值的经验
        for i in range(5):
            exp = {"type": "test", "context": {"i": i}, "content": {}, "outcome": {}}
            small_store.add_experience(exp)

        # 验证只保留最近的经验
        assert len(small_store.experiences) == 3

    def test_get_similar_experiences(self, store, sample_experience):
        """测试获取相似经验"""
        # 添加相似的经验
        for i in range(3):
            exp = {
                "type": "test",
                "context": {"task_type": "search", "domain": "patent"},
                "content": {"index": i},
                "outcome": {},
            }
            store.add_experience(exp)

        # 获取相似经验
        similar = store.get_similar_experiences({"task_type": "search", "domain": "patent"})

        # 验证返回了相似经验
        assert len(similar) == 3

    def test_get_similar_experiences_empty(self, store):
        """测试获取不存在上下文的相似经验"""
        # 添加一些经验
        exp = {
            "type": "test",
            "context": {"task_type": "search"},
            "content": {},
            "outcome": {},
        }
        store.add_experience(exp)

        # 查询不同的上下文
        similar = store.get_similar_experiences({"task_type": "different"})

        # 验证没有返回结果
        assert len(similar) == 0

    def test_get_similar_experiences_with_limit(self, store):
        """测试带限制的相似经验获取"""
        # 添加多个相似经验
        for i in range(10):
            exp = {
                "type": "test",
                "context": {"task_type": "search"},
                "content": {"index": i},
                "outcome": {},
            }
            store.add_experience(exp)

        # 限制返回数量
        similar = store.get_similar_experiences({"task_type": "search"}, limit=5)

        # 验证只返回指定数量
        assert len(similar) == 5

    def test_similar_experiences_sorted_by_time(self, store):
        """测试相似经验按时间排序"""
        # 添加多个经验（会有时间延迟）
        import time

        for i in range(3):
            exp = {
                "type": "test",
                "context": {"task_type": "search"},
                "content": {"index": i},
                "outcome": {},
            }
            store.add_experience(exp)
            time.sleep(0.01)  # 确保时间戳不同

        # 获取相似经验
        similar = store.get_similar_experiences({"task_type": "search"})

        # 验证按时间降序排列（最新的在前）
        for i in range(len(similar) - 1):
            assert similar[i]["timestamp"] >= similar[i + 1]["timestamp"]

    def test_context_key_generation(self, store):
        """测试上下文键生成"""
        # 相同的上下文应该生成相同的键
        context1 = {"task_type": "search", "domain": "patent"}
        context2 = {"domain": "patent", "task_type": "search"}  # 顺序不同

        key1 = store._generate_context_key(context1)
        key2 = store._generate_context_key(context2)

        # 验证键相同（因为json.dumps使用sort_keys=True）
        assert key1 == key2

    def test_empty_experience_store(self, store):
        """测试空经验存储器"""
        # 验证新创建的存储器是空的
        assert len(store.experiences) == 0
        assert len(store.experience_index) == 0

    def test_experience_with_complex_context(self, store):
        """测试包含复杂上下文的经验"""
        complex_context = {
            "task_type": "search",
            "nested": {"level1": {"level2": "value"}},
            "list": [1, 2, 3],
        }

        exp = {
            "type": "test",
            "context": complex_context,
            "content": {},
            "outcome": {},
        }
        store.add_experience(exp)

        # 验证可以检索到
        similar = store.get_similar_experiences(complex_context)
        assert len(similar) == 1
