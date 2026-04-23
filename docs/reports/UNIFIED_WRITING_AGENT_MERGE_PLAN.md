# 统一撰写代理合并方案

> **设计日期**: 2026-04-23
> **状态**: 设计中
> **优先级**: P0（架构简化）

---

## 一、合并理由

### 1.1 当前问题

| 问题 | 影响 | 严重程度 |
|------|------|---------|
| 功能重复 | 权利要求、说明书撰写重复30% | ⚠️ 中 |
| 职责不清 | 用户不知道该用哪个代理 | ⚠️ 中 |
| 维护成本高 | 两套代码需要同步维护 | ⚠️ 中 |
| 选择困惑 | 10个代理已经够复杂了 | ⚠️ 高 |

### 1.2 合并优势

✅ **简化架构**: 10个代理 → 9个代理
✅ **减少困惑**: 一个入口处理所有撰写任务
✅ **降低维护**: 单一代码库，统一的测试
✅ **功能完整**: 整合两者的所有优势

---

## 二、合并后的代理设计

### 2.1 基本信息

```python
# 文件名
unified_patent_writer.py

# 类名
class UnifiedPatentWriter(BaseXiaonaComponent)

# Agent ID
unified-patent-writer

# 显示名称
撰写大师·小娜

# 版本
v2.0.0 (合并版本)
```

### 2.2 核心能力（9个）

合并后保留所有功能，分为4个模块：

#### 📝 **模块1: 申请撰写模块**（来自PatentDraftingProxy）

| 能力 | 方法 | 说明 |
|------|------|------|
| 分析技术交底书 | `analyze_disclosure()` | 深度解析交底书 |
| 评估可专利性 | `assess_patentability()` | 新颖性/创造性/实用性 |
| 撰写说明书 | `draft_specification()` | 生成规范说明书 |
| 撰写权利要求书 | `draft_claims()` | 生成权利要求书 |
| 优化保护范围 | `optimize_protection_scope()` | 数据驱动优化 |
| 审查充分公开 | `review_adequacy()` | 完整性检查 |
| 检测常见错误 | `detect_common_errors()` | 20+错误类型 |

#### 📄 **模块2: 答复撰写模块**（来自WriterAgent）

| 能力 | 方法 | 说明 |
|------|------|------|
| 审查意见答复 | `draft_office_action_response()` | 审查意见答复陈述书 |
| 无效宣告请求书 | `draft_invalidation_petition()` | 无效宣告请求书 |

#### 🔄 **模块3: 流程编排模块**（新增）

| 能力 | 方法 | 说明 |
|------|------|------|
| 完整申请流程 | `draft_full_application()` | 交底书→申请文件（端到端） |
| 答复流程编排 | `orchestrate_response()` | 检索→分析→答复 |

#### 🛠️ **模块4: 辅助工具模块**（新增）

| 能力 | 方法 | 说明 |
|------|------|------|
| 文档格式化 | `format_document()` | 统一格式化输出 |
| 质量评分 | `calculate_quality_score()` | 文档质量评分 |
| 对比分析 | `compare_versions()` | 版本对比分析 |

---

## 三、技术架构

### 3.1 类设计

```python
class UnifiedPatentWriter(BaseXiaonaComponent):
    """
    统一撰写代理 - 小娜撰写大师

    整合专利撰写、答复、无效宣告等所有撰写任务
    """

    def __init__(self, agent_id: str = "unified_patent_writer"):
        super().__init__(agent_id)

        # 子模块初始化
        self.drafting_module = PatentDraftingModule()  # 撰写模块
        self.response_module = ResponseModule()        # 答复模块
        self.orchestration_module = OrchestrationModule()  # 编排模块
        self.utility_module = UtilityModule()          # 工具模块

    def _initialize(self) -> None:
        """注册9个核心能力"""
        capabilities = [
            # 模块1: 申请撰写
            {"name": "analyze_disclosure", ...},
            {"name": "assess_patentability", ...},
            {"name": "draft_specification", ...},
            {"name": "draft_claims", ...},
            {"name": "optimize_protection_scope", ...},
            {"name": "review_adequacy", ...},
            {"name": "detect_common_errors", ...},

            # 模块2: 答复撰写
            {"name": "draft_office_action_response", ...},
            {"name": "draft_invalidation_petition", ...},

            # 模块3: 流程编排
            {"name": "draft_full_application", ...},
            {"name": "orchestrate_response", ...},

            # 模块4: 辅助工具
            {"name": "format_document", ...},
            {"name": "calculate_quality_score", ...},
            {"name": "compare_versions", ...},
        ]
        self._register_capabilities(capabilities)

    async def execute(self, context) -> AgentExecutionResult:
        """统一执行入口"""
        task_type = context.config.get("task_type")

        # 路由到对应的模块
        if task_type in ["draft_specification", "draft_claims", ...]:
            return await self.drafting_module.execute(context)
        elif task_type in ["draft_office_action_response", "draft_invalidation_petition"]:
            return await self.response_module.execute(context)
        elif task_type in ["draft_full_application", "orchestrate_response"]:
            return await self.orchestration_module.execute(context)
        elif task_type in ["format_document", "calculate_quality_score"]:
            return await self.utility_module.execute(context)
```

