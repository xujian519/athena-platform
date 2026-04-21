# 智能体记忆系统集成指南

> **版本**: 1.0
> **最后更新**: 2026-04-21
> **作者**: 徐健

---

## 概述

本文档说明如何在Athena平台的智能体中集成统一记忆系统，实现：
1. 智能体初始化时加载记忆
2. 智能体执行时保存工作历史
3. 智能体学习成果自动更新
4. 项目上下文自动读取

---

## 快速开始

### 1. BaseAgent集成（已完成）

`BaseAgent`类已经集成了记忆系统，提供以下方法：

```python
from core.agents.base_agent import BaseAgent

# 创建带记忆的智能体
agent = BaseAgent(
    name="my_agent",
    role="助手",
    project_path="/path/to/project"  # 指定项目路径
)

# 记忆系统自动启用
if agent._memory_enabled:
    # 加载记忆
    context = agent.get_project_context()

    # 保存记忆
    agent.save_memory(
        MemoryType.PROJECT,
        MemoryCategory.PROJECT_CONTEXT,
        "key",
        "内容"
    )

    # 保存工作历史
    agent.save_work_history(
        task="任务描述",
        result="结果",
        status="success"
    )
```

### 2. 小娜智能体集成

使用`XiaonaAgentWithMemory`类：

```python
from core.agents.xiaona_agent_with_unified_memory import XiaonaAgentWithMemory

# 创建小娜智能体
xiaona = XiaonaAgentWithMemory(
    name="xiaona",
    role="专利法律专家",
    project_path="/Users/xujian/Athena工作平台"
)

# 处理任务（自动加载项目上下文和用户偏好）
result = xiaona.process("分析专利CN123456789A的创造性")

# 更新学习洞察
xiaona.update_insights(
    insight="创造性分析需要考虑现有技术的差异",
    category="patent_analysis"
)

# 查看学习摘要
print(xiaona.get_learning_summary())
```

### 3. 小诺编排者集成

使用`XiaonuoOrchestratorWithMemory`类：

```python
from core.agents.xiaonuo_orchestrator_with_memory import XiaonuoOrchestratorWithMemory

# 创建小诺编排者
xiaonuo = XiaonuoOrchestratorWithMemory(
    name="xiaonuo",
    role="智能体编排者",
    project_path="/Users/xujian/Athena工作平台"
)

# 处理任务（自动加载用户偏好和项目上下文）
result = xiaonuo.process("帮我分析专利CN123456789A的创造性")

# 查看编排统计
stats = xiaonuo.get_orchestration_statistics()
print(f"编排统计: {stats}")
```

---

## 核心API

### BaseAgent记忆方法

#### `load_memory(type, category, key)`
加载记忆内容。

```python
content = agent.load_memory(
    MemoryType.GLOBAL,
    MemoryCategory.USER_PREFERENCE,
    "user_preferences"
)
```

#### `save_memory(type, category, key, content, metadata)`
保存记忆内容。

```python
agent.save_memory(
    MemoryType.PROJECT,
    MemoryCategory.LEGAL_ANALYSIS,
    "analysis_001",
    "# 分析结果\n\n...",
    metadata={"patent_id": "CN123456789A"}
)
```

#### `save_work_history(task, result, status)`
保存工作历史。

```python
agent.save_work_history(
    task="分析专利CN123456789A",
    result="分析完成，发现3个对比文件",
    status="success"
)
```

#### `search_memory(query, type, category, limit)`
搜索记忆。

```python
results = agent.search_memory(
    query="创造性",
    type=MemoryType.PROJECT,
    category=MemoryCategory.LEGAL_ANALYSIS,
    limit=10
)
```

#### `get_project_context()`
获取项目上下文。

```python
context = agent.get_project_context()
```

#### `get_user_preferences()`
获取用户偏好。

```python
preferences = agent.get_user_preferences()
```

#### `update_learning(insights, metadata)`
更新学习成果（仅学习型智能体）。

```python
agent.update_learning(
    insights="学到了新的分析策略",
    metadata={"category": "analysis"}
)
```

---

## 记忆类型和分类

### 记忆类型（MemoryType）

- `GLOBAL`: 全局记忆（跨项目共享）
- `PROJECT`: 项目记忆（项目特定）

### 记忆分类（MemoryCategory）

- `USER_PREFERENCE`: 用户偏好
- `AGENT_LEARNING`: 智能体学习成果
- `PROJECT_CONTEXT`: 项目上下文
- `WORK_HISTORY`: 工作历史
- `AGENT_COLLABORATION`: 智能体协作记录
- `TECHNICAL_FINDINGS`: 技术发现
- `LEGAL_ANALYSIS`: 法律分析

