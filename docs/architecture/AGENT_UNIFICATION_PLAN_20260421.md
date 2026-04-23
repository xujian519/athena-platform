# Agent架构整合方案

**日期**: 2026-04-21
**作者**: Claude Code
**状态**: 待审核

---

## 一、问题诊断

### 1.1 当前问题

**架构分裂**:
- 旧版 `core/xiaonuo_agent/` - 完整AI架构(6大子系统)
- 新版 `core/agents/xiaona/` - 最小化代理壳(我之前工作的)
- 声明式 `core/agents/declarative/` - .md定义的Agent
- **三个系统各自独立,没有统一编排**

**重复建设**:
- 新版的6个代理(ApplicationReviewer等)与旧版功能重复
- 没有利用旧版完整的AI能力(记忆、学习、元认知)
- 工具注册系统不统一

**编排缺失**:
- 声明式Agent只是定义文件,没有实际执行能力
- 旧版ReAct循环只支持简单工具,不支持Agent编排
- 没有Agent之间的上下文传递

### 1.2 错误的代价

**我之前的工作**:
- 为 `core/agents/xiaona/` 的6个代理添加了LLM集成
- 编写了124个测试用例
- 生成了~7220行代码

**问题**:
- 这些工作基于错误的架构假设
- 没有利用现有的完整架构
- 增加了代码冗余

**应该做的**:
- 直接使用 `core/xiaonuo_agent/` 的完整架构
- 将声明式Agent和6个代理作为"工具"注册
- 修改ReAct循环支持Agent编排

---

## 二、整合方案

### 2.1 核心理念

**以旧版XiaonuoAgent为"大脑"**:
- 保留完整的6大子系统
- 利用ReAct循环进行推理
- 利用HTN规划器进行任务分解
- 利用记忆系统存储上下文

**声明式Agent作为"工具/子智能体"**:
- 通过FunctionCallingSystem注册为工具
- 由ReAct循环动态调用
- 支持上下文传递

**清理冗余代码**:
- 标记 `core/agents/xiaona/` 为废弃
- 保留测试代码作为参考

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────┐
│           XiaonuoAgent (大脑)                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │  ReAct循环 (Think-Act-Observe)                    │  │
│  │  1. 分析任务                                       │  │
│  │  2. 选择工具/Agent                                │  │
│  │  3. 执行并观察结果                                 │  │
│  │  4. 迭代直到完成                                   │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  FunctionCallingSystem (工具注册表)                │  │
│  │  - patent-searcher (声明式Agent)                   │  │
│  │  - legal-analyzer (声明式Agent)                    │  │
│  │  - application_reviewer (新代理)                   │  │
│  │  - novelty_analyzer (新代理)                       │  │
│  │  - creativity_analyzer (新代理)                    │  │
│  │  - infringement_analyzer (新代理)                  │  │
│  │  - invalidation_analyzer (新代理)                  │  │
│  │  - writing_reviewer (新代理)                       │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  记忆系统 (三层记忆)                                │  │
│  │  - 工作记忆 (HOT)                                  │  │
│  │  - 语义记忆 (WARM)                                 │  │
│  │  - 情景记忆 (COLD)                                 │  │
│  └───────────────────────────────────────────────────┘  │
│                          │                               │
│  ┌───────────────────────────────────────────────────┐  │
│  │  其他子系统                                         │  │
│  │  - HTN规划器                                       │  │
│  │  - 情感系统                                        │  │
│  │  - 学习引擎                                        │  │
│  │  - 元认知系统                                      │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.3 实施步骤

**Phase 1: Agent适配器** (1-2天)
1. 创建 `AgentAdapter` 类
   - 将声明式Agent定义转换为可调用函数
   - 将新代理类转换为可调用函数
   - 统一接口标准

2. 创建 `AgentToolRegistry`
   - 自动发现声明式Agent
   - 自动发现新代理
   - 注册到FunctionCallingSystem

**Phase 2: ReAct循环增强** (2-3天)
1. 修改 `ReActEngine._decide_action`
   - 支持Agent选择(不只是工具)
   - 添加Agent能力评估
   - 添加上下文传递

2. 修改 `ReActEngine._execute_action`
   - 支持Agent调用
   - 处理Agent返回结果
   - 记录Agent调用链

**Phase 3: 上下文管理** (1-2天)
1. 实现 `AgentContext` 类
   - 存储Agent间共享上下文
   - 支持上下文传递和更新
   - 持久化到记忆系统

2. 修改 `XiaonuoAgent.process`
   - 初始化Agent上下文
   - 传递给每个Agent调用
   - 收集和整合结果

**Phase 4: 清理和优化** (1天)
1. 标记废弃代码
2. 更新文档
3. 迁移测试

---

## 三、技术细节

### 3.1 Agent适配器设计

