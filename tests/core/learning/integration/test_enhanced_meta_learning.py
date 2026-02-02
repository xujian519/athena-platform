#!/usr/bin/env python3
"""
增强元学习系统集成测试
Integration Tests for Enhanced Meta-Learning System

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
from datetime import datetime

import pytest

from core.learning.enhanced_meta_learning import (
    EnhancedMetaLearningEngine,
    LearningResult,
    LearningStrategy,
    MetaLearningTask,
    StrategyPerformance,
)


@pytest.mark.integration
class TestEnhancedMetaLearningEngine:
    """增强元学习引擎集成测试"""

    @pytest.fixture
    async def meta_engine(self):
        """创建元学习引擎实例"""
        engine = EnhancedMetaLearningEngine(agent_id="test_meta_agent")
        # 清空初始状态以便测试
        engine.task_history.clear()
        engine.learning_results.clear()
        engine.strategy_performance.clear()
        return engine

    @pytest.fixture
    def sample_task(self):
        """创建样本元学习任务"""
        return MetaLearningTask(
            task_id="test_task_001",
            task_type="classification",
            support_set=[
                {"input": "专利分析", "output": "legal_domain"},
                {"input": "内容创作", "output": "media_domain"},
                {"input": "技术研发", "output": "tech_domain"},
            ],
            query_set=[
                {"input": "IP管理", "output": "legal_domain"},
                {"input": "文章撰写", "output": "media_domain"},
            ],
            metadata={"domain": "patent_analysis"},
        )

    @pytest.mark.asyncio
    async def test_select_learning_strategy(self, meta_engine, sample_task):
        """测试学习策略选择"""
        strategy = await meta_engine.select_learning_strategy(sample_task)

        assert isinstance(strategy, LearningStrategy)
        assert strategy in LearningStrategy

    @pytest.mark.asyncio
    async def test_learn_from_few_shots(self, meta_engine, sample_task):
        """测试少样本学习"""
        result = await meta_engine.learn_from_few_shots(sample_task)

        assert isinstance(result, LearningResult)
        assert result.task_id == "test_task_001"
        assert isinstance(result.strategy_used, LearningStrategy)
        assert 0.0 <= result.accuracy <= 1.0
        assert 0.0 <= result.efficiency <= 1.0
        assert 0.0 <= result.retention <= 1.0
        assert 0.0 <= result.transferability <= 1.0
        assert result.learning_time >= 0

    @pytest.mark.asyncio
    async def test_learn_with_specific_strategy(self, meta_engine, sample_task):
        """测试使用指定策略学习"""
        result = await meta_engine.learn_from_few_shots(
            sample_task, strategy=LearningStrategy.RAPID_LEARNING
        )

        assert result.strategy_used == LearningStrategy.RAPID_LEARNING
        assert result.accuracy > 0

    @pytest.mark.asyncio
    async def test_strategy_performance_tracking(self, meta_engine):
        """测试策略性能跟踪"""
        # 创建任务
        task = MetaLearningTask(
            task_id="perf_test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "test"}],
        )

        # 执行多次学习以积累性能数据
        for strategy in [
            LearningStrategy.RAPID_LEARNING,
            LearningStrategy.DEEP_LEARNING,
            LearningStrategy.SPACED_REPETITION,
        ]:
            await meta_engine.learn_from_few_shots(task, strategy=strategy)

        # 验证性能跟踪
        assert len(meta_engine.strategy_performance) >= 3

        # 检查每个策略的性能记录
        for strategy, perf in meta_engine.strategy_performance.items():
            assert isinstance(perf, StrategyPerformance)
            assert 0.0 <= perf.accuracy <= 1.0
            assert 0.0 <= perf.efficiency <= 1.0
            assert 0.0 <= perf.retention <= 1.0
            assert perf.usage_count >= 1

    @pytest.mark.asyncio
    async def test_rapid_learning_characteristics(self, meta_engine):
        """测试快速学习策略特征"""
        task = MetaLearningTask(
            task_id="rapid_test",
            task_type="test",
            support_set=[{"input": f"sample_{i}"} for i in range(5)],  # 少样本
            query_set=[{"input": "query"}],
        )

        result = await meta_engine.learn_from_few_shots(
            task, strategy=LearningStrategy.RAPID_LEARNING
        )

        # 快速学习的效率范围（根据实际实现）
        assert 0.6 <= result.efficiency <= 0.95
        # 快速学习确实有保留率特征（根据实际实现）
        assert 0.6 <= result.retention <= 0.9

    @pytest.mark.asyncio
    async def test_spaced_repetition_characteristics(self, meta_engine):
        """测试间隔重复策略特征"""
        task = MetaLearningTask(
            task_id="spaced_test",
            task_type="test",
            support_set=[{"input": f"sample_{i}"} for i in range(20)],  # 较多样本
            query_set=[{"input": "query"}],
        )

        result = await meta_engine.learn_from_few_shots(
            task, strategy=LearningStrategy.SPACED_REPETITION
        )

        # 间隔重复应该有较高的保留率
        assert result.retention > 0.8

    @pytest.mark.asyncio
    async def test_active_recall_characteristics(self, meta_engine):
        """测试主动回忆策略特征"""
        task = MetaLearningTask(
            task_id="recall_test",
            task_type="test",
            support_set=[{"input": f"sample_{i}"} for i in range(15)],
            query_set=[{"input": "query"}],
        )

        result = await meta_engine.learn_from_few_shots(
            task, strategy=LearningStrategy.ACTIVE_RECALL
        )

        # 主动回忆应该有平衡的性能
        assert 0.65 <= result.accuracy <= 0.95
        assert 0.70 <= result.efficiency <= 0.90
        assert 0.75 <= result.retention <= 0.93

    @pytest.mark.asyncio
    async def test_optimize_hyperparameters(self, meta_engine):
        """测试超参数优化"""
        # 创建验证任务
        validation_tasks = [
            MetaLearningTask(
                task_id=f"val_task_{i}",
                task_type="validation",
                support_set=[{"input": f"sample_{j}"} for j in range(5)],
                query_set=[{"input": "query"}],
            )
            for i in range(3)
        ]

        # 优化超参数
        optimized_params = await meta_engine.optimize_hyperparameters(
            validation_tasks, max_iterations=5
        )

        assert "learning_rate" in optimized_params
        assert "batch_size" in optimized_params
        assert "memory_window" in optimized_params
        assert "exploration_rate" in optimized_params
        assert "forgetting_factor" in optimized_params

        # 验证参数范围
        assert 0.001 <= optimized_params["learning_rate"] <= 0.1
        assert 16 <= optimized_params["batch_size"] <= 64
        assert 5 <= optimized_params["memory_window"] <= 20

    @pytest.mark.asyncio
    async def test_knowledge_transfer(self, meta_engine):
        """测试知识迁移"""
        transfer_samples = [
            {"domain": "patent", "content": "patent_analysis"},
            {"domain": "legal", "content": "legal_review"},
        ]

        result = await meta_engine.transfer_knowledge(
            source_domain="patent_analysis",
            target_domain="legal_review",
            transfer_samples=transfer_samples,
        )

        assert "source_domain" in result
        assert "target_domain" in result
        assert "transfer_score" in result
        assert "adapted_knowledge_count" in result
        assert "timestamp" in result

        assert result["source_domain"] == "patent_analysis"
        assert result["target_domain"] == "legal_review"
        assert 0.0 <= result["transfer_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_task_validation_success(self, meta_engine):
        """测试任务验证 - 成功案例"""
        valid_task = MetaLearningTask(
            task_id="valid_task",
            task_type="classification",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        # 应该不抛出异常
        await meta_engine._validate_task(valid_task)

    @pytest.mark.asyncio
    async def test_task_validation_failure_empty_id(self, meta_engine):
        """测试任务验证 - 失败案例（空ID）"""
        invalid_task = MetaLearningTask(
            task_id="",  # 空ID
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        with pytest.raises(ValueError, match="任务ID必须是非空字符串"):
            await meta_engine._validate_task(invalid_task)

    @pytest.mark.asyncio
    async def test_task_validation_failure_too_long_id(self, meta_engine):
        """测试任务验证 - 失败案例（ID过长）"""
        invalid_task = MetaLearningTask(
            task_id="x" * 101,  # 超过100字符
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        with pytest.raises(ValueError, match="任务ID过长"):
            await meta_engine._validate_task(invalid_task)

    @pytest.mark.asyncio
    async def test_task_validation_failure_oversized_support_set(self, meta_engine):
        """测试任务验证 - 失败案例（支持集过大）"""
        invalid_task = MetaLearningTask(
            task_id="test",
            task_type="test",
            support_set=[{"input": f"sample_{i}"} for i in range(1001)],  # 超过1000
            query_set=[{"input": "query"}],
        )

        with pytest.raises(ValueError, match="支持集过大"):
            await meta_engine._validate_task(invalid_task)

    @pytest.mark.asyncio
    async def test_task_validation_failure_oversized_query_set(self, meta_engine):
        """测试任务验证 - 失败案例（查询集过大）"""
        invalid_task = MetaLearningTask(
            task_id="test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": f"query_{i}"} for i in range(1001)],  # 超过1000
        )

        with pytest.raises(ValueError, match="查询集过大"):
            await meta_engine._validate_task(invalid_task)

    @pytest.mark.asyncio
    async def test_task_validation_invalid_sample_type(self, meta_engine):
        """测试任务验证 - 失败案例（无效样本类型）"""
        invalid_task = MetaLearningTask(
            task_id="test",
            task_type="test",
            support_set=["not_a_dict"],  # 应该是字典列表
            query_set=[{"input": "query"}],
        )

        with pytest.raises(ValueError, match="支持集.*必须是字典类型"):
            await meta_engine._validate_task(invalid_task)

    @pytest.mark.asyncio
    async def test_get_statistics(self, meta_engine):
        """测试获取统计信息"""
        # 执行一些学习
        task = MetaLearningTask(
            task_id="stats_test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        await meta_engine.learn_from_few_shots(task)
        await meta_engine.learn_from_few_shots(task)

        stats = await meta_engine.get_statistics()

        assert "agent_id" in stats
        assert "stats" in stats
        assert "hyperparameters" in stats
        assert "strategy_weights" in stats
        assert "strategy_performance" in stats
        assert "avg_accuracy" in stats
        assert "total_strategies" in stats

        assert stats["agent_id"] == "test_meta_agent"
        assert stats["stats"]["total_tasks"] >= 2

    @pytest.mark.asyncio
    async def test_concurrent_meta_learning(self, meta_engine):
        """测试并发元学习"""
        # 创建多个任务
        tasks = []
        for i in range(20):
            task = MetaLearningTask(
                task_id=f"concurrent_task_{i}",
                task_type="test",
                support_set=[{"input": f"sample_{i}_{j}"} for j in range(5)],
                query_set=[{"input": "query"}],
            )
            tasks.append(task)

        # 并发执行学习
        learning_tasks = [
            meta_engine.learn_from_few_shots(task) for task in tasks
        ]

        results = await asyncio.gather(*learning_tasks)

        assert len(results) == 20
        assert len(meta_engine.learning_results) == 20
        assert meta_engine.stats["total_tasks"] == 20

    @pytest.mark.asyncio
    async def test_strategy_weights_update(self, meta_engine):
        """测试策略权重更新"""
        # 执行学习应该影响权重（间接通过性能数据）
        task = MetaLearningTask(
            task_id="weight_test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        await meta_engine.learn_from_few_shots(task, strategy=LearningStrategy.RAPID_LEARNING)

        # 权重可能已更新（取决于实现）
        assert isinstance(meta_engine.strategy_weights, dict)

    @pytest.mark.asyncio
    async def test_task_complexity_calculation(self, meta_engine):
        """测试任务复杂度计算"""
        # 简单任务
        simple_task = MetaLearningTask(
            task_id="simple",
            task_type="simple",
            support_set=[{"input": "test"}],
            query_set=[],
        )

        simple_complexity = meta_engine._calculate_task_complexity(simple_task)
        assert 0.0 <= simple_complexity <= 1.0

        # 复杂任务
        complex_task = MetaLearningTask(
            task_id="complex",
            task_type="complex",
            support_set=[
                {"input": f"test_{i}", "feature1": i, "feature2": i * 2}
                for i in range(100)
            ],
            query_set=[],
        )

        complex_complexity = meta_engine._calculate_task_complexity(complex_task)
        assert 0.0 <= complex_complexity <= 1.0
        # 复杂任务应该有更高的复杂度
        assert complex_complexity > simple_complexity

    @pytest.mark.asyncio
    async def test_improvements_tracking(self, meta_engine):
        """测试改进跟踪"""
        task = MetaLearningTask(
            task_id="improve_test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        # 执行多次学习
        for _ in range(5):
            await meta_engine.learn_from_few_shots(task)

        # 检查改进记录
        assert len(meta_engine.stats["improvements"]) >= 5

        for improvement in meta_engine.stats["improvements"]:
            assert "strategy" in improvement
            assert "accuracy" in improvement
            assert "timestamp" in improvement

    @pytest.mark.asyncio
    async def test_best_strategies_tracking(self, meta_engine):
        """测试最佳策略跟踪"""
        task = MetaLearningTask(
            task_id="best_test",
            task_type="test",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        # 执行多次高准确率学习
        for _ in range(10):
            result = await meta_engine.learn_from_few_shots(task)
            # 如果结果准确率高，应该被记录为最佳策略
            if result.accuracy > 0.85:
                assert result.strategy_used in meta_engine.stats["best_strategies"]


@pytest.mark.integration
class TestMetaLearningTask:
    """元学习任务数据类测试"""

    def test_create_task(self):
        """测试创建任务"""
        task = MetaLearningTask(
            task_id="task_001",
            task_type="classification",
            support_set=[{"input": "test"}],
            query_set=[{"input": "query"}],
        )

        assert task.task_id == "task_001"
        assert task.task_type == "classification"
        assert len(task.support_set) == 1
        assert len(task.query_set) == 1

    def test_task_with_metadata(self):
        """测试带元数据的任务"""
        metadata = {"domain": "patent", "priority": "high"}
        task = MetaLearningTask(
            task_id="task_002",
            task_type="test",
            support_set=[],
            query_set=[],
            metadata=metadata,
        )

        assert task.metadata == metadata


@pytest.mark.integration
class TestLearningResult:
    """学习结果数据类测试"""

    def test_create_result(self):
        """测试创建学习结果"""
        result = LearningResult(
            task_id="task_001",
            strategy_used=LearningStrategy.RAPID_LEARNING,
            accuracy=0.85,
            efficiency=0.90,
            retention=0.75,
            transferability=0.80,
            learning_time=1.5,
            timestamp=datetime.now(),
        )

        assert result.task_id == "task_001"
        assert result.strategy_used == LearningStrategy.RAPID_LEARNING
        assert result.accuracy == 0.85
        assert result.learning_time == 1.5


@pytest.mark.integration
class TestStrategyPerformance:
    """策略性能数据类测试"""

    def test_create_performance(self):
        """测试创建性能记录"""
        perf = StrategyPerformance(
            strategy=LearningStrategy.RAPID_LEARNING,
            accuracy=0.85,
            efficiency=0.90,
            retention=0.75,
            transferability=0.80,
            last_updated=datetime.now(),
            usage_count=10,
        )

        assert perf.strategy == LearningStrategy.RAPID_LEARNING
        assert perf.usage_count == 10


@pytest.mark.integration
class TestLearningStrategy:
    """学习策略枚举测试"""

    def test_all_strategies(self):
        """测试所有学习策略"""
        strategies = [
            LearningStrategy.RAPID_LEARNING,
            LearningStrategy.DEEP_LEARNING,
            LearningStrategy.SPACED_REPETITION,
            LearningStrategy.ACTIVE_RECALL,
            LearningStrategy.INTERLEAVING,
        ]

        assert len(strategies) == 5

        for strategy in strategies:
            assert isinstance(strategy.value, str)


@pytest.mark.integration
class TestEnhancedMetaLearningStress:
    """增强元学习压力测试"""

    @pytest.mark.asyncio
    async def test_high_volume_meta_learning(self):
        """测试大量元学习任务"""
        engine = EnhancedMetaLearningEngine(agent_id="stress_test")

        # 创建100个任务
        tasks = []
        for i in range(100):
            task = MetaLearningTask(
                task_id=f"stress_task_{i}",
                task_type="test",
                support_set=[{"input": f"sample_{i}_{j}"} for j in range(10)],
                query_set=[{"input": "query"}],
            )
            tasks.append(task)

        # 并发执行
        start_time = __import__("time").perf_counter()

        learning_tasks = [engine.learn_from_few_shots(task) for task in tasks]
        results = await asyncio.gather(*learning_tasks)

        elapsed = __import__("time").perf_counter() - start_time

        print(f"\n高容量元学习测试 (100任务):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {100/elapsed:.0f} tasks/sec")

        assert len(results) == 100
        assert engine.stats["total_tasks"] == 100

    @pytest.mark.asyncio
    async def test_hyperparameter_optimization_stress(self):
        """测试超参数优化压力"""
        engine = EnhancedMetaLearningEngine(agent_id="opt_stress")

        # 创建20个验证任务
        validation_tasks = [
            MetaLearningTask(
                task_id=f"val_{i}",
                task_type="validation",
                support_set=[{"input": f"sample_{j}"} for j in range(5)],
                query_set=[{"input": "query"}],
            )
            for i in range(20)
        ]

        import time

        start_time = time.perf_counter()

        # 优化超参数
        optimized_params = await engine.optimize_hyperparameters(
            validation_tasks, max_iterations=20
        )

        elapsed = time.perf_counter() - start_time

        print(f"\n超参数优化压测 (20任务, 20迭代):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  优化后参数: {optimized_params}")

        assert "learning_rate" in optimized_params
        assert elapsed < 30.0  # 应该在30秒内完成

    @pytest.mark.asyncio
    async def test_knowledge_transfer_batch(self):
        """测试批量知识迁移"""
        engine = EnhancedMetaLearningEngine(agent_id="transfer_stress")

        # 批量迁移
        transfers = []
        for i in range(10):
            transfer_samples = [
                {"domain": f"source_{i}", "content": f"content_{j}"}
                for j in range(5)
            ]

            transfer = engine.transfer_knowledge(
                source_domain=f"domain_{i}",
                target_domain=f"target_{i}",
                transfer_samples=transfer_samples,
            )
            transfers.append(transfer)

        results = await asyncio.gather(*transfers)

        print(f"\n批量知识迁移测试 (10次迁移):")
        for i, result in enumerate(results):
            print(
                f"  迁移{i}: {result['source_domain']} -> {result['target_domain']}, "
                f"分数={result['transfer_score']:.3f}"
            )

        assert len(results) == 10
        for result in results:
            assert 0.0 <= result["transfer_score"] <= 1.0