### 3.2 模块化设计

```python
# 模块1: 申请撰写模块
class PatentDraftingModule:
    """
    专利申请撰写模块

    基于PatentDraftingProxy，保留所有专业能力
    """
    def __init__(self):
        self.llm_manager = UnifiedLLMManager()
        self.prompts = PatentDraftingPrompts()

    async def execute(self, context):
        task_type = context.config.get("task_type")
        if task_type == "analyze_disclosure":
            return await self.analyze_disclosure(context.input_data)
        elif task_type == "draft_claims":
            return await self.draft_claims(context.input_data)
        # ... 其他方法

# 模块2: 答复撰写模块
class ResponseModule:
    """
    答复撰写模块

    基于WriterAgent的答复功能
    """
    async def execute(self, context):
        task_type = context.config.get("task_type")
        if task_type == "draft_office_action_response":
            return await self.draft_office_action_response(context.input_data)
        elif task_type == "draft_invalidation_petition":
            return await self.draft_invalidation_petition(context.input_data)

# 模块3: 流程编排模块
class OrchestrationModule:
    """
    流程编排模块

    支持复杂的多步骤流程
    """
    async def draft_full_application(self, input_data):
        # 步骤1: 分析交底书
        disclosure_analysis = await self.analyze_disclosure(input_data)

        # 步骤2: 评估可专利性
        patentability = await self.assess_patentability(input_data, disclosure_analysis)

        # 步骤3: 撰写权利要求
        claims = await self.draft_claims(input_data, patentability)

        # 步骤4: 撰写说明书
        specification = await self.draft_specification(input_data, claims)

        # 步骤5: 质量审查
        review = await self.review_adequacy(specification, claims)

        # 步骤6: 错误检测
        errors = await self.detect_common_errors(specification, claims)

        return {
            "disclosure_analysis": disclosure_analysis,
            "patentability": patentability,
            "claims": claims,
            "specification": specification,
            "review": review,
            "errors": errors,
            "quality_score": self._calculate_score(review, errors)
        }
```

### 3.3 文件结构

```
core/agents/xiaona/
├── unified_patent_writer.py          # 统一入口（主文件，约500行）
├── modules/
│   ├── __init__.py
│   ├── drafting_module.py            # 撰写模块（约800行，来自PatentDraftingProxy）
│   ├── response_module.py            # 答复模块（约400行，来自WriterAgent）
│   ├── orchestration_module.py       # 编排模块（约300行，新增）
│   └── utility_module.py             # 工具模块（约200行，新增）
├── base_component.py                 # 基类（共享）
└── prompts/
    └── unified_writer_prompts.py     # 统一提示词
```

---

## 四、迁移计划

### 4.1 阶段1: 准备阶段（1天）

**任务**：
- [ ] 创建模块化目录结构
- [ ] 备份现有代理文件
- [ ] 编写迁移测试用例

**输出**：
- `core/agents/xiaona/modules/` 目录
- 备份文件：`writer_agent.py.backup`, `patent_drafting_proxy.py.backup`
- 测试文件：`test_unified_writer_migration.py`

### 4.2 阶段2: 模块拆分（2天）

**任务**：
- [ ] 从PatentDraftingProxy提取撰写逻辑 → `drafting_module.py`
- [ ] 从WriterAgent提取答复逻辑 → `response_module.py`
- [ ] 创建编排模块 → `orchestration_module.py`
- [ ] 创建工具模块 → `utility_module.py`

**输出**：
- 4个模块文件
- 模块单元测试

### 4.3 阶段3: 统一入口（1天）

**任务**：
- [ ] 创建`unified_patent_writer.py`
- [ ] 实现路由逻辑
- [ ] 统一接口设计
- [ ] 集成测试

**输出**：
- `unified_patent_writer.py`
- 集成测试文件

### 4.4 阶段4: 向后兼容（1天）

**任务**：
- [ ] 保留旧代理作为适配器
- [ ] 更新`agent_registry.json`
- [ ] 更新文档

**输出**：
- `writer_agent.py` → 适配器（调用UnifiedPatentWriter）
- `patent_drafting_proxy.py` → 适配器（调用UnifiedPatentWriter）
- 更新的文档

### 4.5 阶段5: 清理和优化（1天）

**任务**：
- [ ] 移除重复代码
- [ ] 性能优化
- [ ] 文档完善
- [ ] 代码审查

**输出**：
- 清理后的代码库
- 完整的文档

---

## 五、向后兼容性

### 5.1 旧代理保留为适配器

