# Agent开发快速开始指南

> **适用人群**: Agent开发者
> **前置知识**: Python 3.11+, 异步编程
> **预计时间**: 5-10分钟

---

## 🚀 5分钟快速开始

### Step 1: 创建Agent类（1分钟）

```python
from core.agents.xiaona.base_component import (
    BaseXiaonaComponent,
    AgentCapability,
    AgentExecutionContext,
    AgentExecutionResult,
    AgentStatus,
)

class MyAgent(BaseXiaonaComponent):
    """我的第一个Agent"""

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="my_capability",
                description="我的能力描述",
                input_types=["文本"],
                output_types=["结果"],
                estimated_time=5.0,
            ),
        ])

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return "你是一个专业的Agent..."

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        try:
            # 处理输入
            user_input = context.input_data.get("user_input", "")
            result = await self._process(user_input)

            # 返回成功结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data={"result": result},
            )
        except Exception as e:
            # 返回错误结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
            )
```

### Step 2: 使用Agent（1分钟）

```python
import asyncio

async def main():
    # 创建Agent
    agent = MyAgent(agent_id="my_agent_001")

    # 创建执行上下文
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "user_input": "Hello, Agent!",
        },
        config={},
        metadata={},
    )

    # 执行任务
    result = await agent._execute_with_monitoring(context)

    # 查看结果
    if result.status == AgentStatus.COMPLETED:
        print(f"✅ 成功: {result.output_data}")
    else:
        print(f"❌ 失败: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: 运行测试（1分钟）

```bash
# 创建测试文件
cat > tests/agents/test_my_agent.py << 'EOF'
import pytest
from core.agents.my_agent import MyAgent
from core.agents.xiaona.base_component import AgentExecutionContext, AgentStatus

@pytest.mark.asyncio
async def test_execute_success():
    """测试正常执行"""
    agent = MyAgent(agent_id="test_agent")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"user_input": "test"},
        config={},
        metadata={},
    )

    result = await agent.execute(context)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data is not None
EOF

# 运行测试
pytest tests/agents/test_my_agent.py -v
```

### Step 4: 注册Agent（1分钟）

```python
from core.orchestration.agent_registry import get_agent_registry

# 获取注册表
registry = get_agent_registry()

# 创建Agent
agent = MyAgent(agent_id="my_agent_001")

# 注册Agent
registry.register(agent, phase=1)

# 查询Agent
agent = registry.get_agent("my_agent_001")
print(f"Agent信息: {agent.get_info()}")
```

### Step 5: 完成配置（1分钟）

```bash
# 创建README.md
cat > README.md << 'EOF'
# MyAgent

我的第一个Agent。

## 快速开始

```bash
# 创建Agent
agent = MyAgent(agent_id="my_agent_001")

# 执行任务
result = await agent._execute_with_monitoring(context)
```

## 测试

```bash
pytest tests/agents/test_my_agent.py -v
```
EOF
```

**恭喜！** 🎉 你已经创建了一个完整的Agent！

---

## 📚 10分钟完整教程

### Part 1: 理解核心概念（3分钟）

#### 1.1 Agent生命周期

```
初始化（__init__）
    ↓
初始化钩子（_initialize）
    ├─ 注册能力
    ├─ 初始化LLM
    └─ 加载配置
    ↓
执行（execute）
    ├─ 验证输入
    ├─ 处理任务
    └─ 返回结果
```

#### 1.2 核心组件

| 组件 | 说明 | 必需 |
|------|------|------|
| `_initialize()` | 初始化钩子 | ✅ |
| `execute()` | 执行任务 | ✅ |
| `get_system_prompt()` | 系统提示词 | ✅ |
| `get_capabilities()` | 能力列表 | ✅ 自动 |
| `validate_input()` | 输入验证 | ⚠️ 推荐 |

#### 1.3 数据类

```python
# 执行上下文（输入）
context = AgentExecutionContext(
    session_id="SESSION_001",      # 会话ID
    task_id="TASK_001",             # 任务ID
    input_data={...},               # 输入数据
    config={...},                   # 配置参数
    metadata={...},                 # 元数据
)

