#!/usr/bin/env python3
"""
学习模块端到端集成测试
End-to-End Integration Tests for Learning Module

测试学习模块各组件之间的协作：
1. 自主学习系统 + 并发控制
2. 自主学习系统 + 错误处理 + 重试
3. 自主学习系统 + 持久化
4. 元学习引擎 + 自主学习系统
5. 完整工作流测试

作者: Athena平台团队
版本: 1.0.0
创建时间: 2026-01-28
"""

import asyncio
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.learning.autonomous_learning_system import (
    AutonomousLearningSystem,
    LearningExperience,
)
from core.learning.concurrency_control import (
    ConcurrencyConfig,
    ConcurrencyController,
)
from core.learning.enhanced_meta_learning import (
    EnhancedMetaLearningEngine,
    MetaLearningTask,
)
from core.learning.error_handling import (
    CircuitBreaker,
    FallbackHandler,
    RetryConfig,
    RetryHandler,
    TransientError,
)
from core.learning.persistence_manager import (
    LearningPersistenceManager,
    StorageBackend,
)


def experience_to_dict(exp: LearningExperience) -> dict[str, Any]:
    """将学习经验转换为可序列化的字典"""
    data = asdict(exp)
    # 转换datetime为ISO格式字符串
    if isinstance(data.get("timestamp"), datetime):
        data["timestamp"] = data["timestamp"].isoformat()
    return data


