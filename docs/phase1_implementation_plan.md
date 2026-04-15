# Athena工作平台 Phase 1 实施方案：智能体统一接口

## 📋 项目概述

**目标**: 建立统一的智能体接口标准，迁移现有智能体实现
**周期**: 7个工作日
**优先级**: P0 (最高)
**状态**: 待启动

---

## 🎯 核心目标

### 1.1 业务目标

| 目标 | 当前状态 | 目标状态 | 衡量指标 |
|------|---------|---------|---------|
| 智能体接口统一 | 分散、重复 | 标准化 | 100%智能体实现BaseAgent |
| 代码复用性 | 低 | 高 | 减少50%重复代码 |
| 新智能体开发 | 5天 | 2天 | 开发时间减少60% |
| 维护成本 | 高 | 低 | 单点修改，全局生效 |

### 1.2 技术目标

- 定义完整的BaseAgent抽象接口
- 实现智能体生命周期管理
- 建立智能体注册机制
- 提供完整的测试框架
- 兼容现有功能，零业务中断

---

## 📐 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     Athena 统一智能体架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AgentRegistry (智能体注册中心)                            │   │
│  │  - 智能体注册与发现                                        │   │
│  │  - 能力索引管理                                           │   │
│  │  - 生命周期管理                                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                          │                                        │
│          ┌───────────────┼───────────────┐                       │
│          ▼               ▼               ▼                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ BaseAgent    │ │ AgentContext │ │ AgentRequest │            │
│  │ (抽象基类)    │ │ (上下文)     │ │ (请求模型)   │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│          │               │               │                       │
│          ▼               ▼               ▼                       │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              具体智能体实现                            │       │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │       │
│  │  │ Xiaona  │  │Xiaonuo  │  │ Yunxi   │  │  ...    │  │       │
│  │  │ Legal   │  │Orchestr │  │ IP Mgr  │  │         │  │       │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │       │
│  └──────────────────────────────────────────────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件设计

#### 2.2.1 BaseAgent 抽象基类

