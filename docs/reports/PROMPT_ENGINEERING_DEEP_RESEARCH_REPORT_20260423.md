# Athena Prompt Engineering System Deep Research Report (Calibrated)

> 日期: 2026-04-23
> 范围: 当前项目内提示词资产、加载链路、场景化生成、变量替换、质量评估与运行时集成
> 结论级别: 架构研究 + 诊断报告 + **落地校准**
> **校准说明**: 本报告基于原研究结论，对"三源融合 + 动态提示词主链路"已从方案进入真实落地的现状进行校准，修正现状描述、收敛下一步关键增量、补充已验证路径与风险边界。

---

## 1. Executive Summary

当前项目已经积累了数量可观、质量不低的提示词资产，尤其是 `prompts/` 目录中的四层提示词体系、HITL 协议、业务层任务模板和能力层模板，已经具备较强的方法论价值。部分关键模板经过自带质量评估器评估后，整体得分在 0.78-0.88 区间，说明项目在提示词内容设计层面并不薄弱。

**关键变化（相较于原研究假设）**：

自原研究编制以来，**"三源融合 + 并入动态提示词主链路"已实现真实落地**：

- **`core/legal_prompt_fusion/`** 模块已完成 PostgreSQL（结构化硬证据）+ Neo4j（关系推理与场景编排）+ Obsidian Wiki（背景解释与动态经验知识）的三源统一访问、混合检索、上下文构建与版本联动。
- **主链路 API** `POST /api/v1/prompt-system/prompt/generate`（`core/api/prompt_system_routes.py`）已完成融合注入点的嵌入：场景识别 → 规则检索 → 能力调用 → 三源检索（开关控制）→ 变量替换 → 融合证据块追加 → 缓存返回。
- **版本联动与缓存失效机制**已生效：Wiki revision → template version → 缓存键自动失效。
- **提示词模板缓存（P1优化）**已落地。

**但当前提示词系统仍存在"资产强、运行时弱、链路并行"的问题**：

1. 三源融合虽已并入主链路，但**默认开关关闭**（`LEGAL_PROMPT_FUSION_ENABLED=false`），生产流量尚未默认走融合路径。
2. 提示词系统存在**多套并行实现**，旧链路（`progressive_loader.py`、`unified_prompt_manager*.py`）未被清理，缺乏单一事实源。
3. **部分核心管理器仍存在异步接口误用**，导致设计上的高级能力难以真正生效。
4. 变量替换、上下文拼装、版本选择虽已可用，但**未统一为标准模板协议**（PromptSpec 仍为建议，未落地）。
5. 提示词质量评估更多衡量"格式完整度"，而非真实响应质量。

因此，当前项目的主要矛盾已从"没有运行时"转为**"运行时已建、但未收口、未默认启用、未清理旧链路"**。下一阶段的目标不再是"建立 Prompt Engineering 2.0 工程底座"，而是**"完成从并行体系到主链路的收口，启用已验证能力，清理遗留债务"**。

---

## 2. Research Scope And Method

本次研究重点审查了以下几类对象：

### 2.1 静态提示词资产

- `prompts/foundation/`
- `prompts/data/`
- `prompts/capability/`
- `prompts/business/`
- `prompts/agents/xiaona/`

### 2.2 提示词加载与组装逻辑

- `core/ai/prompts/progressive_loader.py`
- `core/ai/prompts/__init__.py`
- `core/ai/prompts/unified_prompt_manager.py`
- `core/ai/prompts/unified_prompt_manager_extended.py`
- `core/ai/prompts/unified_prompt_manager_production.py`
- `core/ai/prompts/integrated_prompt_generator.py`
- `core/ai/prompts/capability_integrated_prompt_generator.py`

### 2.3 场景化动态提示词系统（主链路）

- `core/api/prompt_system_routes.py`
- `domains/legal/core_modules/legal_world_model/scenario_rule_retriever_optimized.py`
- `domains/legal/core_modules/legal_world_model/scenario_identifier_optimized.py`
- `core/capabilities/prompt_template_cache.py`

### 2.4 三源融合模块（已落地）

- `core/legal_prompt_fusion/models.py`
- `core/legal_prompt_fusion/providers.py`
- `core/legal_prompt_fusion/hybrid_retriever.py`
- `core/legal_prompt_fusion/prompt_context_builder.py`
- `core/legal_prompt_fusion/sync_manager.py`
- `core/legal_prompt_fusion/wiki_indexer.py`
- `core/api/legal_prompt_fusion_routes.py`

### 2.5 业务代理内嵌提示词

- `core/framework/agents/xiaona/patent_drafting_prompts.py`
- `prompts/agents/xiaona/novelty_analyzer_prompts.py`
- 多个 `get_system_prompt()` 风格的代理类