---

## 自定义智能体集成

### 步骤1：继承BaseAgent

```python
from core.agents.base_agent import BaseAgent
from core.memory.unified_memory_system import MemoryType, MemoryCategory

class MyCustomAgent(BaseAgent):
    def __init__(self, name: str, project_path: str = None, **kwargs):
        super().__init__(
            name=name,
            role="自定义智能体",
            project_path=project_path,
            **kwargs
        )

        # 加载历史学习
        if self._memory_enabled:
            self._load_learning()
```

### 步骤2：实现process方法

```python
    def process(self, input_text: str, **kwargs) -> str:
        # 1. 读取项目上下文
        context = self.get_project_context() if self._memory_enabled else None

        # 2. 执行任务
        result = self._perform_task(input_text, context)

        # 3. 保存结果
        if self._memory_enabled:
            self.save_memory(
                MemoryType.PROJECT,
                MemoryCategory.LEGAL_ANALYSIS,
                f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                result
            )

        # 4. 保存工作历史
        if self._memory_enabled:
            self.save_work_history(
                task=input_text[:100],
                result=result[:200],
                status="success"
            )

        return result
```

### 步骤3：实现学习功能

```python
    def _load_learning(self):
        """加载历史学习"""
        content = self.load_memory(
            MemoryType.GLOBAL,
            MemoryCategory.AGENT_LEARNING,
            f"{self.name}_learning"
        )
        if content:
            self.learning_history = json.loads(content)

    def update_insights(self, insight: str):
        """更新学习洞察"""
        self.update_learning(
            insights=insight,
            metadata={"timestamp": datetime.now().isoformat()}
        )
```

---

## 最佳实践

### 1. 向后兼容

确保记忆系统是可选的：

```python
# 总是检查记忆系统是否启用
if self._memory_enabled:
    # 使用记忆系统
    context = self.get_project_context()
else:
    # 降级处理
    context = None
```

### 2. 错误处理

记忆系统故障不应影响核心功能：

```python
try:
    self.save_work_history(task, result, status)
except Exception as e:
    logger.warning(f"工作历史保存失败: {e}")
    # 继续执行，不抛出异常
```

### 3. 性能考虑

记忆加载应该是异步的（TODO）：

```python
# 当前同步版本
if self._memory_enabled:
    self._load_learning()  # 可能阻塞

# 未来异步版本（TODO）
async def async_init(self):
    if self._memory_enabled:
        await self._async_load_learning()
```

### 4. 内容格式

使用Markdown格式存储记忆：

```python
content = f"""# 专利分析结果

**专利号**: {patent_id}
**分析时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 创造性分析

{analysis_result}

## 对比文件

{comparison_results}

---

*由小娜智能体生成*
"""
```

---

## 测试

运行集成测试：

```bash
# 运行所有集成测试
pytest tests/integration/test_agent_memory_integration.py -v

# 运行特定测试类
pytest tests/integration/test_agent_memory_integration.py::TestBaseAgentMemoryIntegration -v

# 运行特定测试方法
pytest tests/integration/test_agent_memory_integration.py::TestBaseAgentMemoryIntegration::test_save_and_load_memory -v
```

---

## 故障排查

### 问题1：记忆系统未启用

**症状**：`_memory_enabled`为`False`

**解决方案**：
- 确保提供了`project_path`参数
- 检查`core.memory.unified_memory_system`模块是否可导入

### 问题2：记忆保存失败

**症状**：`save_memory`返回`False`

**解决方案**：
- 检查项目路径是否存在
- 检查文件系统权限
- 查看日志中的错误信息

### 问题3：记忆加载返回None

**症状**：`load_memory`返回`None`

**解决方案**：
- 确认记忆是否已保存
- 检查`type`、`category`、`key`参数是否正确
- 查看项目`.athena/memory/`目录

---

## 相关文档

- [统一记忆系统设计文档](/Users/xujian/Athena工作平台/docs/architecture/memory/UNIFIED_MEMORY_SYSTEM_DESIGN.md)
- [统一记忆系统API文档](/Users/xujian/Athena工作平台/docs/api/UNIFIED_MEMORY_SYSTEM_API.md)
- [BaseAgent类文档](/Users/xujian/Athena工作平台/core/agents/base_agent.py)

---

## 更新日志

### v1.0 (2026-04-21)
- 初始版本
- BaseAgent记忆系统集成
- 小娜智能体记忆集成
- 小诺编排者记忆集成
- 集成测试套件

---

**维护者**: 徐健 (xujian519@gmail.com)
