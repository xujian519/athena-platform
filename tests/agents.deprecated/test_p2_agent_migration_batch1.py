#!/usr/bin/env python3
"""
P2 Agent迁移测试 - 验证批量迁移的Agent符合统一接口标准

P2 Agent Migration Tests - Batch 1

测试内容：
1. PatentSearchAgentV2 - 专利检索Agent
2. YunxiIPAgentV3 - IP管理Agent
3. 接口合规性验证
4. 功能测试

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-04-21
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any

# 导入被测试的Agent
from core.agents.patent.patent_search_agent_v2 import PatentSearchAgentV2, create_patent_search_agent_v2
from core.agents.yunxi.yunxi_ip_agent_v3 import YunxiIPAgentV3, create_yunxi_ip_agent_v3

# 导入统一接口组件
from core.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)


# ==================== PatentSearchAgentV2测试 ====================

class TestPatentSearchAgentV2:
    """PatentSearchAgentV2测试"""

    def test_patent_search_agent_v2_initialization(self):
        """测试PatentSearchAgentV2初始化"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")
        assert agent.agent_id == "patent_search_test"
        assert agent.status == AgentStatus.IDLE

    def test_patent_search_agent_v2_capabilities(self):
        """测试PatentSearchAgentV2能力注册"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")
        capabilities = agent.get_capabilities()

        assert len(capabilities) == 7

        capability_names = {c.name for c in capabilities}
        assert "analyze_requirement" in capability_names
        assert "extract_keywords" in capability_names
        assert "search_cn_patents" in capability_names
        assert "search_foreign_patents" in capability_names
        assert "search_patent_families" in capability_names
        assert "merge_results" in capability_names
        assert "generate_report" in capability_names

    def test_patent_search_agent_v2_factory_function(self):
        """测试工厂函数"""
        agent = create_patent_search_agent_v2(agent_id="patent_factory_test")
        assert agent.agent_id == "patent_factory_test"

    @pytest.mark.asyncio
    async def test_patent_search_agent_v2_execute_analyze_requirement(self):
        """测试执行需求分析"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "action": "analyze_requirement",
                "params": {"query": "人工智能在自动驾驶中的应用"},
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert "result" in result.output_data

    @pytest.mark.asyncio
    async def test_patent_search_agent_v2_execute_search_cn(self):
        """测试执行中文专利检索"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")

        context = AgentExecutionContext(
            session_id="SESSION_002",
            task_id="TASK_002",
            input_data={
                "action": "search_cn_patents",
                "params": {
                    "keywords": ["人工智能", "自动驾驶"],
                    "limit": 10
                },
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_patent_search_agent_v2_execute_generate_report(self):
        """测试执行报告生成"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")

        context = AgentExecutionContext(
            session_id="SESSION_003",
            task_id="TASK_003",
            input_data={
                "action": "generate_report",
                "params": {
                    "results": [
                        {
                            "patent_number": "CN123456789A",
                            "title": "测试专利",
                            "applicant": "测试公司",
                            "date": "2024-01-01",
                            "abstract": "测试摘要",
                        }
                    ],
                    "format": "markdown",
                },
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert "report" in result.output_data["result"]


# ==================== YunxiIPAgentV3测试 ====================

class TestYunxiIPAgentV3:
    """YunxiIPAgentV3测试"""

    def test_yunxi_ip_agent_v3_initialization(self):
        """测试YunxiIPAgentV3初始化"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")
        assert agent.agent_id == "yunxi_test"
        assert agent.status == AgentStatus.IDLE

    def test_yunxi_ip_agent_v3_capabilities(self):
        """测试YunxiIPAgentV3能力注册"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")
        capabilities = agent.get_capabilities()

        assert len(capabilities) == 3

        capability_names = {c.name for c in capabilities}
        assert "portfolio_management" in capability_names
        assert "patent_valuation" in capability_names
        assert "deadline_tracking" in capability_names

    def test_yunxi_ip_agent_v3_factory_function(self):
        """测试工厂函数"""
        agent = create_yunxi_ip_agent_v3(agent_id="yunxi_factory_test")
        assert agent.agent_id == "yunxi_factory_test"

    @pytest.mark.asyncio
    async def test_yunxi_ip_agent_v3_execute_portfolio_management(self):
        """测试执行专利组合管理"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "action": "portfolio_management",
                "params": {
                    "action": "analyze",
                    "patent_id": "CN123456789A"
                },
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_yunxi_ip_agent_v3_execute_patent_valuation(self):
        """测试执行专利价值评估"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")

        context = AgentExecutionContext(
            session_id="SESSION_002",
            task_id="TASK_002",
            input_data={
                "action": "patent_valuation",
                "params": {
                    "patent_id": "CN987654321A"
                },
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None

    @pytest.mark.asyncio
    async def test_yunxi_ip_agent_v3_execute_deadline_tracking(self):
        """测试执行期限跟踪"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")

        context = AgentExecutionContext(
            session_id="SESSION_003",
            task_id="TASK_003",
            input_data={
                "action": "deadline_tracking",
                "params": {
                    "days": 30
                },
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None


# ==================== 接口合规性测试 ====================

class TestInterfaceCompliance:
    """接口合规性测试"""

    def test_patent_search_agent_v2_interface_compliance(self):
        """测试PatentSearchAgentV2接口合规性"""
        agent = PatentSearchAgentV2(agent_id="patent_search_test")

        # 必须有的属性
        assert hasattr(agent, "agent_id")
        assert hasattr(agent, "status")
        assert hasattr(agent, "config")
        assert hasattr(agent, "_capabilities")

        # 必须有的方法
        assert hasattr(agent, "_initialize")
        assert hasattr(agent, "execute")
        assert hasattr(agent, "get_system_prompt")
        assert hasattr(agent, "get_capabilities")
        assert hasattr(agent, "has_capability")
        assert hasattr(agent, "get_info")
        assert hasattr(agent, "validate_input")

    def test_yunxi_ip_agent_v3_interface_compliance(self):
        """测试YunxiIPAgentV3接口合规性"""
        agent = YunxiIPAgentV3(agent_id="yunxi_test")

        # 必须有的属性
        assert hasattr(agent, "agent_id")
        assert hasattr(agent, "status")
        assert hasattr(agent, "config")
        assert hasattr(agent, "_capabilities")

        # 必须有的方法
        assert hasattr(agent, "_initialize")
        assert hasattr(agent, "execute")
        assert hasattr(agent, "get_system_prompt")
        assert hasattr(agent, "get_capabilities")
        assert hasattr(agent, "has_capability")
        assert hasattr(agent, "get_info")
        assert hasattr(agent, "validate_input")


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """测试多Agent协同工作"""
        # 创建多个Agent
        patent_agent = PatentSearchAgentV2(agent_id="patent_coord")
        ip_agent = YunxiIPAgentV3(agent_id="ip_coord")

        # 专利检索Agent执行检索
        context = AgentExecutionContext(
            session_id="SESSION_MULTI",
            task_id="TASK_MULTI_001",
            input_data={
                "action": "search_cn_patents",
                "params": {
                    "keywords": ["人工智能"],
                    "limit": 10
                },
            },
            config={},
            metadata={},
        )

        result = await patent_agent.execute(context)
        assert result.status == AgentStatus.COMPLETED

        # IP管理Agent执行价值评估
        context = AgentExecutionContext(
            session_id="SESSION_MULTI",
            task_id="TASK_MULTI_002",
            input_data={
                "action": "patent_valuation",
                "params": {
                    "patent_id": "CN123456789A"
                },
            },
            config={},
            metadata={},
        )

        result = await ip_agent.execute(context)
        assert result.status == AgentStatus.COMPLETED


# ==================== 运行测试的便捷函数 ====================

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("P2 Agent迁移测试 - Batch 1")
    print("=" * 60)

    # PatentSearchAgentV2测试
    print("\n🔍 测试PatentSearchAgentV2...")
    patent_test = TestPatentSearchAgentV2()
    patent_test.test_patent_search_agent_v2_initialization()
    patent_test.test_patent_search_agent_v2_capabilities()
    patent_test.test_patent_search_agent_v2_factory_function()
    await patent_test.test_patent_search_agent_v2_execute_analyze_requirement()
    await patent_test.test_patent_search_agent_v2_execute_search_cn()
    await patent_test.test_patent_search_agent_v2_execute_generate_report()
    print("✅ PatentSearchAgentV2测试通过")

    # YunxiIPAgentV3测试
    print("\n💼 测试YunxiIPAgentV3...")
    yunxi_test = TestYunxiIPAgentV3()
    yunxi_test.test_yunxi_ip_agent_v3_initialization()
    yunxi_test.test_yunxi_ip_agent_v3_capabilities()
    yunxi_test.test_yunxi_ip_agent_v3_factory_function()
    await yunxi_test.test_yunxi_ip_agent_v3_execute_portfolio_management()
    await yunxi_test.test_yunxi_ip_agent_v3_execute_patent_valuation()
    await yunxi_test.test_yunxi_ip_agent_v3_execute_deadline_tracking()
    print("✅ YunxiIPAgentV3测试通过")

    # 接口合规性测试
    print("\n🔍 测试接口合规性...")
    compliance_test = TestInterfaceCompliance()
    compliance_test.test_patent_search_agent_v2_interface_compliance()
    compliance_test.test_yunxi_ip_agent_v3_interface_compliance()
    print("✅ 接口合规性测试通过")

    # 集成测试
    print("\n🔗 测试多Agent协同...")
    integration_test = TestIntegration()
    await integration_test.test_multi_agent_coordination()
    print("✅ 集成测试通过")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