### 2.6 质量评估与定量辅助

- `core/ai/prompts/quality_evaluator.py`
- 对四个代表性 Markdown 提示文件进行半定量评分

评分样本结果如下：

| 文件 | overall_score | 观察 |
|------|---------------|------|
| `prompts/foundation/xiaona_core_v3_compressed.md` | 0.843 | 结构紧凑，规则明确，适合作为基础层 |
| `prompts/foundation/hitl_protocol_v4_constraint_repeat.md` | 0.803 | 约束表达清楚，但偏协议型，不适合作为唯一系统提示 |
| `prompts/capability/cap04_inventive_v2_with_whenToUse.md` | 0.878 | 可执行性和流程性最强，业务价值高 |
| `prompts/business/task_2_1_oa_analysis_v2_with_parallel.md` | 0.784 | 可读性强，但运行态可执行性仍依赖外部能力系统 |

这些分数说明，项目的静态提示词资产并不差，问题主要发生在**链路收口和旧体系清理**层。

---

## 3. Current Prompt Engineering Landscape

## 3.1 已存在的五类提示词体系

### A. 四层 Markdown 提示词体系

以 `prompts/` 为中心，形成 Foundation / Data / Capability / Business 四层结构，并叠加 HITL 协议、whenToUse 触发、并行调用说明、业务任务拆解。这是当前项目最有体系感的一套资产。

### B. 渐进式加载体系（遗留，待清理）

`core/ai/prompts/progressive_loader.py` 尝试实现：

- 最小上下文优先
- 按需加载能力层和业务层
- 压缩加载
- 语义缓存

**现状**：默认映射仍指向旧版本资产（`xiaona_l1_foundation_v2_optimized.md`、`hitl_protocol_v3_mandatory.md`、`cap04_inventive.md`、`task_2_1_analyze_office_action.md`），且未与主链路打通。**建议标记为 deprecated，逐步迁移至场景规则驱动体系。**

### C. 统一提示词管理器体系（遗留，待清理）

`unified_prompt_manager` 系列试图整合：

- L1-L4 角色提示词
- Lyra 提示词优化
- 场景规则
- 专家人设

**现状**：设计目标很高，但存在**异步接口误用**（`load_prompt`/`optimize_prompt` 为 async，却在多处被同步调用），导致高级能力实际失效。建议**冻结新增功能**，修复关键缺陷后评估是否整体迁移至主链路。

### D. 场景规则驱动提示词 API（当前生产主链路）

`core/api/prompt_system_routes.py` 的实际对外链路是：

1. 场景识别（`ScenarioIdentifierOptimized`）
2. Neo4j 规则检索（`ScenarioRuleRetrieverOptimized`）
3. 变量替换（`substitute_variables`，简单 `{var}` 替换）
4. 可选能力调用（`execute_capability_workflow`）
5. **三源融合注入**（开关控制）
6. 缓存返回 `system_prompt` / `user_prompt`

**这是目前最接近生产可用的提示词运行时路径，也是唯一已并入三源融合的链路。**

### E. 业务代理内嵌提示词

各类代理、分析器和业务模块中仍保留独立的 Python 字符串模板。这些模板可快速落地，但导致标准分裂和维护成本增加。

---

## 4. Existing Design Logic Analysis

## 4.1 现有设计逻辑的优点

### 1. 提示词已经具备分层意识

四层设计本质上对应了一个非常合理的提示词认知模型：

- L1: 身份与价值观
- L2: 数据能力边界
- L3: 通用能力
- L4: 具体业务任务

这比简单的大一统 system prompt 更适合复杂业务型 AI 助手。

### 2. 已经重视人机协作与决策边界

HITL 协议不是简单礼貌性话术，而是明确规定：

- 用户保留决策权
- 高风险任务必须确认
- 支持中断与回退
- 支持偏好学习

这对法律、专利、文书类高风险场景非常重要。

### 3. 三源融合架构已验证可行

PostgreSQL + Neo4j + Obsidian Wiki 的三源混合检索、统一访问层、上下文构建、版本联动，已经通过代码实现并嵌入主链路。该架构在法律场景下的证据分层（硬法条 / 关系推理 / 实务背景）具备合理性，且缓存失效机制设计正确。

### 4. 已经开始引入触发机制与上下文裁剪

`whenToUse`、渐进式加载、按任务加载能力层，说明项目已经意识到：

- 提示词不能无限堆长
- 不同任务应加载不同上下文
- 触发条件应该明确

这为后续真正的上下文预算管理打下了基础。

### 5. 已经具备把提示词和能力系统绑定的意识

业务层模板不只是"告诉模型该怎么答"，还尝试描述：

- 应调用哪些数据源
- 哪些步骤可以并行
- 哪些判断必须顺序进行