```python
# core/agents/base.py
"""
Athena智能体统一接口基类
所有智能体必须继承此基类并实现其抽象方法
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """智能体状态枚举"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentCapability:
    """智能体能力描述"""
    name: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    examples: List[str] = field(default_factory=list)


@dataclass
class AgentMetadata:
    """智能体元数据"""
    name: str
    version: str
    description: str
    author: str
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentRequest:
    """智能体请求模型"""
    request_id: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResponse:
    """智能体响应模型"""
    request_id: str
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


@dataclass
class HealthStatus:
    """健康状态"""
    status: AgentStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class BaseAgent(ABC):
    """
    智能体统一接口基类

    所有智能体必须继承此类并实现所有抽象方法。
    提供统一的初始化、处理、健康检查和关闭接口。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化智能体

        Args:
            config: 智能体配置字典
        """
        self._config = config or {}
        self._status = AgentStatus.INITIALIZING
        self._metadata = self._load_metadata()
        self._capabilities = self._register_capabilities()
        self._context: Dict[str, Any] = {}

        # 初始化日志
        self._setup_logging()

        logger.info(f"初始化智能体: {self.name} v{self._metadata.version}")

    @property
    def status(self) -> AgentStatus:
        """获取当前状态"""
        return self._status

    @property
    def is_ready(self) -> bool:
        """是否就绪"""
        return self._status == AgentStatus.READY

    # ========== 抽象方法 - 必须实现 ==========

    @property
    @abstractmethod
    def name(self) -> str:
        """
        智能体名称 (唯一标识符)

        Returns:
            智能体名称，如 "xiaona-legal"
        """
        pass

    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化智能体资源

        在此方法中加载模型、建立连接等耗时操作。
        初始化完成后应将状态设置为 READY。
        """
        pass

    @abstractmethod
    async def process(self, request: AgentRequest) -> AgentResponse:
        """
        处理智能体请求的核心方法

        Args:
            request: 智能体请求对象

        Returns:
            AgentResponse: 响应对象
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        关闭智能体，释放资源

        在此方法中关闭连接、释放内存、保存状态等。
        关闭完成后应将状态设置为 SHUTDOWN。
        """
        pass

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """
        健康检查

        Returns:
            HealthStatus: 健康状态对象
        """
        pass

    # ========== 可选方法 - 按需实现 ==========

    def _load_metadata(self) -> AgentMetadata:
        """
        加载智能体元数据 (可选重写)

        Returns:
            AgentMetadata: 元数据对象
        """
        return AgentMetadata(
            name=self.name,
            version="1.0.0",
            description=f"{self.name}智能体",
            author="Athena Team",
            tags=[]
        )

    def _register_capabilities(self) -> List[AgentCapability]:
        """
        注册智能体能力 (可选重写)

        Returns:
            能力列表
        """
        return []

    async def validate_request(self, request: AgentRequest) -> bool:
        """
        验证请求有效性 (可选重写)

        Args:
            request: 待验证的请求

        Returns:
            bool: 是否有效
        """
        return True

    async def before_process(self, request: AgentRequest) -> None:
        """
        处理前钩子 (可选重写)

        Args:
            request: 即将处理的请求
        """
        pass

    async def after_process(self, request: AgentRequest, response: AgentResponse) -> None:
        """
        处理后钩子 (可选重写)

        Args:
            request: 已处理的请求
            response: 生成的响应
        """
        pass

    # ========== 工具方法 ==========

    def _setup_logging(self) -> None:
        """设置日志"""
        self.logger = logging.getLogger(f"agent.{self.name}")

    def get_capabilities(self) -> List[AgentCapability]:
        """获取能力列表"""
        return self._capabilities

    def get_metadata(self) -> AgentMetadata:
        """获取元数据"""
        return self._metadata

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文"""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self._context.get(key, default)

    async def safe_process(self, request: AgentRequest) -> AgentResponse:
        """
        安全处理请求 (包含异常处理和钩子)

        Args:
            request: 请求对象

        Returns:
            AgentResponse: 响应对象
        """
        try:
            # 验证请求
            if not await self.validate_request(request):
                return AgentResponse(
                    request_id=request.request_id,
                    success=False,
                    error="请求验证失败"
                )

            # 检查状态
            if self._status != AgentStatus.READY:
                return AgentResponse(
                    request_id=request.request_id,
                    success=False,
                    error=f"智能体未就绪: {self._status.value}"
                )

            # 更新状态
            self._status = AgentStatus.BUSY

            # 前置钩子
            await self.before_process(request)

            # 核心处理
            response = await self.process(request)

            # 后置钩子
            await self.after_process(request, response)

            return response

        except Exception as e:
            self.logger.error(f"处理请求失败: {e}", exc_info=True)
            self._status = AgentStatus.ERROR
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )
        finally:
            if self._status == AgentStatus.BUSY:
                self._status = AgentStatus.READY


class AgentRegistry:
    """
    智能体注册中心

    管理所有智能体的注册、发现和生命周期。
    """

    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, BaseAgent] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, agent: BaseAgent) -> None:
        """注册智能体"""
        name = agent.name
        if name in cls._agents:
            raise ValueError(f"智能体 {name} 已存在")
        cls._agents[name] = agent
        logger.info(f"注册智能体: {name}")

    @classmethod
    def unregister(cls, name: str) -> None:
        """注销智能体"""
        if name in cls._agents:
            del cls._agents[name]
            logger.info(f"注销智能体: {name}")

    @classmethod
    def get(cls, name: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> List[str]:
        """列出所有智能体名称"""
        return list(cls._agents.keys())

    @classmethod
    def get_by_capability(cls, capability: str) -> List[BaseAgent]:
        """根据能力查找智能体"""
        result = []
        for agent in cls._agents.values():
            for cap in agent.get_capabilities():
                if cap.name == capability:
                    result.append(agent)
                    break
        return result

    @classmethod
    async def initialize_all(cls) -> None:
        """初始化所有智能体"""
        for agent in cls._agents.values():
            if agent.status == AgentStatus.INITIALIZING:
                await agent.initialize()

    @classmethod
    async def shutdown_all(cls) -> None:
        """关闭所有智能体"""
        for agent in cls._agents.values():
            await agent.shutdown()
```

#### 2.2.2 小娜法律智能体迁移示例

