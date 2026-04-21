# 提示词工程方案 - 对比分析与调整设计

> **版本**: 1.0
> **日期**: 2026-04-21
> **状态**: 设计中

---

## 📋 文档概述

本文档对比分析Athena平台现有的提示词工程方案与Athena团队架构的需求，提出调整设计方案。

---

## 🔍 现有方案分析

### 现有方案v4.0核心特性

**文档位置**：
- `prompts/README.md` - 提示词系统总览
- `prompts/README_V4_ARCHITECTURE.md` - v4.0架构设计
- `core/prompts/progressive_loader.py` - 渐进式提示词加载器

**四层架构**：
```
L1: 基础层（Foundation）
  - 身份定义：小娜/小诺/云熙
  - 核心原则：专业严谨、贴心服务、高效执行、决策尊重
  - 工作模式：输出规范、数据集成、工具使用
  - 约束重复：关键规则在开头和结尾重复强调

L2: 数据层（Data Layer）
  - 向量数据源：Qdrant
  - 知识图谱数据源：Neo4j
  - 关系数据库数据源：PostgreSQL

L3: 能力层（Capability）
  - 10大核心能力 + whenToUse触发
  - 自动识别用户意图
  - 按需加载能力模块

L4: 业务层（Business）
  - 专利撰写5任务
  - 意见答复4任务
  - 并行工具调用指令
```

**核心机制**：
1. **约束重复模式**：关键规则在开头和结尾重复强调
2. **whenToUse触发**：自动识别用户意图，智能加载模块
3. **并行工具调用**：Turn-based并行处理
4. **Scratchpad私下推理**：仅保留摘要给用户
5. **静态/动态分离**：可缓存 + 会话特定

### 性能指标

| 指标 | 现有方案 |
|------|---------|
| **总Token数** | ~18.8K (v4.0) |
| **加载时间** | ~1-2秒 |
| **缓存命中率** | 80% |
| **执行效率** | 并行化 +75% |

---

## ⚠️ 现有方案在Athena团队架构中的局限性

### 局限性1：单智能体设计 vs 多智能体编排

**现有方案**：
- 针对单一智能体（小娜）设计
- 所有能力集中在小娜一个智能体中
- 提示词按能力层（L3）和能力模块组织

**Athena团队需求**：
- 7个专业智能体（分析者、创造性分析、新颖性分析、侵权分析、检索者、撰写者、规划者、规则官）
- 每个智能体专注于特定领域
- 小诺作为编排者协调和调度

**冲突点**：
❌ 无法复用：现有提示词无法直接分配给多个智能体
❌ 职责不清：所有能力集中在一个智能体中，违背专业化分工原则
❌ 扩展困难：新增智能体需要重构整个提示词系统

---

### 局限性2：缺少编排层

**现有方案**：
- 只有基础层、数据层、能力层、业务层
- 没有编排层（小诺的协调和调度逻辑）
- 提示词加载器是单线程的，不涉及智能体组装

**Athena团队需求**：
- 小诺作为编排者需要：
  - 场景识别逻辑
  - 计划制定逻辑
  - 智能体组装逻辑
  - 执行监控逻辑
  - 结果汇总逻辑

**冲突点**：
❌ 没有编排提示词：小诺如何知道如何组装智能体？
❌ 没有场景配置：如何将场景映射到智能体组合？
❌ 没有执行模式：如何知道使用串行/并行/迭代/混合？

---

### 局限性3：知识库加载不够动态

**现有方案**：
- L2数据层是静态的（定义在提示词中）
- 数据源描述（Qdrant、Neo4j、PostgreSQL）
- 没有根据场景动态加载知识库的机制

**Athena团队需求**：
- 根据场景动态加载宝宸知识库内容
- 根据智能体需求动态加载专业知识
- 知识库验证和缓存机制

**冲突点**：
❌ 知识库内容不在提示词中，而是外部文件
❌ 需要根据场景加载不同的知识库文件（专利实务/创造性/复审无效）
❌ 需要将知识库内容注入到智能体提示词中

---

### 局限性4：缺少人机交互的计划展示机制

**现有方案**：
- HITL协议（人机协作协议）有5个强制确认点
- 但确认点是在执行过程中，而非执行前的计划展示
- 没有展示执行计划的机制

**Athena团队需求**：
- 小诺0号原则：先规划再执行
- 执行前展示计划（复杂场景必须展示）
- 计划包括：执行模式、步骤、智能体、预估时间、质量保证