这使提示词从"文案"开始向"任务协议"演进。

---

## 5. Structure Pattern Analysis

## 5.1 当前项目中常见的提示词结构模式

### 模式一: 大块系统说明型

代表文件:

- `core/config/system_prompt.py`
- `core/ai/intelligence/dynamic_prompt_generator.py`

特点：

- 角色定义丰富
- 知识库说明详细
- 输出标准明确
- 容易冗长
- 容易引入过时或不一致事实

适用：

- 早期系统提示
- 单模型单业务场景

问题：

- token 成本高
- 易与动态上下文重复
- 知识数量描述容易失真

### 模式二: 规则清单型

代表文件:

- `prompts/foundation/xiaona_core_v3_compressed.md`
- `prompts/foundation/hitl_protocol_v4_constraint_repeat.md`

特点：

- 强调 MUST / MUST NOT
- 可执行性高
- 行为约束明确
- 适合作为基础层

问题：

- 对复杂业务场景支撑不足
- 容易缺少输入输出契约

### 模式三: 工作流协议型

代表文件:

- `prompts/capability/cap04_inventive_v2_with_whenToUse.md`
- `prompts/business/task_2_1_oa_analysis_v2_with_parallel.md`

特点：

- 有阶段划分
- 有工具调用逻辑
- 有中间产物定义
- 有输出格式示例

优点：

- 与 agent/tool 编排天然契合
- 适合转化为标准模板

问题：

- 许多调用是说明性伪代码，不是统一运行协议
- 实际运行系统未必具备对应工具接口

### 模式四: 纯字符串插值型

代表文件:

- `prompts/agents/xiaona/novelty_analyzer_prompts.py`
- `core/framework/agents/xiaona/patent_drafting_prompts.py`

特点：

- 上手快
- 适合单任务
- 容易直接插值业务数据

问题：

- 变量规范松散
- 缺少 schema
- 缺少统一模板治理
- 难复用、难版本化、难追踪

---

## 6. Application Effect Analysis

## 6.1 当前系统的实际效果

结合代码与文档，可以把当前效果分为两个层面：

### 1. 内容资产层效果较好

- 提示词对任务边界、交互方式、业务流程的定义比较充分。
- 对高风险场景有明确的人机协作约束。
- 能力层和业务层模板具备一定领域深度。
- **三源融合上下文在法律场景下的证据分层设计经过代码验证，结构合理。**

### 2. 工程运行层效果不稳定

- 最新模板未必被默认链路使用（`progressive_loader` 仍指向旧版）。
- 不同入口加载的提示词不一致（主链路 vs 旧链路 vs 代理内嵌）。
- **三源融合默认关闭，生产流量尚未实际享受到该能力。**
- 变量替换和模板装配方式不统一（主链路用 `{var}`，其他链路混用 f-string / Jinja2 / `%s`）。
- 场景 API 返回的提示词通常是规则模板替换结果，而不是完整吸收 `prompts/` 资产后的统一产物。

因此，用户最终体验可能出现以下割裂：

1. 某些任务回答非常专业，像经过精心设计。
2. 某些任务退回到通用系统提示或简单模板。
3. 同一场景经不同入口触发时，回答风格、结构、约束强度不一致。
4. **三源融合证据块仅当开关开启且缓存未命中时才会注入，行为不可预期。**

---

## 7. Core Problem Diagnosis

以下问题按优先级进行诊断。

## 7.1 P0: 三源融合已落地但未默认启用

**现状**：

- `core/legal_prompt_fusion/` 模块完整实现了三源统一访问、混合检索、上下文构建、版本联动。
- 主链路 `generate_prompt()` 已嵌入融合注入点（第 484-578 行）。
- 但环境变量 `LEGAL_PROMPT_FUSION_ENABLED` 默认值为 `false`。

**影响**：

- 已完成的三源融合工程投入未产生实际生产价值。
- 新旧链路实际未经历充分流量验证。
- 缓存命中率、融合证据相关性、响应延迟等关键指标缺乏线上数据。

**结论**：

这是当前提示词工程最关键的**"建而未用"**问题。建议通过灰度策略逐步启用，而非直接全量打开。

## 7.2 P0: 运行时高级提示词能力与异步接口存在错配

`unified_prompt_manager.py` 中 `load_prompt()` 和 `optimize_prompt()` 是异步方法，但在以下位置被按同步方法调用：

- `core/ai/prompts/integrated_prompt_generator.py`（第 212 行 `optimize_prompt`，第 276 行 `load_prompt`）
- `core/ai/prompts/unified_prompt_manager_extended.py`（第 209 行 `load_prompt`）
- `core/ai/prompts/unified_prompt_manager_production.py`（第 457 行 `load_prompt`）