```python
# core/agents/xiaona/legal_agent.py
"""
小娜法律智能体 - 统一接口实现
专业的专利分析和法律服务智能体
"""

from typing import Dict, Any, List
from core.agents.base import (
    BaseAgent,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    HealthStatus,
    AgentCapability,
    AgentMetadata
)


class XiaonaLegalAgent(BaseAgent):
    """
    小娜法律智能体

    专注于专利检索、法律分析和案例研究的AI智能体。
    """

    @property
    def name(self) -> str:
        return "xiaona-legal"

    def _load_metadata(self) -> AgentMetadata:
        """加载元数据"""
        return AgentMetadata(
            name=self.name,
            version="2.0.0",
            description="专业专利法律分析智能体，提供专利检索、法律分析和案例研究服务",
            author="Athena Team",
            tags=["legal", "patent", "analysis", "search"]
        )

    def _register_capabilities(self) -> List[AgentCapability]:
        """注册能力"""
        return [
            AgentCapability(
                name="patent-search",
                description="专利检索服务",
                parameters={
                    "query": {"type": "string", "description": "检索关键词"},
                    "database": {"type": "string", "description": "数据库来源", "default": "all"}
                },
                examples=[
                    {"query": "人工智能 深度学习", "database": "cnipa"},
                    {"query": "量子计算机", "database": "uspto"}
                ]
            ),
            AgentCapability(
                name="legal-analysis",
                description="法律分析服务",
                parameters={
                    "patent_id": {"type": "string", "description": "专利号"},
                    "analysis_type": {"type": "string", "description": "分析类型"}
                },
                examples=[
                    {"patent_id": "CN123456789A", "analysis_type": "novelty"}
                ]
            ),
            AgentCapability(
                name="case-retrieval",
                description="案例检索服务",
                parameters={
                    "keywords": {"type": "array", "description": "关键词列表"},
                    "court": {"type": "string", "description": "法院级别"}
                }
            ),
            AgentCapability(
                name="patent-drafting",
                description="专利撰写辅助",
                parameters={
                    "invention": {"type": "string", "description": "技术描述"},
                    "claims": {"type": "integer", "description": "权利要求数量"}
                }
            )
        ]

    async def initialize(self) -> None:
        """初始化智能体"""
        self.logger.info("正在初始化小娜法律智能体...")

        try:
            # 初始化LLM连接
            from core.llm.unified_llm_manager import UnifiedLLMManager
            self.llm = UnifiedLLMManager()

            # 初始化数据库连接
            from patent_platform.workspace.knowledge_graph import neo4j_manager
            self.neo4j = neo4j_manager

            # 初始化向量检索
            from patent_hybrid_retrieval.hybrid_retrieval_system import HybridRetrievalSystem
            self.retriever = HybridRetrievalSystem()

            # 加载法律世界模型
            from core.legal_world_model import LegalWorldModel
            self.legal_model = LegalWorldModel()

            # 更新状态
            self._status = AgentStatus.READY
            self.logger.info("小娜法律智能体初始化完成")

        except Exception as e:
            self._status = AgentStatus.ERROR
            self.logger.error(f"初始化失败: {e}", exc_info=True)
            raise

    async def process(self, request: AgentRequest) -> AgentResponse:
        """处理请求"""
        action = request.action
        params = request.parameters

        self.logger.info(f"处理请求: action={action}, request_id={request.request_id}")

        # 根据action路由到具体处理方法
        handler = self._get_handler(action)
        if handler is None:
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error=f"不支持的操作: {action}"
            )

        # 执行处理
        try:
            result = await handler(params)
            return AgentResponse(
                request_id=request.request_id,
                success=True,
                data=result,
                metadata={"action": action, "agent": self.name}
            )
        except Exception as e:
            self.logger.error(f"处理失败: {e}", exc_info=True)
            return AgentResponse(
                request_id=request.request_id,
                success=False,
                error=str(e)
            )

    def _get_handler(self, action: str):
        """获取处理方法"""
        handlers = {
            "patent-search": self._patent_search,
            "legal-analysis": self._legal_analysis,
            "case-retrieval": self._case_retrieval,
            "patent-drafting": self._patent_drafting
        }
        return handlers.get(action)

    async def _patent_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """专利检索"""
        query = params.get("query")
        database = params.get("database", "all")

        # 使用混合检索系统
        results = await self.retriever.search(
            query=query,
            databases=[database] if database != "all" else None
        )

        return {
            "query": query,
            "database": database,
            "results": results[:10],  # 返回前10条
            "total": len(results)
        }

    async def _legal_analysis(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """法律分析"""
        patent_id = params.get("patent_id")
        analysis_type = params.get("analysis_type", "general")

        # 使用法律世界模型分析
        analysis = await self.legal_model.analyze(
            patent_id=patent_id,
            analysis_type=analysis_type
        )

        return analysis

    async def _case_retrieval(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """案例检索"""
        keywords = params.get("keywords", [])
        court = params.get("court")

        # 从Neo4j检索案例
        cases = await self.neo4j.search_cases(
            keywords=keywords,
            court=court
        )

        return {"cases": cases}

    async def _patent_drafting(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """专利撰写辅助"""
        invention = params.get("invention")
        claims_count = params.get("claims", 5)

        # 使用LLM生成专利草稿
        prompt = self._build_drafting_prompt(invention, claims_count)
        draft = await self.llm.generate(prompt)

        return {"draft": draft}

    def _build_drafting_prompt(self, invention: str, claims: int) -> str:
        """构建撰写提示词"""
        return f"""
作为专利代理专家，根据以下技术描述撰写专利申请文件：

技术描述：{invention}

要求：
1. 撰写{claims}条权利要求
2. 包含技术领域、背景技术、发明内容、附图说明、具体实施方式
3. 使用标准专利术语
4. 确保法律严谨性

请按标准专利申请格式输出。
"""

    async def validate_request(self, request: AgentRequest) -> bool:
        """验证请求"""
        if not request.action:
            return False

        # 检查必需参数
        required_params = {
            "patent-search": ["query"],
            "legal-analysis": ["patent_id"],
            "patent-drafting": ["invention"]
        }

        params_needed = required_params.get(request.action, [])
        for param in params_needed:
            if param not in request.parameters:
                self.logger.warning(f"缺少必需参数: {param}")
                return False

        return True

    async def health_check(self) -> HealthStatus:
        """健康检查"""
        checks = {}

        # 检查LLM
        try:
            llm_status = await self.llm.check_health()
            checks["llm"] = "healthy" if llm_status else "degraded"
        except Exception:
            checks["llm"] = "error"

        # 检查数据库
        try:
            await self.neo4j.ping()
            checks["neo4j"] = "healthy"
        except Exception:
            checks["neo4j"] = "error"

        # 检查检索系统
        try:
            await self.retriever.health_check()
            checks["retriever"] = "healthy"
        except Exception:
            checks["retriever"] = "error"

        # 判断整体状态
        all_healthy = all(v == "healthy" for v in checks.values())
        status = AgentStatus.READY if all_healthy else AgentStatus.ERROR

        return HealthStatus(
            status=status,
            message="所有系统正常" if all_healthy else "部分系统异常",
            details=checks
        )

    async def shutdown(self) -> None:
        """关闭智能体"""
        self.logger.info("正在关闭小娜法律智能体...")

        # 关闭连接
        await self.neo4j.close()
        await self.retriever.close()

        # 更新状态
        self._status = AgentStatus.SHUTDOWN
        self.logger.info("小娜法律智能体已关闭")
```