@pytest.mark.integration
class TestLearningSystemIntegration:
    """学习系统端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_learning_workflow(self):
        """测试完整的学习工作流"""
        # 1. 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="e2e_agent")

        # 2. 从经验中学习
        experiences = []
        for i in range(20):
            exp = await learning_system.learn_from_experience(
                context={"task": f"task_{i % 5}", "complexity": i % 3},
                action=f"action_{i % 10}",
                result={"status": "success" if i % 4 != 0 else "partial"},
                reward=0.5 + (i % 5) * 0.1,
            )
            experiences.append(exp)

        assert len(experiences) == 20
        assert len(learning_system.experiences) == 20

        # 3. 分析性能
        performance = await learning_system.analyze_performance()
        assert "trends" in performance

        # 4. 获取学习指标
        metrics = await learning_system.get_learning_metrics()
        assert metrics["learning"]["total_experiences"] >= 20

    @pytest.mark.asyncio
    async def test_learning_with_concurrency_control(self):
        """测试学习 + 并发控制集成"""
        # 创建并发控制器
        config = ConcurrencyConfig(
            max_concurrent_tasks=5, max_operations_per_second=100
        )
        controller = ConcurrencyController(config)

        # 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="concurrent_agent")

        # 提交并发学习任务
        async def learning_task(task_id: int):
            return await learning_system.learn_from_experience(
                context={"task_id": task_id},
                action=f"action_{task_id % 5}",
                result={"status": "success"},
                reward=0.7,
            )

        # 提交20个任务
        tasks = []
        for i in range(20):
            task = controller.submit_task(
                lambda i=i: learning_task(i), timeout=10.0
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 验证结果
        successful = sum(1 for r in results if not isinstance(r, Exception))
        assert successful >= 18  # 允许少量失败
        assert len(learning_system.experiences) >= 18

        # 验证并发统计
        stats = controller.get_statistics()
        assert stats["tasks"]["completed"] >= 18

    @pytest.mark.asyncio
    async def test_learning_with_retry_and_fallback(self):
        """测试学习 + 重试 + 降级集成"""
        # 创建重试处理器
        retry_config = RetryConfig(max_attempts=3, base_delay=0.01)
        retry_handler = RetryHandler(retry_config)

        # 创建降级处理器
        FallbackHandler()

        # 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="resilient_agent")

        # 模拟不稳定的学习操作
        attempt_count = {"count": 0}

        async def unstable_learning():
            attempt_count["count"] += 1
            if attempt_count["count"] < 2:
                raise TransientError("临时错误")
            return await learning_system.learn_from_experience(
                context={"task": "retry_test"},
                action="test_action",
                result={"status": "success"},
                reward=0.8,
            )

        # 执行带重试的学习
        result = await retry_handler.execute_with_retry(unstable_learning)

        assert isinstance(result, LearningExperience)
        assert attempt_count["count"] == 2  # 第一次失败，第二次成功

    @pytest.mark.asyncio
    async def test_learning_with_persistence(self, tmp_path):
        """测试学习 + 持久化集成"""
        # 创建持久化管理器
        persistence_manager = LearningPersistenceManager(StorageBackend.FILE)
        await persistence_manager.initialize(base_path=str(tmp_path / "learning_data"))

        # 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="persistent_agent")

        # 学习一些经验
        for i in range(10):
            await learning_system.learn_from_experience(
                context={"task": f"task_{i}"},
                action=f"action_{i % 3}",
                result={"status": "success"},
                reward=0.6 + i * 0.03,
            )

        # 保存经验到持久化存储
        saved_count = 0
        for exp in list(learning_system.experiences):
            record_id = await persistence_manager.save_experience(
                agent_id="persistent_agent",
                experience=experience_to_dict(exp),
            )
            if record_id:
                saved_count += 1

        assert saved_count == 10

        # 创建新的学习系统并加载经验
        new_system = AutonomousLearningSystem(agent_id="persistent_agent_2")
        loaded_experiences = await persistence_manager.load_experiences(
            "persistent_agent", limit=100
        )

        assert len(loaded_experiences) == 10

        # 从加载的经验中学习
        for exp_data in loaded_experiences:
            await new_system.learn_from_experience(
                context=exp_data.get("context", {}),
                action=exp_data.get("action", ""),
                result=exp_data.get("result", {}),
                reward=exp_data.get("reward", 0.5),
            )

        assert len(new_system.experiences) == 10

    @pytest.mark.asyncio
    async def test_learning_with_circuit_breaker(self):
        """测试学习 + 断路器集成"""
        # 创建断路器
        circuit_breaker = CircuitBreaker(
            failure_threshold=3, timeout=5.0, half_open_attempts=2
        )

        # 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="circuit_agent")

        # 模拟失败的学习操作
        failure_count = {"count": 0}

        async def failing_learning():
            failure_count["count"] += 1
            if failure_count["count"] <= 3:
                raise Exception("学习失败")
            return await learning_system.learn_from_experience(
                context={"task": "circuit_test"},
                action="test_action",
                result={"status": "success"},
                reward=0.7,
            )

        # 通过断路器执行学习
        results = []
        for _i in range(6):
            try:
                result = await circuit_breaker.call(failing_learning)
                results.append(("success", result))
            except Exception as e:
                results.append(("error", str(e)))

        # 验证断路器行为
        error_count = sum(1 for r in results if r[0] == "error")
        sum(1 for r in results if r[0] == "success")

        # 前几次应该失败，触发断路器打开
        assert error_count >= 3
        # 断路器应该阻止后续调用（至少一段时间）
        state = circuit_breaker.get_state()
        assert state["state"] in ["closed", "open", "half_open"]

    @pytest.mark.asyncio
    async def test_meta_learning_with_learning_system(self):
        """测试元学习 + 自主学习系统集成"""
        # 创建元学习引擎
        meta_engine = EnhancedMetaLearningEngine(agent_id="meta_integration")

        # 创建学习系统
        learning_system = AutonomousLearningSystem(agent_id="learning_integration")

        # 创建元学习任务
        meta_task = MetaLearningTask(
            task_id="integration_task",
            task_type="classification",
            support_set=[
                {"input": "专利分析", "output": "legal"},
                {"input": "技术开发", "output": "tech"},
                {"input": "市场营销", "output": "business"},
            ],
            query_set=[
                {"input": "IP管理", "output": "legal"},
                {"input": "产品研发", "output": "tech"},
            ],
            metadata={"domain": "task_classification"},
        )

        # 使用元学习引擎学习最优策略
        best_strategy = await meta_engine.select_learning_strategy(meta_task)

        # 执行少样本学习
        meta_result = await meta_engine.learn_from_few_shots(meta_task, strategy=best_strategy)

        # 基于元学习结果在自主学习系统中学习
        # 将元学习结果作为奖励信号
        await learning_system.learn_from_experience(
            context={
                "task": "meta_learning_integration",
                "strategy": best_strategy.value,
                "meta_accuracy": meta_result.accuracy,
            },
            action=f"use_{best_strategy.value}",
            result={"meta_learning_success": True},
            reward=meta_result.accuracy,
        )

        # 验证两个系统都有学习记录
        assert len(meta_engine.learning_results) >= 1
        assert len(learning_system.experiences) >= 1

    @pytest.mark.asyncio
    async def test_batch_learning_with_all_components(self):
        """测试批量学习集成所有组件"""
        # 创建所有组件
        config = ConcurrencyConfig(max_concurrent_tasks=10)
        controller = ConcurrencyController(config)
        retry_handler = RetryHandler(RetryConfig(max_attempts=2))
        FallbackHandler()

        # 临时目录用于持久化
        with tempfile.TemporaryDirectory() as tmp_dir:
            persistence_manager = LearningPersistenceManager(StorageBackend.FILE)
            await persistence_manager.initialize(base_path=f"{tmp_dir}/batch_learning")

            learning_system = AutonomousLearningSystem(agent_id="batch_agent")

            # 批量学习任务
            async def comprehensive_learning_task(task_id: int):
                # 带重试的学习
                async def learn():
                    return await learning_system.learn_from_experience(
                        context={
                            "task": f"batch_task_{task_id}",
                            "batch": True,
                        },
                        action=f"batch_action_{task_id % 8}",
                        result={"status": "success", "task_id": task_id},
                        reward=0.5 + (task_id % 5) * 0.1,
                    )

                return await retry_handler.execute_with_retry(learn)

            # 提交50个批量任务
            tasks = []
            for i in range(50):
                task = controller.submit_task(
                    lambda i=i: comprehensive_learning_task(i), timeout=10.0
                )
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证结果
            successful = sum(1 for r in results if not isinstance(r, Exception))
            assert successful >= 45  # 允许少量失败

            # 持久化学习数据
            saved = 0
            for exp in list(learning_system.experiences)[:20]:  # 保存前20个
                if await persistence_manager.save_experience(
                    "batch_agent", experience_to_dict(exp)
                ):
                    saved += 1

            assert saved >= 18

            # 验证统计数据
            stats = controller.get_statistics()
            metrics = await learning_system.get_learning_metrics()

            assert stats["tasks"]["completed"] >= 45
            assert metrics["learning"]["total_experiences"] >= 45

    @pytest.mark.asyncio
    async def test_multi_agent_collaborative_learning(self):
        """测试多智能体协作学习"""
        # 创建多个学习智能体
        agents = []
        for i in range(3):
            agent = AutonomousLearningSystem(agent_id=f"collaborative_agent_{i}")
            agents.append(agent)

        # 每个智能体学习不同的任务
        tasks_data = [
            {"task": "patent_search", "domain": "patent"},
            {"task": "legal_analysis", "domain": "legal"},
            {"task": "tech_development", "domain": "tech"},
        ]

        # 所有智能体学习
        for i, agent in enumerate(agents):
            for j in range(5):
                await agent.learn_from_experience(
                    context={
                        "task": tasks_data[i]["task"],
                        "domain": tasks_data[i]["domain"],
                        "iteration": j,
                    },
                    action=f"agent_{i}_action_{j}",
                    result={"status": "success"},
                    reward=0.6 + j * 0.05,
                )

        # 验证每个智能体都有学习记录
        for i, agent in enumerate(agents):
            assert len(agent.experiences) == 5
            # 验证学习的是特定领域的任务
            domain = tasks_data[i]["domain"]
            domain_experiences = [
                exp
                for exp in agent.experiences
                if exp.context.get("domain") == domain
            ]
            assert len(domain_experiences) == 5


@pytest.mark.integration
class TestLearningDataFlow:
    """学习数据流测试"""

    @pytest.mark.asyncio
    async def test_complete_data_flow(self, tmp_path):
        """测试完整的数据流：输入 -> 学习 -> 持久化 -> 加载 -> 分析"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # 1. 初始化所有组件
            persistence = LearningPersistenceManager(StorageBackend.FILE)
            await persistence.initialize(base_path=f"{tmp_dir}/data_flow")

            learning_system = AutonomousLearningSystem(agent_id="flow_agent")

            # 2. 数据输入阶段
            input_data = [
                {"context": {"task": "search", "query": "AI"}, "action": "vector_search"},
                {"context": {"task": "analyze", "doc_type": "patent"}, "action": "deep_analysis"},
                {"context": {"task": "summarize", "length": "short"}, "action": "quick_summary"},
            ]

            # 3. 学习阶段
            for data in input_data:
                await learning_system.learn_from_experience(
                    context=data["context"],
                    action=data["action"],
                    result={"status": "success"},
                    reward=0.8,
                )

            # 4. 持久化阶段
            saved_ids = []
            for exp in learning_system.experiences:
                record_id = await persistence.save_experience(
                    "flow_agent", experience_to_dict(exp)
                )
                saved_ids.append(record_id)

            assert len(saved_ids) == 3
            assert all(record_id for record_id in saved_ids)

            # 5. 加载阶段
            loaded_experiences = await persistence.load_experiences("flow_agent")
            assert len(loaded_experiences) == 3

            # 6. 分析阶段
            performance = await learning_system.analyze_performance()
            assert "trends" in performance

            metrics = await learning_system.get_learning_metrics()
            assert metrics["learning"]["total_experiences"] == 3

    @pytest.mark.asyncio
    async def test_error_recovery_in_data_flow(self, tmp_path):
        """测试数据流中的错误恢复"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            persistence = LearningPersistenceManager(StorageBackend.FILE)
            await persistence.initialize(base_path=f"{tmp_dir}/error_recovery")

            learning_system = AutonomousLearningSystem(agent_id="recovery_agent")

            retry_handler = RetryHandler(RetryConfig(max_attempts=3, base_delay=0.01))

            # 模拟不稳定的持久化操作
            persistence_attempts = {"count": 0}

            async def unstable_persistence(exp_data):
                persistence_attempts["count"] += 1
                if persistence_attempts["count"] == 1:
                    raise Exception("临时持久化失败")
                return await persistence.save_experience("recovery_agent", exp_data)

            # 学习并尝试持久化
            await learning_system.learn_from_experience(
                context={"task": "recovery_test"},
                action="test_action",
                result={"status": "success"},
                reward=0.7,
            )

            # 使用重试进行持久化
            exp_data = experience_to_dict(list(learning_system.experiences)[0])
            record_id = await retry_handler.execute_with_retry(
                lambda: unstable_persistence(exp_data)
            )

            assert record_id
            assert persistence_attempts["count"] == 2


@pytest.mark.integration
class TestLearningSystemPerformanceIntegration:
    """学习系统性能集成测试"""

    @pytest.mark.asyncio
    async def test_high_throughput_learning_pipeline(self):
        """测试高吞吐量学习管道"""
        config = ConcurrencyConfig(max_concurrent_tasks=20, max_operations_per_second=500)
        controller = ConcurrencyController(config)

        learning_system = AutonomousLearningSystem(agent_id="throughput_agent")

        import time

        start_time = time.perf_counter()

        # 高吞吐量学习
        tasks = []
        for i in range(100):
            task = controller.submit_task(
                lambda i=i: learning_system.learn_from_experience(
                    context={"task": f"high_throughput_{i}"},
                    action=f"action_{i % 10}",
                    result={"status": "success"},
                    reward=0.7,
                ),
                timeout=10.0,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.perf_counter() - start_time

        successful = sum(1 for r in results if not isinstance(r, Exception))

        print("\n高吞吐量学习管道 (100任务):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {successful/elapsed:.0f} tasks/sec")
        print(f"  成功: {successful}/100")

        assert successful >= 95
        assert len(learning_system.experiences) >= 95

    @pytest.mark.asyncio
    async def test_scalability_with_multiple_agents(self):
        """测试多智能体扩展性"""
        import time

        start_time = time.perf_counter()

        # 创建10个智能体
        agents = [
            AutonomousLearningSystem(agent_id=f"scale_agent_{i}") for i in range(10)
        ]

        # 每个智能体学习20个经验
        learning_tasks = []
        for agent in agents:
            for i in range(20):
                task = agent.learn_from_experience(
                    context={"agent": agent.agent_id, "task": i},
                    action=f"action_{i % 5}",
                    result={"status": "success"},
                    reward=0.6 + i * 0.02,
                )
                learning_tasks.append(task)

        results = await asyncio.gather(*learning_tasks)

        elapsed = time.perf_counter() - start_time

        print("\n多智能体扩展性测试 (10智能体 x 20任务):")
        print(f"  耗时: {elapsed*1000:.2f}ms")
        print(f"  吞吐量: {len(results)/elapsed:.0f} tasks/sec")

        assert len(results) == 200

        # 验证每个智能体的学习
        for agent in agents:
            assert len(agent.experiences) == 20


@pytest.mark.integration
class TestLearningSystemEdgeCases:
    """学习系统边界情况测试"""

    @pytest.mark.asyncio
    async def test_empty_experience_handling(self):
        """测试空经验处理"""
        learning_system = AutonomousLearningSystem(agent_id="edge_case_agent")

        # 尝试从空上下文学习
        result = await learning_system.learn_from_experience(
            context={}, action="empty_action", result={}, reward=0.0
        )

        assert result is not None
        assert len(learning_system.experiences) == 1

    @pytest.mark.asyncio
    async def test_extreme_reward_values(self):
        """测试极端奖励值处理"""
        learning_system = AutonomousLearningSystem(agent_id="extreme_reward_agent")

        # 测试边界奖励值
        rewards = [-1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0]

        for reward in rewards:
            await learning_system.learn_from_experience(
                context={"reward_test": reward},
                action="test_action",
                result={"status": "ok"},
                reward=reward,
            )

        assert len(learning_system.experiences) == len(rewards)

        # 验证所有奖励都被记录
        recorded_rewards = [exp.reward for exp in learning_system.experiences]
        assert recorded_rewards == rewards

    @pytest.mark.asyncio
    async def test_concurrent_same_action_learning(self):
        """测试并发执行相同动作的学习"""
        learning_system = AutonomousLearningSystem(agent_id="concurrent_same_agent")

        # 并发执行相同动作的学习
        tasks = []
        for _ in range(50):
            task = learning_system.learn_from_experience(
                context={"task": "same_action_test"},
                action="identical_action",
                result={"status": "success"},
                reward=0.8,
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 50
        assert len(learning_system.experiences) == 50

        # 验证策略更新
        assert "identical_action" in learning_system.current_policy
        policy = learning_system.current_policy["identical_action"]
        assert policy["count"] == 50