这意味着以下高级能力存在实际失效风险：

- L1-L4 角色注入
- Lyra 优化注入
- 默认场景回退提示加载

**影响**：

- 理论设计与实际行为不一致
- 可能将 coroutine 对象当作字符串使用
- 场景增强链路难以稳定上线

**结论**：

这是旧链路的关键实现缺陷，**修复成本低于迁移成本时优先修复，否则应冻结旧链路并加速迁移至主链路**。

## 7.3 P0: 最新高质量提示资产没有成为默认加载链路

`progressive_loader.py` 的默认映射仍然主要指向旧版本资产：

- 核心加载仍使用 `xiaona_l1_foundation_v2_optimized.md`
- HITL 默认加载 `hitl_protocol_v3_mandatory.md`
- 能力映射仍指向 `cap04_inventive.md`
- 业务映射仍指向 `task_2_1_analyze_office_action.md`

而不是项目中更先进的：

- `hitl_protocol_v4_constraint_repeat.md`
- `cap04_inventive_v2_with_whenToUse.md`
- `task_2_1_oa_analysis_v2_with_parallel.md`

**影响**：

- 文档里宣称的 v4 提示词工程优势，默认用户未必真正享受到
- 工程宣传版本与生产加载版本不一致

**结论**：

项目最好的提示词资产尚未进入默认路径。由于 `progressive_loader` 并非当前主链路，**建议不再投入更新 progressive_loader 的映射，而是将优质资产通过场景规则模板的形式接入主链路**。

## 7.4 P1: 提示词系统存在多套并行实现，缺少单一事实源

目前至少存在以下并行体系：

1. `prompts/` Markdown 四层体系
2. `progressive_loader.py` 渐进式加载体系（遗留）
3. `unified_prompt_manager*.py` 统一管理器体系（遗留）
4. `prompt_system_routes.py` 场景规则 API 体系（当前主链路，已并入三源融合）
5. 各业务代理内嵌字符串模板体系
6. `core/config/system_prompt.py` 静态大系统提示体系

**影响**：

- 不同调用链得到不同 system prompt
- 模板更新无法一处修改、全链路生效
- 评估、回归、灰度发布难以统一

**结论**：

当前项目没有真正的 Prompt SSOT。但主链路已经具备成为 SSOT 的雏形。**下一步不是新建一套 SSOT，而是把主链路收口为唯一运行时，其他体系标记为 deprecated 并逐步迁移。**

## 7.5 P1: 变量治理缺失，模板表达规范不统一

当前变量表达方式并存：

- Python f-string
- `str.format(**kwargs)`
- Neo4j 场景规则内 `{var}` 替换
- Markdown 中 `{var}`
- Markdown 中 `[占位说明]`
- 部分模板把变量、示例和占位符混写

存在的问题：

1. 无统一变量命名规范
2. 无 required / optional 区分
3. 无默认值声明
4. 无类型约束
5. 无变量来源标注
6. 无缺失变量处理策略
7. 无注入转义策略（主链路仅有 `html.escape()` 基础防护）

**影响**：

- 容易产生空变量、错变量、脏变量
- 模板迁移困难
- 动态上下文可信度下降

## 7.6 P1: 上下文装配策略不完整，复杂度参数形同虚设

`ProgressivePromptLoader` 虽然定义了 `complexity`，但实际 `build_prompt()` 并未基于复杂度调整装配层级或内容强度，更多只是缓存键的一部分。

主链路目前**尚未实现基于 token budget 的优先级槽位装配**，三源融合证据块是统一追加到 system_prompt 末尾，未根据任务复杂度或 token 预算做裁剪。

**影响**：

- 简单任务可能加载过多信息（含融合证据块后更明显）
- 复杂任务又可能缺少关键约束或证据上下文
- token 成本不可控

## 7.7 P1: 系统提示中的知识事实存在不一致和过时风险

不同文件对数据规模、端口、知识库规模的描述不一致，例如：

- `core/config/system_prompt.py` 中的数据统计与
- `core/ai/intelligence/dynamic_prompt_generator.py` 中的说明

存在明显差异。

**影响**：

- 降低系统提示可信度
- 容易误导模型夸大能力
- 用户一旦验证发现不一致，会损害专业感

**结论**：

知识规模、端口、检索能力等事实不应写死在多个提示文件中，应该由运行时 metadata 自动注入。**三源融合的 `__wiki_revision` 和 `__fusion_template_version` 已部分实践了这一思路，应推广到全部动态事实。**

## 7.8 P2: 提示词质量评估器可用但治理价值有限

`quality_evaluator.py` 的优势在于：

- 可快速给出结构化评分
- 可比较不同模板的形式质量

但局限也很明显：

