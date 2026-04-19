#!/usr/bin/env python3
"""
学习引擎公共工具函数单元测试
Unit Tests for Learning Engine Utility Functions

测试统一学习接口中的公共工具函数

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
from production.core.learning.learning_config import (
    LearningConfig,
    P0AutonomousLearningConfig,
    P2ReinforcementLearningConfig,
)
from production.core.learning.unified_interface import (
    calculate_q_table_reward,
    epsilon_greedy_select,
    get_q_values_from_orchestrator,
)

# =============================================================================
# epsilon_greedy_select 测试
# =============================================================================

class TestEpsilonGreedySelect:
    """ε-贪婪选择策略测试"""

    def test_exploit_best_option(self):
        """测试利用：选择Q值最高的选项"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.1, "b": 0.9, "c": 0.3}

        # 使用很小的epsilon，大概率选择b
        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.0  # 纯利用
        )

        assert selected in options
        assert selected == "b"  # 应该选择Q值最高的
        assert 0.0 <= confidence <= 1.0

    def test_explore_random_option(self):
        """测试探索：随机选择"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.0, "b": 0.0, "c": 0.0}

        # 所有Q值都是0，应该随机选择并返回0.5置信度
        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert selected in options
        assert confidence == 0.5  # 默认置信度

    def test_empty_q_values(self):
        """测试空Q值：应该随机选择"""
        options = ["a", "b", "c"]
        q_values = {}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert selected in options
        assert confidence == 0.5

    def test_all_zero_q_values(self):
        """测试所有Q值为0：应该随机选择"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.0, "b": 0.0, "c": 0.0}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.0
        )

        assert selected in options
        assert confidence == 0.5

    def test_confidence_calculation(self):
        """测试置信度计算"""
        options = ["a", "b"]
        q_values = {"a": 2.0, "b": 0.0}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.0
        )

        assert selected == "a"
        # Q值2.0应该映射到置信度1.0（最大）
        assert confidence == 1.0

    def test_negative_q_values(self):
        """测试负Q值"""
        options = ["a", "b", "c"]
        q_values = {"a": -1.0, "b": -0.5, "c": 0.0}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.0
        )

        # 应该选择Q值最高的（c）
        assert selected == "c"
        # Q值0.0应该映射到置信度0.5
        assert confidence == 0.5

    def test_single_option(self):
        """测试单个选项"""
        options = ["only_one"]
        q_values = {"only_one": 0.5}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.1
        )

        assert selected == "only_one"
        assert 0.0 <= confidence <= 1.0

    def test_extreme_q_values(self):
        """测试极端Q值（最大和最小）"""
        options = ["a", "b"]
        q_values = {"a": 2.0, "b": -2.0}

        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=0.0
        )

        assert selected == "a"
        # Q值2.0应该映射到置信度1.0
        assert confidence == 1.0

    def test_high_epsilon(self):
        """测试高探索率"""
        options = ["a", "b", "c"]
        q_values = {"a": 0.9, "b": 0.1, "c": 0.3}

        # 使用很高的epsilon，主要探索
        selected, confidence = epsilon_greedy_select(
            options=options,
            q_values=q_values,
            epsilon=1.0  # 纯探索
        )

        assert selected in options
        assert confidence == 0.5  # 探索时置信度为0.5


# =============================================================================
# calculate_q_table_reward 测试
# =============================================================================

