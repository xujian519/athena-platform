#!/usr/bin/env python3
"""
学习引擎工具函数性能基准测试
Performance Benchmark Tests for Learning Engine Utility Functions

使用pytest-benchmark对公共工具函数进行性能测试

作者: Athena AI Team
版本: 1.0.0
创建: 2026-01-29
"""

from __future__ import annotations
import sys
from pathlib import Path

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入被测试的函数
from production.core.learning.unified_interface import (
    calculate_q_table_reward,
    epsilon_greedy_select,
    get_q_values_from_orchestrator,
)

# =============================================================================
# 性能基准测试
# =============================================================================

class TestEpsilonGreedySelectPerformance:
    """ε-贪婪选择策略性能测试"""

    def test_benchmark_small_options(self, benchmark):
        """基准测试：少量选项（3个）"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert result[0] in options

    def test_benchmark_medium_options(self, benchmark):
        """基准测试：中等数量选项（10个）"""
        options = [f"option_{i}" for i in range(10)]
        q_values = {f"option_{i}": i / 10.0 for i in range(10)}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert result[0] in options

    def test_benchmark_large_options(self, benchmark):
        """基准测试：大量选项（100个）"""
        options = [f"option_{i}" for i in range(100)]
        q_values = {f"option_{i}": i / 100.0 for i in range(100)}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert result[0] in options

    def test_benchmark_empty_q_values(self, benchmark):
        """基准测试：空Q值"""
        options = ["a", "b", "c"]
        q_values = {}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert result[0] in options

    def test_benchmark_pure_exploitation(self, benchmark):
        """基准测试：纯利用模式（epsilon=0）"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=0.0
        )

        assert result[0] == "b"

    def test_benchmark_pure_exploration(self, benchmark):
        """基准测试：纯探索模式（epsilon=1）"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

        result = benchmark(
            epsilon_greedy_select,
            options=options,
            q_values=q_values,
            epsilon=1.0
        )

        assert result[0] in options


class TestCalculateQTableRewardPerformance:
    """Q学习奖励计算性能测试"""

    def test_benchmark_success_case(self, benchmark):
        """基准测试：成功场景"""
        result = benchmark(
            calculate_q_table_reward,
            success=True,
            confidence=0.9,
            execution_time_ms=500.0,
            user_satisfaction=0.95,
            baseline_time_ms=1000.0
        )

        assert result > 1.0

    def test_benchmark_failure_case(self, benchmark):
        """基准测试：失败场景"""
        result = benchmark(
            calculate_q_table_reward,
            success=False,
            confidence=0.5,
            execution_time_ms=200.0,
            user_satisfaction=None,
            baseline_time_ms=1000.0
        )

        assert result < 0.0

    def test_benchmark_no_satisfaction(self, benchmark):
        """基准测试：无满意度反馈"""
        result = benchmark(
            calculate_q_table_reward,
            success=True,
            confidence=0.8,
            execution_time_ms=800.0,
            user_satisfaction=None,
            baseline_time_ms=1000.0
        )

        assert result > 0.0

    def test_benchmark_extreme_values(self, benchmark):
        """基准测试：极端值"""
        result = benchmark(
            calculate_q_table_reward,
            success=True,
            confidence=1.0,
            execution_time_ms=0.0,
            user_satisfaction=1.0,
            baseline_time_ms=1000.0
        )

        assert result <= 2.0


class TestGetQValuesFromOrchestratorPerformance:
    """从编排器获取Q值性能测试"""

    def test_benchmark_none_interface(self, benchmark):
        """基准测试：None接口"""
        result = benchmark(
            get_q_values_from_orchestrator,
            learning_interface=None,
            state="test_state",
            options=["a", "b", "c"]
        )

        assert result == {}

    def test_benchmark_missing_attribute(self, benchmark):
        """基准测试：缺少属性"""
        class FakeInterface:
            pass

        interface = FakeInterface()

        result = benchmark(
            get_q_values_from_orchestrator,
            learning_interface=interface,
            state="test_state",
            options=["a", "b", "c"]
        )

        assert result == {}

    def test_benchmark_small_options(self, benchmark):
        """基准测试：少量选项"""
        options = ["a", "b", "c"]

        result = benchmark(
            get_q_values_from_orchestrator,
            learning_interface=None,
            state="test_state",
            options=options
        )

        assert result == {}

    def test_benchmark_large_options(self, benchmark):
        """基准测试：大量选项"""
        options = [f"option_{i}" for i in range(100)]

        result = benchmark(
            get_q_values_from_orchestrator,
            learning_interface=None,
            state="test_state",
            options=options
        )

        assert result == {}


class TestIntegrationPerformance:
    """集成性能测试"""

    def test_benchmark_full_workflow(self, benchmark):
        """基准测试：完整工作流"""
        def workflow():
            # 模拟完整的决策流程
            options = ["a", "b", "c"]
            q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

            # 1. 获取Q值（简化）
            # 2. ε-贪婪选择
            selected, confidence = epsilon_greedy_select(
                options=options,
                q_values=q_values,
                epsilon=0.1
            )

            # 3. 计算奖励
            reward = calculate_q_table_reward(
                success=True,
                confidence=confidence,
                execution_time_ms=500.0,
                user_satisfaction=0.9,
                baseline_time_ms=1000.0
            )

            return selected, confidence, reward

        result = benchmark(workflow)

        assert result[0] in ["a", "b", "c"]
        assert 0.0 <= result[1] <= 1.0
        assert -2.0 <= result[2] <= 2.0

    def test_benchmark_repeated_selections(self, benchmark):
        """基准测试：重复选择（模拟多次决策）"""
        def repeated_selections():
            results = []
            options = ["a", "b", "c"]
            q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

            for _ in range(10):
                selected, confidence = epsilon_greedy_select(
                    options=options,
                    q_values=q_values,
                    epsilon=0.1
                )
                results.append((selected, confidence))

            return results

        result = benchmark(repeated_selections)

        assert len(result) == 10


# =============================================================================
# 运行测试
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("⚡ 学习引擎工具函数性能基准测试")
    print("=" * 80)

    # 运行性能测试
    pytest.main([__file__, "-v", "--tb=short", "--benchmark-only"])