- 对关键词和格式依赖较强
- 偏向衡量"看起来像好提示词"
- 不能反映真实回答准确率、拒答率、工具调用正确率、用户满意度

另外，`core/ai/prompts/__init__.py` 中的 `evaluate_prompt_file()` 存在**命名遮蔽导致的递归调用问题**（第 155 行定义 `evaluate_prompt_file(file_path: str)`，第 165 行调用 `evaluate_prompt_file(Path(file_path))`，因同名同参导致无限递归），说明该评估入口本身也需要整理。

---

## 8. Why The Current System Feels Fragmented

当前系统之所以让人感觉"已经做了很多，但整体还不够稳"，原因在于它同时具备了三种发展阶段的产物：

### 阶段一: 提示词文案阶段

重心是把角色、规则、流程写出来。

### 阶段二: 提示词模块化阶段

重心是拆成 foundation / capability / business，并做压缩加载。

### 阶段三: 提示词运行时阶段

重心是场景识别、变量替换、能力编排、**三源融合、缓存、版本联动**。

**项目当前的状态是：阶段三的骨架（主链路 + 三源融合）已经搭好，但阶段一和阶段二的旧产物仍在并行运行，尚未完成统一收口。**

---

## 9. Verified Architecture And Next Increment

## 9.1 已验证落地的架构组件

以下组件已通过代码实现并具备生产可用性：

| 组件 | 文件路径 | 验证状态 | 备注 |
|---|---|---|---|
| 三源统一访问层 | `core/legal_prompt_fusion/providers.py` | ✅ 已落地 | Postgres + Neo4j + Wiki |
| 混合检索器 | `core/legal_prompt_fusion/hybrid_retriever.py` | ✅ 已落地 | 含 source_bias 权重 |
| 上下文构建器 | `core/legal_prompt_fusion/prompt_context_builder.py` | ✅ 已落地 | 四块结构化输出 |
| 版本联动器 | `core/legal_prompt_fusion/sync_manager.py` | ✅ 已落地 | Wiki revision → template version |
| 主链路融合注入 | `core/api/prompt_system_routes.py:484-578` | ✅ 已落地 | 开关控制，默认关闭 |
| 提示词模板缓存 | `core/capabilities/prompt_template_cache.py` | ✅ 已落地 | P1优化 |
| 场景规则检索器 v2.1 | `scenario_rule_retriever_optimized.py` | ✅ 已落地 | LRU缓存、预加载 |
| 独立融合 API | `core/api/legal_prompt_fusion_routes.py` | ✅ 已落地 | `/context/generate`, `/sync/status` |

## 9.2 下一步关键增量（Next Increment）

基于"已落地但未收口"的现状，建议将后续工作收敛为以下**四个关键增量**，而非重新搭建：

### 增量一: 灰度启用三源融合并建立观测

**目标**：让已落地的三源融合产生实际生产价值。

**动作**：

1. 建立灰度开关（按用户/按场景/按流量比例），而非简单的 true/false 环境变量。
2. 定义融合开启后的关键观测指标：
   - `fusion_evidence_hit_rate`（证据非空率）
   - `fusion_avg_latency_ms`（融合额外延迟）
   - `fusion_cache_hit_rate`（含 revision 的缓存命中率）
   - `response_quality_delta`（开启 vs 关闭的响应质量差异）
3. 建立降级策略：当某源不可用时，自动跳过该源，不阻断主链路。

### 增量二: 主链路收口与旧链路清理

**目标**：让 `prompt_system_routes.py` 成为唯一生产运行时。

**动作**：

1. 标记 `progressive_loader.py` 和 `unified_prompt_manager*.py` 为 **deprecated**，冻结新功能开发。
2. 梳理这些旧链路的实际调用方，制定迁移计划。
3. 修复 `unified_prompt_manager` 的异步调用错配问题，或**明确将其能力迁移至主链路**。
4. 将 `prompts/` 中的高质量资产（v4 系列）转化为场景规则模板，接入主链路。

### 增量三: 变量治理与模板协议化

**目标**：统一变量表达，为主链路建立标准模板协议。

**动作**：

1. 统一主链路变量语法为 Jinja2（`{{ var }}`），替代当前简单 `{var}` 替换。
2. 给场景规则模板增加变量 schema（required / optional / type / default）。
3. 实现缺失变量阻断策略（不得静默吞掉关键变量）。
4. 增强注入安全策略（长度限制、控制字符清洗、prompt injection 标记）。

### 增量四: 上下文预算与复杂度分层

**目标**：避免简单任务加载过多信息，复杂任务缺少关键上下文。

**动作**：

1. 定义优先级槽位（P0 必选 / P1 高价值 / P2 可选 / P3 可淘汰）。
2. 根据 `complexity` 参数或 token 预算，裁剪融合证据块的数量和详细程度。
3. 将 `progressive_loader` 的压缩加载思想迁移至主链路，作为 context budget 分配器的组成部分。

