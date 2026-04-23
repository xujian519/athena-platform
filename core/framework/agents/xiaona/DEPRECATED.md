# ⚠️ 废弃通知

**状态**: 已废弃
**废弃日期**: 2026-04-21
**替代方案**: `core/xiaonuo_agent/` (旧版完整架构) + `core/xiaonuo_agent/adapters/`

---

## 废弃原因

此目录包含的代理类是**基于错误的架构假设**创建的：

1. **架构分裂** - 与 `core/xiaonuo_agent/` 的完整架构重复
2. **功能重复** - 旧版已有完整的AI能力（记忆、推理、规划等）
3. **未利用现有架构** - 没有使用旧版的6大子系统
4. **维护成本高** - 两套系统增加维护负担

---

## 迁移路径

### 对于使用者

**旧代码**:
```python
from core.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy

agent = ApplicationDocumentReviewerProxy(agent_id="test")
result = await agent.review_application(data)
```

**新代码** (通过Agent适配器):
```python
from core.xiaonuo_agent.adapters import get_agent_registry

registry = await get_agent_registry()
adapter = registry.get_agent_info("application_reviewer.review_application")["adapter"]
result = await adapter(data=data)
```

**或通过XiaonuoAgent自动调用**:
```python
from core.xiaonuo_agent.xiaonuo_agent import create_xiaonuo_agent

agent = await create_xiaonuo_agent()
response = await agent.process(
    input_text="帮我分析专利申请文件",
    context={"data": application_data}
)
# ReAct循环会自动选择合适的Agent
```

### 对于开发者

1. **LLM集成代码** - 已迁移到 `core/xiaonuo_agent/adapters/agent_adapter.py`
2. **测试代码** - 已迁移到 `tests/xiaonuo_agent/adapters/`
3. **代理类** - 通过 `ProxyAgentAdapter` 自动适配

---

## 文件清单

### 已废弃的文件

| 文件 | 说明 | 替代方案 |
|------|------|---------|
| `application_reviewer_proxy.py` | 申请文件审查代理 | ProxyAgentAdapter("application_reviewer") |
| `writing_reviewer_proxy.py` | 撰写质量审查代理 | ProxyAgentAdapter("writing_reviewer") |
| `novelty_analyzer_proxy.py` | 新颖性分析代理 | ProxyAgentAdapter("novelty_analyzer") |
| `creativity_analyzer_proxy.py` | 创造性分析代理 | ProxyAgentAdapter("creativity_analyzer") |
| `infringement_analyzer_proxy.py` | 侵权分析代理 | ProxyAgentAdapter("infringement_analyzer") |
| `invalidation_analyzer_proxy.py` | 无效宣告代理 | ProxyAgentAdapter("invalidation_analyzer") |
| `base_component.py` | 基类组件 | 直接使用 `core/xiaonuo_agent/xiaonuo_agent.py` |

### 测试文件

| 文件 | 说明 | 迁移目标 |
|------|------|---------|
| `test_application_reviewer_llm_integration.py` | 申请审查测试 | 已整合到适配器测试 |
| `test_writing_reviewer_llm_integration.py` | 撰写审查测试 | 已整合到适配器测试 |
| `test_novelty_analyzer_llm_integration.py` | 新颖性测试 | 已整合到适配器测试 |
| `test_creativity_analyzer_llm_integration.py` | 创造性测试 | 已整合到适配器测试 |
| `test_infringement_analyzer_llm_integration.py` | 侵权测试 | 已整合到适配器测试 |
| `test_invalidation_analyzer_llm_integration.py` | 无效测试 | 已整合到适配器测试 |
| `test_base_component.py` | 基类测试 | `tests/core/agents/xiaona/` (保留) |
| `test_base_component_llm.py` | 基类LLM测试 | `tests/core/agents/xiaona/` (保留) |
| `test_error_handling.py` | 错误处理测试 | `tests/core/agents/xiaona/` (保留) |

---

## 功能保留

虽然代码已废弃，但所有功能都通过以下方式保留：

### 1. Agent适配器系统

所有6个代理都可以通过 `ProxyAgentAdapter` 调用：

```python
from core.xiaonuo_agent.adapters import ProxyAgentAdapter

# 创建适配器
adapter = ProxyAgentAdapter("application_reviewer", "review_application")

# 调用
result = await adapter(data=application_data)
```

### 2. 自动注册到FunctionCallingSystem

所有代理都会自动注册到FunctionCallingSystem：

```python
from core.xiaonuo_agent.adapters import register_all_agents

# 注册所有Agent (29个工具/方法)
stats = await register_all_agents(include_proxies=True)
# {
#     "declarative_agents": 7,
#     "proxy_agents": 22,
#     "total": 29
# }
```

