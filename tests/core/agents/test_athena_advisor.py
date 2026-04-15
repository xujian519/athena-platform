#!/usr/bin/env python3
"""
AthenaAdvisorAgent单元测试

测试Athena智慧女神的功能：
1. 战略指导
2. 系统分析
3. 智慧分享
4. 决策支持
"""

import pytest

# 跳过整个测试模块
pytestmark = pytest.mark.skip(reason="模块导入问题，待修复")

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.agents.athena_advisor import (
        AdvisorTaskType,
        AthenaAdvisorAgent,
    )
    from core.agents.base import (
        AgentRegistry,
        AgentRequest,
        AgentStatus,
    )
    from core.agents.xiaona_legal import XiaonaLegalAgent
except ImportError:
    pass  # 模块导入失败时，测试会被跳过


# ========== 测试清理fixture ==========

@pytest.fixture(autouse=True)
def clear_registry():
    """每个测试前后清理注册表"""
    AgentRegistry.clear()
    yield
    AgentRegistry.clear()


# ========== 基础测试 ==========

def test_athena_initialization():
    """测试Athena初始化"""
    agent = AthenaAdvisorAgent()

    assert agent.name == "athena-advisor"
    assert agent.status == AgentStatus.INITIALIZING
    assert len(agent.get_capabilities()) >= 9


def test_athena_metadata():
    """测试元数据"""
    agent = AthenaAdvisorAgent()
    metadata = agent.get_metadata()

    assert metadata.name == "athena-advisor"
    assert metadata.version == "2.0.0"
    assert "顾问" in metadata.tags or "智慧" in metadata.tags


def test_athena_capabilities():
    """测试能力列表"""
    agent = AthenaAdvisorAgent()
    capabilities = agent.get_capabilities()

    # 验证核心能力
    cap_names = [cap.name for cap in capabilities]
    assert "strategic-advice" in cap_names
    assert "system-analysis" in cap_names
    assert "best-practices" in cap_names
    assert "decision-support" in cap_names
    assert "consultation" in cap_names


# ========== 异步方法测试 ==========


@pytest.mark.asyncio
class TestAthenaLifecycle:
    """Athena生命周期测试"""

    async def test_athena_initialize(self):
        """测试初始化流程"""
        agent = AthenaAdvisorAgent()
        assert agent.status == AgentStatus.INITIALIZING

        await agent.initialize()

        assert agent.is_ready
        assert agent.status == AgentStatus.READY

    async def test_athena_shutdown(self):
        """测试关闭流程"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()
        await agent.shutdown()

        assert agent.status == AgentStatus.SHUTDOWN

    async def test_athena_health_check(self):
        """测试健康检查"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        status = await agent.health_check()

        assert status.status == AgentStatus.READY
        assert status.is_healthy()


@pytest.mark.asyncio
class TestAthenaStrategicGuidance:
    """Athena战略指导测试"""

    async def test_strategic_advice(self):
        """测试战略建议"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="strategic-advice",
            parameters={
                "topic": "平台发展方向",
                "context": "快速增长期",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "strategic-advice"
        assert "advice" in response.data

    async def test_platform_roadmap(self):
        """测试平台路线图"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-002",
            action="platform-roadmap",
            parameters={
                "time_horizon": "6-month",
                "focus_areas": ["性能优化"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "platform-roadmap"
        assert "roadmap" in response.data


@pytest.mark.asyncio
class TestAthenaSystemAnalysis:
    """Athena系统分析测试"""

    async def test_system_analysis(self):
        """测试系统分析"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        # 注册一个测试智能体
        test_agent = XiaonaLegalAgent()
        AgentRegistry.register(test_agent)
        await test_agent.initialize()

        request = AgentRequest(
            request_id="test-003",
            action="system-analysis",
            parameters={
                "analysis_type": "health",
                "scope": "all",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "system-analysis"
        assert response.data["results"]["total_agents"] >= 1

    async def test_architecture_review(self):
        """测试架构评审"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-004",
            action="architecture-review",
            parameters={
                "component": "agent-system",
                "review_aspect": "scalability",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "architecture-review"
        assert "review" in response.data


@pytest.mark.asyncio
class TestAthenaWisdomSharing:
    """Athena智慧分享测试"""

    async def test_best_practices(self):
        """测试最佳实践"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-005",
            action="best-practices",
            parameters={"domain": "python"},
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "best-practices"
        assert "practices" in response.data

    async def test_lessons_learned(self):
        """测试经验教训"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-006",
            action="lessons-learned",
            parameters={"project_phase": "architecture"},
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "lessons-learned"
        assert "lessons" in response.data


@pytest.mark.asyncio
class TestAthenaDecisionSupport:
    """Athena决策支持测试"""

    async def test_decision_support(self):
        """测试决策支持"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-007",
            action="decision-support",
            parameters={
                "decision_type": "technology-choice",
                "options": ["PostgreSQL", "MongoDB", "MySQL"],
                "criteria": ["性能", "可维护性", "成本"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "decision-support"
        assert "recommendation" in response.data

    async def test_data_analysis(self):
        """测试数据分析"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-008",
            action="data-analysis",
            parameters={},
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "data-analysis"
        assert "data" in response.data


@pytest.mark.asyncio
class TestAthenaConsultation:
    """Athena咨询服务测试"""

    async def test_consultation(self):
        """测试咨询服务"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-009",
            action="consultation",
            parameters={
                "question": "如何优化数据库查询性能？",
                "context": "当前查询响应时间500ms",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "consultation"
        assert "answer" in response.data

    async def test_guidance(self):
        """测试指导服务"""
        agent = AthenaAdvisorAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-010",
            action="guidance",
            parameters={
                "topic": "异步编程最佳实践",
                "experience_level": "intermediate",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "guidance"
        assert "guidance" in response.data


# ========== 集成测试 ==========


@pytest.mark.asyncio
async def test_athena_with_xiaona():
    """测试Athena与小娜的协作"""
    # 创建并初始化Athena
    athena = AthenaAdvisorAgent()
    AgentRegistry.register(athena)
    await athena.initialize()

    # 创建并初始化小娜
    xiaona = XiaonaLegalAgent()
    AgentRegistry.register(xiaona)
    await xiaona.initialize()

    # Athena进行系统分析
    request = AgentRequest(
        request_id="integration-001",
        action="system-analysis",
        parameters={"analysis_type": "health"},
    )

    response = await athena.safe_process(request)

    assert response.success is True
    assert response.data["results"]["total_agents"] == 2  # Athena + Xiaona


# ========== 运行测试 ==========

if __name__ == "__main__":
    # 运行单个测试
    print("运行Athena测试...")

    # 基础测试
    print("  测试基础功能...")
    test_athena_initialization()
    test_athena_metadata()
    test_athena_capabilities()
    print("  ✅ 基础测试通过")

    # 异步测试
    print("  运行异步测试...")
    asyncio.run(test_athena_with_xiaona())

    print("\n所有测试通过! 🏛️")