---

## 10. Standardized Template System Proposal (Adjusted)

原研究提出的 `PromptSpec` YAML schema 仍然有价值，但建议**调整落地策略**：

> **不再新建独立的 PromptSpec 运行时，而是将 PromptSpec schema 作为主链路场景规则模板的元数据层**，逐步将现有 Neo4j 场景规则模板升级为符合 PromptSpec 规范的结构。

这样可复用已有的场景规则检索、变量替换、缓存机制，降低迁移成本。

推荐在现有场景规则基础上，逐步补充以下字段：

```yaml
id: patent.oa.analysis.v3
version: 3.0.0
layer: business
domain: patent
task_type: office_action

meta:
  owner: prompt-engineering
  status: production
  tags: [oa, analysis, hitl, parallel]

trigger:
  keywords: [审查意见, OA答复, 驳回理由]
  intent_signals: [office_action]

role:
  identity: 小娜
  persona: 专利法律AI助手
  decision_policy: 用户拥有最终决策权

objective:
  primary_goal: 准确解读审查意见并分解问题

context_policy:
  required_sources: [application_file, office_action]
  optional_sources: [response_history, similar_cases]
  token_budget:
    simple: 3000
    medium: 6000
    complex: 10000

variables:
  required:
    application_number: {type: string, source: user_input}
    oa_text: {type: string, source: document}
  optional:
    response_history: {type: string, default: ""}

fusion_policy:
  enabled: true
  sources: [postgres, neo4j, wiki]
  max_evidence: 12
  relevance_threshold: 0.5

output_contract:
  format: markdown
  sections: [基本信息, 驳回理由, 法律依据, 优先级建议, 需要用户确认]

safety:
  must: [不得跳过强制确认点]
  must_not: [不得伪造法条依据]

evaluation:
  offline_checks: [required_sections, variable_completeness]
  online_metrics: [user_followup_rate, tool_success_rate, fusion_evidence_hit_rate]
```

---

## 11. Variable Governance Proposal

## 11.1 变量命名规范

统一使用 `snake_case`，禁止混用模糊变量名（`data`, `content`, `info`, `context2`）。

## 11.2 变量必须声明四个属性

每个变量都应声明：

1. `type`
2. `required`
3. `source`
4. `default`

## 11.3 模板占位语法统一

**主链路当前使用 `{variable_name}` 简单替换，建议统一升级为 Jinja2 风格**：

- `{{ application_number }}`
- `{{ office_action_text }}`
- `{{ similar_cases | default('暂无') }}`

禁止在正式生产模板中混用：

- `{application_number}`（当前主链路语法，需迁移）
- `[申请号]`
- `%s`
- Python f-string 直插

## 11.4 缺失变量策略

若变量缺失，运行时必须明确选择以下之一：

1. 阻断生成并返回缺失变量清单
2. 使用默认值
3. 降级到低配模板
4. 触发追问式提示

不得静默吞掉关键变量。

## 11.5 注入安全策略

对于用户可控变量，应进行：

- 长度限制
- 控制字符清洗
- Markdown 转义（当前主链路已有 `html.escape()`，需评估是否足够）
- JSON 字段转义
- prompt injection 风险标记

---

## 12. Context Assembly Optimization

## 12.1 建议采用预算驱动的上下文拼装

将上下文拆成以下优先级槽位：

### P0 必选槽位

- 基础身份
- 安全规则
- 当前任务目标
- 输出契约

### P1 高价值槽位

- 当前场景规则
- 必要业务流程
- 必要法条依据
- **三源融合证据（经相关性过滤后）**

### P2 可选增强槽位

- 相似案例
- 历史偏好
- 技术背景
- 长篇范例

### P3 可淘汰槽位

- 宣传性描述
- 系统能力大段介绍
- 过多示例
- 重复强调内容

运行时根据 token budget 从高优先级向低优先级装配。**三源融合证据块应根据 budget 动态裁剪数量和摘要长度，而非全量追加。**

## 12.2 针对复杂度真正分层

当前 `complexity` 参数应被实用化：

### simple

- 仅加载 foundation + 最小 capability
- 不加载长示例
- 不加载案例
- **三源融合仅召回 3 条最高相关性证据**

### medium

- 加载 foundation + capability + 业务步骤
- 注入必要法条和结构模板
- **三源融合召回 5-8 条证据**

### complex

- 加载 foundation + capability + scenario + evidence + output_contract
- 启用强制确认点
- 启用更多中间结果检查
- **三源融合召回 12 条证据（上限）**

---

## 13. Prompt Expression Optimization Suggestions

## 13.1 清晰度优化

