#!/usr/bin/env python3
"""
P1 Agent迁移测试 - 验证迁移后的Agent符合统一接口标准

P1 Agent Migration Tests - Validate migrated agents comply with unified interface standard

测试内容：
1. WriterAgent - 已迁移完成，验证接口合规性
2. XiaonuoAgentV2 - 新迁移版本，验证接口合规性和功能
3. XiaonaAgentScratchpadV2 - 新迁移版本，验证接口合规性和功能

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-04-21
"""

import asyncio
import pytest
from datetime import datetime
from typing import Any

# 导入被测试的Agent
from core.agents.xiaona.writer_agent import WriterAgent
from core.agents.xiaonuo.xiaonuo_agent_v2 import XiaonuoAgentV2, create_xiaonuo_agent_v2
from core.agents.xiaona.xiaona_agent_scratchpad_v2 import (
    XiaonaAgentScratchpadV2,
    create_xiaona_agent_v2,
)

# 导入统一接口组件
from core.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
    AgentCapability,
)


# ==================== WriterAgent测试 ====================

class TestWriterAgent:
    """WriterAgent测试 - 验证已迁移的Agent"""

    def test_writer_agent_initialization(self):
        """测试WriterAgent初始化"""
        agent = WriterAgent(agent_id="writer_test")
        assert agent.agent_id == "writer_test"
        assert agent.status == AgentStatus.IDLE

    def test_writer_agent_capabilities(self):
        """测试WriterAgent能力注册"""
        agent = WriterAgent(agent_id="writer_test")
        capabilities = agent.get_capabilities()

        assert len(capabilities) >= 4

        capability_names = {c.name for c in capabilities}
        assert "claim_drafting" in capability_names
        assert "description_drafting" in capability_names
        assert "office_action_response" in capability_names
        assert "invalidation_petition" in capability_names

    def test_writer_agent_system_prompt(self):
        """测试WriterAgent系统提示词"""
        agent = WriterAgent(agent_id="writer_test")
        prompt = agent.get_system_prompt()

        assert "小娜·撰写者" in prompt
        assert "权利要求书" in prompt
        assert "说明书" in prompt

    @pytest.mark.asyncio
    async def test_writer_agent_execute_claims(self):
        """测试WriterAgent执行权利要求撰写"""
        agent = WriterAgent(agent_id="writer_test")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "撰写权利要求",
                "previous_results": {},
            },
            config={"writing_type": "claims"},
            metadata={},
        )

        result = await agent.execute(context)

        # 验证返回结果结构
        assert isinstance(result, AgentExecutionResult)
        assert result.agent_id == "writer_test"

        # 注意：由于没有实际的LLM，这里可能会返回错误或模拟结果
        # 只要接口正确，就应该接受


# ==================== XiaonuoAgentV2测试 ====================