class TestCalculateQTableReward:
    """Q学习奖励计算测试"""

    def test_success_high_satisfaction(self):
        """测试成功+高满意度"""
        reward = calculate_q_table_reward(
            success=True,
            confidence=0.9,
            execution_time_ms=500.0,
            user_satisfaction=0.95,
            baseline_time_ms=1000.0
        )

        # 应该是高奖励
        assert reward > 1.0
        assert reward <= 2.0  # 不应超过最大值

    def test_success_low_satisfaction(self):
        """测试成功+低满意度"""
        reward = calculate_q_table_reward(
            success=True,
            confidence=0.9,
            execution_time_ms=500.0,
            user_satisfaction=0.3,
            baseline_time_ms=1000.0
        )

        # 满意度低应该降低奖励
        assert 0.0 < reward < 1.5

    def test_failure_fast(self):
        """测试失败但快速"""
        reward = calculate_q_table_reward(
            success=False,
            confidence=0.5,
            execution_time_ms=200.0,
            user_satisfaction=None,
            baseline_time_ms=1000.0
        )

        # 失败应该有负奖励
        assert reward < 0.0

    def test_reward_bounds(self):
        """测试奖励边界"""
        # 最大奖励场景
        max_reward = calculate_q_table_reward(
            success=True,
            confidence=1.0,
            execution_time_ms=0.0,
            user_satisfaction=1.0,
            baseline_time_ms=1000.0
        )
        assert max_reward <= 2.0

        # 最小奖励场景
        min_reward = calculate_q_table_reward(
            success=False,
            confidence=0.0,
            execution_time_ms=10000.0,
            user_satisfaction=0.0,
            baseline_time_ms=1000.0
        )
        assert min_reward >= -2.0

    def test_no_satisfaction(self):
        """测试无满意度反馈"""
        reward = calculate_q_table_reward(
            success=True,
            confidence=0.8,
            execution_time_ms=800.0,
            user_satisfaction=None,  # 无满意度
            baseline_time_ms=1000.0
        )

        # 应该仍然是正奖励（成功+快速）
        assert reward > 0.0

    def test_very_slow_execution(self):
        """测试极慢执行"""
        reward = calculate_q_table_reward(
            success=True,
            confidence=0.9,
            execution_time_ms=5000.0,  # 非常慢
            user_satisfaction=0.5,  # 中等满意度，使时间惩罚更明显
            baseline_time_ms=1000.0
        )

        # 慢速应该有惩罚（实际计算: 1.0 + 0.2 - 0.5 + 0.0 = 0.7）
        assert reward < 1.0
        assert reward > 0.0  # 但仍然是正奖励（因为成功）

    def test_zero_execution_time(self):
        """测试零执行时间"""
        reward = calculate_q_table_reward(
            success=True,
            confidence=0.8,
            execution_time_ms=0.0,  # 瞬时完成
            user_satisfaction=0.7,
            baseline_time_ms=1000.0
        )

        # 极快应该有额外奖励
        assert reward > 1.0

    def test_edge_case_confidence(self):
        """测试置信度边界"""
        # 最小置信度
        reward_min = calculate_q_table_reward(
            success=True,
            confidence=0.0,
            execution_time_ms=1000.0,
            user_satisfaction=0.5
        )

        # 最大置信度
        reward_max = calculate_q_table_reward(
            success=True,
            confidence=1.0,
            execution_time_ms=1000.0,
            user_satisfaction=0.5
        )

        # 高置信度应该有更高奖励
        assert reward_max > reward_min


# =============================================================================
# get_q_values_from_orchestrator 测试
# =============================================================================

class TestGetQValuesFromOrchestrator:
    """从编排器获取Q值测试"""

    def test_none_learning_interface(self):
        """测试None学习接口"""
        q_values = get_q_values_from_orchestrator(
            learning_interface=None,
            state="test_state",
            options=["a", "b"]
        )

        assert q_values == {}

    def test_missing_orchestrator_attribute(self):
        """测试缺少orchestrator属性"""
        class FakeInterface:
            pass

        interface = FakeInterface()
        q_values = get_q_values_from_orchestrator(
            learning_interface=interface,
            state="test_state",
            options=["a", "b"]
        )

        assert q_values == {}

    def test_none_orchestrator(self):
        """测试orchestrator为None"""
        class FakeInterface:
            orchestrator = None

        interface = FakeInterface()
        q_values = get_q_values_from_orchestrator(
            learning_interface=interface,
            state="test_state",
            options=["a", "b"]
        )

        assert q_values == {}


# =============================================================================
# 配置类测试
# =============================================================================

class TestP0AutonomousLearningConfig:
    """P0自主学习配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = P0AutonomousLearningConfig()

        assert config.enable_performance_monitoring is True
        assert config.metrics_cache_size == 1000
        assert config.anomaly_threshold_std == 2.5
        assert config.optimization_trigger_interval == 100


class TestP2ReinforcementLearningConfig:
    """P2强化学习配置测试"""

    def test_default_values(self):
        """测试默认值"""
        config = P2ReinforcementLearningConfig()

        assert config.enable_q_learning is True
        assert config.epsilon == 0.1
        assert config.learning_rate_alpha == 0.1
        assert config.discount_factor_gamma == 0.9
        assert config.q_table_max_value == 2.0
        assert config.q_table_min_value == -2.0


class TestLearningConfig:
    """全局学习配置测试"""

    def test_shared_attributes(self):
        """测试配置属性共享（类级别单例）"""
        config1 = LearningConfig()
        config2 = LearningConfig()

        # 虽然不是同一个实例，但配置属性应该是类级别的
        # 所以修改一个实例的属性会影响所有实例
        assert config1.p2_reinforcement.epsilon == config2.p2_reinforcement.epsilon

        # 修改一个实例的配置
        config1.p2_reinforcement.epsilon = 0.2

        # 另一个实例也应该看到这个变化（因为p2_reinforcement是类属性）
        assert config2.p2_reinforcement.epsilon == 0.2

        # 恢复原值
        LearningConfig.p2_reinforcement.epsilon = 0.1

    def test_default_values(self):
        """测试默认值"""
        config = LearningConfig()

        # P0配置
        assert config.p0_autonomous.enable_performance_monitoring is True

        # P1配置
        assert config.p1_online.replay_buffer_size == 1000

        # P2配置
        assert config.p2_reinforcement.epsilon == 0.1


# =============================================================================
# 运行测试
# =============================================================================
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 学习引擎工具函数单元测试")
    print("=" * 80)

    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
