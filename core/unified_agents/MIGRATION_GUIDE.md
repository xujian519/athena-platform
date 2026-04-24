# Agent架构迁移指南

> **版本**: 1.0.0
> **日期**: 2026-04-24
> **作者**: Athena Team

---

## 📋 目录

- [概述](#概述)
- [迁移步骤](#迁移步骤)
- [代码示例](#代码示例)
- [常见问题](#常见问题)
- [回滚方案](#回滚方案)

---

## 概述

### 为什么要迁移？

统一Agent架构整合了两套系统的最佳实践：

| 特性 | 旧架构 | 新架构 (统一) |
|-----|-------|-------------|
| 位置 | `core/agents/base_agent.py` | `core/unified_agents/base_agent.py` |
| 接口 | `process(input_text)` | `process(request)` + `process_task(input_text)` |
| 配置 | `__init__(name, role, ...)` | `UnifiedAgentConfig` |
| 类型注解 | 部分缺失 | 完整类型注解 |
| 健康检查 | 无 | 标准化接口 |
| 性能统计 | 无 | 自动收集 |
| 生命周期 | 无 | initialize → process → shutdown |

### 兼容性保证

- ✅ **旧代码无需修改** - 兼容层保持向后兼容
- ✅ **渐进式迁移** - 可以逐步迁移各个Agent
- ✅ **并行运行** - 新旧架构可以共存

---

## 迁移步骤

### Phase 1: 准备 (5分钟)

1. **备份现有代码**
```bash
cp core/agents/base_agent.py core/agents/base_agent.py.backup
```

2. **验证新架构可用**
```python
from core.unified_agents import UnifiedBaseAgent
print("新架构可用")
```

### Phase 2: 迁移单个Agent (15-30分钟)

#### 步骤1: 更新导入

```python
# 旧代码
from core.agents.base_agent import BaseAgent

# 新代码
from core.unified_agents import UnifiedBaseAgent, UnifiedAgentConfig
```

#### 步骤2: 更新初始化

```python
# 旧代码
class MyAgent(BaseAgent):
    def __init__(self, name: str, role: str):
        super().__init__(name=name, role=role)

# 新代码
class MyAgent(UnifiedBaseAgent):
    def __init__(self, config: UnifiedAgentConfig):
        super().__init__(config)

    @property
    def name(self) -> str:
        return self._config.name
```

#### 步骤3: 更新process方法

```python
# 旧代码
def process(self, input_text: str, **kwargs) -> str:
    return f"处理: {input_text}"

# 新代码 - 方式1: 使用新接口
async def process(self, request: AgentRequest) -> AgentResponse:
    return AgentResponse.success_response(
        request_id=request.request_id,
        data={"result": f"处理: {request.parameters.get('input')}"}
    )

# 新代码 - 方式2: 保留旧接口 (兼容模式)
async def process_task(self, input_text: str, **kwargs) -> str:
    return f"处理: {input_text}"
```

#### 步骤4: 添加生命周期方法 (可选但推荐)

```python
async def initialize(self) -> None:
    """Agent初始化时调用"""
    self._status = AgentStatus.READY

async def shutdown(self) -> None:
    """Agent关闭时调用"""
    self._status = AgentStatus.SHUTDOWN

async def health_check(self) -> HealthStatus:
    """健康检查"""
    return HealthStatus(status=self._status, message="正常")
```

### Phase 3: 测试验证 (10分钟)

```python
# 测试迁移后的Agent
import asyncio

async def test_migrated_agent():
    config = UnifiedAgentConfig.create_minimal("test", "tester")
    agent = MyAgent(config)

    await agent.initialize()
    response = await agent.process(AgentRequest(
        request_id="test-001",
        action="process",
        parameters={"input": "hello"}
    ))

    assert response.success is True
    await agent.shutdown()

asyncio.run(test_migrated_agent())
```

### Phase 4: 部署 (5分钟)

1. 运行完整测试套件
2. 检查日志确认无错误
3. 逐步替换各模块的Agent

---

## 代码示例

### 示例1: 简单Agent迁移

#### 迁移前

```python
from core.agents.base_agent import BaseAgent

class SimpleAgent(BaseAgent):
    def __init__(self, name: str = "simple"):
        super().__init__(name=name, role="assistant")

    def process(self, input_text: str, **kwargs) -> str:
        return f"收到: {input_text}"

# 使用
agent = SimpleAgent()
result = agent.process("你好")
print(result)  # 收到: 你好
```

#### 迁移后

```python
from core.unified_agents import (
    UnifiedBaseAgent,
    UnifiedAgentConfig,
    AgentRequest,
    AgentResponse,
)

class SimpleAgent(UnifiedBaseAgent):
    def __init__(self, config: UnifiedAgentConfig):
        super().__init__(config)

    async def process(self, request: AgentRequest) -> AgentResponse:
        input_text = request.parameters.get("input", "")
        return AgentResponse.success_response(
            request_id=request.request_id,
            data={"result": f"收到: {input_text}"}
        )

    # 保留旧接口兼容
    async def process_task(self, input_text: str, **kwargs) -> str:
        request = AgentRequest(
            request_id="legacy",
            action="process",
            parameters={"input": input_text}
        )
        response = await self.process(request)
        return response.data.get("result", "")

# 使用
config = UnifiedAgentConfig.create_minimal("simple", "assistant")
agent = SimpleAgent(config)

# 新方式
import asyncio
request = AgentRequest(
    request_id="001",
    action="process",
    parameters={"input": "你好"}
)
response = asyncio.run(agent.process(request))
print(response.data)  # {'result': '收到: 你好'}

# 旧方式 (仍然有效)
result = asyncio.run(agent.process_task("你好"))
print(result)  # 收到: 你好
```

### 示例2: 使用配置构建器

```python
from core.unified_agents import UnifiedAgentConfigBuilder

# 使用构建器创建复杂配置
config = (UnifiedAgentConfigBuilder()
          .name("my-agent")
          .role("expert")
          .model("claude-sonnet-4-6")
          .temperature(0.7)
          .max_tokens(4096)
          .enable_gateway(True)
          .gateway_url("ws://localhost:8005/ws")
          .build())

agent = MyAgent(config)
```

### 示例3: 适配器模式 (无需修改旧Agent)

```python
from core.unified_agents.adapters import LegacyAgentAdapter

# 旧Agent无需修改
class OldAgent:
    def process(self, input_text: str) -> str:
        return f"处理: {input_text}"

# 使用适配器包装
old_agent = OldAgent()
config = UnifiedAgentConfig.create_minimal("old", "legacy")
adapter = LegacyAgentAdapter(old_agent, config)

# 现在旧Agent可以和新架构一起工作
await adapter.initialize()
response = await adapter.process(AgentRequest(...))
```

---

## 常见问题

### Q1: 旧代码会立即失效吗？

**A**: 不会。兼容层保证旧代码继续工作：

```python
# 仍然有效
from core.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    ...
```

### Q2: 必须立即迁移所有Agent吗？

**A**: 不必。新旧架构可以共存，建议：

1. 先迁移新开发的Agent
2. 逐步迁移现有Agent
3. 保持关键Agent稳定后再迁移

### Q3: 新架构的性能如何？

**A**: 新架构性能与旧架构相当或更好：

- 异步处理: 更好的并发性能
- 统计收集: 可监控性能瓶颈
- 健康检查: 更容易发现异常

### Q4: 如何处理依赖旧Agent的代码？

**A**: 使用适配器模式：

```python
from core.unified_agents.adapters import LegacyAgentAdapter

# 无需修改依赖代码
wrapped = LegacyAgentAdapter(old_agent, config)
# wrapped现在和新架构完全兼容
```

### Q5: 迁移后出错怎么办？

**A**: 参见[回滚方案](#回滚方案)

---

## 回滚方案

### 方案1: 恢复备份

```bash
# 恢复备份文件
cp core/agents/base_agent.py.backup core/agents/base_agent.py

# 恢复导入
git checkout HEAD -- core/agents/
```

### 方案2: 使用旧导入路径

兼容层始终可用，无需回滚：

```python
# 仍然可以使用旧导入
from core.agents.base_agent import BaseAgent
```

### 方案3: 禁用新架构

在 `core/unified_agents/__init__.py` 中注释：

```python
# 临时禁用新架构
# from core.unified_agents.base_agent import UnifiedBaseAgent
```

---

## 迁移检查清单

- [ ] 备份现有代码
- [ ] 验证新架构可用
- [ ] 更新导入语句
- [ ] 更新初始化代码
- [ ] 更新process方法
- [ ] 添加生命周期方法
- [ ] 编写/更新测试
- [ ] 运行测试套件
- [ ] 检查日志无错误
- [ ] 更新文档

---

## 技术支持

- **文档**: `core/unified_agents/README.md`
- **示例**: `core/unified_agents/examples.py`
- **测试**: `core/unified_agents/tests.py`
- **问题**: GitHub Issues

---

## 版本历史

| 版本 | 日期 | 变更 |
|-----|------|-----|
| 1.0.0 | 2026-04-24 | 初始版本 |