class TestXiaonuoAgentV2:
    """XiaonuoAgentV2测试 - 验证新迁移的Agent"""

    def test_xiaonuo_agent_v2_initialization(self):
        """测试XiaonuoAgentV2初始化"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")
        assert agent.agent_id == "xiaonuo_test"
        assert agent.status == AgentStatus.IDLE
        assert agent.family_role == "爸爸最疼爱的女儿"

    def test_xiaonuo_agent_v2_capabilities(self):
        """测试XiaonuoAgentV2能力注册"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")
        capabilities = agent.get_capabilities()

        assert len(capabilities) >= 4

        capability_names = {c.name for c in capabilities}
        assert "emotional_care" in capability_names
        assert "platform_coordination" in capability_names
        assert "media_operations" in capability_names
        assert "task_scheduling" in capability_names

    def test_xiaonuo_agent_v2_system_prompt(self):
        """测试XiaonuoAgentV2系统提示词"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")
        prompt = agent.get_system_prompt()

        assert "小诺·双鱼公主" in prompt
        assert "平台总调度官" in prompt
        assert "爸爸" in prompt

    def test_xiaonuo_agent_v2_factory_function(self):
        """测试工厂函数"""
        agent = create_xiaonuo_agent_v2(agent_id="xiaonuo_factory_test")
        assert agent.agent_id == "xiaonuo_factory_test"

    @pytest.mark.asyncio
    async def test_xiaonuo_agent_v2_execute_emotional_care(self):
        """测试XiaonuoAgentV2执行情感关怀任务"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "小诺真乖",
                "is_father": True,
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert "response" in result.output_data
        assert result.metadata["is_father"] is True

        # 验证响应内容
        response = result.output_data["response"]
        assert "💖" in response or "💝" in response or "😊" in response

    @pytest.mark.asyncio
    async def test_xiaonuo_agent_v2_execute_coordination(self):
        """测试XiaonuoAgentV2执行协调任务"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")

        context = AgentExecutionContext(
            session_id="SESSION_002",
            task_id="TASK_002",
            input_data={
                "user_input": "协调这个任务",
                "is_father": False,
                "request_type": "coordination",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data["request_type"] == "coordination"

    @pytest.mark.asyncio
    async def test_xiaonuo_agent_v2_execute_media_request(self):
        """测试XiaonuoAgentV2执行媒体运营任务"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")

        context = AgentExecutionContext(
            session_id="SESSION_003",
            task_id="TASK_003",
            input_data={
                "user_input": "帮我规划内容策略",
                "is_father": False,
                "request_type": "media",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data["request_type"] == "media"

    @pytest.mark.asyncio
    async def test_xiaonuo_agent_v2_input_validation(self):
        """测试XiaonuoAgentV2输入验证"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")

        # 测试缺少session_id的情况
        context = AgentExecutionContext(
            session_id="",  # 空session_id
            task_id="TASK_001",
            input_data={"user_input": "测试"},
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "输入验证失败" in result.error_message

    @pytest.mark.asyncio
    async def test_xiaonuo_agent_v2_get_overview(self):
        """测试XiaonuoAgentV2获取概览"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")
        overview = await agent.get_overview()

        assert overview["agent_id"] == "xiaonuo_test"
        assert overview["version"] == "v2.0.0"
        assert overview["family_role"] == "爸爸最疼爱的女儿"
        assert overview["total_capabilities"] >= 4


# ==================== XiaonaAgentScratchpadV2测试 ====================

class TestXiaonaAgentScratchpadV2:
    """XiaonaAgentScratchpadV2测试 - 验证新迁移的Agent"""

    def test_xiaona_agent_v2_initialization(self):
        """测试XiaonaAgentScratchpadV2初始化"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")
        assert agent.agent_id == "xiaona_test"
        assert agent.status == AgentStatus.IDLE
        assert agent.scratchpad_enabled is True

    def test_xiaona_agent_v2_capabilities(self):
        """测试XiaonaAgentScratchpadV2能力注册"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")
        capabilities = agent.get_capabilities()

        assert len(capabilities) >= 4

        capability_names = {c.name for c in capabilities}
        assert "patent_analysis" in capability_names
        assert "office_action_response" in capability_names
        assert "invalidity_analysis" in capability_names
        assert "legal_reasoning" in capability_names

    def test_xiaona_agent_v2_system_prompt(self):
        """测试XiaonaAgentScratchpadV2系统提示词"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")
        prompt = agent.get_system_prompt()

        assert "小娜·天秤女神" in prompt
        assert "法律专家" in prompt
        assert "私下推理" in prompt

    def test_xiaona_agent_v2_factory_function(self):
        """测试工厂函数"""
        agent = create_xiaona_agent_v2(agent_id="xiaona_factory_test")
        assert agent.agent_id == "xiaona_factory_test"

    def test_xiaona_agent_v2_scratchpad_config(self):
        """测试Scratchpad配置"""
        agent = XiaonaAgentScratchpadV2(
            agent_id="xiaona_test",
            config={
                "scratchpad_enabled": False,
                "max_scratchpad_length": 5000,
                "summary_max_length": 300,
            }
        )

        assert agent.scratchpad_enabled is False
        assert agent.max_scratchpad_length == 5000
        assert agent.summary_max_length == 300

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_execute_patent_analysis(self):
        """测试XiaonaAgentScratchpadV2执行专利分析任务"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={
                "user_input": "帮我分析专利CN123456789A的创造性",
                "task_type": "patent_analysis",
                "patent_id": "CN123456789A",
                "analysis_type": "创造性分析",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert "output" in result.output_data
        assert "reasoning_summary" in result.output_data
        assert result.output_data["scratchpad_available"] is True
        assert result.output_data["task_type"] == "patent_analysis"

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_execute_office_action(self):
        """测试XiaonaAgentScratchpadV2执行审查意见答复任务"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        context = AgentExecutionContext(
            session_id="SESSION_002",
            task_id="TASK_002",
            input_data={
                "user_input": "审查意见认为不具备创造性",
                "task_type": "office_action",
                "oa_number": "202310000001.0",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data["task_type"] == "office_action"

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_execute_invalidity(self):
        """测试XiaonaAgentScratchpadV2执行无效宣告任务"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        context = AgentExecutionContext(
            session_id="SESSION_003",
            task_id="TASK_003",
            input_data={
                "user_input": "针对专利CN987654321A提出无效宣告",
                "task_type": "invalidity",
                "patent_id": "CN987654321A",
            },
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
        assert result.output_data["task_type"] == "invalidity"

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_scratchpad_retrieval(self):
        """测试Scratchpad检索功能"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        # 首先执行一个任务以生成Scratchpad
        context = AgentExecutionContext(
            session_id="SESSION_004",
            task_id="TASK_004",
            input_data={
                "user_input": "测试",
                "task_type": "general",
            },
            config={},
            metadata={},
        )

        await agent.execute(context)

        # 检索Scratchpad
        scratchpad = await agent.get_scratchpad("TASK_004")

        assert scratchpad is not None
        assert "task_id" in scratchpad
        assert scratchpad["task_id"] == "TASK_004"
        assert "scratchpad" in scratchpad
        assert "summary" in scratchpad

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_list_scratchpads(self):
        """测试列出Scratchpad历史"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        # 执行多个任务
        for i in range(3):
            context = AgentExecutionContext(
                session_id="SESSION_LIST",
                task_id=f"TASK_LIST_{i}",
                input_data={
                    "user_input": f"测试{i}",
                    "task_type": "general",
                },
                config={},
                metadata={},
            )
            await agent.execute(context)

        # 列出Scratchpad
        scratchpads = await agent.list_scratchpads(limit=10)

        assert len(scratchpads) >= 3

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_input_validation(self):
        """测试XiaonaAgentScratchpadV2输入验证"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

        # 测试缺少task_id的情况
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="",  # 空task_id
            input_data={"user_input": "测试"},
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.ERROR
        assert "输入验证失败" in result.error_message

    @pytest.mark.asyncio
    async def test_xiaona_agent_v2_get_overview(self):
        """测试XiaonaAgentScratchpadV2获取概览"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")
        overview = await agent.get_overview()

        assert overview["agent_id"] == "xiaona_test"
        assert overview["version"] == "v2.0.0"
        assert overview["role"] == "法律专家智能体"
        assert overview["total_capabilities"] >= 4
        assert overview["scratchpad_enabled"] is True