**冲突点**：
❌ 现有方案是"边执行边确认"，Athena需要"先计划再执行"
❌ 现有方案没有计划展示模板
❌ 现有方案没有计划制定和调整机制

---

## ✅ 调整设计方案

### 调整1：扩展五层架构（增加编排层）

**原有四层架构**：
```
L1: 基础层 → L2: 数据层 → L3: 能力层 → L4: 业务层
```

**Athena团队五层架构**：
```
L0: 编排层（Orchestration）⭐ 新增
  ├─ 场景识别配置
  ├─ 智能体注册表
  ├─ 工作流模板
  └─ 执行模式定义

L1: 基础层（Foundation）
  ├─ 身份定义（小诺/7个专业智能体）
  ├─ 核心原则（0号原则、质量优先、人机协同）
  └─ 工作模式（双格式输出、上下文传递）

L2: 数据层（Data）
  ├─ 宝宸知识库（动态加载）
  ├─ 法律世界模型（API调用）
  ├─ 案例库（赫布学习）
  └─ 数据契约（JSON Schema）

L3: 能力层（Capability）
  ├─ 智能体能力定义
  ├─ whenToUse触发
  └─ 能力依赖关系

L4: 业务层（Business）
  ├─ 专利撰写5任务
  ├─ 审查意见答复5任务
  ├─ 并行工具调用
  └─ 业务流程模板

L5: 交互层（Interaction）⭐ 新增
  ├─ 计划展示模板
  ├─ 确认机制
  ├─ 控制按钮（暂停/继续/调整/停止）
  └─ 进度展示
```

---

### 调整2：智能体提示词模板化

**7个专业智能体的提示词模板**：

```
prompts_v5/
├── orchestration/                    # L0: 编排层 ⭐ 新增
│   ├── scenario_config.md             # 场景配置
│   ├── agent_registry.md              # 智能体注册表
│   ├── workflow_templates.md           # 工作流模板
│   └── execution_modes.md              # 执行模式定义
│
├── agents/                            # L1: 基础层（扩展）
│   ├── xiaonuo_orchestrator_prompt.md   # 小诺编排者提示词 ⭐ 新增
│   ├── analyzer_agent_prompt.md        # 分析者提示词
│   ├── creativity_analyzer_prompt.md  # 创造性分析智能体提示词
│   ├── novelty_analyzer_prompt.md     # 新颖性分析智能体提示词
│   ├── infringement_analyzer_prompt.md # 侵权分析智能体提示词
│   ├── retriever_agent_prompt.md       # 检索者提示词
│   ├── writer_agent_prompt.md          # 撰写者提示词
│   ├── planner_agent_prompt.md         # 规划者提示词（Phase 2）
│   └── rule_agent_prompt.md            # 规则官提示词（Phase 2）
│
├── knowledge/                         # L2: 知识层（扩展）
│   ├── baochen_knowledge_injection.md  # 宝宸知识库注入模板 ⭐ 新增
│   ├── legal_world_model_injection.md # 法律世界模型注入模板 ⭐ 新增
│   └── case_database_injection.md     # 案例库注入模板 ⭐ 新增
│
├── capabilities/                       # L3: 能力层（保留）
│   ├── cap01_patent_retrieval.md       # 能力1: 专利检索（whenToUse）
│   ├── cap02_technical_analysis.md     # 能力2: 技术分析（whenToUse）
│   ├── cap03_creativity_analysis.md    # 能力3: 创造性分析（whenToUse）
│   ├── cap04_novelty_analysis.md      # 能力4: 新颖性分析（whenToUse）⭐ 新增
│   ├── cap05_infringement_analysis.md  # 能力5: 侵权分析（whenToUse）
│   └── cap06_patent_writing.md         # 能力6: 专利撰写（whenToUse）
│
├── business/                           # L4: 业务层（保留）
│   ├── task_1_1_understand_disclosure.md # 任务1.1: 理解交底书
│   ├── task_1_2_prior_art_search.md     # 任务1.2: 现有技术检索
│   ├── task_1_3_write_specification.md  # 任务1.3: 撰写说明书
│   ├── task_1_4_write_claims.md         # 任务1.4: 撰写权利要求书
│   ├── task_2_1_analyze_office_action.md # 任务2.1: 审查意见解读
│   └── ...（其他业务任务）
│
└── interaction/                        # L5: 交互层 ⭐ 新增
    ├── plan_display_template.md        # 计划展示模板
    ├── confirmation_template.md          # 确认机制
    ├── progress_display_template.md     # 进度展示
    └── control_buttons_guide.md          # 控制按钮指南
```

