#!/usr/bin/env python3
"""
Execution模块__init__.py单元测试

测试执行模块的统一导出接口和核心类

测试范围:
- 模块导入验证
- ExecutionEngine基类
- 类型定义（PerformanceMetrics, TaskResult, TaskStatus）
"""

import pytest


# 测试所有主要导入
def test_module_imports():
    """测试模块主要导入"""
    from core.execution import (
        ExecutionEngine,
        PerformanceMetrics,
        TaskResult,
        TaskStatus,
    )

    # 验证导入成功
    assert ExecutionEngine is not None
    assert PerformanceMetrics is not None
    assert TaskResult is not None
    assert TaskStatus is not None


class TestExecutionEngine:
    """测试ExecutionEngine基类"""

    def test_basic_initialization(self):
        """测试基本初始化"""
        from core.execution import ExecutionEngine

        engine = ExecutionEngine("test_agent")

        assert engine.agent_id == "test_agent"
        assert engine.config == {}
        assert engine.initialized is False

    def test_initialization_with_config(self):
        """测试使用配置初始化"""
        from core.execution import ExecutionEngine

        config = {
            "max_concurrent_tasks": 10,
            "timeout": 30,
            "enable_monitoring": True
        }

        engine = ExecutionEngine("test_agent", config)

        assert engine.agent_id == "test_agent"
        assert engine.config == config
        assert engine.initialized is False

    @pytest.mark.asyncio
    async def test_initialize(self):
        """测试初始化方法"""
        from core.execution import ExecutionEngine

        engine = ExecutionEngine("test_agent")
        await engine.initialize()

        assert engine.initialized is True


class TestPerformanceMetrics:
    """测试PerformanceMetrics类"""

    def test_metrics_creation(self):
        """测试指标创建"""
        from core.execution import PerformanceMetrics

        metrics = PerformanceMetrics(
            execution_time_ms=1.5,
            memory_usage_mb=1024,
            cpu_usage_percent=0.8
        )

        assert metrics.execution_time_ms == 1.5
        assert metrics.memory_usage_mb == 1024
        assert metrics.cpu_usage_percent == 0.8

    def test_metrics_default_values(self):
        """测试默认值"""
        from core.execution import PerformanceMetrics

        metrics = PerformanceMetrics()

        # 验证默认值存在（具体值取决于dataclass定义）
        assert metrics is not None


class TestTaskResult:
    """测试TaskResult类"""

    def test_result_creation(self):
        """测试结果创建"""
        from core.execution import TaskResult

        result = TaskResult(
            success=True,
            data="任务完成",
            metadata={"task_id": "task_001"}
        )

        assert result.success is True
        assert result.data == "任务完成"
        assert result.metadata["task_id"] == "task_001"

    def test_result_with_error(self):
        """测试带错误的结果"""
        from core.execution import TaskResult

        result = TaskResult(
            success=False,
            error="任务失败",
            metadata={"task_id": "task_002"}
        )

        assert result.success is False
        assert result.error == "任务失败"


class TestTaskStatus:
    """测试TaskStatus枚举或类"""

    def test_status_values(self):
        """测试状态值"""
        from core.execution import TaskStatus

        # TaskStatus可能是枚举或常量类
        # 验证常见状态存在
        assert hasattr(TaskStatus, 'PENDING') or hasattr(TaskStatus, 'pending')
        assert hasattr(TaskStatus, 'RUNNING') or hasattr(TaskStatus, 'running')
        assert hasattr(TaskStatus, 'COMPLETED') or hasattr(TaskStatus, 'completed')
        assert hasattr(TaskStatus, 'FAILED') or hasattr(TaskStatus, 'failed')


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_execution_flow(self):
        """测试完整执行流程"""
        from core.execution import ExecutionEngine, TaskResult

        # 创建引擎
        engine = ExecutionEngine("test_agent")

        # 初始化
        await engine.initialize()

        # 创建任务结果
        result = TaskResult(
            success=True,
            data="成功",
            metadata={"task_id": "test_task"}
        )

        # 验证
        assert engine.initialized is True
        assert result.success is True

    def test_metrics_integration(self):
        """测试指标集成"""
        from core.execution import PerformanceMetrics, TaskResult

        metrics = PerformanceMetrics(
            execution_time_ms=2.0,
            memory_usage_mb=2048,
            cpu_usage_percent=0.6
        )

        result = TaskResult(
            success=True,
            data="完成",
            metadata={"metrics": metrics}
        )

        # 验证metrics在metadata中
        assert result.success is True
        assert "metrics" in result.metadata


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_config(self):
        """测试空配置"""
        from core.execution import ExecutionEngine

        engine = ExecutionEngine("test_agent", {})

        assert engine.config == {}

    def test_none_config(self):
        """测试None配置"""
        from core.execution import ExecutionEngine

        engine = ExecutionEngine("test_agent", None)

        assert engine.config == {}

    def test_long_agent_id(self):
        """测试超长agent_id"""
        from core.execution import ExecutionEngine

        long_id = "a" * 1000

        engine = ExecutionEngine(long_id)

        assert engine.agent_id == long_id

    def test_special_characters_in_agent_id(self):
        """测试特殊字符agent_id"""
        from core.execution import ExecutionEngine

        special_id = "测试_agent_123!@#$%"

        engine = ExecutionEngine(special_id)

        assert engine.agent_id == special_id


class TestPerformance:
    """测试性能"""

    @pytest.mark.asyncio
    async def test_initialization_speed(self):
        """测试初始化速度"""
        import time

        from core.execution import ExecutionEngine

        start = time.time()
        engine = ExecutionEngine("test_agent")
        await engine.initialize()
        elapsed = time.time() - start

        # 初始化应该很快 (< 0.1秒)
        assert elapsed < 0.1

    def test_metrics_creation_speed(self):
        """测试指标创建速度"""
        import time

        from core.execution import PerformanceMetrics

        start = time.time()
        for _ in range(100):
            PerformanceMetrics(
                execution_time_ms=1.0,
                memory_usage_mb=1024,
                cpu_usage_percent=0.5
            )
        elapsed = time.time() - start

        # 创建100个指标应该很快 (< 0.1秒)
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