# 执行结果（输出）
result = AgentExecutionResult(
    agent_id="my_agent",            # Agent ID
    status=AgentStatus.COMPLETED,   # 执行状态
    output_data={...},              # 输出数据
    execution_time=5.2,             # 执行时间
)
```

---

### Part 2: 创建完整的Agent（5分钟）

#### 2.1 定义Agent类

```python
from typing import Any, Dict
import logging

class TextAnalysisAgent(BaseXiaonaComponent):
    """
    文本分析Agent

    提供文本分析、情感分析、关键词提取等功能。
    """

    def _initialize(self) -> None:
        """初始化Agent"""
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="sentiment_analysis",
                description="情感分析",
                input_types=["文本"],
                output_types=["情感分类", "置信度"],
                estimated_time=3.0,
            ),
            AgentCapability(
                name="keyword_extraction",
                description="关键词提取",
                input_types=["文本"],
                output_types=["关键词列表"],
                estimated_time=2.0,
            ),
        ])

        # 初始化LLM
        from core.llm.unified_llm_manager import UnifiedLLMManager
        self.llm = UnifiedLLMManager()

        self.logger.info(f"文本分析Agent初始化完成: {self.agent_id}")
```

#### 2.2 实现核心方法

```python
    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是文本分析专家。

核心能力：
1. 情感分析：判断文本的情感倾向（正面/负面/中性）
2. 关键词提取：提取文本的核心关键词

工作原则：
- 准确性优先
- 提供置信度评分
- 返回结构化结果
"""

    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """执行任务"""
        try:
            # 获取操作类型
            operation = context.input_data.get("operation", "sentiment_analysis")
            text = context.input_data.get("text", "")

            # 根据操作类型执行
            if operation == "sentiment_analysis":
                result = await self._sentiment_analysis(text)
            elif operation == "keyword_extraction":
                result = await self._keyword_extraction(text)
            else:
                raise ValueError(f"未知的操作: {operation}")

            # 返回成功结果
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.COMPLETED,
                output_data=result,
                metadata={
                    "operation": operation,
                    "text_length": len(text),
                },
            )

        except Exception as e:
            self.logger.exception(f"任务执行失败: {context.task_id}")
            return AgentExecutionResult(
                agent_id=self.agent_id,
                status=AgentStatus.ERROR,
                error_message=str(e),
            )
```

#### 2.3 实现具体功能

```python
    async def _sentiment_analysis(self, text: str) -> Dict[str, Any]:
        """情感分析"""
        prompt = f"""请分析以下文本的情感倾向：

文本：{text}

请返回JSON格式：
{{
    "sentiment": "正面/负面/中性",
    "confidence": 0.95,
    "reasoning": "分析理由"
}}
"""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        import json
        result = json.loads(response)
        return result

    async def _keyword_extraction(self, text: str) -> Dict[str, Any]:
        """关键词提取"""
        prompt = f"""请从以下文本中提取关键词：

文本：{text}