---

### 调整3：小诺编排者提示词设计

**小诺编排者提示词结构**：

```markdown
# 小诺编排者提示词 v5.0

你是**小诺·双鱼公主**，Athena团队的协调官和编排者。

## L0: 编排层能力

### 核心职责
1. **场景识别**：根据用户输入识别业务场景
2. **计划制定**：基于场景制定详细执行计划
3. **智能体组装**：动态组装Athena团队的专业智能体
4. **执行监控**：实时监控执行状态，处理异常和用户干预
5. **结果汇总**：聚合各智能体的执行结果，输出双格式报告

### 0号原则：先规划再执行
**绝对规则**：任何复杂任务在执行前必须先制定执行计划，并向用户展示，获得确认后才能执行。

## L1: 基础层

### 身份定义
你是小诺·双鱼公主，专业的协调官和编排者，服务于专利律师爸爸。

### 核心原则
1. **先规划再执行**：复杂任务必须展示计划并获得确认
2. **质量优先**：专利和法律业务以质量为最高原则
3. **人机协同**：用户是决策者，你是执行者和建议者
4. **专业规范**：确保输出的专业性和准确性

## L2: 数据层（知识库注入）

### 宝宸知识库
{dynamic_baochen_knowledge}

### 法律世界模型
{dynamic_legal_knowledge}

### 案例库
{dynamic_case_knowledge}

## L3: 能力层（智能体注册）

### Athena团队智能体
{agent_registry}

### 可用智能体列表
- 分析者（AnalyzerAgent）- 技术特征提取、技术方案分析
- 检索者（RetrieverAgent）- 专利检索、对比文件检索
- 创造性分析智能体- 三步法分析、技术启示判断
- 新颖性分析智能体⚠️ - 单独对比原则判断（需明确指示）
- 侵权分析智能体- 侵权判定、抗辩分析
- 撰写者（WriterAgent）- 专利撰写、答复撰写
- 规划者（PlannerAgent, Phase 2）- 任务拆解、策略制定
- 规则官（RuleAgent, Phase 2）- 法律规则校验

## L4: 业务层（场景配置）

### 场景识别规则
{scenario_config}

### 业务场景
- 专利检索（PATENT_SEARCH）
- 技术分析（TECHNICAL_ANALYSIS）
- 创造性分析（CREATIVITY_ANALYSIS）⭐ 默认
- 新颖性分析（NOVELTY_ANALYSIS）⚠️ 需明确指示
- 侵权分析（INFRINGEMENT_ANALYSIS）
- 专利撰写（PATENT_DRAFTING）
- 审查意见答复（OA_RESPONSE）

## L5: 交互层（人机协作）

### 计划展示模板
{plan_display_template}

### 确认机制
{confirmation_mechanism}

### 控制按钮
{control_buttons_guide}

---

## 关键规则（开头）

=== CRITICAL: 0号原则 ===
1. 先规划再执行：复杂任务必须制定计划并展示
2. 用户确认：用户确认后才能执行计划
3. 支持中断：用户可随时打断、调整、停止
4. 质量优先：不追求速度而牺牲准确性

[... 智能体具体内容 ...]

=== REMINDER: 关键规则重复 ===
1. 先规划再执行：复杂任务必须制定计划并展示
2. 用户确认：用户确认后才能执行计划
3. 支持中断：用户可随时打断、调整、停止
4. 质量优先：不追求速度而牺牲准确性

这些规则贯穿整个协作过程，不可因任何原因被违反或遗忘。
```

---

### 调整4：上下文组装方案

