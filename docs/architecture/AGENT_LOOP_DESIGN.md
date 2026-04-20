# Agent Loop 核心引擎 - 设计文档

> **任务ID**: #2
> **开始时间**: 2026-04-20 18:00
> **状态**: 研究与设计阶段

---

## 📋 设计目标

设计并实现统一的 Agent Loop 核心引擎，简化代理逻辑，参考 OpenHarness 的 engine/ 设计。

### 核心目标
1. **无限循环引擎**: while True 循环处理 LLM 响应和工具调用
2. **流式响应处理**: 支持 LLM 流式输出
3. **工具执行循环**: 自动处理工具调用和结果反馈
4. **简化代理逻辑**: 代理只需定义工具和提示词

---

## 🏗️ 架构设计

### 核心循环（参考 OpenHarness）

```python
while True:
    # 1. 调用 LLM
    response = await api.stream(messages, tools)
    
    # 2. 检查停止条件
    if response.stop_reason != "tool_use":
        break  # 模型执行完成
    
    # 3. 处理工具调用
    for tool_call in response.tool_uses:
        # 4. 执行工具
        result = await execute_tool(tool_call)
        
        # 5. 添加到消息历史
        messages.append({
            "role": "tool",
            "content": result
        })
    
    # 6. 循环继续
```

### 组件架构

```
┌─────────────────────────────────────────┐
│           BaseAgentLoop                │
├─────────────────────────────────────────┤
│  ┌─────────────────────────────────┐  │
│  │   LLMAdapter                      │  │
│  │   - call_llm()                   │  │
│  │   - stream_response()            │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │   StreamingHandler               │  │
│  │   - handle_stream()              │  │
│  │   - process_delta()              │  │
│  └─────────────────────────────────┘  │
│  ┌─────────────────────────────────┐  │
│  │   ToolExecutor                   │  │
│  │   - execute_tool()               │  │
│  │   - handle_result()              │  │
│  └─────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

---

## 📦 核心组件

### 1. BaseAgentLoop（基类）

```python
class BaseAgentLoop:
    """Agent Loop 基类
    
    实现标准的代理执行循环。
    """
    
    def __init__(
        self,
        llm_adapter: LLMAdapter,
        tool_registry: ToolRegistry,
        system_prompt: str,
    ):
        self.llm_adapter = llm_adapter
        self.tool_registry = tool_registry
        self.system_prompt = system_prompt
    
    async def run(
        self,
        user_message: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """执行 Agent Loop
        
        Args:
            user_message: 用户消息
            context: 上下文信息
            
        Returns:
            str: 代理的最终响应
        """
```

### 2. LLMAdapter（LLM 适配器）

```python
class LLMAdapter:
    """LLM API 适配器
    
    统一不同 LLM 提供商的接口。
    """
    
    async def call_llm(
        self,
        messages: list[dict],
        tools: list[dict],
        stream: bool = True,
    ) -> LLMResponse:
        """调用 LLM
        
        Args:
            messages: 消息历史
            tools: 工具列表
            stream: 是否流式输出
            
        Returns:
            LLMResponse: LLM 响应
        """
```

### 3. StreamingHandler（流式处理器）

```python
class StreamingHandler:
    """流式响应处理器
    
    处理 LLM 的流式输出。
    """
    
    async def handle_stream(
        self,
        stream: AsyncIterator,
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        """处理流式响应
        
        Args:
            stream: 流式响应迭代器
            on_delta: 增量回调函数
            
        Returns:
            str: 完整响应
        """
```

### 4. ToolExecutor（工具执行器）

```python
class ToolExecutor:
    """工具执行器
    
    执行工具并处理结果。
    """
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: dict[str, Any],
    ) -> ToolResult:
        """执行工具
        
        Args:
            tool_id: 工具 ID
            parameters: 工具参数
            
        Returns:
            ToolResult: 工具执行结果
        """
```

---

## 🔄 数据流

```
用户输入
    ↓
构建消息历史
    ↓
┌─────────────────┐
│  Agent Loop     │
│  ┌───────────┐  │
│  │调用 LLM   │  │
│  └─────┬─────┘  │
│        │        │
│   流式响应     │
│        │        │
│  ┌─────▼─────┐  │
│  │停止条件？  │  │
│  └─────┬─────┘  │
│       否        │
│  ┌─────▼─────┐  │
│  │有工具调用？│  │
│  └─────┬─────┘  │
│       是        │
│  ┌─────▼─────┐  │
│  │执行工具   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │添加结果   │  │
│  └───────────┘  │
└─────────────────┘
    ↓
返回最终响应
```

---

## 🎯 与现有系统集成

### 1. BaseAgent 集成

```python
# core/agents/base_agent.py

class BaseAgent:
    """现有代理基类"""
    
    def __init__(self, name: str):
        self.name = name
        # 添加 Agent Loop 支持
        self.use_agent_loop = True
        self.agent_loop = None
    
    async def process(self, message: str) -> str:
        """处理消息（兼容旧接口）"""
        if self.use_agent_loop and self.agent_loop:
            return await self.agent_loop.run(message)
        else:
            # 旧的处理逻辑
            return await self._legacy_process(message)
```

### 2. 工具系统集成

```python
# 使用统一工具注册表
from core.tools.unified_registry import get_unified_registry

tool_registry = get_unified_registry()
tools = tool_registry.list_tools()

# 转换为 LLM 工具格式
llm_tools = [
    {
        "name": tool.id,
        "description": tool.description,
        "input_schema": tool.input_schema,
    }
    for tool in tools
]
```

### 3. LLM 管理器集成

```python
# 使用现有统一 LLM 管理器
from core.llm.unified_llm_manager import UnifiedLLMManager

llm_manager = UnifiedLLMManager()
response = await llm_manager.stream_response(
    messages=messages,
    tools=llm_tools,
)
```

---

## 📊 性能目标

| 指标 | 目标 | 说明 |
|------|------|------|
| 首次响应时间 | <2s | 用户消息到首次输出 |
| 流式延迟 | <500ms | 每个 token 的延迟 |
| 工具执行时间 | <30s | 单个工具执行超时 |
| 内存占用 | <50MB | 单个代理实例 |

---

## ✅ 验收标准

### 功能验收
- [ ] Agent Loop 正确实现
- [ ] 流式响应正常工作
- [ ] 工具调用循环正确执行
- [ ] 错误处理和重试机制有效
- [ ] 向后兼容性保持

### 性能验收
- [ ] 响应时间无明显增加（<5%）
- [ ] 内存占用增加可控（<10%）
- [ ] 并发性能无明显下降

### 质量验收
- [ ] 单元测试覆盖率 >80%
- [ ] 所有测试通过
- [ ] 代码审查通过
- [ ] 文档完整

---

## 📚 参考资料

### 内部文档
- [Athena 平台架构](../../CLAUDE.md)
- [BaseAgent 代码](../../core/agents/base_agent.py)
- [统一 LLM 管理器](../../core/llm/unified_llm_manager.py)

### 外部参考
- [OpenHarness Engine](/Users/xujian/Downloads/OpenHarness-main/engine/)

---

**创建时间**: 2026-04-20 18:00
**作者**: 徐健
**状态**: 设计完成，待实施
