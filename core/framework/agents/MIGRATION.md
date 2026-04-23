# BaseAgent 迁移指南

## 📋 概述

本指南帮助您将旧架构智能体迁移到新的BaseAgent统一接口。

**适用人群**: 智能体开发者
**迁移难度**: 中等
**预计时间**: 1-2小时/智能体

---

## 🔄 为什么要迁移？

| 旧架构问题 | 新架构优势 |
|-----------|-----------|
| 每个智能体有自己的基类 | 统一的BaseAgent接口 |
| 请求/响应格式不统一 | 标准化的AgentRequest/Response |
| 无统一注册机制 | AgentRegistry自动管理 |
| 无健康检查 | 内置health_check() |
| 无能力自描述 | AgentCapability元数据 |
| 生命周期管理混乱 | 明确的状态机 |

---

## 🚀 快速迁移

### 迁移检查清单

- [ ] 1. 评估旧智能体功能
- [ ] 2. 创建新智能体类（继承BaseAgent）
- [ ] 3. 实现必需的抽象方法
- [ ] 4. 迁移核心逻辑
- [ ] 5. 添加能力定义
- [ ] 6. 编写测试
- [ ] 7. 更新调用代码
- [ ] 8. 验证功能

---

## 📝 迁移步骤

### 步骤1: 评估旧智能体

**示例旧智能体**:

```python
from core.base_agent_with_memory import MemoryEnabledAgent, AgentRole

class OldPatentAgent(MemoryEnabledAgent):
    def __init__(self, agent_id: str):
        super().__init__(
            agent_id=agent_id,
            agent_type=AgentType.LEGAL,
            role=AgentRole.EXPERT
        )

    async def search_patent(self, query: str) -> Dict:
        """搜索专利"""
        # 实现逻辑
        return {"results": []}
```

**分析要点**:
- ✅ 功能: 专利搜索
- ✅ 输入: query (str)
- ✅ 输出: Dict
- ✅ 使用记忆系统
- ❌ 无统一的请求/响应格式
- ❌ 无能力自描述

### 步骤2: 创建新智能体

```python
from core.agents.base import (
    BaseAgent,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    AgentCapability,
)
from typing import List, Dict, Any

class NewPatentAgent(BaseAgent):
    """新专利搜索智能体"""

    @property
    def name(self) -> str:
        return "patent-search"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="patent-search",
                description="搜索专利数据库",
                parameters={
                    "query": {
                        "type": "string",
                        "description": "搜索关键词",
                        "required": True
                    }
                },
                examples=[
                    {
                        "query": "深度学习",
                        "results": ["专利1", "专利2"]
                    }
                ]
            )
        ]

    async def initialize(self) -> None:
        """初始化"""
        # 初始化记忆系统（可选）
        from core.memory.unified_memory import UnifiedAgentMemorySystem
        self.memory = UnifiedAgentMemorySystem(self.name)
        await self.memory.initialize()

        # 标记为就绪
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""
        try:
            if request.action == "patent-search":
                results = await self._search_patent(
                    request.parameters.get("query")
                )
                return AgentResponse.success(data=results)
            else:
                return AgentResponse.error(
                    error=f"不支持的操作: {request.action}"
                )
        except Exception as e:
            return AgentResponse.error(error=str(e))

    async def _search_patent(self, query: str) -> Dict[str, Any]:
        """搜索专利（核心逻辑）"""
        # 迁移原有逻辑
        return {"results": [], "query": query}

    async def shutdown(self) -> None:
        """关闭"""
        if hasattr(self, 'memory'):
            await self.memory.shutdown()
        self._status = AgentStatus.SHUTDOWN
```

### 步骤3: 更新调用代码

**旧代码**:

```python
agent = OldPatentAgent("patent-001")
results = await agent.search_patent("深度学习")
```

**新代码**:

```python
from core.agents.base import AgentRegistry, AgentRequest

# 创建并注册
agent = NewPatentAgent()
AgentRegistry.register(agent)
await agent.initialize()

# 使用
request = AgentRequest(
    request_id="search-001",
    action="patent-search",
    parameters={"query": "深度学习"}
)
response = await agent.safe_process(request)

if response.success:
    print(response.data["results"])
else:
    print(f"错误: {response.error}")
```

---

## 🔧 常见迁移模式

### 模式1: 简单功能智能体

**场景**: 只有单一功能的智能体

```python
# === 旧代码 ===
class SimpleAgent:
    async def do_work(self, input_data: str) -> str:
        return f"processed: {input_data}"

# === 新代码 ===
class SimpleAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "simple-agent"

    async def initialize(self) -> None:
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        result = await self._do_work(request.parameters.get("input"))
        return AgentResponse.success(data={"result": result})

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN
```