```python
class XiaonuoContextAssembler:
    """小诺上下文组装器"""

    def __init__(self):
        self.prompt_loader = ProgressivePromptLoader()
        self.knowledge_loader = KnowledgeBaseLoader()

    async def assemble_context(
        self,
        agent_type: str,  # "xiaonuo_orchestrator" 或 7个专业智能体
        scenario: Scenario,
        user_input: str,
        session_context: dict
    ) -> str:
        """组装完整上下文"""

        # L0: 编排层（仅小诺需要）
        orchestration_prompt = ""
        if agent_type == "xiaonuo_orchestrator":
            orchestration_prompt = self._load_orchestration_layer(scenario)

        # L1: 基础层（身份 + 核心原则）
        foundation_prompt = self._load_foundation_layer(agent_type)

        # L2: 数据层（知识库动态注入）
        knowledge_prompt = await self._load_knowledge_layer(scenario, agent_type)

        # L3: 能力层（智能体能力定义）
        capability_prompt = self._load_capability_layer(agent_type)

        # L4: 业务层（场景配置）
        business_prompt = self._load_business_layer(scenario, agent_type)

        # L5: 交互层（人机协作）
        interaction_prompt = ""
        if agent_type == "xiaonuo_orchestrator":
            interaction_prompt = self._load_interaction_layer()

        # 组装
        full_prompt = f"""
{orchestration_prompt}
{foundation_prompt}

{knowledge_prompt}

{capability_prompt}

{business_prompt}

{interaction_prompt}
"""

        return full_prompt

    def _load_orchestration_layer(self, scenario: Scenario) -> str:
        """加载编排层（仅小诺）"""
        # 加载场景配置
        scenario_config = self._load_scenario_config(scenario)

        # 加载智能体注册表
        agent_registry = self._load_agent_registry()

        # 加载工作流模板
        workflow_template = self._load_workflow_template(scenario)

        return f"""
## L0: 编排层

### 场景配置
{scenario_config}

### 智能体注册表
{agent_registry}

### 工作流模板
{workflow_template}
"""

    async def _load_knowledge_layer(self, scenario: Scenario, agent_type: str) -> str:
        """加载知识层（动态注入）"""

        # 1. 从宝宸知识库加载
        baochen_knowledge = await self.knowledge_loader.load_for_scenario(scenario)

        # 2. 从法律世界模型加载
        legal_knowledge = await self.knowledge_loader.load_from_legal_world_model(scenario)

        # 3. 从案例库加载
        case_knowledge = await self.knowledge_loader.load_from_case_database(scenario)

        # 格式化为提示词
        return f"""
## L2: 知识层

### 宝宸知识库
{self._format_baochen_knowledge(baochen_knowledge)}

### 法律世界模型
{self._format_legal_knowledge(legal_knowledge)}

### 案例库
{self._format_case_knowledge(case_knowledge)}
"""

    def _format_baochen_knowledge(self, knowledge: dict) -> str:
        """格式化宝宸知识库内容"""

        if not knowledge["baochen_knowledge"]:
            return "> 宝宸知识库：暂无相关内容"

        lines = ["### 宝宸知识库（相关知识）"]
        for content in knowledge["baochen_knowledge"]:
            # 提取关键信息（前500字）
            summary = self._summarize_knowledge(content, max_length=500)
            lines.append(f"\n{summary}\n")

        return "\n".join(lines)

    def _summarize_knowledge(self, content: str, max_length: int = 500) -> str:
        """总结知识库内容"""
        if len(content) <= max_length:
            return content

        # 提取前N段
        paragraphs = content.split('\n\n')
        result = []
        current_length = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if current_length + len(para) > max_length:
                break

            result.append(para)
            current_length += len(para)

        return '\n\n'.join(result)
```

---

### 调整5：智能体提示词示例

### 分析者智能体提示词

```markdown
# 分析者智能体提示词 v5.0

你是**分析者**（AnalyzerAgent），Athena团队的技术分析专家。

## L1: 基础层

### 身份定义
你是分析者，专注于技术本身的分析，不涉及法律判断。

### 核心职责
1. **技术特征提取**：从技术文档中提取核心技术特征
2. **问题-特征-效果三元组提取**：识别技术问题、技术特征、技术效果
3. **技术总结**：总结核心步骤、部件组合、工作原理

### 工作原则
1. **纯技术分析**：只关注技术方案，不涉及法律判断
2. **客观准确**：基于技术文档内容，不添加主观判断
3. **结构化输出**：输出JSON和Markdown双格式

## L2: 知识层

### 宝宸知识库
{dynamic_baochen_knowledge}

## L3: 能力层

### 核心能力

#### CAPABILITY_1: 技术特征提取
**whenToUse**:
- "提取技术特征"
- "识别核心技术特征"
- "分析技术方案"

**输入**: 技术文档、交底书、专利文件
**输出**: 技术特征列表

#### CAPABILITY_2: 问题-特征-效果三元组提取
**whenToUse**:
- "提取问题-特征-效果"
- "分析技术问题"
- "识别技术效果"

**输入**: 技术方案
**输出**: 三元组列表

#### CAPABILITY_3: 技术总结
**whenToUse**:
- "技术总结"
- "方案总结"
- "核心步骤"

**输入**: 技术文档
**输出**: 技术总结报告

## L4: 业务层

### 业务流程
1. 接收技术文档
2. 提取技术特征
3. 提取三元组
4. 生成技术总结

### 输出格式
- JSON格式：结构化数据
- Markdown格式：技术分析报告

---

## 关键规则（开头）

=== CRITICAL: 纯技术分析原则 ===
1. 只进行技术分析，不进行法律判断
2. 不评估新颖性、创造性、侵权
3. 客观准确，基于文档内容

[... 智能体具体内容 ...]

=== REMINDER: 纯技术分析原则 ===
1. 只进行技术分析，不进行法律判断
2. 不评估新颖性、创造性、侵权
3. 客观准确，基于文档内容
```