#### 2.2.3 智能体工厂

```python
# core/agents/factory.py
"""
智能体工厂 - 负责创建和管理智能体实例
"""

from typing import Type, Dict, Any, Optional
from core.agents.base import BaseAgent, AgentRegistry


class AgentFactory:
    """
    智能体工厂

    根据配置动态创建和管理智能体实例。
    """

    _agent_classes: Dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register_agent_class(cls, agent_class: Type[BaseAgent]) -> None:
        """注册智能体类"""
        # 创建临时实例获取名称
        temp_instance = agent_class()
        name = temp_instance.name
        cls._agent_classes[name] = agent_class
        del temp_instance
        print(f"注册智能体类: {name}")

    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """创建智能体实例"""
        if name not in cls._agent_classes:
            raise ValueError(f"未知的智能体类型: {name}")

        agent_class = cls._agent_classes[name]
        agent = agent_class(config)

        # 注册到注册中心
        AgentRegistry.register(agent)

        return agent

    @classmethod
    def create_and_initialize(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseAgent:
        """创建并初始化智能体"""
        agent = cls.create(name, config)
        import asyncio
        asyncio.run(agent.initialize())
        return agent

    @classmethod
    def list_available_agents(cls) -> list:
        """列出可用的智能体类型"""
        return list(cls._agent_classes.keys())


# 自动注册智能体类
def auto_register_agents():
    """自动导入并注册所有智能体"""
    import importlib
    import inspect
    from pathlib import Path

    agents_dir = Path(__file__).parent
    for module_file in agents_dir.rglob("*_agent.py"):
        module_path = str(module_file.relative_to(agents_dir.parent / "agents"))
        module_name = module_path.replace("/", ".").replace(".py", "")

        try:
            module = importlib.import_module(f"core.agents.{module_name}")
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and issubclass(obj, BaseAgent) and obj != BaseAgent:
                    AgentFactory.register_agent_class(obj)
        except ImportError as e:
            print(f"导入模块 {module_name} 失败: {e}")
```