### 模式2: 多功能智能体

**场景**: 有多个不同操作的智能体

```python
# === 旧代码 ===
class MultiAgent:
    async def method_a(self, data): pass
    async def method_b(self, data): pass
    async def method_c(self, data): pass

# === 新代码 ===
class MultiAgent(BaseAgent):
    async def process(self, request: AgentRequest) -> AgentResponse:
        action_handlers = {
            "method-a": self._handle_method_a,
            "method-b": self._handle_method_b,
            "method-c": self._handle_method_c,
        }

        handler = action_handlers.get(request.action)
        if handler:
            result = await handler(request.parameters)
            return AgentResponse.success(data=result)
        else:
            return AgentResponse.error(f"未知操作: {request.action}")
```

### 模式3: 带状态智能体

**场景**: 需要维护内部状态的智能体

```python
class StatefulAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self._state = {}  # 内部状态
        self._cache = {}  # 缓存

    async def initialize(self) -> None:
        # 初始化状态
        self._state = {"initialized": True}
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        # 使用和更新状态
        self._state["last_request"] = request.request_id
        return AgentResponse.success(data={"state": self._state})
```

### 模式4: 带记忆智能体

**场景**: 需要记忆功能的智能体

```python
class MemoryAgent(BaseAgent):
    async def initialize(self) -> None:
        # 初始化记忆系统
        from core.memory.unified_memory import UnifiedAgentMemorySystem
        self.memory = UnifiedAgentMemorySystem(self.name)
        await self.memory.initialize()
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        # 存储到记忆
        await self.memory.store(
            memory_type="short_term",
            content=request.action,
            metadata={"request_id": request.request_id}
        )

        # 处理请求
        result = await self._handle(request)

        return AgentResponse.success(data=result)

    async def shutdown(self) -> None:
        await self.memory.shutdown()
        self._status = AgentStatus.SHUTDOWN
```

---

## ⚠️ 常见问题

### Q1: 如何处理异步初始化依赖？

**问题**: 智能体A需要智能体B先初始化

**解决方案**: 使用AgentRegistry的依赖管理

```python
async def initialize_with_dependencies():
    # 先初始化B
    agent_b = AgentB()
    AgentRegistry.register(agent_b)
    await agent_b.initialize()

    # 再初始化A
    agent_a = AgentA()
    AgentRegistry.register(agent_a)
    await agent_a.initialize()
```

### Q2: 如何处理错误？

**问题**: 旧代码直接抛异常

**解决方案**: 使用AgentResponse.error()

```python
async def process(self, request: AgentRequest) -> AgentResponse:
    try:
        result = await self._do_work(request.parameters)
        return AgentResponse.success(data=result)
    except ValueError as e:
        return AgentResponse.error(
            error=f"参数错误: {e}",
            data={"error_code": "INVALID_PARAM"}
        )
    except Exception as e:
        return AgentResponse.error(error=f"处理失败: {e}")
```

### Q3: 如何添加中间件/钩子？

**解决方案**: 重写钩子方法

```python
class AgentWithHooks(BaseAgent):
    async def before_process(self, request: AgentRequest) -> None:
        """处理前钩子"""
        # 记录日志、验证权限等
        logger.info(f"处理请求: {request.action}")

    async def after_process(
        self,
        request: AgentRequest,
        response: AgentResponse
    ) -> AgentResponse:
        """处理后钩子"""
        # 添加元数据、记录指标等
        response.metadata = {
            "processed_at": datetime.now().isoformat(),
            "agent": self.name
        }
        return response
```

---

## ✅ 验证清单

迁移完成后，请验证：

- [ ] 智能体可以正确注册到AgentRegistry
- [ ] initialize()成功执行，状态变为READY
- [ ] 所有action都能正确处理
- [ ] 错误情况返回正确的error响应
- [ ] shutdown()正确清理资源
- [ ] get_capabilities()返回正确的能力列表
- [ ] health_check()返回正确的健康状态
- [ ] 单元测试通过
- [ ] 集成测试通过

---

## 📚 迁移示例

### 完整示例: XiaonaLegalAgent

查看已完成的迁移示例：

```bash
# 查看源码
cat core/agents/xiaona_legal.py

# 查看测试
cat tests/core/agents/test_xiaona_legal.py

# 运行测试
pytest tests/core/agents/test_xiaona_legal.py -v
```

---

## 🆘 获取帮助

如有问题，请参考：

- [API文档](./API.md)
- [模块说明](./README.md)
- [示例代码](./example_agent.py)

或联系Athena团队。

---

**最后更新**: 2026-02-21
**版本**: 2.0.0
