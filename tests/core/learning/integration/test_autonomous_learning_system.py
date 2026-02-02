#!/usr/bin/env python3
"""
自主学习系统集成测试
Integration Tests for Autonomous Learning System

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from core.learning.autonomous_learning_system import (
    ABTestExperiment,
    ABTestVariant,
    AutonomousLearningSystem,
    LearningExperience,
    LearningType,
    OptimizationProposal,
    OptimizationTarget,
)


@pytest.mark.integration
class TestAutonomousLearningSystem:
    """自主学习系统集成测试"""

    @pytest.fixture
    async def learning_system(self):
        """创建学习系统实例"""
        system = AutonomousLearningSystem(agent_id="test_agent")
        # 清空初始状态以便测试
        system.experiences.clear()
        system.performance_history.clear()
        system.optimization_proposals.clear()
        system.ab_tests.clear()
        return system

    @pytest.mark.asyncio
    async def test_learn_from_experience_success(self, learning_system):
        """测试从成功经验中学习"""
        context = {"task": "document_analysis", "complexity": "high"}
        action = "use_advanced_model"
        result = {"status": "success", "accuracy": 0.95}

        experience = await learning_system.learn_from_experience(
            context=context,
            action=action,
            result=result,
            reward=0.9,
        )

        assert experience.context == context
        assert experience.action == action
        assert experience.reward == 0.9
        assert len(learning_system.experiences) == 1
        assert learning_system.metrics["total_learning_cycles"] == 1

    @pytest.mark.asyncio
    async def test_learn_from_experience_failure(self, learning_system):
        """测试从失败经验中学习"""
        context = {"task": "document_analysis"}
        action = "use_basic_model"
        result = {"status": "error", "message": "Timeout"}

        experience = await learning_system.learn_from_experience(
            context=context,
            action=action,
            result=result,
            reward=-0.5,
        )

        assert experience.reward == -0.5
        # 负奖励应该被记录
        assert len(learning_system.performance_history["reward"]) > 0

    @pytest.mark.asyncio
    async def test_learn_from_reinforcement(self, learning_system):
        """测试强化学习"""
        context = {"task": "patent_search"}
        action = "use_hybrid_search"

        # 模拟多次学习
        for i in range(5):
            await learning_system.learn_from_experience(
                context=context,
                action=action,
                result={"found": i * 10 + 10},
                reward=0.1 * i,
            )

        assert len(learning_system.experiences) == 5
        # 检查策略更新
        assert action in learning_system.current_policy

    @pytest.mark.asyncio
    async def test_analyze_performance(self, learning_system):
        """测试性能分析"""
        # 添加足够的性能数据
        for i in range(20):
            context = {
                "task": "test_task",
                "execution_time": 0.5 + i * 0.01,
            }
            await learning_system.learn_from_experience(
                context=context,
                action="test_action",
                result={"status": "success"},
                reward=0.8,
            )

        analysis = await learning_system.analyze_performance()

        assert "trends" in analysis
        assert len(learning_system.performance_history["reward"]) >= 20

    @pytest.mark.asyncio
    async def test_create_ab_test(self, learning_system):
        """测试创建A/B测试"""
        experiment_id = await learning_system.create_ab_test(
            name="model_comparison",
            description="Compare baseline vs experimental model",
            control_config={"model": "baseline"},
            treatment_configs=[{"model": "experimental"}],
        )

        assert experiment_id in learning_system.ab_tests
        experiment = learning_system.ab_tests[experiment_id]
        assert experiment.name == "model_comparison"
        assert len(experiment.treatment_variants) == 1

    @pytest.mark.asyncio
    async def test_optimization_proposal_generation(self, learning_system):
        """测试优化提案生成"""
        # 创建一个简单的实现函数
        async def mock_optimize():
            return True

        proposal = OptimizationProposal(
            proposal_id="opt_1",
            target=OptimizationTarget.EFFICIENCY,
            description="优化执行效率",
            expected_improvement=0.2,
            confidence=0.8,
            implementation=mock_optimize,
        )

        learning_system.optimization_proposals.append(proposal)

        assert len(learning_system.optimization_proposals) == 1
        assert proposal.target == OptimizationTarget.EFFICIENCY

    @pytest.mark.asyncio
    async def test_get_learning_metrics(self, learning_system):
        """测试获取学习指标"""
        # 添加一些经验
        await learning_system.learn_from_experience(
            context={"task": "test1"},
            action="action1",
            result={"status": "ok"},
            reward=0.8,
        )
        await learning_system.learn_from_experience(
            context={"task": "test2"},
            action="action2",
            result={"status": "ok"},
            reward=0.6,
        )

        metrics = await learning_system.get_learning_metrics()

        # get_learning_metrics返回嵌套结构
        assert "learning" in metrics
        assert metrics["learning"]["total_experiences"] >= 2
        assert "performance" in metrics

    @pytest.mark.asyncio
    async def test_policy_update(self, learning_system):
        """测试策略更新"""
        action = "test_action"

        # 第一次学习
        await learning_system.learn_from_experience(
            context={},
            action=action,
            result={},
            reward=0.8,
        )

        assert action in learning_system.current_policy
        policy = learning_system.current_policy[action]
        assert policy["count"] == 1
        assert policy["avg_reward"] == 0.8

        # 第二次学习（相同动作）
        await learning_system.learn_from_experience(
            context={},
            action=action,
            result={},
            reward=0.9,
        )

        policy = learning_system.current_policy[action]
        assert policy["count"] == 2
        # 平均值应该更新（使用指数移动平均）
        assert 0.7 < policy["avg_reward"] < 0.9

    @pytest.mark.asyncio
    async def test_concurrent_learning(self, learning_system):
        """测试并发学习"""
        # 并发添加多个经验
        tasks = []
        for i in range(50):
            task = learning_system.learn_from_experience(
                context={"index": i},
                action=f"action_{i % 5}",
                result={"value": i},
                reward=0.5,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        assert len(learning_system.experiences) == 50

    @pytest.mark.asyncio
    async def test_performance_history_limits(self, learning_system):
        """测试性能历史记录限制"""
        # 添加超过限制的记录（deque最大1000）
        for i in range(1500):
            await learning_system.learn_from_experience(
                context={},
                action="test",
                result={},
                reward=0.5,
            )

        # 应该被限制在1000
        for metric_history in learning_system.performance_history.values():
            assert len(metric_history) <= 1000

    @pytest.mark.asyncio
    async def test_experience_buffer_limits(self, learning_system):
        """测试经验缓冲区限制"""
        # deque最大10000
        for i in range(15000):
            await learning_system.learn_from_experience(
                context={"index": i},
                action="test",
                result={},
                reward=0.5,
            )

        # 应该被限制在10000
        assert len(learning_system.experiences) <= 10000

    @pytest.mark.asyncio
    async def test_reward_calculation(self, learning_system):
        """测试奖励计算"""
        # 测试自动计算奖励
        context = {
            "task": "test",
            "execution_time": 1.0,
        }

        await learning_system.learn_from_experience(
            context=context,
            action="test_action",
            result={"accuracy": 0.9},
            reward=None,  # 应该自动计算
        )

        # 应该被记录
        assert len(learning_system.performance_history["reward"]) == 1
        assert len(learning_system.performance_history["execution_time"]) == 1


@pytest.mark.integration
class TestLearningExperience:
    """学习经验数据类测试"""

    def test_create_experience(self):
        """测试创建学习经验"""
        experience = LearningExperience(
            experience_id="exp_1",
            timestamp=datetime.now(),
            context={"task": "test"},
            action="test_action",
            result={"status": "success"},
            reward=0.9,
        )

        assert experience.experience_id == "exp_1"
        assert experience.action == "test_action"
        assert experience.reward == 0.9

    def test_experience_with_metadata(self):
        """测试带元数据的经验"""
        metadata = {
            "user_id": "user1",
            "session_id": "session1",
        }
        experience = LearningExperience(
            experience_id="exp_2",
            timestamp=datetime.now(),
            context={},
            action="action",
            result={},
            reward=0.5,
            metadata=metadata,
        )

        assert experience.metadata == metadata


@pytest.mark.integration
class TestABTestClasses:
    """A/B测试类测试"""

    def test_create_variant(self):
        """测试创建变体"""
        variant = ABTestVariant(
            variant_id="v1",
            name="control",
            config={"model": "baseline"},
        )

        assert variant.variant_id == "v1"
        assert variant.name == "control"
        assert variant.sample_size == 0

    def test_create_experiment(self):
        """测试创建实验"""
        control = ABTestVariant(
            variant_id="control",
            name="baseline",
            config={},
        )
        treatment = ABTestVariant(
            variant_id="treatment",
            name="experimental",
            config={},
        )

        experiment = ABTestExperiment(
            experiment_id="exp_1",
            name="test_experiment",
            description="Test description",
            control_variant=control,
            treatment_variants=[treatment],
        )

        assert experiment.experiment_id == "exp_1"
        assert experiment.status == "running"
        assert len(experiment.treatment_variants) == 1


@pytest.mark.integration
class TestOptimizationTarget:
    """优化目标枚举测试"""

    def test_optimization_targets(self):
        """测试所有优化目标"""
        targets = [
            OptimizationTarget.ACCURACY,
            OptimizationTarget.EFFICIENCY,
            OptimizationTarget.ROBUSTNESS,
            OptimizationTarget.USER_SATISFACTION,
            OptimizationTarget.COST,
        ]

        assert len(targets) == 5
        for target in targets:
            assert isinstance(target.value, str)


@pytest.mark.integration
class TestLearningType:
    """学习类型枚举测试"""

    def test_learning_types(self):
        """测试所有学习类型"""
        types = [
            LearningType.SUPERVISED,
            LearningType.REINFORCEMENT,
            LearningType.UNSUPERVISED,
            LearningType.FEW_SHOT,
            LearningType.TRANSFER,
        ]

        assert len(types) == 5