---

## 📝 实施计划

### 3.1 任务分解

| 任务ID | 任务名称 | 负责人 | 预计工时 | 前置任务 |
|--------|---------|--------|---------|---------|
| **T1.1** | BaseAgent接口实现 | - | 0.5天 | - |
| **T1.2** | AgentRegistry实现 | - | 0.5天 | T1.1 |
| **T1.3** | XiaonaLegalAgent迁移 | - | 1天 | T1.2 |
| **T1.4** | XiaonuoAgent迁移 | - | 1天 | T1.3 |
| **T1.5** | YunxiAgent迁移 | - | 1天 | T1.3 |
| **T1.6** | 单元测试编写 | - | 1天 | T1.1-T1.5 |
| **T1.7** | 集成测试 | - | 0.5天 | T1.6 |
| **T1.8** | 文档编写 | - | 1天 | T1.1-T1.7 |

### 3.2 详细时间表

```
Week 1 - Day 1 (Monday)
├── T1.1: BaseAgent接口实现 (4小时)
│   ├── 定义抽象方法
│   ├── 实现数据模型
│   └── 编写文档字符串
└── T1.2: AgentRegistry实现 (4小时)
    ├── 注册机制
    ├── 发现机制
    └── 生命周期管理

Week 1 - Day 2 (Tuesday)
└── T1.3: XiaonaLegalAgent迁移 (8小时)
    ├── 分析现有实现
    ├── 迁移核心功能
    ├── 适配新接口
    └── 本地测试

Week 1 - Day 3 (Wednesday)
├── T1.4: XiaonuoAgent迁移 (4小时)
│   └── (同T1.3流程)
└── T1.5: YunxiAgent迁移 (4小时)
    └── (同T1.3流程)

Week 1 - Day 4 (Thursday)
└── T1.6: 单元测试编写 (8小时)
    ├── BaseAgent测试
    ├── AgentRegistry测试
    ├── XiaonaLegalAgent测试
    └── Mock外部依赖

Week 1 - Day 5 (Friday)
├── T1.7: 集成测试 (4小时)
│   ├── 端到端流程测试
│   └── 性能基准测试
└── T1.8: 文档编写 (4小时)
    ├── API文档
    ├── 迁移指南
    └── 最佳实践
```

---

## 🧪 测试策略

### 4.1 单元测试

