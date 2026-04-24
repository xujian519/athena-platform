# 统一Agent系统

整合Athena平台两套Agent架构的最佳实践，提供统一的Agent接口。

## 概述

统一Agent系统解决了平台中存在两套Agent架构的问题：
- **传统架构** (`core/agents/`) - 基于简单接口的Agent
- **新一代架构** (`core/framework/agents/`) - 基于统一接口的现代化Agent

统一系统提供：
1. **双接口模式** - 兼容两种接口（`process_task` + `process`）
2. **统一生命周期** - `initialize` → `process` → `shutdown`
3. **可选依赖** - Gateway和记忆系统（可选集成）
4. **适配器模式** - 包装传统Agent实现兼容

## 文件结构

```
core/unified_agents/
├── __init__.py       # 模块导出
├── base.py           # 数据类型定义（状态、消息、转换器）
├── base_agent.py     # 统一Agent基类
├── config.py         # 配置管理和构建器
├── adapters.py       # 适配器实现
├── examples.py       # 使用示例
└── tests.py          # 测试文件
```

## 快速开始

### 创建新Agent

```python
import asyncio
from core.unified_agents.base import (
    AgentRequest, AgentResponse, AgentStatus, HealthStatus
)
from core.unified_agents.config import UnifiedAgentConfig
from core.unified_agents.base_agent import UnifiedBaseAgent

class MyAgent(UnifiedBaseAgent):
    @property
    def name(self) -> str:
        return "my-agent"

    async def initialize(self) -> None:
        # 初始化逻辑
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        # 处理逻辑
        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"result": "ok"}
        )

    async def shutdown(self) -> None:
        # 清理逻辑
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status=self._status)

# 使用
async def main():
    config = UnifiedAgentConfig.create_minimal("my-agent", "processor")
    agent = MyAgent(config)
    await agent.initialize()

    response = await agent.process(AgentRequest(
        request_id="test-001",
        action="process",
        parameters={"input": "hello"}
    ))

    print(response.data)
    await agent.shutdown()

asyncio.run(main())
```

### 适配传统Agent

```python
from core.unified_agents.adapters import LegacyAgentAdapter
from core.unified_agents.config import UnifiedAgentConfig

# 传统Agent
legacy_agent = XiaonaLegalAgent()

# 包装为统一接口
config = UnifiedAgentConfig.create_minimal("xiaona-legal", "legal-expert")
adapter = LegacyAgentAdapter(legacy_agent, config)

await adapter.initialize()

# 使用新接口
response = await adapter.process(AgentRequest(...))
```

### 使用适配器工厂

```python
from core.unified_agents.adapters import AdapterFactory

# 自动检测并创建适配器
unified_agent = AdapterFactory.create_agent(legacy_agent)

await unified_agent.initialize()
```

## 配置管理

### 基础配置

```python
from core.unified_agents.config import UnifiedAgentConfig

config = UnifiedAgentConfig.create_minimal("agent-name", "agent-role")
```

### 使用构建器

```python
from core.unified_agents.config import UnifiedAgentConfigBuilder

config = (UnifiedAgentConfigBuilder()
    .name("my-agent")
    .role("processor")
    .model("gpt-4")
    .temperature(0.5)
    .enable_memory(True)
    .build())
```

### 使用模板

```python
from core.unified_agents.config import ConfigTemplates

# 法律专家Agent配置
legal_config = ConfigTemplates.legal_agent("xiaona-legal")

# 协调器Agent配置
coord_config = ConfigTemplates.coordinator_agent("xiaonuo-coord")
```

## 消息格式转换

统一系统支持两种消息格式的自动转换：

```python
from core.unified_agents.base import MessageConverter, TaskMessage, AgentRequest

# 传统 → 新格式
task_msg = TaskMessage(
    sender_id="user",
    recipient_id="agent",
    task_type="process",
    content={"input": "test"}
)

new_request = MessageConverter.task_to_request(task_msg)

# 新格式 → 传统
task_msg = MessageConverter.request_to_task(new_request, "agent")
```

## API参考

### UnifiedBaseAgent

核心抽象基类，所有Agent必须继承。

**必须实现的方法：**
- `name: str` - Agent名称属性
- `async initialize() -> None` - 初始化
- `async process(request: AgentRequest) -> AgentResponse` - 处理请求
- `async shutdown() -> None` - 关闭
- `async health_check() -> HealthStatus` - 健康检查

**可选重写的方法：**
- `async validate_request(request) -> bool` - 验证请求
- `_load_metadata() -> AgentMetadata` - 加载元数据
- `_register_capabilities() -> List[AgentCapability]` - 注册能力

### 数据类型

| 类型 | 说明 |
|------|------|
| `AgentStatus` | Agent状态枚举（INITIALIZING, READY, BUSY, ERROR, SHUTDOWN） |
| `AgentRequest` | 新一代请求格式 |
| `AgentResponse` | 新一代响应格式 |
| `TaskMessage` | 传统任务消息格式 |
| `ResponseMessage` | 传统响应消息格式 |
| `HealthStatus` | 健康状态 |
| `AgentCapability` | 能力描述 |
| `AgentMetadata` | 元数据 |

## 运行测试

```bash
# 运行所有测试
cd /Users/xujian/Athena工作平台
python -m asyncio core.unified_agents.tests

# 运行示例
python -m asyncio core.unified_agents.examples
```

## 迁移指南

### 从传统架构迁移

1. **保持传统代码不变** - 使用适配器包装
2. **逐步迁移** - 新Agent使用统一接口
3. **最终清理** - 迁移完成后删除传统代码

### 从新一代架构迁移

新一代架构已经接近统一接口，只需：
1. 继承 `UnifiedBaseAgent` 而非 `core.framework.agents.base.BaseAgent`
2. 更新导入路径
3. 验证功能完整性

## 设计原则

1. **向后兼容** - 适配器模式保持传统代码可用
2. **可选依赖** - Gateway和记忆系统可选集成
3. **简洁优先** - 只实现必要功能，避免过度工程
4. **类型安全** - 完整的类型注解
5. **测试友好** - 易于测试和验证

## 版本

当前版本: 1.0.0
发布日期: 2026-04-24
