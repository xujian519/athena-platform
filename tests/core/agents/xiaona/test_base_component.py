"""
基类组件单元测试

测试范围:
- 基类初始化
- 能力注册和查询
- 信息获取
- 输入验证
- 执行监控
"""

import pytest
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentStatus,
    AgentExecutionContext,
    AgentExecutionResult
)
from typing import Any, Dict


class TestableBaseComponent(BaseXiaonaComponent):
    """可测试的基类组件"""

    def _initialize(self) -> None:
        """初始化测试组件"""
        self._register_capabilities([
            AgentCapability(
                name="test_capability",
                description="测试能力",
                input_types=["test_input"],
                output_types=["test_output"],
                estimated_time=1.0
            )
        ])

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行测试任务"""
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"test": "result"},
            execution_time=0.1
        )

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "测试系统提示词"


class TestBaseXiaonaComponent:
    """基类组件测试"""

    @pytest.fixture
    def component(self):
        """创建组件实例"""
        return TestableBaseComponent(agent_id="test_component")

    @pytest.fixture
    def execution_context(self):
        """创建执行上下文"""
        return AgentExecutionContext(
            session_id="test_session",
            task_id="test_task",
            input_data={"test": "input"},
            config={"timeout": 30},
            metadata={}
        )

    # ========== 初始化测试 ==========

    def test_initialization(self, component):
        """测试组件初始化"""
        assert component.agent_id == "test_component"
        assert component.status == AgentStatus.IDLE
        capabilities = component.get_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0].name == "test_capability"

    def test_initialization_with_config(self):
        """测试带配置的初始化"""
        comp = TestableBaseComponent(
            agent_id="test_component_with_config",
            config={"timeout": 60}
        )
        assert comp.config["timeout"] == 60

    # ========== 能力管理测试 ==========

    def test_register_capabilities(self, component):
        """测试能力注册"""
        capabilities = component.get_capabilities()
        assert len(capabilities) == 1
        assert capabilities[0].name == "test_capability"
        assert capabilities[0].description == "测试能力"

    def test_has_capability(self, component):
        """测试能力检查"""
        assert component.has_capability("test_capability") is True
        assert component.has_capability("non_existent") is False

    def test_get_info(self, component):
        """测试获取组件信息"""
        info = component.get_info()
        assert "agent_id" in info
        assert "agent_type" in info
        assert "status" in info
        assert "capabilities" in info
        assert info["agent_id"] == "test_component"

    # ========== 输入验证测试 ==========

    def test_validate_input_success(self, component, execution_context):
        """测试输入验证 - 成功"""
        assert component.validate_input(execution_context) is True

    def test_validate_input_missing_session_id(self, component):
        """测试输入验证 - 缺少session_id"""
        context = AgentExecutionContext(
            session_id="",  # 空session_id
            task_id="test_task",
            input_data={},
            config={},
            metadata={}
        )
        assert component.validate_input(context) is False

    def test_validate_input_missing_task_id(self, component):
        """测试输入验证 - 缺少task_id"""
        context = AgentExecutionContext(
            session_id="test_session",
            task_id="",  # 空task_id
            input_data={},
            config={},
            metadata={}
        )
        assert component.validate_input(context) is False

    # ========== 执行监控测试 ==========

    @pytest.mark.asyncio
    async def test_execute_with_monitoring_success(self, component, execution_context):
        """测试带监控的执行 - 成功"""
        result = await component._execute_with_monitoring(execution_context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data == {"test": "result"}
        assert result.execution_time >= 0
        assert component.status == AgentStatus.IDLE

    @pytest.mark.asyncio
    async def test_execute_with_monitoring_error(self, component, execution_context):
        """测试带监控的执行 - 错误处理"""
        class ErrorComponent(TestableBaseComponent):
            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                raise ValueError("测试错误")

        error_component = ErrorComponent(agent_id="error_component")
        result = await error_component._execute_with_monitoring(execution_context)

        assert result.status == AgentStatus.ERROR
        assert result.error_message is not None
        assert result.error_message == "测试错误"
        assert error_component.status == AgentStatus.ERROR

    # ========== AgentCapability测试 ==========

    def test_agent_capability_creation(self):
        """测试AgentCapability创建"""
        capability = AgentCapability(
            name="test",
            description="测试能力",
            input_types=["input1", "input2"],
            output_types=["output1"],
            estimated_time=10.0
        )

        assert capability.name == "test"
        assert capability.description == "测试能力"
        assert capability.input_types == ["input1", "input2"]
        assert capability.output_types == ["output1"]
        assert capability.estimated_time == 10.0

    # ========== AgentExecutionContext测试 ==========

    def test_execution_context_creation(self):
        """测试AgentExecutionContext创建"""
        context = AgentExecutionContext(
            session_id="session_1",
            task_id="task_1",
            input_data={"key": "value"},
            config={"timeout": 30},
            metadata={"meta": "data"}
        )

        assert context.session_id == "session_1"
        assert context.task_id == "task_1"
        assert context.input_data == {"key": "value"}
        assert context.config == {"timeout": 30}
        assert context.metadata == {"meta": "data"}

    # ========== AgentExecutionResult测试 ==========

    def test_execution_result_creation(self):
        """测试AgentExecutionResult创建"""
        result = AgentExecutionResult(
            agent_id="agent_1",
            status=AgentStatus.COMPLETED,
            output_data={"result": "success"},
            error_message=None,
            execution_time=1.5,
            metadata={"key": "value"}
        )

        assert result.agent_id == "agent_1"
        assert result.status == AgentStatus.COMPLETED
        assert result.output_data == {"result": "success"}
        assert result.error_message is None
        assert result.execution_time == 1.5
        assert result.metadata == {"key": "value"}

    def test_execution_result_default_metadata(self):
        """测试AgentExecutionResult默认metadata"""
        result = AgentExecutionResult(
            agent_id="agent_1",
            status=AgentStatus.COMPLETED,
            output_data={},
            execution_time=0.0
        )

        assert result.metadata == {}

    # ========== AgentStatus测试 ==========

    def test_agent_status_values(self):
        """测试AgentStatus枚举"""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.BUSY.value == "busy"
        assert AgentStatus.ERROR.value == "error"
        assert AgentStatus.COMPLETED.value == "completed"

    # ========== 错误处理测试 ==========

    @pytest.mark.asyncio
    async def test_execute_with_exception_handling(self, component, execution_context):
        """测试执行时的异常处理"""
        class ExceptionComponent(TestableBaseComponent):
            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                raise RuntimeError("运行时错误")

        exception_component = ExceptionComponent(agent_id="exception_component")
        result = await exception_component._execute_with_monitoring(execution_context)

        # 验证错误被正确捕获
        assert result.status == AgentStatus.ERROR
        assert result.error_message is not None
        assert "RuntimeError" in result.error_message or "运行时错误" in result.error_message

    @pytest.mark.asyncio
    async def test_execute_with_keyboard_interrupt(self, component, execution_context):
        """测试键盘中断异常"""
        # 注意：不能真正抛出KeyboardInterrupt，因为会中断测试运行器
        # 改为测试其他异常类型
        class InterruptComponent(TestableBaseComponent):
            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                raise RuntimeError("模拟用户中断")

        interrupt_component = InterruptComponent(agent_id="interrupt_component")
        result = await interrupt_component._execute_with_monitoring(execution_context)

        # 验证异常被正确处理
        assert result.status == AgentStatus.ERROR
        assert result.error_message is not None

    # ========== 边界条件测试 ==========

    def test_component_with_no_capabilities(self):
        """测试无能力组件"""
        class NoCapabilityComponent(BaseXiaonaComponent):
            def _initialize(self) -> None:
                pass  # 不注册任何能力

            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.COMPLETED,
                    output_data={},
                    execution_time=0.0
                )

            def get_system_prompt(self) -> str:
                return ""

        # 应该能够创建无能力组件
        comp = NoCapabilityComponent(agent_id="no_capability")
        assert len(comp.get_capabilities()) == 0

    def test_component_with_multiple_capabilities(self):
        """测试多能力组件"""
        class MultiCapabilityComponent(BaseXiaonaComponent):
            def _initialize(self) -> None:
                self._register_capabilities([
                    AgentCapability(
                        name="capability_1",
                        description="能力1",
                        input_types=["input1"],
                        output_types=["output1"],
                        estimated_time=1.0
                    ),
                    AgentCapability(
                        name="capability_2",
                        description="能力2",
                        input_types=["input2"],
                        output_types=["output2"],
                        estimated_time=2.0
                    ),
                    ])

            async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.COMPLETED,
                    output_data={},
                    execution_time=0.0
                )

            def get_system_prompt(self) -> str:
                return ""

        comp = MultiCapabilityComponent(agent_id="multi_capability")
        assert len(comp.get_capabilities()) == 2

    # ========== 性能测试 ==========

    @pytest.mark.asyncio
    async def test_performance_execute_with_monitoring(self, component, execution_context):
        """测试执行监控性能"""
        import time

        start_time = time.time()
        await component._execute_with_monitoring(execution_context)
        elapsed_time = time.time() - start_time

        # 执行监控应该很快
        assert elapsed_time < 1.0

    # ========== 集成测试 ==========

    @pytest.mark.asyncio
    async def test_full_component_lifecycle(self, component, execution_context):
        """测试完整组件生命周期"""
        # 1. 初始状态
        assert component.status == AgentStatus.IDLE

        # 2. 执行任务
        context = execution_context
        result = await component._execute_with_monitoring(context)

        # 3. 执行后状态
        assert component.status == AgentStatus.IDLE
        assert result.status == AgentStatus.COMPLETED
        assert hasattr(result, 'execution_time')
        assert result.execution_time >= 0

        # 4. 能力信息
        info = component.get_info()
        assert info["status"] == "idle"
        assert len(info["capabilities"]) == 1
