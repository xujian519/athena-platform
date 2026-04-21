# Agent接口实现指南

> **版本**: v1.0
> **日期**: 2026-04-21
> **目标受众**: Agent开发者

---

## 📋 目录

1. [概述](#概述)
2. [准备工作](#准备工作)
3. [实现基础Agent](#实现基础agent)
4. [实现高级功能](#实现高级功能)
5. [测试与验证](#测试与验证)
6. [部署与注册](#部署与注册)
7. [常见问题](#常见问题)

---

## 概述

### 目标

本指南将帮助你：
- ✅ 从零开始实现一个符合标准的Agent
- ✅ 理解Agent的生命周期和接口
- ✅ 掌握Agent开发的最佳实践
- ✅ 编写高质量的Agent代码

### 前置知识

在开始之前，你应该：
- 熟悉Python 3.11+语法
- 了解异步编程（async/await）
- 了解Athena平台的基本架构
- 阅读过《统一Agent接口标准》

### 开发环境

```bash
# 确保Python版本
python3 --version  # 应该是 3.11+

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v
```

---

## 准备工作

### 1. 理解Agent架构

**Agent的三大核心**:

```
1. 基类（BaseXiaonaComponent）
   └─ 定义统一接口和生命周期

2. 能力（AgentCapability）
   └─ 描述Agent能做什么

3. 执行上下文（AgentExecutionContext）
   └─ 传递输入数据和配置
```

### 2. 选择Agent类型

**常见的Agent类型**:

| 类型 | 职责 | 示例 |
|------|------|------|
| **检索型** | 检索专利、论文、案例 | RetrieverAgent |
| **分析型** | 分析专利、法律问题 | AnalyzerAgent |
| **撰写型** | 撰写文档、报告 | WriterAgent |
| **协调型** | 协调其他Agent | XiaonuoAgent |

### 3. 设计Agent能力

**能力设计原则**:
- ✅ 单一职责：一个能力做一件事
- ✅ 清晰命名：使用动词+名词
- ✅ 合理估算：基于实际测试预估时间

**示例**:
```python
AgentCapability(
    name="patent_search",  # 清晰：专利检索
    description="在多个专利数据库中检索相关专利",  # 详细描述
    input_types=["查询关键词", "技术领域"],  # 明确输入
    output_types=["专利列表", "检索统计"],  # 明确输出
    estimated_time=15.0,  # 基于测试的估算
)
```

---

## 实现基础Agent

### Step 1: 创建Agent类

**文件**: `core/agents/my_agent.py`

```python
"""
我的Agent

负责XXX任务的Agent。
"""

from typing import Any, Dict, Optional
import logging

from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

logger = logging.getLogger(__name__)


class MyAgent(BaseXiaonaComponent):
    """
    我的Agent

    负责XXX任务的Agent。

    Attributes:
        config: 配置参数
    """

    def _initialize(self) -> None:
        """
        Agent初始化钩子

        在此方法中：
        1. 注册能力
        2. 初始化LLM客户端
        3. 加载提示词
        4. 初始化工具
        """
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="my_capability",
                description="我的能力描述",
                input_types=["输入类型"],
                output_types=["输出类型"],
                estimated_time=5.0,
            ),
        ])

        # 初始化LLM
        from core.llm.unified_llm_manager import UnifiedLLMManager
        self.llm_manager = UnifiedLLMManager()

        # 获取工具注册表
        from core.tools.unified_registry import get_unified_registry
        self.tool_registry = get_unified_registry()

        self.logger.info(f"MyAgent初始化完成: {self.agent_id}")

    def get_system_prompt(self) -> str:
        """
        获取系统提示词

        Returns:
            系统提示词字符串
        """
        return """你是MyAgent，负责XXX任务。

你的核心能力：
1. 能力1描述
2. 能力2描述

工作原则：
- 原则1
- 原则2

输出格式：
- 输出1
- 输出2
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行Agent任务

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        try:
            # 验证输入
            if not self.validate_input(context):
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message="输入验证失败",
                )

            # 获取输入
            user_input = context.input_data.get("user_input", "")

            # 执行任务
            result = await self._do_work(user_input, context.config)

            # 返回成功结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                metadata={
                    "input_length": len(user_input),
                },
            )

        except Exception as e:
            # 返回错误结果
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                output_data=None,
                error_message=str(e),
            )

    async def _do_work(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        实际的工作逻辑

        Args:
            user_input: 用户输入
            config: 配置参数

        Returns:
            工作结果
        """
        # 实现你的具体逻辑
        result = {"output": "处理结果"}

        return result
```

### Step 2: 实现输入验证

```python
def validate_input(self, context: AgentExecutionContext) -> bool:
    """
    验证输入数据

    Args:
        context: 执行上下文

    Returns:
        验证是否通过
    """
    # 基础验证
    if not context.session_id:
        self.logger.error("缺少session_id")
        return False

    if not context.task_id:
        self.logger.error("缺少task_id")
        return False

    # 业务验证
    user_input = context.input_data.get("user_input", "")
    if not user_input:
        self.logger.error("缺少user_input")
        return False

    if len(user_input) > 10000:
        self.logger.error(f"输入过长: {len(user_input)}字符")
        return False

    return True
```

### Step 3: 测试基础Agent

**文件**: `tests/agents/test_my_agent.py`

```python
import pytest
from core.agents.my_agent import MyAgent
from core.agents.xiaona.base_component import (
    AgentExecutionContext,
    AgentStatus,
)

class TestMyAgent:
    """MyAgent测试"""

    @pytest.mark.asyncio
    async def test_basic_execution(self):
        """测试基本执行"""
        agent = MyAgent(agent_id="test_my_agent")

        context = AgentExecutionContext(
            session_id="SESSION_001",
            task_id="TASK_001",
            input_data={"user_input": "测试输入"},
            config={},
            metadata={},
        )

        result = await agent.execute(context)

        assert result.status == AgentStatus.COMPLETED
        assert result.output_data is not None
```

**运行测试**:
```bash
pytest tests/agents/test_my_agent.py -v
```

---

## 实现高级功能

### 1. 使用LLM

```python
async def _do_work(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """实际的工作逻辑"""
    # 构建提示词
    prompt = f"""请处理以下输入：

输入：{user_input}

请返回JSON格式：
{{
    "result": "处理结果"
}}
"""

    # 调用LLM
    response = await self.llm_manager.generate(
        prompt=prompt,
        system_prompt=self.get_system_prompt(),
        model=config.get("model", "kimi-k2.5"),
    )

    # 解析结果
    import json
    result = json.loads(response)

    return result
```

### 2. 使用工具

```python
async def _do_work(self, user_input: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """实际的工作逻辑"""
    # 获取工具
    tool = self.tool_registry.get("patent_search")

    if not tool:
        return {"error": "工具不可用"}

    # 调用工具
    result = await tool.function(
        query=user_input,
        database=config.get("database", "cnipa"),
        limit=config.get("limit", 50),
    )

    return result
```

### 3. 处理前序Agent的结果

```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    """执行Agent任务"""
    try:
        # 获取前序Agent的结果
        previous_results = context.input_data.get("previous_results", {})

        # 使用前序结果
        if "retriever" in previous_results:
            patents = previous_results["retriever"]["patents"]
            # 使用检索结果
            result = await self._analyze_patents(patents)
        else:
            # 不使用前序结果
            result = await self._do_work(context.input_data["user_input"], context.config)

        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data=result,
        )

    except Exception as e:
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            error_message=str(e),
        )
```

### 4. 实现重试机制

```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    """执行Agent任务"""
    max_retries = context.config.get("max_retries", 3)

    for attempt in range(max_retries):
        try:
            result = await self._do_work_with_retry(context)

            if result.status == AgentStatus.COMPLETED:
                return result
            else:
                # 判断是否可以重试
                can_retry = result.metadata.get("can_retry", False)
                if not can_retry or attempt == max_retries - 1:
                    return result

        except Exception as e:
            if attempt == max_retries - 1:
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message=f"执行失败（已重试{max_retries}次）: {str(e)}",
                )
```

### 5. 实现进度报告

```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    """执行Agent任务"""
    steps = [
        ("步骤1", self._step1),
        ("步骤2", self._step2),
        ("步骤3", self._step3),
    ]

    results = {}

    for step_name, step_func in steps:
        self.logger.info(f"开始{step_name}")
        try:
            result = await step_func(context)
            results[step_name] = result
            self.logger.info(f"完成{step_name}")
        except Exception as e:
            self.logger.error(f"{step_name}失败: {e}")
            results[step_name] = {"error": str(e)}

    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.COMPLETED,
        output_data={"steps": results},
    )
```

---

## 测试与验证

### 1. 单元测试

```python
class TestMyAgentUnit:
    """单元测试"""

    @pytest.mark.asyncio
    async def test_initialize(self):
        """测试初始化"""
        agent = MyAgent(agent_id="test")
        assert agent.agent_id == "test"
        assert len(agent.get_capabilities()) >= 1

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """测试成功执行"""
        agent = MyAgent(agent_id="test")

        # Mock依赖
        with patch.object(agent, 'llm_manager') as mock_llm:
            mock_llm.generate = AsyncMock(return_value='{"result": "test"}')

            context = AgentExecutionContext(
                session_id="SESSION_001",
                task_id="TASK_001",
                input_data={"user_input": "test"},
                config={},
                metadata={},
            )

            result = await agent.execute(context)

            assert result.status == AgentStatus.COMPLETED
```

### 2. 集成测试

```python
class TestMyAgentIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_with_llm(self):
        """测试与LLM的集成"""
        from core.llm.unified_llm_manager import UnifiedLLMManager

        agent = MyAgent(agent_id="test")

        # 验证LLM Manager已初始化
        assert agent.llm_manager is not None
        assert isinstance(agent.llm_manager, UnifiedLLMManager)

    @pytest.mark.asyncio
    async def test_with_tool_registry(self):
        """测试与工具注册表的集成"""
        agent = MyAgent(agent_id="test")

        # 验证工具注册表已初始化
        assert agent.tool_registry is not None
```

### 3. 接口合规性测试

```python
from tests.agents.test_interface_compliance_simple import InterfaceComplianceChecker

def test_compliance():
    """测试接口合规性"""
    agent = MyAgent(agent_id="test")

    checker = InterfaceComplianceChecker()
    results = checker.check_agent_instance(agent)

    # 打印结果
    print("\n=== 接口合规性检查 ===")
    for result in results["passed"]:
        print(f"✅ {result['check']}: {result['message']}")
    for result in results["warnings"]:
        print(f"⚠️  {result['check']}: {result['message']}")
    for result in results["failed"]:
        print(f"❌ {result['check']}: {result['message']}")

    # 断言：不应该有失败项
    assert len(results["failed"]) == 0
```

### 4. 运行测试

```bash
# 运行所有测试
pytest tests/agents/test_my_agent.py -v

# 运行特定测试
pytest tests/agents/test_my_agent.py::TestMyAgentUnit::test_initialize -v

# 运行并生成覆盖率报告
pytest tests/agents/test_my_agent.py --cov=core.agents.my_agent --cov-report=html
```

---

## 部署与注册

### 1. 注册Agent

```python
from core.orchestration.agent_registry import get_agent_registry

# 获取注册表
registry = get_agent_registry()

# 创建Agent
agent = MyAgent(agent_id="my_agent_001")

# 注册Agent
registry.register(agent, phase=1)

print(f"Agent {agent.agent_id} 注册成功")
```

### 2. 在工作流中使用

```python
from core.orchestration.workflow_builder import WorkflowBuilder
from core.orchestration.agent_registry import get_agent_registry
from core.orchestration.scenario_detector import ScenarioDetector

async def main():
    # 注册Agent
    registry = get_agent_registry()
    agent = MyAgent(agent_id="my_agent_001")
    registry.register(agent, phase=1)

    # 构建工作流
    builder = WorkflowBuilder(
        agent_registry=registry,
        scenario_detector=ScenarioDetector(),
    )

    # 构建工作流
    workflow = builder.build_workflow(
        scenario=Scenario.CUSTOM_TASK,
        user_input="执行任务",
        session_id="SESSION_001",
    )

    # 执行工作流
    for step in workflow:
        agent = registry.get_agent(step.agent_id)
        result = await agent._execute_with_monitoring(step.context)
        print(f"步骤 {step.step_id}: {result.status}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 常见问题

### Q1: 如何调试Agent？

**A**: 使用日志和断点：

```python
# 使用日志
self.logger.info(f"调试信息: {variable}")
self.logger.debug(f"输入数据: {context.input_data}")

# 使用断点
import pdb; pdb.set_trace()
```

### Q2: 如何测试异步方法？

**A**: 使用pytest-asyncio：

```python
@pytest.mark.asyncio
async def test_async_method():
    result = await agent.execute(context)
    assert result.status == AgentStatus.COMPLETED
```

### Q3: 如何处理长时间运行的任务？

**A**: 使用后台任务和进度报告：

```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    # 创建后台任务
    task = asyncio.create_task(self._long_running_task())

    # 定期报告进度
    while not task.done():
        await asyncio.sleep(1)
        self.logger.info("任务进行中...")

    result = await task
    return result
```

### Q4: 如何优化性能？

**A**:
- ✅ 使用异步操作
- ✅ 并行执行独立任务
- ✅ 缓存LLM响应
- ✅ 使用连接池

---

## 附录

### A. 完整示例

参见：`examples/agents/example_agent.py`

### B. 测试示例

参见：`tests/agents/test_retriever_agent_extended.py`

### C. 相关文档

- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](../design/AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [Agent接口合规性检查清单](AGENT_INTERFACE_COMPLIANCE_CHECKLIST.md)
- [快速开始指南](QUICK_START_AGENT_DEVELOPMENT.md)

---

**祝你开发顺利！** 🎉

如有问题，请查阅完整文档或提交Issue。