```python
# writer_agent.py (适配器版本)
class WriterAgent(BaseXiaonaComponent):
    """
    适配器：向后兼容

    实际调用UnifiedPatentWriter
    """
    def __init__(self, agent_id: str = "writer_agent"):
        super().__init__(agent_id)
        self.unified_writer = UnifiedPatentWriter()

    async def execute(self, context):
        # 路由到统一代理
        old_task_type = context.config.get("writing_type")
        new_task_type = self._map_task_type(old_task_type)

        context.config["task_type"] = new_task_type
        return await self.unified_writer.execute(context)

    def _map_task_type(self, old_type):
        """映射旧任务类型到新任务类型"""
        mapping = {
            "claims": "draft_claims",
            "description": "draft_specification",
            "office_action_response": "draft_office_action_response",
            "invalidation": "draft_invalidation_petition",
        }
        return mapping.get(old_type, "draft_full_application")

# patent_drafting_proxy.py (适配器版本)
class PatentDraftingProxy(BaseXiaonaComponent):
    """
    适配器：向后兼容

    实际调用UnifiedPatentWriter
    """
    def __init__(self, agent_id: str = "patent_drafting_proxy"):
        super().__init__(agent_id)
        self.unified_writer = UnifiedPatentWriter()

    async def execute(self, context):
        # 直接路由到统一代理
        return await self.unified_writer.execute(context)
```

### 5.2 配置文件更新

```json
{
  "agents": {
    "xiaona": {
      "sub_agents": [
        "RetrieverAgent",
        "AnalyzerAgent",
        "UnifiedPatentWriter",        # 新：统一撰写代理
        "NoveltyAnalyzerProxy",
        "CreativityAnalyzerProxy",
        "InfringementAnalyzerProxy",
        "InvalidationAnalyzerProxy",
        "ApplicationReviewerProxy",
        "WritingReviewerProxy"
      ],
      "deprecated": [
        "WriterAgent",                 // 标记为废弃
        "PatentDraftingProxy"          // 标记为废弃
      ],
      "capabilities": {
        "patent_writing": {
          "name": "专利撰写",
          "component": "UnifiedPatentWriter",  // 更新
          "version": "2.0.0",
          "note": "合并WriterAgent和PatentDraftingProxy"
        }
      }
    }
  }
}
```

---

## 六、使用示例

### 6.1 直接使用统一代理

```python
from core.agents.xiaona.unified_patent_writer import UnifiedPatentWriter

writer = UnifiedPatentWriter()

# 场景1: 完整申请流程
result = await writer.execute(AgentExecutionContext(
    task_id="task_001",
    config={"task_type": "draft_full_application"},
    input_data={"disclosure_file": "交底书.docx"}
))

# 场景2: 审查意见答复
result = await writer.execute(AgentExecutionContext(
    task_id="task_002",
    config={"task_type": "draft_office_action_response"},
    input_data={"office_action": "审查意见.pdf"}
))

# 场景3: 无效宣告请求书
result = await writer.execute(AgentExecutionContext(
    task_id="task_003",
    config={"task_type": "draft_invalidation_petition"},
    input_data={"target_patent": "CN123456A", "evidence": [...]}
))
```

### 6.2 使用旧代理（向后兼容）

```python
# 旧代码仍然可以工作
from core.agents.xiaona.writer_agent import WriterAgent
from core.agents.xiaona.patent_drafting_proxy import PatentDraftingProxy

# WriterAgent → 内部调用UnifiedPatentWriter
writer = WriterAgent()
result = await writer.execute(context)

# PatentDraftingProxy → 内部调用UnifiedPatentWriter
proxy = PatentDraftingProxy()
result = await proxy.execute(context)
```

---

## 七、风险评估

### 7.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 模块拆分导致bug | 中 | 完整的单元测试+集成测试 |
| 性能下降 | 低 | 性能基准测试 |
| 向后兼容性破坏 | 高 | 保留适配器，完整测试 |

### 7.2 业务风险

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 用户困惑 | 中 | 详细文档+迁移指南 |
| 现有代码失效 | 高 | 向后兼容适配器 |
| 学习曲线 | 低 | 清晰的使用示例 |

---

## 八、预期收益

### 8.1 定量收益

| 指标 | 当前 | 目标 | 改善 |
|------|------|------|------|
| 代理数量 | 10个 | 9个 | -10% |
| 代码行数 | 2423行 | ~2200行 | -9% |
| 维护成本 | 2个代理 | 1个代理 | -50% |
| 功能重复率 | 30% | 0% | -100% |

### 8.2 定性收益

✅ **架构简化**: 10→9个代理，职责更清晰
✅ **减少困惑**: 一个入口处理所有撰写任务
✅ **功能完整**: 整合所有撰写能力
✅ **易于扩展**: 模块化设计，易于添加新功能
✅ **向后兼容**: 旧代码无需修改

---

## 九、时间表

| 阶段 | 工作量 | 时间 | 负责人 |
|------|--------|------|--------|
| 阶段1: 准备 | 1天 | Day 1 | - |
| 阶段2: 模块拆分 | 2天 | Day 2-3 | - |
| 阶段3: 统一入口 | 1天 | Day 4 | - |
| 阶段4: 向后兼容 | 1天 | Day 5 | - |
| 阶段5: 清理优化 | 1天 | Day 6 | - |
| **总计** | **6天** | **1周** | - |

---

## 十、下一步行动

### 立即行动

- [ ] 审批合并方案
- [ ] 创建开发分支
- [ ] 开始阶段1：准备阶段

### 后续行动

- [ ] 执行阶段2-5
- [ ] 代码审查
- [ ] 文档更新
- [ ] 发布说明

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-23
