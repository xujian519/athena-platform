# 小娜专业智能体系统 - 使用指南

> **版本**: 1.0.0 (Phase 1)
> **更新时间**: 2026-04-21
> **作者**: Athena平台团队

---

## 📋 目录

1. [系统概述](#系统概述)
2. [核心概念](#核心概念)
3. [架构设计](#架构设计)
4. [快速开始](#快速开始)
5. [API参考](#api参考)
6. [开发指南](#开发指南)
7. [测试指南](#测试指南)
8. [常见问题](#常见问题)

---

## 系统概述

小娜专业智能体系统是Athena平台的核心创新之一，将原有的小娜智能体拆分为多个专业智能体，通过小诺的动态编排实现灵活组合。

### 核心特性

- ✅ **渐进式拆分**: 分3个阶段逐步实现，降低风险
- ✅ **动态编排**: 小诺根据业务场景自动组装智能体
- ✅ **向后兼容**: 保留小娜统一入口，不影响现有功能
- ✅ **易于扩展**: 新增智能体只需注册到注册表
- ✅ **监控完善**: 完整的执行状态监控和错误恢复

### Phase 1 智能体

| 智能体 | ID | 职责 | 能力 |
|--------|-----|------|------|
| **检索者** | `xiaona_retriever` | 专利检索 | 关键词扩展、多数据库检索、结果筛选 |
| **分析者** | `xiaona_analyzer` | 技术分析 | 特征提取、新颖性分析、创造性分析 |
| **撰写者** | `xiaona_writer` | 文书撰写 | 权利要求书、说明书、审查意见答复 |

---

## 核心概念

### 1. 智能体注册表 (AgentRegistry)

类似统一工具注册表，管理所有专业智能体的注册、发现和获取。

```python
from core.orchestration.agent_registry import get_agent_registry

registry = get_agent_registry()

# 注册智能体
registry.register(agent, phase=1)

# 获取智能体
agent = registry.get_agent("xiaona_retriever")

# 查询智能体
agents = registry.find_agents_by_capability("patent_search")
```

### 2. 场景识别器 (ScenarioDetector)

根据用户输入自动识别业务场景。

```python
from core.orchestration.scenario_detector import ScenarioDetector

detector = ScenarioDetector()

# 识别场景
scenario = detector.detect("帮我检索关于自动驾驶的专利")
# 返回: Scenario.PATENT_SEARCH

# 获取需要的智能体
agents = detector.get_required_agents(scenario)
# 返回: ["xiaona_retriever"]
```

### 3. 工作流构建器 (WorkflowBuilder)

根据场景构建智能体执行工作流。

```python
from core.orchestration.workflow_builder import WorkflowBuilder

builder = WorkflowBuilder(registry, detector)

# 构建工作流
steps = builder.build_workflow(
    scenario=Scenario.PATENT_SEARCH,
    user_input="检索自动驾驶专利",
    session_id="session_001",
    config={"limit": 50}
)
```

### 4. 执行监控器 (ExecutionMonitor)

监控工作流执行状态，支持断点续传。

```python
from core.orchestration.execution_monitor import ExecutionMonitor

monitor = ExecutionMonitor()

# 创建工作流状态
state = monitor.create_workflow_state("workflow_001")

# 查询进度
progress = monitor.get_progress("workflow_001", total_steps=5)
```

---

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────┐
│  Go网关 (8005) - 统一入口               │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│  小诺编排者 (XiaonuoOrchestrator)        │
│  - 场景识别                              │
│  - 智能体组装                            │
│  - 工作流编排                            │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│  编排系统 (Orchestration)                │
│  - AgentRegistry (智能体注册表)          │
│  - ScenarioDetector (场景识别器)        │
│  - WorkflowBuilder (工作流构建器)        │
│  - ExecutionMonitor (执行监控器)         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│  小娜专业智能体 (Phase 1)                │
│  ┌────────────┬────────────┬────────────┐│
│  │ 检索者     │ 分析者     │ 撰写者     ││
│  │ Retriever  │ Analyzer   │ Writer     ││
│  └────────────┴────────────┴────────────┘│
└─────────────────────────────────────────┘
```

### 目录结构

```
core/
  agents/
    xiaona/
      __init__.py
      base_component.py          # 基础组件类
      retriever_agent.py         # 检索者
      analyzer_agent.py          # 分析者
      writer_agent.py            # 撰写者
    xiaonuo_orchestrator.py      # 小诺编排者

  orchestration/
    __init__.py
    agent_registry.py            # 智能体注册表
    scenario_detector.py         # 场景识别器
    workflow_builder.py          # 工作流构建器
    execution_monitor.py         # 执行监控器

examples/
  xiaona_agents_test.py          # 测试示例
```

---

## 快速开始

### 1. 安装依赖

```bash
# 系统会自动安装Python 3.11+依赖
poetry install
```

### 2. 运行测试

```bash
# 运行完整测试
python examples/xiaona_agents_test.py

# 或使用pytest
pytest tests/agents/test_xiaona_agents.py -v
```

### 3. 使用示例

```python
import asyncio
from core.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

async def main():
    # 创建小诺编排者
    xiaonuo = XiaonuoOrchestrator()

    # 处理用户请求
    user_input = "帮我检索关于自动驾驶掉头的专利"
    result = await xiaonuo.process(user_input)

    # 查看结果
    print(result)

asyncio.run(main())
```

**输出示例**:

```json
{
  "status": "success",
  "scenario": "patent_search",
  "workflow_id": "workflow_20260421123456_abc12345",
  "total_time": 15.23,
  "steps_completed": 1,
  "steps_total": 1,
  "output": {
    "keywords": ["自动驾驶", "掉头", "路径规划", "autonomous driving"],
    "patents": [
      {"patent_id": "CN123456789A", "title": "自动驾驶车辆掉头方法"},
      ...
    ],
    "total_count": 50,
    "filtered_count": 20
  },
  "step_details": {
    "step_1_xiaona_retriever": {
      "agent_id": "xiaona_retriever",
      "status": "completed",
      "execution_time": 15.23
    }
  }
}
```

---

## API参考

### XiaonuoOrchestrator

小诺编排者，系统的主入口。

#### `__init__(name, config)`

初始化编排者。

**参数**:
- `name` (str): 智能体名称
- `config` (dict): 配置参数

**示例**:
```python
xiaonuo = XiaonuoOrchestrator(
    name="xiaonuo_orchestrator",
    config={"model": "kimi-k2.5"}
)
```

#### `async process(user_input, session_id)`

处理用户请求。

**参数**:
- `user_input` (str): 用户输入
- `session_id` (str): 会话ID

**返回**:
- `str`: JSON格式结果字符串

**示例**:
```python
result = await xiaonuo.process(
    "分析专利CN123456789A的创造性",
    session_id="session_001"
)
```

#### `get_agent_status()`

获取所有智能体状态。

**返回**:
- `dict`: 智能体状态字典

**示例**:
```python
status = xiaonuo.get_agent_status()
print(status["statistics"])
# {'total_agents': 3, 'enabled': 3, 'total_capabilities': 9}
```

---

## 开发指南

### 创建新的专业智能体

#### 1. 继承BaseXiaonaComponent

```python
from core.agents.xiaona.base_component import BaseXiaonaComponent

class MySpecialAgent(BaseXiaonaComponent):
    def _initialize(self):
        # 注册能力
        self._register_capabilities([
            AgentCapability(
                name="my_capability",
                description="我的能力",
                input_types=["输入类型"],
                output_types=["输出类型"],
                estimated_time=10.0,
            ),
        ])

    def get_system_prompt(self):
        return "你是..."

    async def execute(self, context):
        # 实现执行逻辑
        return AgentExecutionResult(
            agent_id=self.agent_id,
            status=AgentStatus.COMPLETED,
            output_data={"result": "..."},
        )
```

#### 2. 注册到AgentRegistry

```python
# 在XiaonuoOrchestrator._register_xiaona_agents()中添加
from core.agents.xiaona.my_special_agent import MySpecialAgent

my_agent = MySpecialAgent(
    agent_id="xiaona_my_special",
    config=self.config
)
self.agent_registry.register(my_agent, phase=2)
```

#### 3. 更新场景配置

在`ScenarioDetector`中添加新的场景配置：

```python
self.scenarios[Scenario.MY_SCENARIO] = ScenarioConfig(
    scenario=Scenario.MY_SCENARIO,
    name="我的场景",
    description="...",
    keywords=["关键词1", "关键词2"],
    required_agents=["xiaona_my_special"],
    optional_agents=[],
    execution_mode="sequential"
)
```

---

## 测试指南

### 单元测试

```python
import pytest
from core.agents.xiaona.retriever_agent import RetrieverAgent

@pytest.mark.asyncio
async def test_retriever_agent():
    agent = RetrieverAgent(
        agent_id="test_retriever",
        config={}
    )

    # 测试能力注册
    capabilities = agent.get_capabilities()
    assert len(capabilities) == 3

    # 测试场景识别
    assert agent.has_capability("patent_search")
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_workflow_execution():
    from core.agents.xiaonuo_orchestrator import XiaonuoOrchestrator

    xiaonuo = XiaonuoOrchestrator()
    result = await xiaonuo.process("检索自动驾驶专利")

    result_dict = json.loads(result)
    assert result_dict["status"] == "success"
    assert result_dict["scenario"] == "patent_search"
```

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/agents/test_xiaona_agents.py -v

# 并行运行
pytest tests/ -n auto
```

---

## 常见问题

### Q1: 如何调试智能体执行过程？

**A**: 使用ExecutionMonitor查询执行状态：

```python
progress = xiaonuo.execution_monitor.get_progress(
    workflow_id="workflow_001",
    total_steps=3
)
print(progress)
# {'progress': 66.67, 'completed': 2, 'remaining': 1}
```

### Q2: 如何添加新的执行模式？

**A**: 在WorkflowBuilder中实现新的构建方法：

```python
def _build_my_mode(self, agent_ids, ...):
    # 实现自定义工作流逻辑
    pass
```

### Q3: 如何处理智能体执行失败？

**A**: 系统会自动记录失败步骤，可以通过can_resume()检查：

```python
if xiaonuo.execution_monitor.can_resume("workflow_001"):
    # 重新执行失败的工作流
    pass
```

### Q4: Phase 2和Phase 3什么时候实现？

**A**: 根据Phase 1的使用情况和反馈决定。预计时间线：
- Phase 2: 4-6周后（规划者、规则官）
- Phase 3: 8-12周后（润色师、翻译官）

---

## 相关文档

- [技术实现详细报告](./XIAONA_AGENTS_IMPLEMENTATION_REPORT.md)
- [API完整文档](../api/XIAONA_AGENTS_API.md)
- [测试用例文档](../../tests/agents/README.md)

---

## 联系方式

- **维护者**: 徐健 (xujian519@gmail.com)
- **项目仓库**: /Users/xujian/Athena工作平台
- **文档更新**: 2026-04-21

---

**End of Document**