建议将现有提示词中的表达从"能力宣讲"改为"执行协议"。

### 当前常见表达

"你具备以下核心能力……"

### 建议替换表达

"当前任务中，你必须先完成 A，再完成 B；若缺少 C，则停止并追问。"

原因：

- 更利于模型执行
- 更少冗余
- 更容易测试

## 13.2 精确性优化

应避免：

- "尽量"
- "适当"
- "必要时"
- "合理"

这种缺少判定条件的表述。

应改为：

- "若未检出法条依据，则输出 `缺少法律依据` 并请求补充材料"
- "当对比文件数量超过 5 个时，仅保留相关性最高的 3 个"

## 13.3 上下文关联性优化

每个业务模板都应明确：

1. 输入来自哪里
2. 哪些内容必须引用
3. 哪些内容仅可参考
4. 哪些内容必须回传给用户确认

## 13.4 输出契约优化

建议把"输出示例"升级为"输出契约"，明确：

- 格式
- 字段
- 顺序
- 可空规则
- 失败回退格式

---

## 14. Verified Implementation Path

基于已落地的架构组件，建议调整实施路径如下：

## Phase 1: 灰度启用与观测（2 周）

**目标**：让三源融合产生实际生产价值，并建立可信数据。

**动作**：

1. 将 `LEGAL_PROMPT_FUSION_ENABLED` 从布尔开关升级为灰度策略（按 domain / task_type / 流量比例）。
2. 接入现有观测系统，追踪融合核心指标：
   - `fusion_evidence_hit_rate`
   - `fusion_avg_latency_ms`
   - `fusion_cache_hit_rate`
   - `prompt_generate_total_latency_ms`
3. 建立降级策略：某源异常时自动跳过，记录 `fusion_source_degradation_count`。
4. 修复 `evaluate_prompt_file()` 递归命名问题。

**产出**：

- 灰度配置文档
- 融合指标 Dashboard
- `evaluate_prompt_file()` 修复 PR

## Phase 2: 主链路收口与旧链路清理（4 周）

**目标**：让主链路成为唯一生产运行时。

**动作**：

1. 标记 `progressive_loader.py` 和 `unified_prompt_manager*.py` 为 deprecated，输出迁移指南。
2. 修复 `unified_prompt_manager` 异步调用错配，或明确将其能力（L1-L4 角色、Lyra 优化）迁移至主链路。
3. 将 `prompts/` 中 v4 系列优质资产转化为场景规则模板，接入主链路。
4. 清理 `core/config/system_prompt.py` 中的过时硬编码事实，改为运行时 metadata 注入。

**产出**：

- `PROMPT_DEPRECATION_LIST.md`
- 迁移后的场景规则模板（OA 解读、创造性分析、新颖性分析）
- 旧链路调用方清零清单

## Phase 3: 变量治理与模板协议化（3 周）

**目标**：统一变量表达，建立模板协议。

**动作**：

1. 将主链路变量替换从 `{var}` 升级为 Jinja2（`{{ var }}`）。
2. 给场景规则模板增加变量 schema 和缺失变量阻断策略。
3. 增强注入安全策略（长度限制、控制字符清洗、prompt injection 标记）。
4. 建立 Prompt Inventory（含状态：production / staging / deprecated）。

**产出**：

- `core/prompt_engine/renderer.py`（Jinja2 渲染器）
- `core/prompt_engine/validators.py`（变量校验器）
- `PROMPT_INVENTORY.md`

## Phase 4: 上下文预算与评估闭环（3 周）

**目标**：实现 token 预算治理和质量评估闭环。

**动作**：

1. 实现基于优先级槽位的 context budget 分配器。
2. 根据 complexity 参数动态裁剪三源融合证据块。
3. 建立线上观测指标（首答正确率、追问率、工具调用成功率、JSON 合规率）。
4. 建立 prompt version rollback 机制（利用已有的 `__fusion_template_version` 机制扩展）。

**产出**：

- `core/prompt_engine/context_budget.py`
- 线上指标 Dashboard
- 版本回滚操作手册

---

## 15. Expected Effect Evaluation

如果按上述路径推进，预期收益如下：

## 15.1 响应质量

- 角色一致性提升（主链路统一收口）
- 输出结构更稳定（模板协议化）
- 无依据回答减少（三源融合灰度启用）
- 同场景跨入口风格更加统一

## 15.2 用户体验

- 追问更少（高质量模板接入主链路）
- 确认点更自然
- 高风险场景更可信（融合证据支撑）
- 回答可预期性更高

## 15.3 工程效率

- 模板修改可以单点生效（主链路唯一化）
- 新场景上线速度提高（PromptSpec 元数据层）
- 回归测试更容易（旧链路清理后测试面收窄）
- 提示词版本更可追溯（version rollback 机制）