### 3. ReAct循环自动调用

通过XiaonuoAgent的ReAct循环自动选择和调用：

```python
from core.xiaonuo_agent.xiaonuo_agent import create_xiaonuo_agent

agent = await create_xiaonuo_agent()
response = await agent.process("帮我分析专利申请文件")
# ReAct循环会自动:
# 1. 识别任务类型: patent_analysis
# 2. 选择合适的Agent
# 3. 调用Agent并获取结果
# 4. 返回综合答案
```

---

## 迁移示例

### 示例1: 申请文件审查

**旧代码**:
```python
from core.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy

reviewer = ApplicationDocumentReviewerProxy(agent_id="reviewer")
result = await reviewer.review_application(application_data)
```

**新代码** (方式1 - 直接适配器):
```python
from core.xiaonuo_agent.adapters import ProxyAgentAdapter

adapter = ProxyAgentAdapter("application_reviewer", "review_application")
result = await adapter(data=application_data)
```

**新代码** (方式2 - 通过注册表):
```python
from core.xiaonuo_agent.adapters import get_agent_registry

registry = await get_agent_registry()
adapter = registry.get_agent_info("application_reviewer.review_application")["adapter"]
result = await adapter(data=application_data)
```

**新代码** (方式3 - 自动调用):
```python
from core.xiaonuo_agent.xiaonuo_agent import create_xiaonuo_agent

agent = await create_xiaonuo_agent()
response = await agent.process(
    "帮我审查这份专利申请文件",
    context={"application_data": application_data}
)
```

### 示例2: 新颖性分析

**旧代码**:
```python
from core.agents.xiaona.novelty_analyzer_proxy import NoveltyAnalyzerProxy

analyzer = NoveltyAnalyzerProxy(agent_id="analyzer")
result = await analyzer.analyze_novelty(patent_data, prior_art)
```

**新代码**:
```python
from core.xiaonuo_agent.adapters import ProxyAgentAdapter

adapter = ProxyAgentAdapter("novelty_analyzer", "analyze_novelty")
result = await adapter(data={"patent": patent_data, "prior_art": prior_art})
```

---

## 常见问题

### Q1: 我的代码还在使用 `core.agents.xiaona`，怎么办？

**A**: 您可以继续使用，但建议迁移到新架构。迁移非常简单，见上面的迁移示例。

### Q2: 测试文件怎么办？

**A**: 测试文件已迁移到新位置：
- `tests/xiaonuo_agent/adapters/` - 适配器测试
- `tests/xiaonuo_agent/reasoning/` - ReAct编排测试
- `tests/core/agents/xiaona/` - 保留部分基础测试

### Q3: LLM集成功能还在吗？

**A**: 在！LLM集成功能已经整合到：
- `AgentAdapter` - 声明式Agent的LLM调用
- `ProxyAgentAdapter` - 代理Agent的LLM调用
- 功能完全保留，甚至更强大（自动Agent选择）

### Q4: 我需要重写所有代码吗？

**A**: 不需要！新架构向后兼容。您可以：
1. 继续使用旧代码（会收到警告）
2. 逐步迁移到新架构
3. 使用XiaonuoAgent自动调用（无需手动选择Agent）

---

## 技术细节

### 为什么废弃？

**问题1: 架构分裂**
- 旧版 `core/xiaonuo_agent/` 是完整的AI智能体架构
- 新版 `core/agents/xiaona/` 只是最小化代理壳
- 两个系统各自独立，没有统一编排

**问题2: 功能重复**
- 新版的6个代理与旧版功能重复
- 没有利用旧版的6大子系统（记忆、推理、规划等）
- 增加了代码冗余

**问题3: 维护成本**
- 两套系统需要分别维护
- 测试用例重复
- 文档和配置分散

### 解决方案

**统一到旧版架构**:
- 以 `core/xiaonuo_agent/` 为核心
- 通过适配器系统整合所有Agent
- ReAct循环统一调度
- 单一的测试和文档体系

---

## 时间线

- **2026-04-21**: 标记为废弃
- **2026-05-01**: 停止新功能开发
- **2026-06-01**: 进入只读模式
- **2026-07-01**: 移除代码（如有必要）

---

## 联系方式

如有疑问，请联系：
- 项目维护者: Claude Code
- 文档: `docs/architecture/AGENT_UNIFICATION_PLAN_20260421.md`
- 架构分析: `docs/architecture/XIAONUO_AGENT_ARCHITECTURE_ANALYSIS_20260421.md`

---

**请迁移到新架构！** 🚀