请返回JSON格式：
{{
    "keywords": ["关键词1", "关键词2", ...],
    "scores": [0.95, 0.87, ...]
}}
"""

        response = await self.llm.generate(
            prompt=prompt,
            system_prompt=self.get_system_prompt(),
            model="kimi-k2.5",
        )

        import json
        result = json.loads(response)
        return result
```

#### 2.4 添加输入验证

```python
    def validate_input(self, context: AgentExecutionContext) -> bool:
        """验证输入"""
        # 基础验证
        if not context.session_id:
            self.logger.error("缺少session_id")
            return False

        if not context.task_id:
            self.logger.error("缺少task_id")
            return False

        # 业务验证
        text = context.input_data.get("text", "")
        if not text:
            self.logger.error("缺少text字段")
            return False

        if len(text) > 10000:
            self.logger.error("文本过长（>10000字符）")
            return False

        return True
```

---

### Part 3: 测试和部署（2分钟）

#### 3.1 编写单元测试

```python
# tests/agents/test_text_analysis_agent.py
import pytest
from core.agents.text_analysis_agent import TextAnalysisAgent
from core.agents.xiaona.base_component import AgentExecutionContext, AgentStatus

@pytest.mark.asyncio
async def test_sentiment_analysis_positive():
    """测试正面情感分析"""
    agent = TextAnalysisAgent(agent_id="test_agent")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "operation": "sentiment_analysis",
            "text": "今天天气真好！",
        },
        config={},
        metadata={},
    )

    result = await agent.execute(context)

    assert result.status == AgentStatus.COMPLETED
    assert result.output_data["sentiment"] == "正面"
    assert result.output_data["confidence"] > 0.8

@pytest.mark.asyncio
async def test_keyword_extraction():
    """测试关键词提取"""
    agent = TextAnalysisAgent(agent_id="test_agent")
    context = AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={
            "operation": "keyword_extraction",
            "text": "人工智能和机器学习是未来的趋势。",
        },
        config={},
        metadata={},
    )

    result = await agent.execute(context)

    assert result.status == AgentStatus.COMPLETED
    assert "keywords" in result.output_data
    assert len(result.output_data["keywords"]) > 0
```

#### 3.2 集成到工作流

```python
from core.orchestration.workflow_builder import WorkflowBuilder
from core.orchestration.agent_registry import get_agent_registry
from core.orchestration.scenario_detector import Scenario

async def main():
    # 注册Agent
    registry = get_agent_registry()
    agent = TextAnalysisAgent(agent_id="text_analyzer")
    registry.register(agent, phase=1)

    # 创建工作流
    builder = WorkflowBuilder(
        agent_registry=registry,
        scenario_detector=ScenarioDetector(),
    )

    # 构建工作流
    workflow = builder.build_workflow(
        scenario=Scenario.TEXT_ANALYSIS,
        user_input="分析这段文本的情感",
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

## 🎯 最佳实践

### 1. 能力设计

**DO** ✅:
```python
AgentCapability(
    name="sentiment_analysis",  # 小写+下划线
    description="分析文本的情感倾向",  # 清晰描述
    input_types=["文本"],  # 明确输入
    output_types=["情感分类", "置信度"],  # 明确输出
    estimated_time=3.0,  # 合理估算
)
```

**DON'T** ❌:
```python
AgentCapability(
    name="SA",  # ❌ 不要缩写
    description="做一些分析",  # ❌ 描述模糊
    input_types=["input"],  # ❌ 不明确
    output_types=["output"],  # ❌ 不明确
    estimated_time=0.0,  # ❌ 不合理
)
```

### 2. 错误处理

**DO** ✅:
```python
try:
    result = await self._do_work(context)
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.COMPLETED,
        output_data=result,
    )
except Exception as e:
    self.logger.exception(f"任务失败: {context.task_id}")
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.ERROR,
        error_message=str(e),
    )
```

**DON'T** ❌:
```python
# ❌ 不要抛出异常
result = await self._do_work(context)
if not result:
    raise ValueError("结果为空")
```

### 3. 日志记录

**DO** ✅:
```python
self.logger.info(f"开始执行任务: {context.task_id}")
self.logger.debug(f"输入数据: {context.input_data}")
self.logger.warning(f"文本较长: {len(text)}字符")
self.logger.error(f"任务失败: {error}")
```

**DON'T** ❌:
```python
print("开始执行任务")  # ❌ 使用logger
```

---

## 📖 延伸阅读

- [统一Agent接口标准](../design/UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](../design/AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [接口合规性检查清单](AGENT_INTERFACE_COMPLIANCE_CHECKLIST.md)
- [示例Agent代码](../../examples/agents/example_agent.py)

---

## 🆘 常见问题

### Q1: 如何调试Agent？

A: 使用日志和断点：
```python
self.logger.debug(f"调试信息: {variable}")
import pdb; pdb.set_trace()  # 断点
```

### Q2: 如何测试异步方法？

A: 使用pytest-asyncio：
```python
@pytest.mark.asyncio
async def test_my_async_method():
    result = await agent.execute(context)
    assert result.status == AgentStatus.COMPLETED
```

### Q3: 如何处理长时间运行的任务？

A: 使用后台任务：
```python
async def execute(self, context: AgentExecutionContext):
    task = asyncio.create_task(self._long_running_task())
    result = await asyncio.wait_for(task, timeout=300.0)
    return result
```

---

**祝你开发顺利！** 🎉

如有问题，请查阅完整文档或提交Issue。