```python
# tests/core/agents/test_base_agent.py
"""BaseAgent单元测试"""

import pytest
import asyncio
from core.agents.base import (
    BaseAgent,
    AgentRequest,
    AgentResponse,
    AgentStatus,
    AgentRegistry
)


class MockAgent(BaseAgent):
    """用于测试的Mock智能体"""

    @property
    def name(self) -> str:
        return "mock-agent"

    async def initialize(self) -> None:
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse(
            request_id=request.request_id,
            success=True,
            data={"result": "ok"}
        )

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN

    async def health_check(self) -> HealthStatus:
        return HealthStatus(status=AgentStatus.READY)


@pytest.mark.asyncio
class TestBaseAgent:
    """BaseAgent测试类"""

    async def test_agent_initialization(self):
        """测试智能体初始化"""
        agent = MockAgent()
        assert agent.name == "mock-agent"
        assert agent.status == AgentStatus.INITIALIZING

    async def test_agent_initialize(self):
        """测试初始化流程"""
        agent = MockAgent()
        await agent.initialize()
        assert agent.is_ready

    async def test_agent_process_request(self):
        """测试请求处理"""
        agent = MockAgent()
        await agent.initialize()

        request = AgentRequest(
            request_id="test-001",
            action="test",
            parameters={"key": "value"}
        )

        response = await agent.safe_process(request)
        assert response.success
        assert response.request_id == "test-001"

    async def test_agent_health_check(self):
        """测试健康检查"""
        agent = MockAgent()
        await agent.initialize()

        status = await agent.health_check()
        assert status.status == AgentStatus.READY

    async def test_agent_shutdown(self):
        """测试关闭流程"""
        agent = MockAgent()
        await agent.initialize()
        await agent.shutdown()

        assert agent.status == AgentStatus.SHUTDOWN


@pytest.mark.asyncio
class TestAgentRegistry:
    """AgentRegistry测试类"""

    async def test_register_agent(self):
        """测试智能体注册"""
        agent = MockAgent()
        AgentRegistry.register(agent)

        assert "mock-agent" in AgentRegistry.list_agents()

    async def test_get_agent(self):
        """测试获取智能体"""
        agent = MockAgent()
        AgentRegistry.register(agent)

        retrieved = AgentRegistry.get("mock-agent")
        assert retrieved is agent

    async def test_duplicate_registration(self):
        """测试重复注册"""
        agent1 = MockAgent()
        agent2 = MockAgent()

        AgentRegistry.register(agent1)
        with pytest.raises(ValueError):
            AgentRegistry.register(agent2)
```

### 4.2 集成测试

```python
# tests/integration/test_agent_workflow.py
"""智能体工作流集成测试"""

import pytest
from core.agents.factory import AgentFactory, auto_register_agents
from core.agents.base import AgentRequest


@pytest.mark.asyncio
class TestAgentWorkflow:
    """智能体工作流测试"""

    async def test_xiaona_patent_search(self):
        """测试小娜专利检索流程"""
        # 自动注册所有智能体
        auto_register_agents()

        # 创建并初始化小娜
        xiaona = AgentFactory.create_and_initialize("xiaona-legal")

        # 构造请求
        request = AgentRequest(
            request_id="test-001",
            action="patent-search",
            parameters={
                "query": "人工智能",
                "database": "cnipa"
            }
        )

        # 处理请求
        response = await xiaona.safe_process(request)

        # 验证响应
        assert response.success
        assert "results" in response.data

        # 清理
        await xiaona.shutdown()

    async def test_multi_agent_collaboration(self):
        """测试多智能体协作"""
        auto_register_agents()

        # 创建多个智能体
        xiaona = AgentFactory.create_and_initialize("xiaona-legal")
        xiaonuo = AgentFactory.create_and_initialize("xiaonuo-orchestrator")

        # 模拟协作场景
        patent_request = AgentRequest(
            request_id="test-002",
            action="patent-analysis",
            parameters={"patent_id": "CN123456789A"}
        )

        # 小娜分析专利
        analysis = await xiaona.safe_process(patent_request)

        # 小诺调度后续任务
        if analysis.success:
            task_request = AgentRequest(
                request_id="test-003",
                action="schedule-tasks",
                parameters={"analysis": analysis.data}
            )
            task_result = await xiaonuo.safe_process(task_request)
            assert task_result.success

        # 清理
        await xiaona.shutdown()
        await xiaonuo.shutdown()
```

---

## 📚 迁移指南

### 5.1 现有智能体迁移步骤

**步骤1: 分析现有实现**

```bash
# 1. 找到现有智能体文件
ls core/agents/xiaona*.py

# 2. 分析核心功能
grep -n "def " xiaona_professional_v4.py | head -20
```

**步骤2: 创建新智能体类**

```python
# 创建 core/agents/xiaona/legal_agent_v2.py
# 从 BaseAgent 继承
# 实现所有抽象方法
```

**步骤3: 迁移核心逻辑**

```python
# 保留原有核心方法
async def _patent_search(self, params):
    # 从旧实现复制核心逻辑
    pass
```

**步骤4: 编写迁移测试**

```python
# 确保功能等价性
# 对比新旧实现结果
```

**步骤5: 更新调用方**

```python
# 更新所有调用点
# 从: agent = XiaonaProfessional()
# 到: agent = AgentFactory.create("xiaona-legal")
```

