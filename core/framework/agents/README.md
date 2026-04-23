# Core Agents - Athena智能体统一接口

## 📋 概述

`core/agents/`模块是Athena工作平台的智能体统一接口，提供标准化的智能体生命周期管理、请求处理和响应机制。

**版本**: 2.0.0
**作者**: Athena Team
**最后更新**: 2026-02-21

---

## 🏗️ 模块结构

```
core/agents/
├── __init__.py              # 模块导出
├── base.py                  # BaseAgent抽象基类 + AgentRegistry
├── factory.py               # AgentFactory工厂类
├── example_agent.py         # 示例智能体
│
├── xiaona_legal.py          # 小娜·法律专家
├── xiaonuo_coordinator.py   # 小诺·调度官
├── athena_advisor.py        # Athena·智慧顾问
│
├── multi_agent_demo.py      # 多智能体协作演示
│
├── API.md                   # API文档
├── MIGRATION.md             # 迁移指南
└── README.md                # 本文档
```

---

## 🤖 内置智能体

### 小娜·法律专家 (XiaonaLegalAgent)

**角色**: 专利法律专家
**文件**: `xiaona_legal.py`
**能力数**: 10

| 能力 | 说明 |
|------|------|
| `office-action-response` | 审查意见答复 |
| `invalidity-request` | 无效宣告请求 |
| `patent-drafting` | 专利撰写 |
| `patent-compliance` | 合规性审查 |
| `novelty-analysis` | 新颖性分析 |
| `inventiveness-analysis` | 创造性分析 |
| `claim-analysis` | 权利要求分析 |
| `patent-search` | 专利检索 |
| `technology-landscape` | 技术全景分析 |
| `legal-consultation` | 法律咨询 |

### 小诺·双鱼公主 (XiaonuoAgent)

**角色**: 平台任务调度官
**文件**: `xiaonuo_coordinator.py`
**能力数**: 9

| 能力 | 说明 |
|------|------|
| `list-agents` | 列出所有智能体 |
| `get-agent-status` | 获取智能体状态 |
| `schedule-task` | 调度任务到指定智能体 |
| `parallel-execute` | 并行执行多个任务 |
| `sequential-execute` | 顺序执行多个任务 |
| `orchestrate-workflow` | 编排复杂工作流 |
| `platform-status` | 平台状态概览 |
| `health-check-all` | 全局健康检查 |
| `chat` | 温暖陪伴对话 |

### Athena·智慧顾问 (AthenaAdvisorAgent)

**角色**: 平台战略顾问
**文件**: `athena_advisor.py`
**能力数**: 9

| 能力 | 说明 |
|------|------|
| `strategic-advice` | 战略建议 |
| `platform-roadmap` | 平台路线图 |
| `system-analysis` | 系统分析 |
| `architecture-review` | 架构评审 |
| `best-practices` | 最佳实践 |
| `lessons-learned` | 经验教训 |
| `decision-support` | 决策支持 |
| `consultation` | 咨询服务 |
| `guidance` | 指导服务 |

---

## 🚀 快速开始

### 基础用法

```python
from core.agents.base import BaseAgent, AgentRequest, AgentResponse, AgentRegistry
from core.agents.xiaona_legal import XiaonaLegalAgent

# 1. 创建智能体
xiaona = XiaonaLegalAgent()
AgentRegistry.register(xiaona)

# 2. 初始化
await xiaona.initialize()

# 3. 执行任务
request = AgentRequest(
    request_id="search-001",
    action="patent-search",
    parameters={
        "query": "深度学习 图像识别",
        "search_fields": ["title", "abstract"],
    }
)
response = await xiaona.safe_process(request)

# 4. 处理结果
if response.success:
    print(f"找到 {response.data['total_results']} 条专利")
else:
    print(f"错误: {response.error}")

# 5. 关闭
await xiaona.shutdown()
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
request = AgentRequest(
    request_id="schedule-001",
    action="schedule-task",
    parameters={
        "target_agent": "xiaona-legal",
        "action": "patent-search",
        "parameters": {"query": "AI专利"},
    }
)
response = await xiaonuo.safe_process(request)
```

