# BaseAgent API 文档

## 📋 概述

BaseAgent是Athena平台的统一智能体接口，提供标准化的智能体生命周期管理、请求处理和响应机制。

**版本**: 2.0.0
**作者**: Athena Team
**最后更新**: 2026-02-21

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│                    AgentRegistry                         │
│              (模块级单例注册中心)                         │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴──────────┐
         │                      │
    ┌────▼─────┐          ┌────▼─────┐
    │ BaseAgent│          │AgentFactory│
    │ (抽象基类)│          │  (工厂)    │
    └────┬─────┘          └───────────┘
         │
    ┌────┴──────────────────────┬────────────┬────────────┐
    │                            │            │            │
┌───▼──────┐ ┌─────────────┐ ┌───▼──────┐ ┌───▼────────┐
│XiaonaLegal│ │XiaonuoAgent │ │AthenaAdvisor│ │   未来扩展  │
└──────────┘ └─────────────┘ └──────────┘ └────────────┘
```

---

## 📦 核心组件

### 1. 数据模型

#### AgentStatus

智能体状态枚举：

```python
class AgentStatus(Enum):
    INITIALIZING = "initializing"  # 初始化中
    READY = "ready"                # 就绪
    BUSY = "busy"                  # 忙碌
    ERROR = "error"                # 错误
    SHUTDOWN = "shutdown"          # 已关闭
```

#### AgentCapability

智能体能力描述：

```python
@dataclass
class AgentCapability:
    name: str              # 能力名称
    description: str       # 能力描述
    parameters: Dict[str, Any]  # 参数定义
    examples: List[Dict]  # 使用示例
```

#### AgentMetadata

智能体元数据：

```python
@dataclass
class AgentMetadata:
    name: str              # 智能体名称
    version: str           # 版本号
    description: str       # 描述
    author: str            # 作者
    tags: List[str]        # 标签
```

#### AgentRequest

统一的请求格式：

```python
@dataclass
class AgentRequest:
    request_id: str        # 请求ID
    action: str            # 操作类型
    parameters: Dict[str, Any]  # 参数
    context: Dict[str, Any] | None = None  # 上下文
```

#### AgentResponse

统一的响应格式：

```python
@dataclass
class AgentResponse:
    request_id: str        # 请求ID
    success: bool          # 是否成功
    data: Dict[str, Any]   # 响应数据
    error: str | None = None  # 错误信息
    metadata: Dict[str, Any] | None = None  # 元数据

    @classmethod
    def success(cls, data: Dict[str, Any]) -> AgentResponse:
        """创建成功响应"""

    @classmethod
    def error(cls, error: str, data: Dict[str, Any] | None = None) -> AgentResponse:
        """创建错误响应"""
```

### 2. BaseAgent抽象基类

```python
class BaseAgent(ABC):
    """智能体基类"""

    # === 必须实现的抽象属性和方法 ===

    @property
    @abstractmethod
    def name(self) -> str:
        """智能体唯一名称"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化智能体"""

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""

    @abstractmethod
    async def shutdown(self) -> None:
        """关闭智能体"""

    # === 可选重写的钩子方法 ===

    def validate_request(self, request: AgentRequest) -> bool:
        """验证请求（同步）"""

    async def validate_request_async(self, request: AgentRequest) -> bool:
        """验证请求（异步）"""

    async def before_process(self, request: AgentRequest) -> None:
        """处理前钩子"""

    async def after_process(
        self,
        request: AgentRequest,
        response: AgentResponse
    ) -> AgentResponse:
        """处理后钩子"""

    def get_capabilities(self) -> List[AgentCapability]:
        """获取能力列表"""

    def get_metadata(self) -> AgentMetadata:
        """获取元数据"""

    # === 公共API ===

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""

    @property
    def is_ready(self) -> bool:
        """是否就绪"""

    async def safe_process(self, request: AgentRequest) -> AgentResponse:
        """安全处理请求（带异常捕获）"""

    async def health_check(self) -> HealthStatus:
        """健康检查"""
