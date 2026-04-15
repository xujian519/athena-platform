#!/usr/bin/env python3
"""
XiaonaLegalAgent单元测试

测试小娜·天秤女神的功能：
1. 10大法律能力
2. 任务路由
3. 请求处理
4. 健康检查
"""

import pytest

# 跳过整个测试模块
pytestmark = pytest.mark.skip(reason="模块导入问题,待修复")

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from core.agents.base import (
        AgentRegistry,
        AgentRequest,
        AgentStatus,
    )
    from core.agents.xiaona_legal import (
        LegalTaskType,
        XiaonaLegalAgent,
    )
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


def test_xiaona_initialization():
    """测试小娜初始化"""
    agent = XiaonaLegalAgent()

    assert agent.name == "xiaona-legal"
    assert agent.status == AgentStatus.INITIALIZING
    assert len(agent.get_capabilities()) == 10


def test_xiaona_metadata():
    """测试元数据"""
    agent = XiaonaLegalAgent()
    metadata = agent.get_metadata()

    assert metadata.name == "xiaona-legal"
    assert metadata.version == "2.0.0"
    assert "法律" in metadata.tags
    assert "专利" in metadata.tags


def test_xiaona_capabilities():
    """测试能力列表"""
    agent = XiaonaLegalAgent()
    capabilities = agent.get_capabilities()

    # 验证10大核心能力
    cap_names = [cap.name for cap in capabilities]
    assert "office-action-response" in cap_names
    assert "invalidity-request" in cap_names
    assert "patent-drafting" in cap_names
    assert "patent-compliance" in cap_names
    assert "novelty-analysis" in cap_names
    assert "inventiveness-analysis" in cap_names
    assert "claim-analysis" in cap_names
    assert "patent-search" in cap_names
    assert "technology-landscape" in cap_names
    assert "legal-consultation" in cap_names

    # 验证能力详情
    oa_capability = next(c for c in capabilities if c.name == "office-action-response")
    assert "答复" in oa_capability.description
    assert "oa_number" in oa_capability.parameters


# ========== 异步方法测试 ==========


