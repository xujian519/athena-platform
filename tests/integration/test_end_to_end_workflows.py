#!/usr/bin/env python3
"""
端到端测试套件 - Agent协作工作流验证

测试跨Agent工作流，验证：
1. 检索-分析-撰写流程 (RetrieverAgent → AnalyzerAgent → WriterAgent)
2. 协调流程 (XiaonuoAgent调度其他Agent)
3. 完整案例 (端到端的专利分析流程)

Author: Athena Team
Version: 1.0.0
Date: 2026-04-21
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入统一接口
from core.framework.agents.base import (
    AgentRegistry,
    AgentRequest,
    AgentStatus,
)

# 导入测试的Agent
try:
    from core.framework.agents.xiaona_with_legal_world import XiaonaWithLegalWorld
    from core.framework.agents.xiaonuo_coordinator import XiaonuoAgent

    from core.framework.agents.patent_search_agent import PatentSearchAgent
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason=f"Agent导入失败: {e}")


# ========== 测试Fixtures ==========


@pytest.fixture(scope="function", autouse=True)
async def clear_registry():
    """每个测试前后清理注册表"""
    AgentRegistry.clear()
    yield
    await AgentRegistry.shutdown_all()
    AgentRegistry.clear()


@pytest.fixture
async def initialized_agents():
    """初始化所有测试Agent"""
    if not AGENTS_AVAILABLE:
        pytest.skip("Agents不可用")

    agents = {}

    try:
        # 初始化小诺（调度器）
        xiaonuo = XiaonuoAgent()
        await xiaonuo.initialize()
        AgentRegistry.register(xiaonuo)
        agents["xiaonuo"] = xiaonuo

        # 初始化小娜（法律专家）
        xiaona = XiaonaWithLegalWorld(
            integration_mode="fallback"  # 测试环境使用回退模式
        )
        await xiaona.initialize()
        AgentRegistry.register(xiaona)
        agents["xiaona"] = xiaona

        # 初始化专利检索Agent
        try:
            patent_search = PatentSearchAgent()
            await patent_search.initialize()
            AgentRegistry.register(patent_search)
            agents["patent_search"] = patent_search
        except Exception:
            # 专利检索Agent可能需要外部依赖，跳过
            pass

        yield agents

    finally:
        # 清理
        for agent in agents.values():
            try:
                await agent.shutdown()
            except Exception:
                pass


@pytest.fixture
def sample_patent_request() -> dict[str, Any]:
    """示例专利分析请求"""
    return {
        "request_id": "e2e-test-001",
        "action": "patent-analysis",
        "parameters": {
            "query": "结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法",
            "analysis_type": "novelity_creativity",
            "include_patent_drafting": False,
        },
        "context": {
            "user_id": "test_user",
            "session_id": "test_session",
        }
    }


@pytest.fixture
def sample_oa_request() -> dict[str, Any]:
    """示例审查意见答复请求"""
    return {
        "request_id": "e2e-test-002",
        "action": "office-action-response-with-legal-world",
        "parameters": {
            "oa_text": "权利要求1-3不具备创造性，理由是...",
            "application_no": "202410000000.0",
            "claims": "1. 一种自动驾驶掉头路段脱困规划方法...",
        }
    }


# ========== 测试类 ==========


@pytest.mark.asyncio
@pytest.mark.integration
class TestRetrieverAnalyzerWriterWorkflow:
    """
    检索-分析-撰写工作流测试

    验证数据在Agent间的传递和协作
    """

    async def test_retriever_to_analyzer_flow(self, initialized_agents, sample_patent_request):
        """测试检索Agent到分析Agent的数据流"""
        xiaonuo = initialized_agents.get("xiaonuo")
        xiaona = initialized_agents.get("xiaona")

        if not xiaonuo or not xiaona:
            pytest.skip("必需的Agent未初始化")

        # 步骤1: 专利检索（使用小娜的专利检索能力）
        search_request = AgentRequest(
            request_id="e2e-search-001",
            action="patent-search",
            parameters={
                "query": "自动驾驶 路径规划",
                "max_results": 5,
            }
        )

        search_response = await xiaona.safe_process(search_request)

        # 验证检索响应
        assert search_response.success is True
        assert "results" in search_response.data or search_response.data.get("status") in ["success", "pending"]

        # 步骤2: 使用检索结果进行分析
        analysis_request = AgentRequest(
            request_id="e2e-analysis-001",
            action="creativity-analysis-with-legal-world",
            parameters={
                "patent_content": "一种结合拟人驾驶行为的自动驾驶掉头路段脱困规划方法",
                "closest_prior_art": search_response.data.get("results", [{}])[0].get("title", "")
                if search_response.data.get("results")
                else "现有自动驾驶路径规划方法"
            }
        )

        analysis_response = await xiaona.safe_process(analysis_request)

        # 验证分析响应
        assert analysis_response.success is True
        assert analysis_response.data.get("status") == "success"

    async def test_sequential_workflow_execution(self, initialized_agents):
        """测试顺序工作流执行"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 定义工作流步骤
        workflow = [
            {
                "agent": "xiaona-legal-world",
                "action": "get-stats",
                "parameters": {}
            },
            {
                "agent": "xiaona-legal-world",
                "action": "get-capabilities",
                "parameters": {}
            }
        ]

        # 通过小诺编排工作流
        request = AgentRequest(
            request_id="e2e-workflow-001",
            action="orchestrate-workflow",
            parameters={
                "workflow": workflow,
                "mode": "sequential"
            }
        )

        response = await xiaonuo.safe_process(request)

        # 验证工作流执行结果
        assert response.success is True
        assert response.data["task_type"] == "sequential-execute"
        assert response.data["total_tasks"] == 2
        assert response.data["success_count"] >= 1

    async def test_parallel_workflow_execution(self, initialized_agents):
        """测试并行工作流执行"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 定义并行工作流
        workflow = [
            {
                "agent": "xiaona-legal-world",
                "action": "get-stats",
                "parameters": {}
            },
            {
                "agent": "xiaona-legal-world",
                "action": "health-check",
                "parameters": {}
            }
        ]

        request = AgentRequest(
            request_id="e2e-parallel-001",
            action="orchestrate-workflow",
            parameters={
                "workflow": workflow,
                "mode": "parallel"
            }
        )

        start_time = time.time()
        response = await xiaonuo.safe_process(request)
        (time.time() - start_time) * 1000

        # 验证并行执行结果
        assert response.success is True
        assert response.data["task_type"] == "parallel-execute"
        # 并行执行应该比顺序快（这里只验证执行成功）
        assert response.data["executed_tasks"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
class TestCoordinationWorkflow:
    """
    协调流程测试

    验证XiaonuoAgent的调度和编排能力
    """

    async def test_xiaonuo_scheduling(self, initialized_agents):
        """测试小诺的调度能力"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 列出所有Agent
        request = AgentRequest(
            request_id="e2e-list-001",
            action="list-agents",
            parameters={}
        )

        response = await xiaonuo.safe_process(request)

        # 验证
        assert response.success is True
        assert response.data["total_count"] >= 1
        agent_names = [a["name"] for a in response.data["agents"]
        assert "xiaonuo-coordinator" in agent_names or "xiaona-legal-world" in agent_names

    async def test_xiaonuo_platform_status(self, initialized_agents):
        """测试平台状态获取"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        request = AgentRequest(
            request_id="e2e-platform-001",
            action="platform-status",
            parameters={}
        )

        response = await xiaonuo.safe_process(request)

        # 验证
        assert response.success is True
        assert "platform_state" in response.data
        assert "total_agents" in response.data["platform_state"]

    async def test_xiaonuo_health_check_all(self, initialized_agents):
        """测试全局健康检查"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        request = AgentRequest(
            request_id="e2e-health-001",
            action="health-check-all",
            parameters={}
        )

        response = await xiaonuo.safe_process(request)

        # 验证
        assert response.success is True
        assert response.data["task_type"] == "health-check-all"
        assert response.data["total_agents"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
class TestCompletePatentWorkflow:
    """
    完整专利分析流程测试

    端到端验证完整的专利分析工作流
    """

    async def test_complete_patent_analysis_workflow(self, initialized_agents, sample_patent_request):
        """测试完整专利分析工作流"""
        xiaonuo = initialized_agents.get("xiaonuo")
        xiaona = initialized_agents.get("xiaona")

        if not xiaonuo or not xiaona:
            pytest.skip("必需的Agent未初始化")

        # 步骤1: 智能规划（通过小诺）
        plan_request = AgentRequest(
            request_id="e2e-plan-001",
            action="intelligent-plan",
            parameters={
                "user_input": sample_patent_request["parameters"]["query"],
                "context": sample_patent_request["context"]
            }
        )

        plan_response = await xiaonuo.safe_process(plan_request)
        assert plan_response.success is True

        # 步骤2: 专利检索
        search_request = AgentRequest(
            request_id="e2e-search-002",
            action="patent-search",
            parameters={
                "query": sample_patent_request["parameters"]["query"],
                "max_results": 10
            }
        )

        search_response = await xiaona.safe_process(search_request)

        # 步骤3: 创造性分析
        analysis_request = AgentRequest(
            request_id="e2e-analysis-002",
            action="creativity-analysis-with-legal-world",
            parameters={
                "patent_content": sample_patent_request["parameters"]["query"],
                "closest_prior_art": "已知技术"
            }
        )

        analysis_response = await xiaona.safe_process(analysis_request)

        # 验证所有步骤
        assert plan_response.success is True
        assert search_response.success is True or search_response.data.get("status") == "pending"
        assert analysis_response.success is True

    async def test_oa_response_workflow(self, initialized_agents, sample_oa_request):
        """测试审查意见答复工作流"""
        xiaona = initialized_agents.get("xiaona")

        if not xiaona:
            pytest.skip("小娜Agent未初始化")

        # 创建审查意见答复请求
        request = AgentRequest(**sample_oa_request)

        response = await xiaona.safe_process(request)

        # 验证响应
        assert response.success is True
        assert response.data.get("status") in ["success", "pending"]


@pytest.mark.asyncio
@pytest.mark.integration
class TestAgentCollaboration:
    """
    Agent间协作测试

    验证Agent间的消息传递和状态同步
    """

    async def test_agent_communication_via_registry(self, initialized_agents):
        """测试通过注册中心的Agent通信"""
        xiaonuo = initialized_agents.get("xiaonuo")
        xiaona = initialized_agents.get("xiaona")

        if not xiaonuo or not xiaona:
            pytest.skip("必需的Agent未初始化")

        # 小诺调度小娜
        request = AgentRequest(
            request_id="e2e-comm-001",
            action="schedule-task",
            parameters={
                "target_agent": "xiaona-legal-world",
                "action": "get-stats",
                "parameters": {}
            }
        )

        response = await xiaonuo.safe_process(request)

        # 验证调度结果
        assert response.success is True
        assert response.data["task_type"] == "schedule-task"

    async def test_cross_agent_context_sharing(self, initialized_agents):
        """测试跨Agent的上下文共享"""
        xiaona = initialized_agents.get("xiaona")

        if not xiaona:
            pytest.skip("小娜Agent未初始化")

        # 设置上下文
        xiaona.set_context("test_session_id", "e2e-test-123")
        xiaona.set_context("test_user_id", "test-user")

        # 验证上下文
        assert xiaona.get_context("test_session_id") == "e2e-test-123"
        assert xiaona.get_context("test_user_id") == "test-user"

    async def test_agent_state_propagation(self, initialized_agents):
        """测试Agent状态传播"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 获取初始状态
        initial_status = await xiaonuo.health_check()

        # 执行任务
        request = AgentRequest(
            request_id="e2e-state-001",
            action="get-stats",
            parameters={}
        )

        await xiaonuo.safe_process(request)

        # 获取最终状态
        final_status = await xiaonuo.health_check()

        # 验证状态
        assert initial_status.status == AgentStatus.READY
        assert final_status.status == AgentStatus.READY
        assert final_status.is_healthy()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceAndScalability:
    """
    性能和可扩展性测试

    验证系统在负载下的表现
    """

    async def test_concurrent_requests(self, initialized_agents):
        """测试并发请求处理"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 创建多个并发请求
        requests = [
            AgentRequest(
                request_id=f"e2e-concurrent-{i}",
                action="get-stats",
                parameters={}
            )
            for i in range(10)
        ]

        # 并发执行
        start_time = time.time()
        results = await asyncio.gather(*[
            xiaonuo.safe_process(req)
            for req in requests
        ])
        execution_time = (time.time() - start_time) * 1000

        # 验证所有请求成功
        successful = sum(1 for r in results if r.success)
        assert successful >= 8  # 至少80%成功率
        assert execution_time < 5000  # 5秒内完成

    async def test_workflow_performance(self, initialized_agents):
        """测试工作流性能"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 创建中等复杂度的工作流
        workflow = [
            {
                "agent": "xiaona-legal-world",
                "action": "get-stats",
                "parameters": {}
            }
            for _ in range(5)
        ]

        request = AgentRequest(
            request_id="e2e-perf-001",
            action="orchestrate-workflow",
            parameters={
                "workflow": workflow,
                "mode": "sequential"
            }
        )

        start_time = time.time()
        response = await xiaonuo.safe_process(request)
        execution_time = (time.time() - start_time) * 1000

        # 验证性能
        assert response.success is True
        assert execution_time < 10000  # 10秒内完成


@pytest.mark.asyncio
@pytest.mark.integration
class TestErrorHandlingAndRecovery:
    """
    错误处理和恢复测试

    验证系统在错误情况下的行为
    """

    async def test_invalid_action_handling(self, initialized_agents):
        """测试无效动作处理"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        request = AgentRequest(
            request_id="e2e-error-001",
            action="invalid-action",
            parameters={}
        )

        response = await xiaonuo.safe_process(request)

        # 验证错误处理
        assert response.success is False
        assert "不支持" in response.error or "无效" in response.error

    async def test_agent_failure_handling(self, initialized_agents):
        """测试Agent失败处理"""
        xiaonuo = initialized_agents.get("xiaonuo")

        if not xiaonuo:
            pytest.skip("小诺Agent未初始化")

        # 尝试调度不存在的Agent
        request = AgentRequest(
            request_id="e2e-error-002",
            action="schedule-task",
            parameters={
                "target_agent": "nonexistent-agent",
                "action": "test",
                "parameters": {}
            }
        )

        response = await xiaonuo.safe_process(request)

        # 验证错误处理
        assert response.success is True  # 调度请求成功
        assert response.data["success"] is False  # 但任务执行失败
        assert "不存在" in response.data["error"]


# ========== 测试辅助函数 ==========


def print_test_results():
    """打印测试结果摘要"""
    print("\n" + "=" * 60)
    print("端到端测试套件 - 执行摘要")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print("测试场景:")
    print("  1. 检索-分析-撰写工作流")
    print("  2. 协调流程")
    print("  3. 完整专利分析流程")
    print("  4. Agent间协作")
    print("  5. 性能和可扩展性")
    print("  6. 错误处理和恢复")
    print("=" * 60)


if __name__ == "__main__":
    """直接运行测试"""
    print_test_results()
    pytest.main([__file__, "-v", "-s", "--tb=short"])