```

### 3. AgentRegistry注册中心

```python
class AgentRegistry:
    """智能体注册中心（模块级单例）"""

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """注册智能体"""

    @classmethod
    def unregister(cls, name: str) -> bool:
        """注销智能体"""

    @classmethod
    def get(cls, name: str) -> BaseAgent | None:
        """获取智能体"""

    @classmethod
    def get_all(cls) -> Dict[str, BaseAgent]:
        """获取所有智能体"""

    @classmethod
    def list_agents(cls) -> List[str]:
        """列出所有智能体名称"""

    @classmethod
    def find_by_capability(cls, capability: str) -> List[BaseAgent]:
        """根据能力查找智能体"""

    @classmethod
    def get_ready_agents(cls) -> List[BaseAgent]:
        """获取就绪的智能体"""

    @classmethod
    def clear(cls) -> None:
        """清空注册表"""

    @classmethod
    async def shutdown_all(cls) -> None:
        """关闭所有智能体"""
```

### 4. AgentFactory工厂

```python
class AgentFactory:
    """智能体工厂"""

    @staticmethod
    def create_agent(
        agent_type: str,
        config: Dict[str, Any]
    ) -> BaseAgent:
        """创建智能体"""

    @staticmethod
    def create_from_yaml(config_path: str) -> BaseAgent:
        """从YAML配置创建"""

# 便捷函数
def create_agent_from_config(config: Dict[str, Any]) -> BaseAgent:
    """从配置创建智能体"""

def create_agents_from_yaml(yaml_path: str) -> List[BaseAgent]:
    """从YAML批量创建智能体"""
```

---

## 🚀 使用指南

### 基础用法

```python
from core.agents.base import (
    BaseAgent,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    AgentRegistry,
)

# 1. 创建智能体
class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my-agent"

    async def initialize(self) -> None:
        self.status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.success(data={"result": "done"})

    async def shutdown(self) -> None:
        self.status = AgentStatus.SHUTDOWN

# 2. 注册智能体
agent = MyAgent()
AgentRegistry.register(agent)

# 3. 使用智能体
await agent.initialize()
request = AgentRequest(
    request_id="req-001",
    action="process",
    parameters={"input": "data"}
)
response = await agent.safe_process(request)
print(response.data)  # {"result": "done"}

# 4. 关闭智能体
await agent.shutdown()
```

### 使用内置智能体

```python
from core.agents.xiaona_legal import XiaonaLegalAgent
from core.agents.xiaonuo_coordinator import XiaonuoAgent
from core.agents.athena_advisor import AthenaAdvisorAgent

# 创建小娜（法律专家）
xiaona = XiaonaLegalAgent()
AgentRegistry.register(xiaona)
await xiaona.initialize()

# 执行专利检索
request = AgentRequest(
    request_id="search-001",
    action="patent-search",
    parameters={
        "query": "深度学习 图像识别",
        "search_fields": ["title", "abstract"],
    }
)
response = await xiaona.safe_process(request)
```

### 多智能体协作

```python
from core.agents.xiaona_legal import XiaonaLegalAgent
from core.agents.xiaonuo_coordinator import XiaonuoAgent
from core.agents.base import AgentRegistry

# 创建并注册智能体
xiaona = XiaonaLegalAgent()
xiaonuo = XiaonuoAgent()

AgentRegistry.register(xiaona)
AgentRegistry.register(xiaonuo)

await xiaona.initialize()
await xiaonuo.initialize()

# 小诺调度小娜执行任务
schedule_request = AgentRequest(
    request_id="schedule-001",
    action="schedule-task",
    parameters={
        "target_agent": "xiaona-legal",
        "action": "patent-search",
        "parameters": {"query": "AI"},
    }
)
response = await xiaonuo.safe_process(schedule_request)
```

---

## 🔌 扩展指南

### 创建自定义智能体

```python
from core.agents.base import BaseAgent, AgentRequest, AgentResponse
from core.agents.base import AgentCapability, AgentMetadata, AgentStatus

