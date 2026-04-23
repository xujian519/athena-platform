"""
练习3：测试Agent
===============

目标：为Agent编写完整的测试套件

任务要求：
1. 编写单元测试
2. 使用Mock模拟LLM响应
3. 测试正常流程和异常流程
4. 达到80%以上覆盖率

测试要求：
- 使用pytest和pytest-asyncio
- 使用unittest.mock模拟外部依赖
- 测试所有public方法
- 测试错误处理
"""


import pytest

from core.framework.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)

# TODO: 导入你要测试的Agent
# from core.framework.agents.my_agent import MyAgent


class TestMyAgent:
    """
    TODO: Agent测试套件

    替换MyAgent为你创建的Agent类名
    """

    @pytest.fixture
    def agent(self):
        """创建Agent实例"""
        # TODO: 替换为你的Agent类
        # return MyAgent(agent_id="test_agent")
        pass

    @pytest.fixture
    def basic_context(self):
        """创建基本执行上下文"""
        return AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"test": "data"},
            config={},
            metadata={},
        )

    # ==================== 初始化测试 ====================

    def test_agent_initialization(self, agent):
        """
        TODO: 测试Agent初始化

        验证：
        - agent_id正确设置
        - 能力已注册
        - LLM Manager已初始化（如果使用）
        """
        assert agent.agent_id == "test_agent"
        assert len(agent.get_capabilities()) > 0
        # TODO: 添加更多断言

    def test_capabilities_registration(self, agent):
        """
        TODO: 测试能力注册

        验证：
        - 能力数量正确
        - 能力名称正确
        - 能力描述完整
        """
        capabilities = agent.get_capabilities()

        # 检查至少有一个能力
        assert len(capabilities) >= 1

        # TODO: 检查具体能力
        # capability_names = [c.name for c in capabilities]
        # assert "my_capability" in capability_names

    # ==================== execute方法测试 ====================

    @pytest.mark.asyncio
    async def test_execute_success(self, agent, basic_context):
        """
        TODO: 测试正常执行

        模拟LLM响应，验证：
        - 返回COMPLETED状态
        - output_data不为空
        - metadata正确设置
        """
        # TODO: Mock LLM响应（如果使用LLM）
        # with patch.object(agent, 'llm') as mock_llm:
        #     mock_llm.generate = AsyncMock(return_value="Mocked response")
        #
        #     result = await agent.execute(basic_context)
        #
        #     assert result.status == AgentStatus.COMPLETED
        #     assert result.output_data is not None
        pass

    @pytest.mark.asyncio
    async def test_execute_with_missing_input(self, agent):
        """
        TODO: 测试缺少必需输入

        验证：
        - 返回ERROR状态
        - error_message描述问题
        """
        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_002",
            input_data={},  # 空输入
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.ERROR
        assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_execute_with_llm_error(self, agent, basic_context):
        """
        TODO: 测试LLM调用失败

        模拟LLM抛出异常，验证：
        - 异常被捕获
        - 返回ERROR状态
        - 错误被记录
        """
        # TODO: Mock LLM抛出异常
        # with patch.object(agent.llm, 'generate', side_effect=Exception("LLM错误")):
        #     result = await agent.execute(basic_context)
        #
        #     assert result.status == AgentStatus.ERROR
        pass

    # ==================== 辅助方法测试 ====================

    def test_get_system_prompt(self, agent):
        """
        TODO: 测试系统提示词

        验证：
        - 返回字符串
        - 包含关键信息
        """
        prompt = agent.get_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # TODO: 检查提示词内容
        # assert "你的角色" in prompt or "你是一个" in prompt

    def test_validate_input_valid(self, agent, basic_context):
        """
        TODO: 测试有效输入验证

        验证有效输入通过验证
        """
        # TODO: 根据你的Agent调整输入数据
        is_valid = agent.validate_input(basic_context)
        assert is_valid is True

    def test_validate_input_invalid_session(self, agent):
        """
        TODO: 测试无效session_id

        验证缺少session_id被拒绝
        """
        context = AgentExecutionContext(
            session_id="",  # 空session_id
            task_id="TASK_001",
            input_data={},
            config={},
            metadata={},
        )

        is_valid = agent.validate_input(context)
        assert is_valid is False

    # ==================== get_info方法测试 ====================

    def test_get_info(self, agent):
        """
        TODO: 测试get_info方法

        验证返回的信息包含：
        - agent_id
        - agent_type
        - status
        - capabilities
        """
        info = agent.get_info()

        assert "agent_id" in info
        assert "agent_type" in info
        assert "status" in info
        assert "capabilities" in info
        assert isinstance(info["capabilities"], list)

    # ==================== 性能测试 ====================

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_execute_performance(self, agent, basic_context):
        """
        TODO: 测试执行性能

        验证执行时间在合理范围内
        """
        import time

        start_time = time.time()

        # TODO: Mock LLM以避免实际调用
        # with patch.object(agent.llm, 'generate', new_callable=AsyncMock) as mock_llm:
        #     mock_llm.return_value = "Response"
        #     result = await agent.execute(basic_context)

        end_time = time.time()
        end_time - start_time

        # TODO: 根据你的Agent调整性能期望
        # assert execution_time < 10.0  # 应该在10秒内完成


# ==================== 接口合规性测试 ====================

def test_interface_compliance():
    """
    TODO: 接口合规性检查

    使用InterfaceComplianceChecker验证Agent符合统一接口标准
    """

    # TODO: 创建你的Agent实例
    # agent = MyAgent(agent_id="compliance_test")

    # checker = InterfaceComplianceChecker()
    # results = checker.check_agent_instance(agent)

    # 打印结果
    # print("\n=== 接口合规性检查 ===")
    # for result in results["passed"]:
    #     print(f"✅ {result['check']}: {result['message']}")
    # for result in results["warnings"]:
    #     print(f"⚠️  {result['check']}: {result['message']}")
    # for result in results["failed"]:
    #     print(f"❌ {result['check']}: {result['message']}")

    # 断言：不应该有失败项
    # assert len(results["failed"]) == 0, f"合规性检查失败: {results['failed']}"
    pass


# ==================== 运行测试 ====================

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