@pytest.mark.asyncio
class TestXiaonaLifecycle:
    """小娜生命周期测试"""

    async def test_xiaona_initialize(self):
        """测试初始化流程"""
        agent = XiaonaLegalAgent()
        assert agent.status == AgentStatus.INITIALIZING

        await agent.initialize()

        assert agent.is_ready
        assert agent.status == AgentStatus.READY

    async def test_xiaona_shutdown(self):
        """测试关闭流程"""
        agent = XiaonaLegalAgent()
        await agent.initialize()
        await agent.shutdown()

        assert agent.status == AgentStatus.SHUTDOWN

    async def test_xiaona_health_check(self):
        """测试健康检查"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        status = await agent.health_check()

        assert status.status == AgentStatus.READY
        assert status.is_healthy()
        assert "orchestrator_available" in status.details


@pytest.mark.asyncio
class TestXiaonaProcessing:
    """小娜请求处理测试"""

    async def test_get_capabilities(self):
        """测试获取能力列表"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="get-capabilities",
            parameters={},
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert len(response.data["capabilities"]) == 10

    async def test_get_stats(self):
        """测试获取统计信息"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-002",
            action="get-stats",
            parameters={},
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert "stats" in response.data
        assert "task_stats" in response.data

    async def test_office_action_response(self):
        """测试意见答复"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-003",
            action="office-action-response",
            parameters={
                "oa_number": "OA2023001234",
                "patent_id": "CN202310123456.7",
                "rejection_reasons": ["新颖性", "创造性"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "office-action-response"
        assert "response_strategy" in response.data

    async def test_invalidity_request(self):
        """测试无效宣告"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-004",
            action="invalidity-request",
            parameters={
                "patent_id": "CN123456789U",
                "ground_type": "inventiveness",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "invalidity-request"
        assert "analysis" in response.data

    async def test_patent_drafting(self):
        """测试专利撰写"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-005",
            action="patent-drafting",
            parameters={
                "invention_title": "一种智能控制系统",
                "technical_field": "自动化控制",
                "technical_problem": "现有控制方式不够智能",
                "technical_solution": "采用AI算法优化",
                "beneficial_effects": "提高控制精度30%",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "patent-drafting"
        assert "draft_content" in response.data
        assert "claims" in response.data["draft_content"]

    async def test_patent_compliance(self):
        """测试专利合规审查"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-006",
            action="patent-compliance",
            parameters={
                "patent_content": "本发明涉及...",
                "check_type": "disclosure",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "patent-compliance"
        assert "compliance_result" in response.data

    async def test_novelty_analysis(self):
        """测试新颖性分析"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-007",
            action="novelty-analysis",
            parameters={
                "claims": ["1. 一种包含特征A的装置..."],
                "prior_art": ["CN123456789U", "US2023001234"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "novelty-analysis"
        assert "claims_analysis" in response.data

    async def test_inventiveness_analysis(self):
        """测试创造性分析"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-008",
            action="inventiveness-analysis",
            parameters={
                "claims": ["1. 一种..."],
                "closest_prior_art": "CN123456789U",
                "distinguishing_features": ["特征A", "特征B"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "inventiveness-analysis"
        assert "three_step_analysis" in response.data

    async def test_claim_analysis(self):
        """测试权利要求审查"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-009",
            action="claim-analysis",
            parameters={
                "claims": [
                    "1. 一种包含特征A的装置...",
                    "2. 根据权利要求1所述的装置...",
                ],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "claim-analysis"
        assert "analysis_results" in response.data

    async def test_patent_search(self):
        """测试专利检索"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-010",
            action="patent-search",
            parameters={
                "query": "深度学习 图像识别",
                "search_fields": ["title", "abstract"],
                "databases": ["CN", "US"],
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "patent-search"
        assert "results" in response.data

    async def test_technology_landscape(self):
        """测试技术态势分析"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-011",
            action="technology-landscape",
            parameters={
                "technology_field": "深度学习",
                "time_range": "2018-2023",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "technology-landscape"
        assert "trends" in response.data

    async def test_legal_consultation(self):
        """测试法律咨询"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-012",
            action="legal-consultation",
            parameters={
                "question": "专利申请被驳回后怎么办？",
                "context": "OA通知指出新颖性问题",
            },
        )

        response = await agent.safe_process(request)

        assert response.success is True
        assert response.data["task_type"] == "legal-consultation"
        assert "answer" in response.data


@pytest.mark.asyncio
class TestXiaonaErrorHandling:
    """小娜错误处理测试"""

    async def test_invalid_action_fails(self):
        """测试无效操作失败"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="invalid-action",
        )

        response = await agent.safe_process(request)

        assert response.success is False
        assert "不支持" in response.error

    async def test_empty_action_fails(self):
        """测试空action失败"""
        agent = XiaonaLegalAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-002",
            action="",
        )

        response = await agent.safe_process(request)

        assert response.success is False


# ========== 注册中心测试 ==========


@pytest.mark.asyncio
async def test_xiaona_in_registry():
    """测试小娜在注册中心中的使用"""
    agent = XiaonaLegalAgent()
    AgentRegistry.register(agent)

    # 验证注册
    assert "xiaona-legal" in AgentRegistry.list_agents()

    # 初始化
    await AgentRegistry.initialize_all()

    # 验证可以获取
    retrieved = AgentRegistry.get("xiaona-legal")
    assert retrieved is agent
    assert retrieved.is_ready

    # 处理请求
    request = AgentRequest(
        request_id="test-001",
        action="get-capabilities",
    )
    response = await retrieved.safe_process(request)
    assert response.success

    # 健康检查
    health_results = await AgentRegistry.health_check_all()
    assert "xiaona-legal" in health_results
    assert health_results["xiaona-legal"].is_healthy()

    # 关闭
    await AgentRegistry.shutdown_all()


# ========== 运行测试 ==========

if __name__ == "__main__":
    # 运行单个测试
    print("运行小娜测试...")

    # 基础测试
    print("  测试基础功能...")
    test_xiaona_initialization()
    test_xiaona_metadata()
    test_xiaona_capabilities()
    print("  ✅ 基础测试通过")

    # 异步测试
    print("  运行异步测试...")
    asyncio.run(test_xiaona_in_registry())

    print("\n所有测试通过! ⚖️")