### 运行演示

```bash
# 运行多智能体协作演示
python3 core/agents/multi_agent_demo.py
```

---

## 📚 文档索引

| 文档 | 说明 |
|------|------|
| [API.md](./API.md) | 完整的API参考文档 |
| [MIGRATION.md](./MIGRATION.md) | 旧架构迁移指南 |

---

## 🧪 测试

### 运行所有测试

```bash
# 运行所有智能体测试
pytest tests/core/agents/ -v

# 运行特定智能体测试
pytest tests/core/agents/test_xiaona_legal.py -v
pytest tests/core/agents/test_xiaonuo_coordinator.py -v
pytest tests/core/agents/test_athena_advisor.py -v

# 查看测试覆盖率
pytest tests/core/agents/ --cov=core/agents --cov-report=html
```

### 测试覆盖情况

| 模块 | 测试数 | 覆盖率 |
|------|--------|--------|
| base.py | 35 | 95%+ |
| xiaona_legal.py | 21 | 90%+ |
| xiaonuo_coordinator.py | 19 | 90%+ |
| athena_advisor.py | 17 | 90%+ |
| **总计** | **92** | **92%** |

---

## 🔌 扩展开发

### 创建自定义智能体

```python
from core.agents.base import BaseAgent, AgentRequest, AgentResponse
from core.agents.base import AgentCapability, AgentStatus

class MyAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "my-agent"

    def get_capabilities(self) -> List[AgentCapability]:
        return [
            AgentCapability(
                name="my-action",
                description="我的自定义操作",
                parameters={"input": {"type": "string"}},
                examples=[{"input": "test"}]
            )
        ]

    async def initialize(self) -> None:
        self._status = AgentStatus.READY

    async def process(self, request: AgentRequest) -> AgentResponse:
        if request.action == "my-action":
            result = await self._handle_action(request.parameters)
            return AgentResponse.success(data=result)
        return AgentResponse.error(f"未知操作: {request.action}")

    async def shutdown(self) -> None:
        self._status = AgentStatus.SHUTDOWN

    async def _handle_action(self, params: dict) -> dict:
        # 实现具体逻辑
        return {"result": "done"}
```

详细指南请参考 [API.md](./API.md) 和 [MIGRATION.md](./MIGRATION.md)。

---

## 📊 架构设计

### 设计原则

1. **统一接口**: 所有智能体使用相同的请求/响应格式
2. **生命周期管理**: 明确的初始化-处理-关闭流程
3. **能力自描述**: 智能体能自我声明其能力
4. **异常安全**: safe_process()保证不会抛出未捕获异常
5. **可观测性**: 内置健康检查和状态管理

### 状态机

```
     ┌──────────────┐
     │ INITIALIZING │
     └──────┬───────┘
            │ initialize()
            ▼
     ┌──────────────┐
     │    READY     │ ◄──┐
     └──────┬───────┘    │
            │ process()   │
            ▼             │
     ┌──────────────┐    │
     │     BUSY     │────┘
     └──────┬───────┘
            │
            ├──────────┐
            ▼          ▼
     ┌──────────┐ ┌──────────┐
     │  READY   │ │  ERROR   │
     └──────────┘ └────┬─────┘
                       │
                       ▼
                  ┌─────────┐
                  │ SHUTDOWN │
                  └─────────┘
```

---

## 🤝 贡献指南

### 代码规范

- 遵循 PEP 8
- 使用类型注解
- 添加完整的docstring
- 编写单元测试

### 提交流程

1. Fork项目
2. 创建特性分支
3. 编写代码和测试
4. 运行 `pytest` 确保测试通过
5. 提交Pull Request

---

## 📞 联系方式

- **项目**: Athena工作平台
- **团队**: Athena Team
- **邮箱**: xujian519@gmail.com

---

## 📄 许可证

版权所有 © 2026 Athena Team

---

**最后更新**: 2026-02-21
**版本**: 2.0.0
