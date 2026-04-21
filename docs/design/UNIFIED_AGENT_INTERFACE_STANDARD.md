# 统一Agent接口标准

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 基于已有代码提炼的标准

---

## 📋 目录

1. [概述](#概述)
2. [核心接口](#核心接口)
3. [数据类定义](#数据类定义)
4. [生命周期管理](#生命周期管理)
5. [能力描述系统](#能力描述系统)
6. [接口合规性检查](#接口合规性检查)
7. [最佳实践](#最佳实践)

---

## 概述

### 设计目标

统一Agent接口标准旨在为Athena平台的所有Agent提供：

- ✅ **一致的接口**: 所有Agent遵循相同的接口模式
- ✅ **清晰的生命周期**: 明确的初始化、执行、清理流程
- ✅ **自描述能力**: Agent能够描述自己的能力
- ✅ **标准化结果**: 统一的执行结果格式
- ✅ **易于测试**: 清晰的接口便于编写测试

### 适用范围

本标准适用于：

- 小娜专业智能体（RetrieverAgent, AnalyzerAgent, WriterAgent等）
- 小诺智能体（XiaonuoAgent）
- 云熙智能体（YunxiAgent）
- 未来新增的所有Agent

### 参考实现

本标准基于以下代码提炼：

- `core/agents/xiaona/base_component.py` - BaseXiaonaComponent
- `core/orchestration/agent_registry.py` - AgentRegistry
- `core/orchestration/workflow_builder.py` - WorkflowBuilder

---

## 核心接口

### 1. Agent基类接口

所有Agent必须继承自统一的基类，并实现以下接口：

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class BaseAgent(ABC):
    """统一Agent基类"""

    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化Agent

        Args:
            agent_id: Agent唯一标识
            config: 配置参数
        """
        self.agent_id = agent_id
        self.config = config or {}
        self.status = AgentStatus.IDLE
        self._capabilities: List[AgentCapability] = []

        # 初始化日志
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # 调用子类初始化
        self._initialize()

    @abstractmethod
    def _initialize(self) -> None:
        """
        Agent初始化钩子（子类必须实现）

        子类应该在此方法中：
        1. 注册能力（self._register_capabilities）
        2. 初始化LLM客户端
        3. 加载提示词
        4. 初始化工具
        """
        pass

    @abstractmethod
    async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
        """
        执行Agent任务（子类必须实现）

        Args:
            context: 执行上下文

        Returns:
            执行结果
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        获取系统提示词（子类必须实现）

        Returns:
            系统提示词字符串
        """
        pass
```

### 2. 能力管理接口

```python
    def _register_capabilities(self, capabilities: List[AgentCapability]) -> None:
        """
        注册Agent能力

        Args:
            capabilities: 能力列表
        """
        self._capabilities = capabilities
        self.logger.info(f"注册 {len(capabilities)} 个能力: {[c.name for c in capabilities]}")

    def get_capabilities(self) -> List[AgentCapability]:
        """
        获取Agent能力列表

        Returns:
            能力列表
        """
        return self._capabilities.copy()

    def has_capability(self, capability_name: str) -> bool:
        """
        检查是否具备某项能力

        Args:
            capability_name: 能力名称

        Returns:
            是否具备该能力
        """
        return any(c.name == capability_name for c in self._capabilities)
```

### 3. 信息获取接口

```python
    def get_info(self) -> Dict[str, Any]:
        """
        获取Agent信息

        Returns:
            Agent信息字典
        """
        return {
            "agent_id": self.agent_id,
            "agent_type": self.__class__.__name__,
            "status": self.status.value,
            "capabilities": [
                {
                    "name": c.name,
                    "description": c.description,
                    "input_types": c.input_types,
                    "output_types": c.output_types,
                    "estimated_time": c.estimated_time,
                }
                for c in self._capabilities
            ],
            "config": self.config,
        }
```

### 4. 输入验证接口

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

        return True
```

---

## 数据类定义

### 1. AgentStatus - 状态枚举

```python
from enum import Enum

class AgentStatus(Enum):
    """Agent状态枚举"""
    IDLE = "idle"           # 空闲
    BUSY = "busy"           # 忙碌
    ERROR = "error"         # 错误
    COMPLETED = "completed" # 完成
```

### 2. AgentCapability - 能力描述

```python
from dataclasses import dataclass

@dataclass
class AgentCapability:
    """Agent能力描述"""
    name: str              # 能力名称
    description: str       # 能力描述
    input_types: List[str] # 支持的输入类型
    output_types: List[str] # 输出类型
    estimated_time: float  # 预估执行时间（秒）
```

### 3. AgentExecutionContext - 执行上下文

```python
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class AgentExecutionContext:
    """Agent执行上下文"""
    session_id: str                      # 会话ID
    task_id: str                         # 任务ID
    input_data: Dict[str, Any]          # 输入数据
    config: Dict[str, Any]              # 配置参数
    metadata: Dict[str, Any]            # 元数据
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
```

### 4. AgentExecutionResult - 执行结果

```python
@dataclass
class AgentExecutionResult:
    """Agent执行结果"""
    agent_id: str                        # Agent ID
    status: AgentStatus                  # 执行状态
    output_data: Optional[Dict[str, Any]] # 输出数据
    error_message: Optional[str] = None  # 错误信息
    execution_time: float = 0.0          # 执行时间（秒）
    metadata: Dict[str, Any] = None      # 元数据

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
```

---

## 生命周期管理

### 1. 初始化阶段

```
__init__(agent_id, config)
    ↓
_initialize()  # 子类实现
    ↓
    - 注册能力
    - 初始化LLM
    - 加载提示词
    - 初始化工具
```

**要求**:
- ✅ 子类必须实现 `_initialize()` 方法
- ✅ 在 `_initialize()` 中注册至少一个能力
- ✅ 在 `_initialize()` 中初始化所有依赖

### 2. 执行阶段

```
调用 _execute_with_monitoring(context)
    ↓
validate_input(context)  # 验证输入
    ↓
execute(context)  # 子类实现
    ↓
返回 AgentExecutionResult
```

**要求**:
- ✅ 子类必须实现 `execute()` 方法（异步）
- ✅ `execute()` 方法必须返回 `AgentExecutionResult`
- ✅ 正常执行返回 `status=AgentStatus.COMPLETED`
- ✅ 执行失败返回 `status=AgentStatus.ERROR`

### 3. 错误处理

```python
try:
    result = await self.execute(context)
    # 记录执行时间
    result.execution_time = execution_time
    return result
except Exception as e:
    # 返回错误结果
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.ERROR,
        output_data=None,
        error_message=str(e),
        execution_time=execution_time,
    )
```

**要求**:
- ✅ 所有异常必须被捕获
- ✅ 异常必须返回 `AgentExecutionResult`，不能抛出
- ✅ 错误信息必须清晰描述问题

---

## 能力描述系统

### 1. 能力注册

```python
def _initialize(self) -> None:
    """初始化Agent"""
    self._register_capabilities([
        AgentCapability(
            name="patent_search",
            description="专利检索",
            input_types=["查询关键词", "技术领域"],
            output_types=["专利列表", "检索报告"],
            estimated_time=15.0,
        ),
        AgentCapability(
            name="keyword_expansion",
            description="关键词扩展",
            input_types=["初始关键词"],
            output_types=["扩展关键词列表"],
            estimated_time=5.0,
        ),
    ])
```

### 2. 能力查询

```python
# 获取所有能力
capabilities = agent.get_capabilities()

# 检查是否具备某项能力
has_search = agent.has_capability("patent_search")

# 获取Agent信息
info = agent.get_info()
```

### 3. 能力命名规范

- ✅ 使用小写字母和下划线：`patent_search`
- ✅ 使用动词+名词：`search_patents`, `analyze_claims`
- ✅ 名称应该清晰描述功能
- ❌ 避免缩写：`pat_search` → `patent_search`

---

## 接口合规性检查

### 检查清单

实现新Agent时，必须满足以下要求：

#### 基础要求

- [ ] 继承自 `BaseXiaonaComponent`
- [ ] 实现 `_initialize()` 方法
- [ ] 实现 `execute()` 方法（异步）
- [ ] 实现 `get_system_prompt()` 方法
- [ ] 在 `_initialize()` 中注册至少一个能力

#### 代码质量

- [ ] 所有公共方法有类型注解
- [ ] 所有公共方法有文档字符串
- [ ] 异步方法使用 `async def`
- [ ] 错误处理不抛出异常，返回 `AgentExecutionResult`

#### 测试要求

- [ ] 单元测试覆盖率 > 80%
- [ ] 测试包含正常流程
- [ ] 测试包含异常流程
- [ ] 测试包含边界情况

### 自动化检查

使用以下工具检查接口合规性：

```bash
# 运行接口合规性测试
pytest tests/agents/test_interface_compliance.py -v

# 检查测试覆盖率
pytest tests/agents/test_your_agent.py --cov=core.agents.your_agent --cov-report=html
```

---

## 最佳实践

### 1. 能力设计

**DO** ✅:
```python
AgentCapability(
    name="patent_search",
    description="在多个专利数据库中检索相关专利",
    input_types=["查询关键词", "技术领域", "数据库列表"],
    output_types=["专利列表", "检索统计"],
    estimated_time=15.0,
)
```

**DON'T** ❌:
```python
AgentCapability(
    name="do_something",  # 名称不清晰
    description="做一些事情",  # 描述模糊
    input_types=["input"],  # 输入类型不明确
    output_types=["output"],  # 输出类型不明确
    estimated_time=0.0,  # 时间估算不准确
)
```

### 2. 错误处理

**DO** ✅:
```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    try:
        # 执行任务
        result = await self._do_work(context)
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data=result,
        )
    except Exception as e:
        self.logger.exception(f"任务执行失败: {context.task_id}")
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            output_data=None,
            error_message=f"任务执行失败: {str(e)}",
        )
```

**DON'T** ❌:
```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    # 直接抛出异常
    result = await self._do_work(context)
    if not result:
        raise ValueError("结果为空")  # ❌ 不要抛出异常
```

### 3. 日志记录

**DO** ✅:
```python
self.logger.info(f"开始执行任务: {context.task_id}")
self.logger.debug(f"输入数据: {context.input_data}")
self.logger.warning(f"未找到相关结果: {context.task_id}")
self.logger.error(f"任务执行失败: {context.task_id}, 错误: {e}")
```

**DON'T** ❌:
```python
print(f"开始执行任务: {context.task_id}")  # ❌ 使用logger而非print
```

### 4. 异步执行

**DO** ✅:
```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    # 使用await调用异步方法
    keywords = await self._expand_keywords(user_input)
    results = await self._execute_search(keywords)
    return AgentExecutionResult(...)
```

**DON'T** ❌:
```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    # 不要在异步函数中阻塞
    results = blocking_search(keywords)  # ❌ 阻塞调用
    return AgentExecutionResult(...)
```

---

## 附录

### A. 完整示例

参见：`core/agents/xiaona/retriever_agent.py`

### B. 测试示例

参见：`tests/agents/test_interface_compliance.py`

### C. 迁移指南

参见：`docs/guides/AGENT_INTERFACE_MIGRATION_GUIDE.md`

---

**文档维护**: 本文档应随着Agent接口的演进持续更新。

**反馈渠道**: 如有问题或建议，请提交Issue或PR。
