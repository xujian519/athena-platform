# Core Legacy Directory

此目录包含Athena工作平台的旧架构代码，已被新的`core/agents/`架构替代。

## 📁 文件列表

| 文件 | 替代方案 | 状态 |
|------|---------|------|
| `base_agent_with_memory.py` | `core/agents/base.py` - BaseAgent | 已废弃 |
| `base_module.py` | `core/agents/base.py` - BaseAgent | 已废弃 |
| `athena_enhanced.py` | `core/agents/athena_advisor.py` - AthenaAdvisorAgent | 已废弃 |

## 🔄 迁移指南

### 从MemoryEnabledAgent迁移到BaseAgent

```python
# === 旧代码 ===
from core.base_agent_with_memory import MemoryEnabledAgent, AgentRole

class MyAgent(MemoryEnabledAgent):
    def __init__(self, agent_id: str, agent_type: AgentType):
        super().__init__(agent_id, agent_type, AgentRole.EXPERT)

# === 新代码 ===
from core.agents.base import BaseAgent, AgentRequest, AgentResponse

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my-agent"

    async def initialize(self) -> None:
        """初始化智能体"""
        self.status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""
        return AgentResponse.success(data={"result": "done"})
```

### 关键差异

| 特性 | 旧架构 | 新架构 |
|------|--------|--------|
| **基类** | MemoryEnabledAgent | BaseAgent |
| **请求处理** | `execute()` | `process(request: AgentRequest)` |
| **响应** | 返回dict | 返回AgentResponse对象 |
| **状态管理** | AgentRole枚举 | AgentStatus状态机 |
| **记忆系统** | 集成在基类中 | 可选集成 |
| **注册机制** | 手动注册 | AgentRegistry自动管理 |

### 记忆系统集成

新架构中，记忆系统是可选的：

```python
from core.agents.base import BaseAgent
from core.memory.unified_memory import UnifiedAgentMemorySystem

class MyAgentWithMemory(BaseAgent):
    def __init__(self):
        super().__init__()
        # 可选：添加记忆系统
        self.memory = UnifiedAgentMemorySystem("my-agent")

    async def initialize(self) -> None:
        await self.memory.initialize()
        self.status = AgentStatus.READY
```

## ⚠️ 重要说明

1. **不要修改这些文件** - 它们仅用于向后兼容
2. **优先使用新架构** - 所有新功能应使用`core/agents/`
3. **逐步迁移** - 旧代码应在方便时迁移到新架构
4. **Deprecation警告** - 使用旧代码时会显示警告

## 📚 相关文档

- [BaseAgent API文档](../agents/API.md)
- [智能体迁移指南](../agents/MIGRATION.md)
- [agents模块说明](../agents/README.md)

---

**最后更新**: 2026-02-21
**维护者**: Athena平台团队
