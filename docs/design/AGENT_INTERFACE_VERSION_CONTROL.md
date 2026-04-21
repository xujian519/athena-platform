# Agent接口版本控制策略

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 正式发布

---

## 📋 目录

1. [概述](#概述)
2. [版本号规范](#版本号规范)
3. [向后兼容性](#向后兼容性)
4. [废弃策略](#废弃策略)
5. [迁移指南](#迁移指南)
6. [版本检测](#版本检测)

---

## 概述

### 目标

Agent接口版本控制旨在：

- ✅ **平滑演进**: 支持接口的渐进式演进
- ✅ **向后兼容**: 尽量保持向后兼容性
- ✅ **清晰标识**: 明确标识接口版本
- ✅ **平稳迁移**: 提供清晰的迁移路径

### 适用范围

本策略适用于：

- 统一Agent接口（`BaseXiaonaComponent`）
- Agent通信协议（`AgentExecutionContext`, `AgentExecutionResult`）
- Agent注册表（`AgentRegistry`）
- 工作流构建器（`WorkflowBuilder`）

---

## 版本号规范

### 语义化版本

采用[语义化版本](https://semver.org/lang/zh-CN/)（Semantic Versioning）规范：

```
主版本号.次版本号.修订号 (MAJOR.MINOR.PATCH)

示例: 1.2.3
```

**版本号规则**:

| 变更类型 | 版本号变更 | 示例 | 说明 |
|---------|-----------|------|------|
| **破坏性变更** | 主版本号+1 | 1.2.3 → 2.0.0 | 不兼容的API修改 |
| **新增功能** | 次版本号+1 | 1.2.3 → 1.3.0 | 向后兼容的功能新增 |
| **问题修复** | 修订号+1 | 1.2.3 → 1.2.4 | 向后兼容的问题修复 |

### 当前版本

```
统一Agent接口: v1.0.0
Agent通信协议: v1.0.0
```

---

## 向后兼容性

### 兼容性原则

**DO** ✅:
- ✅ 新增可选字段（数据类）
- ✅ 新增方法（接口）
- ✅ 新增枚举值
- ✅ 新增可选参数
- ✅ 扩展返回值类型（使用继承）

**DON'T** ❌:
- ❌ 删除现有字段
- ❌ 修改字段类型
- ❌ 删除现有方法
- ❌ 修改方法签名（不兼容的变更）
- ❌ 修改必需参数

### 兼容性示例

#### ✅ 向后兼容的变更

**新增可选字段**:
```python
# v1.0.0
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]

# v1.1.0 - 向后兼容
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    priority: str = "normal"  # 新增可选字段，有默认值
```

**新增方法**:
```python
# v1.0.0
class BaseAgent:
    def execute(self, context): pass

# v1.1.0 - 向后兼容
class BaseAgent:
    def execute(self, context): pass
    def execute_batch(self, contexts): pass  # 新增方法
```

**新增枚举值**:
```python
# v1.0.0
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"

# v1.1.0 - 向后兼容
class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    SUSPENDED = "suspended"  # 新增状态
```

#### ❌ 破坏性变更

**删除字段**:
```python
# v1.0.0
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    timeout: float

# v2.0.0 - 破坏性变更
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    # timeout字段被删除
```

**修改字段类型**:
```python
# v1.0.0
@dataclass
class AgentCapability:
    name: str
    estimated_time: float

# v2.0.0 - 破坏性变更
@dataclass
class AgentCapability:
    name: str
    estimated_time: int  # 类型从float改为int
```

**修改方法签名**:
```python
# v1.0.0
class BaseAgent:
    def execute(self, context: AgentExecutionContext): pass

# v2.0.0 - 破坏性变更
class BaseAgent:
    def execute(  # 签名不兼容
        self,
        context: AgentExecutionContext,
        options: Dict[str, Any]  # 新增必需参数
    ): pass
```

---

## 废弃策略

### 废弃流程

```
1. 标记废弃 (Deprecated)
   ↓
2. 文档说明
   ↓
3. 提供替代方案
   ↓
4. 等待过渡期（至少2个次版本）
   ↓
5. 移除（下一个主版本）
```

### 废弃标记

使用 `@deprecated` 装饰器标记废弃的API：

```python
import warnings
from functools import wraps

def deprecated(reason: str, version: str):
    """
    标记废弃的API

    Args:
        reason: 废弃原因
        version: 废弃的版本
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} 已废弃（v{version}）: {reason}",
                DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


# 使用示例
class BaseAgent:
    @deprecated(
        reason="请使用 get_agent_info() 方法",
        version="1.1.0"
    )
    def get_info(self) -> Dict[str, Any]:
        """已废弃：获取Agent信息"""
        return {"agent_id": self.agent_id}
```

### 废弃示例

#### 示例1: 废弃字段

```python
# v1.0.0
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    old_field: str  # 旧字段

# v1.1.0 - 标记废弃
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    new_field: str  # 新字段
    old_field: str = ""  # 保留但标记废弃

    def __post_init__(self):
        if self.old_field and not self.new_field:
            warnings.warn(
                "old_field 已废弃（v1.1.0），请使用 new_field",
                DeprecationWarning
            )

# v2.0.0 - 移除
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    new_field: str  # 旧字段已被移除
```

#### 示例2: 废弃方法

```python
# v1.0.0
class BaseAgent:
    def old_method(self): pass

# v1.1.0 - 标记废弃，提供新方法
class BaseAgent:
    @deprecated(
        reason="请使用 new_method() 方法",
        version="1.1.0"
    )
    def old_method(self):
        """已废弃：旧方法"""
        return self.new_method()

    def new_method(self): pass

# v2.0.0 - 移除
class BaseAgent:
    def new_method(self): pass  # 旧方法已被移除
```

---

## 迁移指南

### 版本迁移流程

```
1. 阅读版本发布说明
   ↓
2. 检查废弃警告
   ↓
3. 更新代码
   ↓
4. 运行测试
   ↓
5. 部署新版本
```

### v1.0 → v1.1 迁移

**假设的变更**:

```python
# v1.0.0
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": "..."},
)

# v1.1.0 - 新增可选字段
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": "..."},
    priority="high",  # 新增字段
)
```

**迁移步骤**:

1. **检查废弃警告**:
```bash
# 运行时启用废弃警告
python -W default::DeprecationWarning your_app.py
```

2. **更新代码**（可选）:
```python
# 如果需要使用新功能
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": "..."},
    priority="high",  # 使用新字段
)
```

3. **运行测试**:
```bash
pytest tests/ -v
```

### v1.x → v2.0 迁移

**假设的破坏性变更**:

```python
# v1.x
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    timeout: float  # 旧字段

# v2.0.0
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any]  # 新字段，timeout移入config
```

**迁移步骤**:

1. **阅读迁移指南**:
```markdown
# v2.0.0 迁移指南

## 变更说明
timeout字段从AgentExecutionContext移到了config中

## 迁移步骤
1. 将 context.timeout 改为 context.config["timeout"]
2. 更新所有创建context的代码
```

2. **更新代码**:
```python
# 旧代码
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": "..."},
    timeout=300.0,
)

# 新代码
context = AgentExecutionContext(
    session_id="SESSION_001",
    task_id="TASK_001",
    input_data={"user_input": "..."},
    config={"timeout": 300.0},
)
```

3. **运行测试**:
```bash
pytest tests/ -v
```

4. **更新测试数据**:
```python
# 更新测试fixtures
@pytest.fixture
def execution_context():
    return AgentExecutionContext(
        session_id="SESSION_001",
        task_id="TASK_001",
        input_data={"user_input": "..."},
        config={"timeout": 300.0},
    )
```

---

## 版本检测

### Agent版本信息

每个Agent应该报告其接口版本：

```python
class BaseAgent:
    # 接口版本
    INTERFACE_VERSION = "1.0.0"

    def get_interface_version(self) -> str:
        """获取Agent支持的接口版本"""
        return self.INTERFACE_VERSION
```

### 版本兼容性检查

```python
from packaging import version

def check_interface_compatibility(
    required_version: str,
    agent_version: str
) -> bool:
    """
    检查接口版本兼容性

    Args:
        required_version: 需要的版本
        agent_version: Agent的版本

    Returns:
        是否兼容
    """
    # 主版本号必须相同
    required = version.parse(required_version)
    agent = version.parse(agent_version)

    if required.major != agent.major:
        return False

    # Agent的次版本号应该 >= 需要的次版本号
    if agent.minor < required.minor:
        return False

    return True


# 使用示例
agent_version = agent.get_interface_version()
required_version = "1.2.0"

if not check_interface_compatibility(required_version, agent_version):
    raise ValueError(
        f"接口版本不兼容: 需要 {required_version}, "
        f"Agent提供 {agent_version}"
    )
```

### 上下文版本检测

```python
@dataclass
class AgentExecutionContext:
    session_id: str
    task_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any]
    metadata: Dict[str, Any]
    protocol_version: str = "1.0.0"  # 协议版本

    def __post_init__(self):
        """验证协议版本"""
        supported_versions = ["1.0.0", "1.1.0"]
        if self.protocol_version not in supported_versions:
            raise ValueError(
                f"不支持的协议版本: {self.protocol_version}, "
                f"支持的版本: {supported_versions}"
            )
```

---

## 最佳实践

### 1. 版本号管理

**DO** ✅:
```python
# 在模块级别定义版本号
__version__ = "1.0.0"

# 在类中使用版本号
class BaseAgent:
    INTERFACE_VERSION = __version__
```

**DON'T** ❌:
```python
# 不要硬编码版本号
class BaseAgent:
    def some_method(self):
        if version == "1.0.0":  # 硬编码
            pass
```

### 2. 废弃通知

**DO** ✅:
```python
# 提前通知废弃
@deprecated(
    reason="请使用 new_method()，旧方法将在v2.0.0移除",
    version="1.1.0"
)
def old_method(self): pass
```

**DON'T** ❌:
```python
# 不要突然移除
# v1.0.0: 有 old_method()
# v2.0.0: 直接删除（没有过渡期）
```

### 3. 版本文档

**DO** ✅:
```markdown
# 每个版本都应该有:
- 版本发布说明（CHANGELOG.md）
- 迁移指南（MIGRATION_v1_to_v2.md）
- API变更日志（API_CHANGES.md）
```

**DON'T** ❌:
```python
# 不要在没有文档的情况下发布新版本
# 更不要进行破坏性变更而不提供迁移指南
```

---

## 附录

### A. 版本号示例

| 版本号 | 变更类型 | 说明 |
|--------|---------|------|
| 1.0.0 | 初始版本 | 首个稳定版本 |
| 1.0.1 | Bug修复 | 修复了execute()方法的bug |
| 1.1.0 | 新增功能 | 新增execute_batch()方法 |
| 1.2.0 | 新增功能 | 新增SUSPENDED状态 |
| 2.0.0 | 破坏性变更 | 修改了AgentExecutionContext的字段 |

### B. 变更日志模板

```markdown
# [版本号] - 发布日期

## 新增功能
- 新增XXX功能
- 新增YYY方法

## 破坏性变更
- XXX字段已废弃，请使用YYY
- ZZZ方法签名已修改

## 废弃
- AAA方法将在v2.0.0移除

## Bug修复
- 修复了XXX的bug
- 修复了YYY的问题

## 文档更新
- 更新了XXX文档
- 新增了YYY示例
```

### C. 相关文档

- [统一Agent接口标准](UNIFIED_AGENT_INTERFACE_STANDARD.md)
- [Agent通信协议规范](AGENT_COMMUNICATION_PROTOCOL_SPEC.md)
- [接口实现指南](../guides/AGENT_INTERFACE_IMPLEMENTATION_GUIDE.md)
- [接口迁移指南](../guides/AGENT_INTERFACE_MIGRATION_GUIDE.md)

---

**文档维护**: 本文档应随版本更新持续维护。

**反馈渠道**: 如有问题或建议，请提交Issue或PR。