## 15.4 风险控制

- 变量缺失和空注入可提前发现（变量校验器）
- 过时知识与虚假能力描述减少（metadata 注入）
- 多入口行为漂移可被识别（统一观测指标）
- 融合异常可降级不阻断（降级策略）

---

## 16. KPI Recommendation

建议建立以下指标：

### 质量指标

- `first_answer_acceptance_rate`
- `followup_rate`
- `json_contract_pass_rate`
- `citation_presence_rate`
- `tool_call_success_rate`

### 体验指标

- `avg_confirmation_turns`
- `avg_response_latency`
- `user_edit_distance`
- `user_satisfaction_score`

### 工程指标

- `prompt_template_reuse_rate`
- `deprecated_prompt_ratio`
- `runtime_fallback_rate`
- `missing_variable_rate`

### 融合专项指标（新增）

- `fusion_evidence_hit_rate`
- `fusion_avg_latency_ms`
- `fusion_cache_hit_rate`
- `fusion_source_degradation_count`
- `response_quality_delta_with_fusion`

---

## 17. Immediate Action List

建议本周优先完成以下 10 项：

1. **建立三源融合灰度开关**（替代 `LEGAL_PROMPT_FUSION_ENABLED` 的布尔值，支持按 domain / task_type 灰度）。
2. 接入融合核心指标的观测（evidence_hit_rate、latency、cache_hit_rate）。
3. 修复 `unified_prompt_manager` 链路中的异步调用错配（加 `await` 或标记废弃）。
4. 修复 `evaluate_prompt_file()` 递归命名问题。
5. 明确当前生产默认提示文件版本，输出 `PROMPT_INVENTORY.md` 初版。
6. 停止在多个模块中硬编码知识规模和端口信息，统一改为运行时 metadata 注入。
7. 给主链路场景规则模板补充变量 schema（required / optional / type）。
8. 建立三源融合降级策略（某源异常时自动跳过，不阻断主链路）。
9. 标记 `progressive_loader` 和 `unified_prompt_manager*.py` 为 deprecated。
10. 选取 OA 解读场景做第一批**融合启用试点**，对比开启/关闭的响应质量差异。

---

## 18. Risk Boundary (New)

以下风险边界必须在推进过程中持续监控：

| 风险项 | 边界定义 | 监控方式 | 触发动作 |
|---|---|---|---|
| 融合延迟爆炸 | `fusion_avg_latency_ms > 500ms` | 观测 Dashboard | 降低 top_k_per_source、启用缓存预填充 |
| 证据质量下降 | `fusion_evidence_hit_rate < 60%` | 观测 Dashboard | 检查 Wiki 索引状态、PostgreSQL schema 对齐 |
| 缓存频繁失效 | `fusion_cache_hit_rate < 30%` | 观测 Dashboard | 检查 Wiki revision 计算是否过于敏感（文件 mtime 抖动） |
| 旧链路回归 | deprecated 模块被新增调用 | 代码审查 + CI 检测 | 阻断 PR、强制迁移 |
| 变量注入安全 | 用户输入未转义进入 system_prompt | 安全扫描 + 渗透测试 | 升级 `html.escape()` 为更严格的清洗策略 |
| token 成本失控 | 融合后单请求 token 增长 > 30% | 成本监控 | 启用 context budget 裁剪、降低 max_evidence |
| 模型指令污染 | 融合证据块中出现指令性语句 | 人工抽检 + 正则过滤 | 增强 `verify_relevance` 的过滤能力 |

---

## 19. Final Judgment

当前项目的提示词工程已经跨过了"从零搭建"阶段，也跨过了"只有方案没有实现"的阶段。**三源融合与动态提示词主链路已经真实落地，但处于"建而未用、用而未收"的状态。**

如果继续沿用当前多体系并存、版本并行、变量分裂、运行时拼接不统一的方式，提示词资产会越来越多，但系统整体质量不会线性提升，反而会出现：

- 维护难
- 行为飘
- 版本乱
- 评估虚

**反之，当前项目已经具备的核心优势是：**

1. 主链路架构清晰，三源融合已验证可行。
2. 缓存、版本联动、场景规则检索等基础设施已就位。
3. 高质量提示词资产已有储备，只需接入主链路。

**下一阶段的核心任务不再是"继续建底座"，而是：**

> **灰度启用已验证能力 → 收口主链路为唯一运行时 → 清理旧链路债务 → 建立观测与回滚闭环。**

这也是本次校准后的核心结论：

**项目已经拥有足够好的提示词内容资产，也拥有了可运行的三源融合主链路。下一阶段的关键是把"已建成的能力"真正变为"默认行为"，并把并行体系收敛为单一事实源。**