### 5.2 兼容性策略

```python
# core/agents/legacy/compat.py
"""
向后兼容层
在迁移期间保持旧API可用
"""

class XiaonaProfessional:
    """
    旧版XiaonaProfessional的兼容包装器
    将旧接口转发到新的BaseAgent实现
    """

    def __init__(self):
        from core.agents.factory import AgentFactory
        self._new_agent = AgentFactory.create("xiaona-legal")
        import asyncio
        asyncio.run(self._new_agent.initialize())

    def process_query(self, query: str) -> dict:
        """旧接口方法"""
        import asyncio
        request = AgentRequest(
            request_id="legacy",
            action="patent-search",
            parameters={"query": query}
        )
        response = asyncio.run(self._new_agent.safe_process(request))
        return response.data if response.success else {"error": response.error}
```

---

## 📊 验收标准

### 6.1 功能验收

- [ ] 所有核心智能体(Xiaona, Xiaonuo, Yunxi)完成迁移
- [ ] 新实现功能与旧实现功能等价
- [ ] 所有单元测试通过 (覆盖率 > 80%)
- [ ] 所有集成测试通过
- [ ] 性能不低于旧实现 (±10%)

### 6.2 质量验收

- [ ] 代码通过类型检查 (mypy)
- [ ] 代码通过静态分析 (pylint/flake8)
- [ ] 所有公共方法有docstring
- [ ] 关键流程有日志记录
- [ ] 异常处理完善

### 6.3 文档验收

- [ ] BaseAgent API文档完整
- [ ] 智能体开发指南
- [ ] 迁移指南
- [ ] 故障排查手册

---

## 🚀 部署方案

### 7.1 分阶段部署

```
Phase 1: 并行运行 (Week 1)
├── 保留旧实现
├── 部署新实现到 /core/agents/v2/
├── 灰度切流 10% 到新实现
└── 监控错误率和性能

Phase 2: 主切流 (Week 2)
├── 新实现流量提升到 50%
├── 对比新旧实现结果
└── 修复发现的问题

Phase 3: 全量切换 (Week 3)
├── 新实现流量 100%
├── 旧实现标记为 deprecated
└── 移除旧实现代码

Phase 4: 清理 (Week 4)
├── 删除旧实现文件
├── 清理兼容层代码
└── 更新所有文档
```

### 7.2 回滚方案

```python
# config/feature_flags.yaml
feature_flags:
  use_v2_agents:
    enabled: true
    rollout_percentage: 10  # 可以快速调整
    safe_mode: true          # 出错自动回滚
```

---

## 📖 附录

### A. 完整文件清单

```
core/agents/
├── __init__.py
├── base.py              # BaseAgent基类
├── factory.py           # 智能体工厂
├── registry.py          # 注册中心 (内嵌在base.py)
├── xiaona/
│   ├── __init__.py
│   ├── legal_agent.py   # 小娜法律智能体
│   └── capabilities.py  # 能力定义
├── xiaonuo/
│   ├── __init__.py
│   ├── orchestrator_agent.py  # 小诺编排智能体
│   └── capabilities.py
├── yunxi/
│   ├── __init__.py
│   ├── ip_agent.py      # 云熙IP管理智能体
│   └── capabilities.py
└── legacy/
    ├── compat.py        # 兼容层
    └── deprecated/      # 旧实现(临时保留)

tests/
├── unit/
│   └── agents/
│       ├── test_base_agent.py
│       ├── test_factory.py
│       └── test_registry.py
└── integration/
    └── agents/
        ├── test_xiaona_workflow.py
        └── test_multi_agent.py
```

### B. 配置示例

```yaml
# config/agents.yaml
agents:
  xiaona-legal:
    enabled: true
    config:
      llm_model: "claude-3.5-sonnet"
      max_retries: 3
      timeout: 30

  xiaonuo-orchestrator:
    enabled: true
    config:
      max_concurrent_tasks: 10
      task_timeout: 60

  yunxi-ip:
    enabled: false  # 按需启用
    config:
      database_uri: "postgresql://localhost/ip_db"
```

---

**文档版本**: v1.0
**创建日期**: 2025-02-21
**维护者**: 徐健 (xujian519@gmail.com)
