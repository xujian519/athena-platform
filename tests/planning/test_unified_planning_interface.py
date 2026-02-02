#!/usr/bin/env python3
"""
统一规划接口测试
Unified Planning Interface Tests

测试核心规划接口的功能:
- UnifiedPlannerRegistry
- PlannerIntegrationBridge
- PlannerCoordinator
- PlanningRequest/PlanningResult

作者: 小诺·双鱼座
创建时间: 2025-12-18
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.planning.unified_planning_interface import (
    BasePlanner,
    PlannerCoordinator,
    PlannerIntegrationBridge,
    PlannerType,
    PlanningRequest,
    PlanningResult,
    Priority,
    TaskStatus,
    UnifiedPlannerRegistry,
    get_planner_coordinator,
    get_planner_registry,
)


# ========== 测试规划器实现 ==========

class MockPlanner(BasePlanner):
    """模拟规划器用于测试"""

    def __init__(self, name: str = "测试规划器"):
        super().__init__(name, PlannerType.TASK_PLANNER)
        self.plans_created = []
        self.plans_executed = []

    async def create_plan(self, request: PlanningRequest) -> PlanningResult:
        """创建规划"""
        plan_id = f"plan_{len(self.plans_created) + 1}"
        self.plans_created.append(request)

        return PlanningResult(
            request_id=request.id,
            planner_type=self.planner_type,
            success=True,
            plan_id=plan_id,
            steps=[{"step": 1, "action": "测试步骤"}],
            estimated_duration=timedelta(minutes=30),
            confidence_score=0.85,
            status=TaskStatus.PENDING,
        )

    async def execute_plan(self, plan_id: str) -> bool:
        """执行规划"""
        self.plans_executed.append(plan_id)
        return True

    async def get_plan_status(self, plan_id: str) -> dict:
        """获取规划状态"""
        return {
            "plan_id": plan_id,
            "status": "completed" if plan_id in self.plans_executed else "pending",
        }

    async def update_plan(self, plan_id: str, updates: dict) -> bool:
        """更新规划"""
        return True


# ========== UnifiedPlannerRegistry 测试 ==========

class TestUnifiedPlannerRegistry:
    """统一规划器注册中心测试"""

    @pytest.fixture
    def registry(self):
        """创建注册中心实例"""
        return UnifiedPlannerRegistry()

    @pytest.fixture
    def mock_planner(self):
        """创建模拟规划器"""
        return MockPlanner()

    def test_register_planner(self, registry, mock_planner):
        """测试注册规划器"""
        registry.register_planner(mock_planner)

        assert mock_planner.planner_type in registry.planners
        assert registry.planners[mock_planner.planner_type] == mock_planner

    def test_get_planner(self, registry, mock_planner):
        """测试获取规划器"""
        registry.register_planner(mock_planner)

        retrieved = registry.get_planner(mock_planner.planner_type)

        assert retrieved is not None
        assert retrieved == mock_planner

    def test_get_nonexistent_planner(self, registry):
        """测试获取不存在的规划器"""
        retrieved = registry.get_planner(PlannerType.GOAL_MANAGER)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_submit_request_success(self, registry, mock_planner):
        """测试成功提交请求"""
        registry.register_planner(mock_planner)

        request = PlanningRequest(
            title="测试请求",
            description="这是一个测试请求",
            priority=Priority.HIGH,
        )

        result = await registry.submit_request(request)

        assert result.success is True
        assert result.plan_id is not None
        assert result.confidence_score == 0.85

    @pytest.mark.asyncio
    async def test_submit_request_no_planner(self, registry):
        """测试提交请求到未注册的规划器"""
        request = PlanningRequest(
            type=PlannerType.GOAL_MANAGER,
            title="测试请求",
            description="这是一个测试请求",
        )

        result = await registry.submit_request(request)

        assert result.success is False
        assert "未找到类型" in result.feedback

    @pytest.mark.asyncio
    async def test_get_result(self, registry, mock_planner):
        """测试获取结果"""
        registry.register_planner(mock_planner)

        request = PlanningRequest(title="测试请求")
        result = await registry.submit_request(request)

        cached_result = await registry.get_result(request.id)

        assert cached_result is not None
        assert cached_result.request_id == request.id

    def test_get_status(self, registry, mock_planner):
        """测试获取注册中心状态"""
        registry.register_planner(mock_planner)

        status = registry.get_status()

        assert status["registered_planners"] == 1
        assert PlannerType.TASK_PLANNER.value in status["planner_types"]
        assert status["cached_results"] == 0


# ========== PlannerIntegrationBridge 测试 ==========

class TestPlannerIntegrationBridge:
    """规划器集成桥接测试"""

    @pytest.fixture
    def registry(self):
        """创建注册中心实例"""
        return UnifiedPlannerRegistry()

    @pytest.fixture
    def bridge(self, registry):
        """创建集成桥接实例"""
        return PlannerIntegrationBridge(registry)

    @pytest.fixture
    def mock_planner(self, registry):
        """注册模拟规划器"""
        planner = MockPlanner()
        registry.register_planner(planner)
        return planner

    def test_register_integration_adapter(self, bridge):
        """测试注册集成适配器"""
        def adapter_func(source_data):
            return PlanningRequest(title=f"从{source_data.get('source', '未知')}转换")

        bridge.register_integration_adapter(
            "external_system", PlannerType.TASK_PLANNER, adapter_func
        )

        key = "external_system -> task_planner"
        assert key in bridge.integration_adapters

    @pytest.mark.asyncio
    async def test_integrate_request_success(self, bridge, mock_planner):
        """测试成功集成请求"""

        def adapter_func(source_data):
            return PlanningRequest(
                title=source_data.get("title", "默认标题"),
                description=source_data.get("description", ""),
            )

        bridge.register_integration_adapter(
            "test_source", PlannerType.TASK_PLANNER, adapter_func
        )

        source_data = {
            "title": "外部系统请求",
            "description": "来自外部系统的请求",
        }

        result = await bridge.integrate_request(
            source_data, "test_source", PlannerType.TASK_PLANNER
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_integrate_request_no_adapter(self, bridge):
        """测试未注册适配器的集成请求"""

        source_data = {"title": "测试请求"}

        result = await bridge.integrate_request(
            source_data, "unknown_source", PlannerType.TASK_PLANNER
        )

        assert result.success is False
        assert "未找到集成适配器" in result.feedback


# ========== PlannerCoordinator 测试 ==========

class TestPlannerCoordinator:
    """规划器协调器测试"""

    @pytest.fixture
    def registry(self):
        """创建注册中心并注册多个规划器"""
        registry = UnifiedPlannerRegistry()
        registry.register_planner(MockPlanner("规划器1"))
        registry.register_planner(MockPlanner("规划器2"))
        registry.register_planner(MockPlanner("规划器3"))
        return registry

    @pytest.fixture
    def coordinator(self, registry):
        """创建协调器实例"""
        return PlannerCoordinator(registry)

    @pytest.mark.asyncio
    async def test_coordinate_multi_planner_request(self, coordinator):
        """测试协调多规划器请求"""
        requests = [
            PlanningRequest(
                title=f"请求{i+1}",
                priority=Priority.MEDIUM,
            )
            for i in range(3)
        ]

        results = await coordinator.coordinate_multi_planner_request(requests)

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_coordinate_with_priority_ordering(self, coordinator):
        """测试优先级排序"""
        requests = [
            PlanningRequest(title="低优先级", priority=Priority.LOW),
            PlanningRequest(title="紧急", priority=Priority.URGENT),
            PlanningRequest(title="中等", priority=Priority.MEDIUM),
        ]

        results = await coordinator.coordinate_multi_planner_request(requests)

        assert len(results) == 3
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_create_dependency_chain(self, coordinator):
        """测试创建依赖链"""
        requests = [
            PlanningRequest(title=f"任务{i+1}")
            for i in range(3)
        ]

        dependencies = {
            requests[1].id: [requests[0].id],  # 任务2依赖任务1
            requests[2].id: [requests[1].id],  # 任务3依赖任务2
        }

        results = await coordinator.create_dependency_chain(requests, dependencies)

        assert len(results) == 3
        assert all(isinstance(r, PlanningResult) for r in results.values())
        assert all(r.success for r in results.values())

    @pytest.mark.asyncio
    async def test_create_dependency_chain_with_failure(self, coordinator, registry):
        """测试依赖链中的失败处理"""
        # 注册一个会失败的规划器
        class FailingPlanner(BasePlanner):
            def __init__(self):
                super().__init__("失败规划器", PlannerType.TASK_PLANNER)

            async def create_plan(self, request: PlanningRequest) -> PlanningResult:
                return PlanningResult(
                    request_id=request.id,
                    planner_type=self.planner_type,
                    success=False,
                    feedback="模拟失败",
                )

            async def execute_plan(self, plan_id: str) -> bool:
                return False

            async def get_plan_status(self, plan_id: str) -> dict:
                return {"status": "failed"}

            async def update_plan(self, plan_id: str, updates: dict) -> bool:
                return False

        # 将第一个规划器替换为失败的规划器
        failing_planner = FailingPlanner()
        registry.planners[PlannerType.TASK_PLANNER] = failing_planner

        requests = [
            PlanningRequest(title=f"任务{i+1}")
            for i in range(3)
        ]

        dependencies = {
            requests[1].id: [requests[0].id],
            requests[2].id: [requests[1].id],
        }

        results = await coordinator.create_dependency_chain(requests, dependencies)

        # 第一个任务失败，后续任务也应该失败
        assert not results[requests[0].id].success
        assert not results[requests[1].id].success
        assert "前置依赖" in results[requests[1].id].feedback


# ========== 全局函数测试 ==========

class TestGlobalFunctions:
    """全局函数测试"""

    def test_get_planner_registry(self):
        """测试获取全局注册中心"""
        registry = get_planner_registry()
        assert isinstance(registry, UnifiedPlannerRegistry)

    def test_get_planner_coordinator(self):
        """测试获取全局协调器"""
        coordinator = get_planner_coordinator()
        assert isinstance(coordinator, PlannerCoordinator)

    def test_singleton_registry(self):
        """测试注册中心单例"""
        registry1 = get_planner_registry()
        registry2 = get_planner_registry()
        assert registry1 is registry2


# ========== 集成测试 ==========

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 1. 创建注册中心
        registry = UnifiedPlannerRegistry()

        # 2. 注册规划器
        planner1 = MockPlanner("主规划器")
        planner2 = MockPlanner("备用规划器")
        registry.register_planner(planner1)
        registry.register_planner(planner2)

        # 3. 创建桥接器
        bridge = PlannerIntegrationBridge(registry)

        # 4. 注册适配器
        def adapter(source_data):
            return PlanningRequest(
                title=source_data["title"],
                description=source_data.get("description", ""),
                priority=Priority(source_data.get("priority", 2)),
            )

        bridge.register_integration_adapter("api", PlannerType.TASK_PLANNER, adapter)

        # 5. 创建协调器
        coordinator = PlannerCoordinator(registry)

        # 6. 提交多个请求
        requests = [
            PlanningRequest(
                title=f"任务{i+1}",
                description=f"任务{i+1}的描述",
                priority=Priority.HIGH if i == 0 else Priority.MEDIUM,
            )
            for i in range(3)
        ]

        # 7. 协调执行
        results = await coordinator.coordinate_multi_planner_request(requests)

        # 8. 验证结果
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.plan_id is not None for r in results)

        # 9. 验证规划器被正确调用
        assert len(planner1.plans_created) + len(planner2.plans_created) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