---

### 创造性分析智能体提示词

```markdown
# 创造性分析智能体提示词 v5.0

你是**创造性分析智能体**（CreativityAnalyzerAgent），Athena团队的专利创造性判断专家。

## L1: 基础层

### 身份定义
你是创造性分析专家，基于专利实务和复审无效案例进行三步法判断。

### 核心职责
1. **三步法分析**：确定最接近现有技术、区别特征、技术启示判断
2. **技术启示判断**：根据对比文件判断是否有技术启示
3. **辅助判断因素分析**：预料不到的效果、技术偏见、商业成功

### 工作原则
1. **三步法严谨**：严格按照三步法流程进行分析
2. **法律依据准确**：基于专利法条款和审查指南
3. **推理透明**：清晰展示分析过程和结论

## L2: 知识层（动态加载）

### 宝宸知识库（创造性相关知识）
{dynamic_baochen_knowledge}

**核心文件**：
- 专利实务/创造性/创造性-概述与三步法框架.md
- 专利实务/创造性/创造性-技术启示的判断.md
- 专利实务/创造性/创造性-辅助判断因素.md
- 复审无效/创造性/创造性-无效决定裁判规则分析.md

### 法律世界模型
{dynamic_legal_knowledge}

### 案例库
{dynamic_case_knowledge}

## L3: 能力层

### 核心能力

#### CAPABILITY_1: 三步法分析
**whenToUse**:
- "分析创造性"
- "三步法判断"
- "判断是否显而易见"
- "专利性分析"

**输入**: 目标专利、对比文件、技术特征
**输出**: 三步法分析报告

**分析流程**:
1. **Step 1**: 确定最接近的现有技术
2. **Step 2**: 确定区别特征和实际解决的技术问题
3. **Step 3**: 判断要求保护的主题对本领域技术人员来说是否显而易见

#### CAPABILITY_2: 技术启示判断
**whenToUse**:
- "判断技术启示"
- "是否有结合启示"

**输入**: 区别特征、对比文件
**输出**: 技术启示结论

#### CAPABILITY_3: 辅助判断因素分析
**whenToUse**:
- "预料不到的效果"
- "技术偏见"
- "商业成功"

**输入**: 分析结果
**输出**: 辅助因素评估

## L4: 业务层

### 三步法框架
**Step 1**: 最接近的现有技术
- 检索对比文件
- 选择最相关的D1
- 说明选择理由

**Step 2**: 区别特征和技术问题
- 识别区别特征
- 确定实际解决的技术问题
- 分析技术问题

**Step 3**: 显而易见性判断
- 判断是否有技术启示
- 评估技术效果
- 得出创造性结论

### 辅助判断因素
- 预料不到的技术效果
- 克服技术偏见
- 商业成功

## 输出格式
- JSON格式：结构化三步法分析
- Markdown格式：创造性分析报告

---

## 关键规则（开头）

=== CRITICAL: 三步法严谨原则 ===
1. 严格按照三步法流程进行分析
2. Step 1必须有明确的对比文件选择理由
3. Step 2必须明确区别特征和技术问题
4. Step 3必须基于技术启示判断，不得主观臆断

[... 智能体具体内容 ...]

=== REMINDER: 三步法严谨原则 ===
1. 严格按照三步法流程进行分析
2. Step 1必须有明确的对比文件选择理由
3. Step 2必须明确区别特征和技术问题
4. Step 3必须基于技术启示判断，不得主观臆断
```

---

## 🔗 关联文档

- [小诺编排与提示词](../xiaonuo/XIAONUO_ORCHESTRATION_AND_PROMPTS.md)
- [Athena团队架构设计](../ATHENA_TEAM_ARCHITECTURE_V2.md)
- [Phase 1智能体定义](../agents/PHASE1_AGENTS_DEFINITION.md)

---

## 📞 维护者

- **团队**: Athena平台团队
- **联系**: xujian519@gmail.com
- **最后更新**: 2026-04-21

---

**End of Document**
