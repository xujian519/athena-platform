# Agent通信协议规范

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 基于已有代码提炼的协议规范

---

## 📋 目录

1. [概述](#概述)
2. [消息格式定义](#消息格式定义)
3. [消息类型](#消息类型)
4. [通信模式](#通信模式)
5. [错误处理协议](#错误处理协议)
6. [序列化规范](#序列化规范)
7. [安全规范](#安全规范)
8. [最佳实践](#最佳实践)

---

## 概述

### 设计目标

Agent通信协议旨在：

- ✅ **统一格式**: 所有Agent间通信使用统一的消息格式
- ✅ **类型安全**: 明确的消息类型，避免歧义
- ✅ **可扩展**: 支持未来新增消息类型
- ✅ **易于调试**: 清晰的消息结构便于调试
- ✅ **性能优化**: 支持高效的消息序列化

### 通信场景

Agent间通信发生在以下场景：

1. **用户 → Agent**: 用户请求通过小诺传递给具体Agent
2. **Agent → Agent**: Agent间传递中间结果
3. **Agent → 用户**: Agent返回执行结果
4. **Agent → 系统**: Agent报告状态和错误

### 参考实现

本规范基于以下代码提炼：

- `core/agents/xiaona/base_component.py` - AgentExecutionContext, AgentExecutionResult
- `core/orchestration/workflow_builder.py` - WorkflowStep, WorkflowResult
- `core/orchestration/execution_monitor.py` - ExecutionMonitor

---

## 消息格式定义

### 1. 执行上下文（ExecutionContext）

用于传递给Agent的输入消息：

```python
from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class AgentExecutionContext:
    """Agent执行上下文 - 输入消息格式"""

    # === 基础信息 ===
    session_id: str                      # 会话ID - 唯一标识一次会话
    task_id: str                         # 任务ID - 唯一标识一个任务

    # === 输入数据 ===
    input_data: Dict[str, Any]          # 输入数据 - 包含用户输入和中间结果
                                        # 示例: {"user_input": "检索自动驾驶专利", "previous_results": {}}

    # === 配置参数 ===
    config: Dict[str, Any]              # 配置参数 - 控制Agent行为
                                        # 示例: {"databases": ["cnipa", "wipo"], "limit": 50}

    # === 元数据 ===
    metadata: Dict[str, Any]            # 元数据 - 附加信息
                                        # 示例: {"priority": "high", "deadline": "2026-04-22"}

    # === 时间戳 ===
    start_time: Optional[datetime] = None  # 开始时间 - Agent开始执行时设置
    end_time: Optional[datetime] = None    # 结束时间 - Agent完成执行时设置
```

#### input_data 字段规范

```python
# 标准输入字段
input_data = {
    # 必需字段
    "user_input": str,              # 用户输入 - 用户的原始请求

    # 可选字段 - 传递前序Agent的结果
    "previous_results": {
        "agent_id": {               # 前序Agent的ID
            "output_data": dict,    # 该Agent的输出数据
            "metadata": dict,       # 该Agent的元数据
        }
    },

    # 可选字段 - 附加信息
    "attachments": list,            # 附件列表 - 文件、图片等
    "context": str,                 # 背景信息 - 补充说明
}
```

#### config 字段规范

```python
# 标准配置字段
config = {
    # 执行控制
    "timeout": float,               # 超时时间（秒）- 默认300.0
    "retry_count": int,             # 重试次数 - 默认3
    "execution_mode": str,          # 执行模式 - "sequential"/"parallel"/"iterative"

    # 业务配置
    "databases": list,              # 数据库列表
    "limit": int,                   # 结果数量限制
    "threshold": float,             # 阈值参数

    # LLM配置
    "model": str,                   # 模型名称 - 默认"kimi-k2.5"
    "temperature": float,           # 温度参数 - 默认0.7
    "max_tokens": int,              # 最大tokens - 默认4000
}
```

---

### 2. 执行结果（ExecutionResult）

用于Agent返回的输出消息：

```python
from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class AgentExecutionResult:
    """Agent执行结果 - 输出消息格式"""

    # === 基础信息 ===
    agent_id: str                        # Agent ID - 执行任务的Agent标识
    status: AgentStatus                  # 执行状态 - IDLE/BUSY/ERROR/COMPLETED

    # === 输出数据 ===
    output_data: Optional[Dict[str, Any]] # 输出数据 - Agent执行的结果
                                         # 示例: {"patents": [...], "total_count": 50}

    # === 错误信息 ===
    error_message: Optional[str] = None  # 错误信息 - 当status=ERROR时提供

    # === 性能指标 ===
    execution_time: float = 0.0          # 执行时间（秒）- 从start_time到end_time的耗时

    # === 元数据 ===
    metadata: Dict[str, Any] = None      # 元数据 - 附加信息
                                         # 示例: {"search_databases": ["cnipa", "wipo"]}

    def __post_init__(self):
        """确保metadata不为None"""
        if self.metadata is None:
            self.metadata = {}
```

#### output_data 字段规范

```python
# 标准输出字段
output_data = {
    # 结果数据
    "result": Any,                   # 主要结果 - 根据任务类型而定

    # 统计信息
    "total_count": int,             # 总数量
    "filtered_count": int,          # 筛选后数量
    "success_count": int,           # 成功数量

    # 详细数据
    "items": list,                  # 结果列表 - 分页数据
    "details": dict,                # 详细信息

    # 中间结果
    "intermediate_results": dict,   # 中间结果 - 调试用
}
```

#### status 字段规范

```python
# Agent状态枚举
class AgentStatus(Enum):
    IDLE = "idle"                  # 空闲 - Agent未执行任务
    BUSY = "busy"                  # 忙碌 - Agent正在执行任务
    ERROR = "error"                # 错误 - Agent执行失败
    COMPLETED = "completed"        # 完成 - Agent执行成功
```

---

### 3. 工作流步骤（WorkflowStep）

用于编排系统的工作流定义：

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class WorkflowStep:
    """工作流步骤 - 工作流中的一个执行单元"""

    # === 基础信息 ===
    step_id: str                              # 步骤ID - 唯一标识
    agent_id: str                             # Agent ID - 要执行的Agent
    context: AgentExecutionContext            # 执行上下文 - 传递给Agent的输入

    # === 依赖管理 ===
    dependencies: List[str] = field(default_factory=list)  # 依赖的步骤ID
                                                          # 示例: ["step_1_retriever"]

    # === 执行控制 ===
    retry_count: int = 0                      # 当前重试次数
    max_retries: int = 3                      # 最大重试次数
    timeout: float = 300.0                    # 超时时间（秒）
```

---

### 4. 工作流结果（WorkflowResult）

用于工作流执行结果：

```python
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class WorkflowResult:
    """工作流执行结果 - 工作流的完整执行结果"""

    # === 基础信息 ===
    workflow_id: str                          # 工作流ID
    scenario: Scenario                        # 场景类型 - PATENT_SEARCH/CREATIVITY_ANALYSIS等

    # === 执行状态 ===
    status: AgentStatus                       # 执行状态 - IDLE/BUSY/ERROR/COMPLETED

    # === 步骤结果 ===
    steps: Dict[str, AgentExecutionResult]   # 各步骤执行结果 - key为step_id

    # === 最终输出 ===
    final_output: Optional[Dict[str, Any]]   # 最终输出 - 工作流的最终结果

    # === 性能指标 ===
    total_time: float = 0.0                  # 总执行时间（秒）

    # === 错误信息 ===
    error_message: Optional[str] = None      # 错误信息 - 任何步骤出错时的错误描述

    # === 元数据 ===
    metadata: Dict[str, Any] = field(default_factory=dict)
```

---

## 消息类型

### 1. 请求消息（REQUEST）

**用途**: 用户或系统向Agent发送请求

**字段要求**:
- ✅ 必需: `session_id`, `task_id`, `input_data`
- ✅ 可选: `config`, `metadata`

**示例**:
```python
context = AgentExecutionContext(
    session_id="SESSION_20260421_001",
    task_id="TASK_20260421_001",
    input_data={
        "user_input": "检索关于自动驾驶掉头的专利",
        "previous_results": {},
    },
    config={
        "databases": ["cnipa", "wipo"],
        "limit": 50,
    },
    metadata={
        "priority": "high",
    },
)
```

---

### 2. 响应消息（RESPONSE）

**用途**: Agent返回执行结果

**字段要求**:
- ✅ 必需: `agent_id`, `status`, `execution_time`
- ✅ 可选: `output_data`, `error_message`, `metadata`

**示例 - 成功响应**:
```python
result = AgentExecutionResult(
    agent_id="xiaona_retriever",
    status=AgentStatus.COMPLETED,
    output_data={
        "patents": [...],
        "total_count": 50,
    },
    execution_time=15.3,
    metadata={
        "search_databases": ["cnipa", "wipo"],
    },
)
```

**示例 - 错误响应**:
```python
result = AgentExecutionResult(
    agent_id="xiaona_retriever",
    status=AgentStatus.ERROR,
    output_data=None,
    error_message="数据库连接失败: CNIPA",
    execution_time=5.2,
)
```

---

### 3. 通知消息（NOTIFICATION）

**用途**: Agent向系统发送状态通知

**使用场景**:
- Agent状态变更（IDLE → BUSY → COMPLETED）
- Agent进度报告（处理进度百分比）
- Agent警告信息（非致命错误）

**实现方式**:
```python
# 通过日志系统发送
self.logger.info(f"Agent状态变更: {self.status} → {new_status}")
self.logger.warning(f"检索结果较少: 找到5个专利，建议扩展关键词")
```

---

### 4. 错误消息（ERROR）

**用途**: Agent报告执行错误

**字段要求**:
- ✅ 必需: `status=AgentStatus.ERROR`
- ✅ 必需: `error_message` - 清晰描述错误
- ✅ 推荐: `metadata["error_type"]` - 错误类型
- ✅ 推荐: `metadata["error_traceback"]` - 错误堆栈（调试用）

**示例**:
```python
result = AgentExecutionResult(
    agent_id="xiaona_retriever",
    status=AgentStatus.ERROR,
    output_data=None,
    error_message="检索失败: 数据库查询超时",
    execution_time=300.0,
    metadata={
        "error_type": "TimeoutError",
        "error_code": "DB_TIMEOUT",
        "timeout_seconds": 300.0,
        "database": "cnipa",
    },
)
```

---

## 通信模式

### 1. 串行模式（Sequential）

**描述**: Agent按顺序依次执行

**特点**:
- ✅ 简单清晰
- ✅ 后续Agent可以使用前序Agent的结果
- ❌ 总执行时间长（所有Agent执行时间之和）

**工作流**:
```
Agent1 → Agent2 → Agent3 → Agent4
   ↓        ↓        ↓        ↓
 Result1 → Result2 → Result3 → Result4
```

**代码示例**:
```python
# workflow_builder.py
def _build_sequential_workflow(...):
    steps = []
    for i, agent_id in enumerate(agent_ids):
        step = WorkflowStep(
            step_id=f"step_{i+1}_{agent_id}",
            agent_id=agent_id,
            context=context,
            dependencies=[f"step_{i}_{agent_ids[i-1]}"] if i > 0 else [],
        )
        steps.append(step)
    return steps
```

---

### 2. 并行模式（Parallel）

**描述**: 多个Agent同时执行

**特点**:
- ✅ 执行时间短（最慢的Agent执行时间）
- ✅ 适合独立任务
- ❌ Agent间无法传递结果

**工作流**:
```
   → Agent1 ──→
   → Agent2 ──→ 汇总结果
   → Agent3 ──→
```

**代码示例**:
```python
# workflow_builder.py
def _build_parallel_workflow(...):
    steps = []
    for i, agent_id in enumerate(agent_ids):
        step = WorkflowStep(
            step_id=f"step_{i+1}_{agent_id}",
            agent_id=agent_id,
            context=context,
            dependencies=[],  # 无依赖
        )
        steps.append(step)
    return steps
```

---

### 3. 迭代模式（Iterative）

**描述**: Agent循环执行直到满足条件

**特点**:
- ✅ 适合需要优化的任务
- ✅ 可以逐步改进结果
- ❌ 执行时间不确定
- ❌ 需要明确的终止条件

**工作流**:
```
Agent执行 → 检查结果 → 满足条件？
   ↓                    ↓
  否                   是 → 结束
   ↓
重新执行
```

**使用场景**:
- 检索结果不满意，扩展关键词重新检索
- 分析结果不理想，调整策略重新分析

---

### 4. 混合模式（Hybrid）

**描述**: 串行+并行组合

**特点**:
- ✅ 灵活性最高
- ✅ 可以优化执行时间
- ❌ 复杂度高

**工作流**:
```
[并行] Planner + Retriever
   ↓           ↓
[串行] Analyzer → RuleAgent → Writer
```

**代码示例**:
```python
# workflow_builder.py
def _build_hybrid_workflow(...):
    steps = []

    # 第一阶段：并行
    for agent_id in ["xiaona_planner", "xiaona_retriever"]:
        steps.append(WorkflowStep(
            step_id=f"step_1_{agent_id}",
            agent_id=agent_id,
            context=context,
            dependencies=[],
        ))

    # 第二阶段：串行
    for agent_id in ["xiaona_analyzer", "xiaona_writer"]:
        steps.append(WorkflowStep(
            step_id=f"step_2_{agent_id}",
            agent_id=agent_id,
            context=context,
            dependencies=["step_1_xiaona_planner", "step_1_xiaona_retriever"],
        ))

    return steps
```

---

## 错误处理协议

### 1. 错误分类

| 错误类型 | 错误码 | 描述 | 处理策略 |
|---------|-------|------|---------|
| 输入错误 | `INVALID_INPUT` | 输入数据不符合要求 | 不重试，返回错误 |
| 配置错误 | `INVALID_CONFIG` | 配置参数错误 | 不重试，返回错误 |
| 网络错误 | `NETWORK_ERROR` | 网络连接失败 | 重试3次 |
| 超时错误 | `TIMEOUT_ERROR` | 执行超时 | 重试1次，增加超时时间 |
| 资源错误 | `RESOURCE_ERROR` | 资源不可用（数据库、LLM） | 重试3次 |
| 逻辑错误 | `LOGIC_ERROR` | Agent内部逻辑错误 | 不重试，返回错误 |
| 未知错误 | `UNKNOWN_ERROR` | 未分类的错误 | 重试1次 |

### 2. 错误响应格式

```python
result = AgentExecutionResult(
    agent_id="xiaona_retriever",
    status=AgentStatus.ERROR,
    output_data=None,
    error_message="检索失败: 数据库连接超时",
    execution_time=300.0,
    metadata={
        # 错误分类
        "error_type": "TIMEOUT_ERROR",
        "error_code": "DB_TIMEOUT",

        # 错误详情
        "error_message": "数据库连接超时",
        "error_details": {
            "database": "cnipa",
            "timeout_seconds": 300.0,
            "connection_string": "jdbc:postgresql://localhost:5432/athena",
        },

        # 调试信息
        "error_traceback": "...",  # 仅在调试模式
        "suggestion": "建议检查数据库连接或增加超时时间",

        # 重试信息
        "retry_count": 3,
        "max_retries": 3,
        "can_retry": False,  # 是否可以重试
    },
)
```

### 3. 错误处理流程

```
Agent执行
   ↓
捕获异常
   ↓
分类错误
   ↓
可以重试？
   ↓ 是
重试 → 成功？
   ↓        ↓ 是
 否        返回成功
   ↓
返回错误
```

### 4. 错误恢复策略

```python
async def execute_with_retry(self, context: AgentExecutionContext) -> AgentExecutionResult:
    """带重试的执行"""
    max_retries = context.config.get("max_retries", 3)

    for attempt in range(max_retries):
        try:
            result = await self.execute(context)
            if result.status == AgentStatus.COMPLETED:
                return result
            else:
                # 判断是否可以重试
                can_retry = result.metadata.get("can_retry", False)
                if not can_retry:
                    return result

        except Exception as e:
            self.logger.warning(f"执行失败(尝试 {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                # 最后一次尝试失败
                return AgentExecutionResult(
                    agent_id=self.agent_id,
                    status=AgentStatus.ERROR,
                    error_message=f"执行失败（已重试{max_retries}次）: {str(e)}",
                )

    # 不应该到这里
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.ERROR,
        error_message="未知错误",
    )
```

---

## 序列化规范

### 1. JSON序列化

**用途**: Agent间通信、日志记录、调试

**支持的数据类型**:
- ✅ 基本类型: `str`, `int`, `float`, `bool`, `None`
- ✅ 容器类型: `list`, `dict`
- ✅ 日期时间: `datetime` → ISO 8601字符串
- ✅ 枚举类型: `Enum` → 字符串值
- ✅ 数据类: `@dataclass` → 字典

**示例**:
```python
import json
from datetime import datetime
from dataclasses import asdict

# 序列化
context = AgentExecutionContext(...)
context_dict = {
    "session_id": context.session_id,
    "task_id": context.task_id,
    "input_data": context.input_data,
    "config": context.config,
    "metadata": context.metadata,
    "start_time": context.start_time.isoformat() if context.start_time else None,
    "end_time": context.end_time.isoformat() if context.end_time else None,
}
context_json = json.dumps(context_dict, ensure_ascii=False, indent=2)

# 反序列化
context_dict = json.loads(context_json)
context = AgentExecutionContext(
    session_id=context_dict["session_id"],
    task_id=context_dict["task_id"],
    input_data=context_dict["input_data"],
    config=context_dict["config"],
    metadata=context_dict["metadata"],
    start_time=datetime.fromisoformat(context_dict["start_time"]) if context_dict["start_time"] else None,
    end_time=datetime.fromisoformat(context_dict["end_time"]) if context_dict["end_time"] else None,
)
```

### 2. Pickle序列化

**用途**: 进程间通信、缓存

**示例**:
```python
import pickle

# 序列化
result = AgentExecutionResult(...)
result_bytes = pickle.dumps(result)

# 反序列化
result = pickle.loads(result_bytes)
```

### 3. MessagePack序列化（推荐用于高性能场景）

**用途**: 高性能通信、大数据传输

**安装**:
```bash
pip install msgpack
```

**示例**:
```python
import msgpack

# 序列化
context = AgentExecutionContext(...)
context_bytes = msgpack.packb(asdict(context))

# 反序列化
context_dict = msgpack.unpackb(context_bytes, raw=False)
context = AgentExecutionContext(**context_dict)
```

---

## 安全规范

### 1. 敏感信息保护

**禁止在消息中包含**:
- ❌ 密码、API密钥、Token
- ❌ 个人隐私信息（身份证、手机号、邮箱）
- ❌ 未授权的内部数据

**示例**:
```python
# ❌ 错误
context = AgentExecutionContext(
    input_data={
        "user_input": "检索专利",
        "api_key": "sk-1234567890",  # 不要包含敏感信息
    },
)

# ✅ 正确
context = AgentExecutionContext(
    input_data={
        "user_input": "检索专利",
        "credential_id": "CRED_001",  # 使用引用而非实际密钥
    },
)
```

### 2. 输入验证

**必须验证**:
- ✅ `session_id` 格式（防止注入攻击）
- ✅ `task_id` 格式（防止注入攻击）
- ✅ `input_data` 类型（防止类型混淆攻击）
- ✅ `config` 参数（防止配置攻击）

**示例**:
```python
import re

def validate_input(self, context: AgentExecutionContext) -> bool:
    """验证输入"""
    # 验证session_id格式
    if not re.match(r'^SESSION_[0-9]+_[0-9]+$', context.session_id):
        self.logger.error(f"无效的session_id格式: {context.session_id}")
        return False

    # 验证task_id格式
    if not re.match(r'^TASK_[0-9]+_[0-9]+$', context.task_id):
        self.logger.error(f"无效的task_id格式: {context.task_id}")
        return False

    # 验证input_data类型
    if not isinstance(context.input_data, dict):
        self.logger.error("input_data必须是字典类型")
        return False

    return True
```

### 3. 权限控制

**权限检查**:
```python
async def execute(self, context: AgentExecutionContext) -> AgentExecutionResult:
    """执行任务"""
    # 检查权限
    user_role = context.metadata.get("user_role", "guest")
    if user_role == "guest" and self.requires_premium():
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.ERROR,
            error_message="该功能需要Premium权限",
        )

    # 执行任务
    ...
```

---

## 最佳实践

### 1. 消息设计

**DO** ✅:
```python
context = AgentExecutionContext(
    session_id="SESSION_20260421_001",
    task_id="TASK_20260421_001",
    input_data={
        "user_input": "检索关于自动驾驶掉头的专利",
        "databases": ["cnipa", "wipo"],
        "limit": 50,
    },
    config={
        "timeout": 300.0,
        "max_retries": 3,
    },
)
```

**DON'T** ❌:
```python
context = AgentExecutionContext(
    session_id="xxx",  # ❌ session_id格式不规范
    task_id="yyy",     # ❌ task_id格式不规范
    input_data="检索专利",  # ❌ input_data类型错误，应该是dict
    config="some config",  # ❌ config类型错误，应该是dict
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
except TimeoutError as e:
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.ERROR,
        error_message=f"执行超时: {str(e)}",
        metadata={
            "error_type": "TIMEOUT_ERROR",
            "can_retry": True,
        },
    )
except Exception as e:
    self.logger.exception(f"执行失败: {context.task_id}")
    return AgentExecutionResult(
        agent_id=self.agent_id,
        status=AgentStatus.ERROR,
        error_message=f"执行失败: {str(e)}",
        metadata={
            "error_type": "UNKNOWN_ERROR",
            "can_retry": False,
        },
    )
```

### 3. 日志记录

**DO** ✅:
```python
self.logger.info(f"开始执行任务: {context.task_id}")
self.logger.debug(f"输入数据: {context.input_data}")
self.logger.info(f"任务完成: {context.task_id}, 耗时: {execution_time:.2f}秒")
self.logger.warning(f"检索结果较少: 找到{len(results)}个专利")
self.logger.error(f"任务执行失败: {context.task_id}, 错误: {e}")
```

### 4. 性能优化

**DO** ✅:
```python
# 使用异步操作
results = await asyncio.gather(
    self._search_database("cnipa", query),
    self._search_database("wipo", query),
    self._search_database("epo", query),
)

# 使用连接池
async with self.db_pool.acquire() as conn:
    result = await conn.fetch(query)
```

---

## 附录

### A. 完整消息示例

参见：`examples/agent_communication_examples.py`

### B. 错误码列表

参见：`docs/api/AGENT_ERROR_CODES.md`

### C. 性能基准

参见：`docs/reports/AGENT_PERFORMANCE_BENCHMARK.md`

---

**文档维护**: 本文档应随着通信协议的演进持续更新。

**反馈渠道**: 如有问题或建议，请提交Issue或PR。