```python
class AgentAdapter:
    """Agent适配器,将不同类型的Agent转换为统一接口"""

    def __init__(self, agent_def: AgentDefinition):
        self.agent_def = agent_def

    async def __call__(self, **kwargs) -> Dict[str, Any]:
        """调用Agent"""
        # 1. 构建输入
        input_data = self._prepare_input(kwargs)

        # 2. 调用LLM
        response = await self._call_llm(input_data)

        # 3. 解析结果
        return self._parse_response(response)

    def _prepare_input(self, kwargs: Dict) -> str:
        """准备LLM输入"""
        # 使用Agent的system_prompt + 用户输入
        pass

    async def _call_llm(self, input_data: str) -> str:
        """调用LLM"""
        # 使用UnifiedLLMManager
        pass

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        # 解析JSON或Markdown
        pass
```

### 3.2 工具注册流程

```python
async def register_all_agents():
    """注册所有Agent到FunctionCallingSystem"""

    # 1. 获取FunctionCallingSystem
    fc_system = await get_function_calling_system()

    # 2. 注册声明式Agent
    loader = get_loader()
    for agent_def in loader.load_all().values():
        adapter = AgentAdapter(agent_def)
        fc_system.register_tool(
            name=agent_def.name,
            description=agent_def.description,
            function=adapter,
            category="agent",
            metadata={
                "type": "declarative",
                "tools": agent_def.tools,
                "model": agent_def.model
            }
        )

    # 3. 注册新代理
    from core.agents.xiaona.application_reviewer_proxy import ApplicationDocumentReviewerProxy
    # ... 其他代理

    agent_classes = [
        ("application_reviewer", ApplicationDocumentReviewerProxy),
        ("novelty_analyzer", NoveltyAnalyzerProxy),
        # ... 其他代理
    ]

    for name, cls in agent_classes:
        adapter = ProxyAgentAdapter(cls)
        fc_system.register_tool(
            name=name,
            description=cls.__doc__,
            function=adapter,
            category="agent",
            metadata={"type": "proxy"}
        )
```

### 3.3 ReAct循环修改

```python
async def _decide_action(self, thought: Thought, task: str, available_tools: Dict, context: Dict, step: int) -> Action:
    """决定下一步行动 - 支持Agent选择"""

    # 1. 识别任务类型
    task_type = await self._identify_task_type(task, thought)

    # 2. 如果是复杂任务,选择Agent
    if task_type in ["patent_analysis", "legal_consulting", "literature_review"]:
        # 选择合适的Agent
        agent_name = await self._select_agent(task_type, available_tools)

        return Action(
            step=step,
            action_type=agent_name,
            parameters={"task": task, "context": context},
            reasoning=f"使用Agent '{agent_name}' 处理 {task_type} 任务"
        )

    # 3. 简单任务,使用工具
    else:
        tool_name = await self._select_tool(task, available_tools)
        return Action(...)
```

### 3.4 上下文管理

```python
@dataclass
class AgentContext:
    """Agent间共享上下文"""
    session_id: str
    task_id: str
    shared_data: Dict[str, Any]
    agent_call_chain: List[str]
    memory_references: List[str]

    def update(self, key: str, value: Any):
        """更新上下文"""
        self.shared_data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文"""
        return self.shared_data.get(key, default)
```

---

## 四、风险评估

### 4.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|---------|
| 旧版代码理解不充分 | 高 | 中 | 先全面阅读旧版代码,编写架构文档 |
| Agent适配器性能问题 | 中 | 低 | 异步调用,缓存LLM响应 |
| 上下文传递复杂度 | 中 | 中 | 设计简单的上下文协议 |
| 旧版代码bug | 高 | 低 | 充分测试,逐步迁移 |

### 4.2 项目风险

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|------|---------|
| 工作量估计不足 | 中 | 中 | 分阶段实施,每阶段评估 |
| 与现有功能冲突 | 高 | 低 | 保留旧代码作为备份 |
| 用户不接受新架构 | 低 | 低 | 提供平滑迁移路径 |

---

## 五、成功标准

### 5.1 功能标准

- ✅ 所有声明式Agent可通过ReAct循环调用
- ✅ 所有新代理可通过ReAct循环调用
- ✅ Agent间可共享上下文
- ✅ 支持Agent编排(串行/并行)
- ✅ 记忆系统正确存储Agent调用历史

### 5.2 性能标准

- Agent调用延迟 <5秒
- 上下文传递开销 <100ms
- 内存占用增长 <20%

### 5.3 质量标准

- 代码覆盖率 >70%
- 所有测试通过
- 代码审查通过

---

## 六、下一步行动

1. **审核本方案** - 确认技术方向
2. **Phase 1实施** - 创建Agent适配器
3. **逐步验证** - 每个Phase完成后测试
4. **持续优化** - 根据测试结果调整

---

**附录: 旧版架构分析**

详见: `docs/architecture/XIAONUO_AGENT_ARCHITECTURE_ANALYSIS.md` (待创建)