class CustomAgent(BaseAgent):
    """自定义智能体示例"""

    def __init__(self):
        super().__init__()
        self._status = AgentStatus.INITIALIZING
        self._capabilities = self._register_capabilities()

    @property
    def name(self) -> str:
        return "custom-agent"

    def _register_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="custom-action",
                description="自定义操作",
                parameters={
                    "input": {"type": "string", "required": true}
                },
                examples=[
                    {"input": "example", "output": "result"}
                ]
            )
        ]

    async def initialize(self) -> None:
        """初始化逻辑"""
        # 执行初始化操作
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""
        try:
            # 验证请求
            if request.action == "custom-action":
                result = await self._handle_custom_action(request.parameters)
                return AgentResponse.success(data=result)
            else:
                return AgentResponse.error(
                    error=f"不支持的操作: {request.action}"
                )
        except Exception as e:
            return AgentResponse.error(error=str(e))

    async def _handle_custom_action(self, params: Dict) -> Dict:
        """处理自定义操作"""
        # 实现具体逻辑
        return {"result": "success"}

    async def shutdown(self) -> None:
        """关闭逻辑"""
        self._status = AgentStatus.SHUTDOWN

    # 可选：重写钩子
    async def before_process(self, request: AgentRequest) -> None:
        """处理前：记录日志等"""
        pass

    async def after_process(
        self,
        request: AgentRequest,
        response: AgentResponse
    ) -> AgentResponse:
        """处理后：添加元数据等"""
        response.metadata = {"processed_by": self.name}
        return response
```

### 集成记忆系统

```python
from core.agents.base import BaseAgent
from core.memory.unified_memory import UnifiedAgentMemorySystem

class AgentWithMemory(BaseAgent):
    """带记忆系统的智能体"""

    def __init__(self):
        super().__init__()
        # 添加记忆系统
        self.memory = UnifiedAgentMemorySystem(f"{self.name}-memory")

    async def initialize(self) -> None:
        await self.memory.initialize()
        self.status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        # 存储到记忆
        await self.memory.store(
            memory_type="short_term",
            content=f"处理请求: {request.action}",
            metadata={"request_id": request.request_id}
        )

        # 处理请求
        response = await self._handle_request(request)

        return response

    async def shutdown(self) -> None:
        await self.memory.shutdown()
        self.status = AgentStatus.SHUTDOWN
```

---

## 📊 状态转换图

```
     ┌──────────────┐
     │ INITIALIZING │ (创建时)
     └──────┬───────┘
            │ initialize()
            ▼
     ┌──────────────┐
     │    READY     │ (就绪)
     └──────┬───────┘
            │ process()
            ▼
     ┌──────────────┐
     │     BUSY     │ (处理中)
     └──────┬───────┘
            │
            ├───────────┐
            ▼           ▼
     ┌──────────┐ ┌──────────┐
     │  READY   │ │  ERROR   │
     └──────────┘ └────┬─────┘
                       │
                       ▼
                  ┌─────────┐
                  │ SHUTDOWN │ (关闭后)
                  └─────────┘
```

---

## 🔧 API参考

### 异常处理

```python
class AgentError(Exception):
    """智能体基础异常"""

class AgentNotFoundError(AgentError):
    """智能体不存在"""

class AgentAlreadyRegisteredError(AgentError):
    """智能体已注册"""

class InvalidRequestError(AgentError):
    """无效请求"""

class AgentNotReadyError(AgentError):
    """智能体未就绪"""
```

### 健康状态

```python
@dataclass
class HealthStatus:
    status: AgentStatus
    is_healthy: bool
    details: Dict[str, Any] | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
```

---

## 📚 相关文档

- [迁移指南](./MIGRATION.md)
- [模块说明](./README.md)
- [工厂模式](./factory.py)
- [示例代码](./example_agent.py)

---

**最后更新**: 2026-02-21
**版本**: 2.0.0