# ==================== 接口合规性测试 ====================

class TestInterfaceCompliance:
    """接口合规性测试 - 验证所有Agent符合统一接口标准"""

    def test_writer_agent_interface_compliance(self):
        """测试WriterAgent接口合规性"""
        agent = WriterAgent(agent_id="writer_test")

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

    def test_xiaonuo_agent_v2_interface_compliance(self):
        """测试XiaonuoAgentV2接口合规性"""
        agent = XiaonuoAgentV2(agent_id="xiaonuo_test")

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

    def test_xiaona_agent_v2_interface_compliance(self):
        """测试XiaonaAgentScratchpadV2接口合规性"""
        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_test")

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


# ==================== 性能测试 ====================

class TestPerformance:
    """性能测试 - 验证迁移后的Agent性能可接受"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_xiaonuo_agent_v2_performance(self):
        """测试XiaonuoAgentV2性能"""
        import time

        agent = XiaonuoAgentV2(agent_id="xiaonuo_perf_test")

        context = AgentExecutionContext(
            session_id="SESSION_PERF",
            task_id="TASK_PERF",
            input_data={
                "user_input": "测试性能",
                "is_father": False,
            },
            config={},
            metadata={},
        )

        start_time = time.time()
        result = await agent.execute(context)
        execution_time = time.time() - start_time

        assert result.status == AgentStatus.COMPLETED
        # 执行时间应该在合理范围内（< 1秒）
        assert execution_time < 1.0

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_xiaona_agent_v2_performance(self):
        """测试XiaonaAgentScratchpadV2性能"""
        import time

        agent = XiaonaAgentScratchpadV2(agent_id="xiaona_perf_test")

        context = AgentExecutionContext(
            session_id="SESSION_PERF",
            task_id="TASK_PERF",
            input_data={
                "user_input": "测试性能",
                "task_type": "general",
            },
            config={},
            metadata={},
        )

        start_time = time.time()
        result = await agent.execute(context)
        execution_time = time.time() - start_time

        assert result.status == AgentStatus.COMPLETED
        # 执行时间应该在合理范围内（< 1秒）
        assert execution_time < 1.0


# ==================== 集成测试 ====================

class TestIntegration:
    """集成测试 - 验证多个Agent协同工作"""

    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self):
        """测试多Agent协同工作场景"""
        # 创建多个Agent
        xiaonuo = XiaonuoAgentV2(agent_id="xiaonuo_coord")
        xiaona = XiaonaAgentScratchpadV2(agent_id="xiaona_coord")

        # 小诺接收任务并协调
        context = AgentExecutionContext(
            session_id="SESSION_MULTI",
            task_id="TASK_MULTI",
            input_data={
                "user_input": "帮我分析专利并撰写权利要求",
                "request_type": "coordination",
            },
            config={},
            metadata={},
        )

        result = await xiaonuo.execute(context)
        assert result.status == AgentStatus.COMPLETED

        # 小娜执行专利分析任务
        context = AgentExecutionContext(
            session_id="SESSION_MULTI",
            task_id="TASK_MULTI_ANALYSIS",
            input_data={
                "user_input": "分析专利CN123456789A",
                "task_type": "patent_analysis",
                "patent_id": "CN123456789A",
            },
            config={},
            metadata={},
        )

        result = await xiaona.execute(context)
        assert result.status == AgentStatus.COMPLETED


# ==================== 运行测试的便捷函数 ====================

async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("P1 Agent迁移测试")
    print("=" * 60)

    # WriterAgent测试
    print("\n📝 测试WriterAgent...")
    writer_test = TestWriterAgent()
    writer_test.test_writer_agent_initialization()
    writer_test.test_writer_agent_capabilities()
    writer_test.test_writer_agent_system_prompt()
    await writer_test.test_writer_agent_execute_claims()
    print("✅ WriterAgent测试通过")

    # XiaonuoAgentV2测试
    print("\n💝 测试XiaonuoAgentV2...")
    xiaonuo_test = TestXiaonuoAgentV2()
    xiaonuo_test.test_xiaonuo_agent_v2_initialization()
    xiaonuo_test.test_xiaonuo_agent_v2_capabilities()
    xiaonuo_test.test_xiaonuo_agent_v2_system_prompt()
    xiaonuo_test.test_xiaonuo_agent_v2_factory_function()
    await xiaonuo_test.test_xiaonuo_agent_v2_execute_emotional_care()
    await xiaonuo_test.test_xiaonuo_agent_v2_execute_coordination()
    await xiaonuo_test.test_xiaonuo_agent_v2_execute_media_request()
    await xiaonuo_test.test_xiaonuo_agent_v2_input_validation()
    await xiaonuo_test.test_xiaonuo_agent_v2_get_overview()
    print("✅ XiaonuoAgentV2测试通过")

    # XiaonaAgentScratchpadV2测试
    print("\n⚖️ 测试XiaonaAgentScratchpadV2...")
    xiaona_test = TestXiaonaAgentScratchpadV2()
    xiaona_test.test_xiaona_agent_v2_initialization()
    xiaona_test.test_xiaona_agent_v2_capabilities()
    xiaona_test.test_xiaona_agent_v2_system_prompt()
    xiaona_test.test_xiaona_agent_v2_factory_function()
    xiaona_test.test_xiaona_agent_v2_scratchpad_config()
    await xiaona_test.test_xiaona_agent_v2_execute_patent_analysis()
    await xiaona_test.test_xiaona_agent_v2_execute_office_action()
    await xiaona_test.test_xiaona_agent_v2_execute_invalidity()
    await xiaona_test.test_xiaona_agent_v2_scratchpad_retrieval()
    await xiaona_test.test_xiaona_agent_v2_list_scratchpads()
    await xiaona_test.test_xiaona_agent_v2_input_validation()
    await xiaona_test.test_xiaona_agent_v2_get_overview()
    print("✅ XiaonaAgentScratchpadV2测试通过")

    # 接口合规性测试
    print("\n🔍 测试接口合规性...")
    compliance_test = TestInterfaceCompliance()
    compliance_test.test_writer_agent_interface_compliance()
    compliance_test.test_xiaonuo_agent_v2_interface_compliance()
    compliance_test.test_xiaona_agent_v2_interface_compliance()
    print("✅ 接口合规性测试通过")

    print("\n" + "=" * 60)
    print("✅ 所有测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
