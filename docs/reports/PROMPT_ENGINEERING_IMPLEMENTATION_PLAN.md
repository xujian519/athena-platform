# Athena Prompt Engineering 实施计划

> 基于 `PROMPT_ENGINEERING_DEEP_RESEARCH_REPORT_20260423.md`（校准版）拆解
> 版本: v1.0
> 总周期: 12 周
> 目标: 将已落地的三源融合 + 动态提示词主链路从"建而未用"推进到"生产默认、旧链路清零、可观测、可治理"

---

## 目录

1. [计划总览](#1-计划总览)
2. [Phase 1: 灰度启用与观测（W1-W2）](#2-phase-1-灰度启用与观测w1-w2)
3. [Phase 2: 主链路收口与旧链路清理（W3-W6）](#3-phase-2-主链路收口与旧链路清理w3-w6)
4. [Phase 3: 变量治理与模板协议化（W7-W9）](#4-phase-3-变量治理与模板协议化w7-w9)
5. [Phase 3.5: 稳定性保障周（W10）](#5-phase-35-稳定性保障周w10)
6. [Phase 4: 上下文预算与评估闭环（W11-W12）](#6-phase-4-上下文预算与评估闭环w11-w12)
7. [验收标准总表](#7-验收标准总表)
8. [风险应对预案](#8-风险应对预案)
9. [资源需求](#9-资源需求)
10. [附录：任务看板模板](#10-附录任务看板模板)

---

## 1. 计划总览

### 1.1 阶段里程碑

```
W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11 W12
|=== Phase 1 ===|
                |======= Phase 2 =======|
                                        |=== Phase 3 ===|
                                                        |休|
                                                            |=== Phase 4 ===|
```

| 阶段 | 周期 | 核心目标 | 关键产出 |
|---|---|---|---|
| Phase 1 | W1-W2 | 让三源融合产生实际生产价值 | 灰度策略、观测 Dashboard、紧急修复 |
| Phase 2 | W3-W6 | 主链路成为唯一生产运行时 | 旧链路 deprecated、资产迁移、异步修复 |
| Phase 3 | W7-W9 | 统一变量表达，建立模板协议 | Jinja2 渲染器、变量校验器、Prompt Inventory |
| Phase 3.5 | W10 | 稳定性保障，不引入新功能 | 回归测试、性能基线、文档补齐 |
| Phase 4 | W11-W12 | Token 预算治理 + 质量评估闭环 | Context Budget、线上指标、回滚机制 |

### 1.2 关键依赖链

```
[Phase 1] 灰度开关 & 观测
    │
    ▼
[Phase 2] 旧链路清理 ──→ 主链路唯一化
    │                         │
    ▼                         ▼
[Phase 3] 变量治理 ─────→ Jinja2 渲染器接入主链路
    │                         │
    ▼                         ▼
[Phase 3.5] 稳定周 ───→ 全链路回归通过
    │
    ▼
[Phase 4] Context Budget ──→ 三源融合证据动态裁剪
              │
              ▼
        线上指标 & 回滚机制
```

### 1.3 每日/每周节奏

- **每日**: 15min 站会（昨日完成 / 今日计划 / 阻塞项）
- **每周五**: 1hr 复盘（指标变化、风险刷新、下周调整）
- **每阶段末**: 里程碑评审（对照验收标准 Go / No-Go）

---

## 2. Phase 1: 灰度启用与观测（W1-W2）

**目标**: 将 `LEGAL_PROMPT_FUSION_ENABLED` 从布尔开关升级为可灰度、可观测、可降级的生产特性，让三源融合开始服务真实流量。

### W1 详细任务

#### Day 1-2: 灰度开关设计与实现

**任务 1.1.1**: 设计灰度配置 Schema
- **负责人**: 后端开发
- **输入**: 当前 `is_legal_prompt_fusion_enabled()` 实现
- **输出**: `core/legal_prompt_fusion/rollout_config.py`
- **具体动作**:
  ```python
  @dataclass
  class FusionRolloutConfig:
      global_enabled: bool = False          # 总开关
      domain_whitelist: list[str] = field(default_factory=list)   # ["patent"]
      task_type_whitelist: list[str] = field(default_factory=list) # ["office_action"]
      traffic_percentage: int = 0           # 0-100
      user_id_hash_prefix: str = ""         # 按用户哈希前缀
      
      def should_enable(self, domain: str, task_type: str, user_id: str = "") -> bool:
          # 实现分层判断逻辑
  ```
- **验收标准**:
  - [ ] 配置支持热重载（不重启服务生效）
  - [ ] 分层判断顺序正确：总开关 → domain → task_type → traffic_percentage → user_hash
  - [ ] 单元测试覆盖所有组合场景

**任务 1.1.2**: 替换原有布尔开关
- **负责人**: 后端开发
- **输入**: `core/api/prompt_system_routes.py` 第 212 行
- **输出**: PR（改动范围控制在 `prompt_system_routes.py` 和新增配置模块）
- **具体动作**:
  1. 删除 `is_legal_prompt_fusion_enabled()` 的纯环境变量判断
  2. 接入 `FusionRolloutConfig`
  3. 保留环境变量作为 fallback：`LEGAL_PROMPT_FUSION_ENABLED=true` 时默认 `global_enabled=true, traffic_percentage=100`
- **验收标准**:
  - [ ] 原有 `LEGAL_PROMPT_FUSION_ENABLED=true` 行为不变（向后兼容）
  - [ ] 新增配置文件 `config/prompt_fusion_rollout.yaml` 可覆盖环境变量
  - [ ] 代码审查通过

#### Day 3-4: 观测指标埋点

**任务 1.2.1**: 定义融合核心指标结构
- **负责人**: 后端开发 + SRE
- **输出**: `core/legal_prompt_fusion/metrics.py`
- **具体动作**:
  ```python
  @dataclass
  class FusionMetrics:
      request_id: str
      domain: str
      task_type: str
      fusion_enabled: bool
      latency_ms: float           # 融合额外耗时
      evidence_count: int         # 返回证据总数
      evidence_by_source: dict[str, int]  # {"postgres": 3, "neo4j": 2, "wiki": 1}
      cache_hit: bool
      wiki_revision: str
      template_version: str
      source_degradation: list[str]  # 哪些源被降级跳过了
      error: str | None
  ```

**任务 1.2.2**: 在主链路埋点
- **负责人**: 后端开发
- **输入**: `core/api/prompt_system_routes.py` 的 `generate_prompt()`
- **输出**: PR
- **具体动作**:
  1. 在融合调用前后增加计时：`fusion_start = time.monotonic()`
  2. 记录每个源的返回数量和耗时
  3. 记录缓存命中状态
  4. 异常时记录 `source_degradation` 和 `error`
  5. 将指标异步发送到指标收集器（不阻塞主链路）
- **验收标准**:
  - [ ] 融合开启的请求 100% 产生指标记录
  - [ ] 融合关闭的请求也产生基线记录（用于对比）
  - [ ] 指标发送失败不阻断主链路（try/except + 日志）

#### Day 5: 降级策略实现

**任务 1.3.1**: 单源异常自动降级
- **负责人**: 后端开发
- **输入**: `core/legal_prompt_fusion/providers.py`
- **输出**: PR
- **具体动作**:
  1. 每个 provider（Postgres / Neo4j / Wiki）增加异常捕获
  2. 某源超时或异常时，记录 `source_degradation`，返回空列表，不抛错
  3. 三源全部异常时，system_prompt 不追加融合块，但正常返回（等价于融合关闭）
  4. 增加单次 provider 调用超时：默认 200ms（可配置）
- **验收标准**:
  - [ ] 模拟 Postgres 故障，请求仍成功返回，融合块含 Neo4j + Wiki 证据
  - [ ] 模拟三源全部故障，请求成功返回，融合块为空但不报错
  - [ ] 降级事件写入 warning 日志

### W2 详细任务

#### Day 6-7: 观测 Dashboard 搭建

**任务 1.4.1**: 指标收集与存储
- **负责人**: SRE
- **输出**: 指标收集 pipeline（复用现有观测基础设施）
- **具体动作**:
  1. 将 `FusionMetrics` 数据接入现有日志/指标系统（如 Prometheus / Grafana / ELK）
  2. 建立以下指标聚合：
     - `fusion_evidence_hit_rate = 有证据的请求数 / 融合开启请求数`
     - `fusion_avg_latency_ms = avg(latency_ms)`
     - `fusion_cache_hit_rate = 缓存命中数 / 融合开启请求数`
     - `fusion_source_degradation_rate = 降级请求数 / 融合开启请求数`
- **验收标准**:
  - [ ] Dashboard 可实时查看（延迟 < 30s）
  - [ ] 支持按 domain / task_type / 时间范围过滤

**任务 1.4.2**: 告警规则
- **负责人**: SRE
- **输出**: 告警规则配置
- **具体动作**:
  ```yaml
  alerts:
    - name: FusionLatencyHigh
      condition: fusion_avg_latency_ms > 500
      duration: 5m
      severity: warning
      action: 通知值班群，自动降低 traffic_percentage
    
    - name: FusionEvidenceLow
      condition: fusion_evidence_hit_rate < 0.6
      duration: 10m
      severity: warning
      action: 通知值班群，检查 Wiki 索引状态
    
    - name: FusionCacheMissBurst
      condition: fusion_cache_hit_rate < 0.3
      duration: 5m
      severity: critical
      action: 检查 wiki_revision 计算是否过于敏感
  ```
- **验收标准**:
  - [ ] 告警可正常触发（通过手动注入测试数据验证）
  - [ ] 告警通知渠道已配置（Slack / 钉钉 / 邮件）

#### Day 8-9: 小流量灰度试点

**任务 1.5.1**: OA 解读场景灰度 5%
- **负责人**: 后端开发 + 业务验证
- **输出**: 灰度运行报告
- **具体动作**:
  1. 配置灰度：`domain=patent`, `task_type=office_action`, `traffic_percentage=5`
  2. 持续观察 Dashboard 24 小时
  3. 人工抽检 20 条开启融合 vs 20 条未开启融合的响应，对比质量差异
  4. 记录异常情况
- **验收标准**:
  - [ ] 融合开启请求的 `fusion_avg_latency_ms < 300ms`（P95）
  - [ ] 无 500 错误归因于融合模块
  - [ ] 人工抽检无"融合证据块干扰模型输出格式"的案例

**任务 1.5.2**: 紧急修复 `evaluate_prompt_file()` 递归问题
- **负责人**: 后端开发
- **输入**: `core/ai/prompts/__init__.py` 第 155-165 行
- **输出**: Hotfix PR
- **具体动作**:
  1. 将函数重命名为 `evaluate_prompt_file_path(file_path: str)` 或调整内部调用使用 `Path` 的完整 import
  2. 或者使用 `from pathlib import Path as _Path` 避免遮蔽
- **验收标准**:
  - [ ] 调用 `evaluate_prompt_file("some.md")` 不再递归溢出
  - [ ] 单元测试通过

#### Day 10: Phase 1 评审

**任务 1.6.1**: 里程碑评审会
- **参与人**: 全团队
- **议程**:
  1. Dashboard 演示
  2. 灰度数据回顾（latency、evidence hit rate、error rate）
  3. 阻塞项同步
  4. Phase 2 计划确认
- **Go/No-Go 标准**:
  - [ ] 灰度运行 48h 无 P0 故障
  - [ ] `fusion_avg_latency_ms` P95 < 500ms
  - [ ] 降级策略通过故障注入测试

---

## 3. Phase 2: 主链路收口与旧链路清理（W3-W6）

**目标**: 让 `prompt_system_routes.py` 成为唯一生产运行时，旧链路标记 deprecated 并开始迁移。

### W3: 旧链路梳理与标记

#### 任务 2.1.1: 全量调用矩阵梳理
- **负责人**: 后端开发
- **输出**: `docs/reports/PROMPT_RUNTIME_MATRIX.md`
- **具体动作**:
  1. 用 `grep -rn` 扫描全仓库对以下模块的导入和调用：
     - `progressive_loader`
     - `unified_prompt_manager`
     - `unified_prompt_manager_extended`
     - `unified_prompt_manager_production`
     - `integrated_prompt_generator`
     - `capability_integrated_prompt_generator`
  2. 按调用方（业务模块 / 测试 / 脚本）分类统计
  3. 评估每个调用方的迁移成本（高 / 中 / 低）
- **验收标准**:
  - [ ] 调用矩阵覆盖 100% 的导入点
  - [ ] 每个调用方标注：当前功能、迁移目标、预估工作量

#### 任务 2.1.2: 标记 Deprecated
- **负责人**: 后端开发
- **输出**: PR（纯标记，不改逻辑）
- **具体动作**:
  1. 在 `progressive_loader.py`、`unified_prompt_manager*.py` 模块顶部添加：
     ```python
     import warnings
     warnings.warn(
         "This module is deprecated and will be removed in v3.0. "
         "Use core.api.prompt_system_routes.generate_prompt() instead.",
         DeprecationWarning,
         stacklevel=2,
     )
     ```
  2. 在 `core/ai/prompts/__init__.py` 的导出列表中注释说明 deprecated 状态
  3. 更新 `PROMPT_DEPRECATION_LIST.md`
- **验收标准**:
  - [ ] 导入 deprecated 模块时产生 `DeprecationWarning`
  - [ ] CI 不因此失败（或 CI 配置允许 deprecation warning）

#### 任务 2.1.3: 异步调用错配修复评估
- **负责人**: 后端开发
- **输出**: 技术决策文档（修复 vs 迁移）
- **具体动作**:
  1. 定位所有同步调用异步方法的代码点：
     - `integrated_prompt_generator.py:212` (`optimize_prompt`)
     - `integrated_prompt_generator.py:276` (`load_prompt`)
     - `unified_prompt_manager_extended.py:209` (`load_prompt`)
     - `unified_prompt_manager_production.py:457` (`load_prompt`)
  2. 评估两种方案：
     - **方案 A**: 加 `await`，但需将调用链全部改为 async（影响面大）
     - **方案 B**: 将 `load_prompt`/`optimize_prompt` 改为 sync 实现（内部用 `asyncio.run` 或重构为 sync）
     - **方案 C**: 直接废弃这些调用点，将 L1-L4 角色加载和 Lyra 优化迁移至主链路
  3. 推荐方案并说明理由
- **验收标准**:
  - [ ] 决策文档通过技术评审
  - [ ] 明确选择修复或迁移的代码路径

### W4: 异步错配修复 + 资产迁移准备

#### 任务 2.2.1: 执行异步错配修复（按决策）
- **负责人**: 后端开发
- **输出**: PR
- **假设选择方案 C（迁移至主链路）**:
  1. 在 `prompt_system_routes.py` 的 `generate_prompt()` 中增加 L1-L4 角色注入点
  2. 将 `prompts/foundation/` 中的角色模板读取逻辑封装为 `load_role_prompt(layer: str)`
  3. 在场景规则模板中增加 `role_layer` 字段，标记需要加载哪些层
  4. 移除 `integrated_prompt_generator.py` 中对 `unified_prompt_manager` 的调用
- **假设选择方案 A（加 await）**:
  1. 将 `integrated_prompt_generator.py` 的调用方法改为 async
  2. 逐层向上修改直到入口
  3. 确保所有测试通过
- **验收标准**:
  - [ ] 修复后异步方法不再被同步调用
  - [ ] 相关测试通过
  - [ ] 无新增 500 错误

#### 任务 2.2.2: v4 资产转化为场景规则模板
- **负责人**: 提示词工程师 + 后端开发
- **输出**: Neo4j 场景规则模板（3 个）
- **具体动作**:
  1. 选取 3 个最高价值模板：
     - `prompts/foundation/hitl_protocol_v4_constraint_repeat.md` → 作为所有场景的 safety 基础块
     - `prompts/capability/cap04_inventive_v2_with_whenToUse.md` → 创造性分析场景
     - `prompts/business/task_2_1_oa_analysis_v2_with_parallel.md` → OA 解读场景
  2. 将 Markdown 内容转化为 `ScenarioRule` 的 `system_prompt_template` / `user_prompt_template`
  3. 补充变量占位符（当前用 `{var}`，后续 Phase 3 统一升级）
  4. 写入 Neo4j 规则库（复用 `scenario_rule_retriever_optimized.py` 的存储格式）
- **验收标准**:
  - [ ] 3 个模板可通过 `retrieve_rule()` 正常检索
  - [ ] `substitute_variables()` 替换后输出与原 Markdown 内容语义一致
  - [ ] 人工验证 5 条请求的 system_prompt 质量不低于原静态模板

### W5: 渐进式迁移调用方

#### 任务 2.3.1: 低风险调用方迁移
- **负责人**: 后端开发
- **输出**: PR
- **具体动作**:
  1. 从调用矩阵中选取"仅导入但未实际使用"或"单元测试调用"的代码点
  2. 删除无用导入
  3. 将测试中的调用替换为主链路 API 调用或直接 mock
  4. 每次改动后跑全量测试
- **验收标准**:
  - [ ] 清理的导入点不再出现
  - [ ] 全量测试通过

#### 任务 2.3.2: 中风险调用方迁移
- **负责人**: 后端开发 + 业务模块负责人
- **输出**: PR
- **具体动作**:
  1. 选取 2-3 个核心业务代理的 `get_system_prompt()` 方法
  2. 将 Python 字符串模板替换为对主链路 `generate_prompt()` 的调用
  3. 或者将 Python 字符串模板内容提取为 Markdown，接入场景规则库
  4. 确保业务代理的行为一致性（对比迁移前后的输出）
- **验收标准**:
  - [ ] 迁移后的代理输出与原输出差异 < 5%（通过自动化 diff 或人工抽检）
  - [ ] 业务模块单元测试通过

### W6: 收口与评审

#### 任务 2.4.1: 主链路唯一化验证
- **负责人**: QA
- **输出**: 测试报告
- **具体动作**:
  1. 检查全仓库，确认非测试/非 deprecated 代码中已无 `progressive_loader` 和 `unified_prompt_manager*` 的导入
  2. 跑全量集成测试（含提示词生成链路）
  3. 压测主链路 API（QPS、延迟、错误率）
- **验收标准**:
  - [ ] 非 deprecated 代码中旧链路导入清零
  - [ ] 集成测试 100% 通过
  - [ ] 压测 QPS 不低于清理前基线

#### 任务 2.4.2: Phase 2 里程碑评审
- **参与人**: 全团队
- **Go/No-Go 标准**:
  - [ ] 旧链路已标记 deprecated 且无新增调用
  - [ ] 主链路已承载 100% 生产流量
  - [ ] v4 资产至少 2 个已接入场景规则库
  - [ ] 异步调用错配已修复

---

## 4. Phase 3: 变量治理与模板协议化（W7-W9）

**目标**: 统一变量表达，建立模板协议，让主链路具备变量校验和缺失阻断能力。

### W7: Jinja2 渲染器与变量 Schema

#### 任务 3.1.1: Jinja2 渲染器实现
- **负责人**: 后端开发
- **输出**: `core/prompt_engine/renderer.py`
- **具体动作**:
  ```python
  from jinja2 import Environment, BaseLoader, StrictUndefined

  class PromptRenderer:
      def __init__(self):
          self.env = Environment(
              loader=BaseLoader(),
              undefined=StrictUndefined,  # 缺失变量直接抛异常
              autoescape=False,           # 我们自行控制转义
          )
      
      def render(self, template: str, variables: dict) -> str:
          jinja_template = self.env.from_string(template)
          return jinja_template.render(**variables)
  ```
  1. 实现 `PromptRenderer` 类
  2. 支持自定义过滤器（如 `default`、`truncate`）
  3. 支持 `StrictUndefined`，确保缺失变量不静默通过

#### 任务 3.1.2: 变量 Schema 定义
- **负责人**: 后端开发 + 提示词工程师
- **输出**: `core/prompt_engine/schema.py`
- **具体动作**:
  ```python
  @dataclass
  class VariableSpec:
      name: str
      type: str  # string | int | float | bool | list | dict
      required: bool = True
      source: str = ""  # user_input | document | extracted | system
      default: Any = None
      description: str = ""
      max_length: int | None = None  # 注入安全：长度限制
  
  @dataclass
  class PromptSchema:
      variables: list[VariableSpec]
      template_version: str
  ```
  1. 定义 `VariableSpec` 和 `PromptSchema`
  2. 为 W4 迁移的 3 个场景规则模板编写 schema

#### 任务 3.1.3: 场景规则模板语法升级
- **负责人**: 提示词工程师
- **输出**: 更新后的 Neo4j 场景规则
- **具体动作**:
  1. 将 `system_prompt_template` / `user_prompt_template` 中的 `{var}` 替换为 `{{ var }}`
  2. 增加 `| default('暂无')` 等过滤器
  3. 更新 `scenario_rule_retriever_optimized.py` 的 `substitute_variables()` 方法，支持 Jinja2（或新建 `Jinja2ScenarioRule` 子类，逐步切换）
- **验收标准**:
  - [ ] 模板渲染结果与原 `{var}` 替换结果一致（对比测试）
  - [ ] `StrictUndefined` 在缺失变量时抛出 `UndefinedError`

### W8: 变量校验器与缺失阻断

#### 任务 3.2.1: 变量校验器实现
- **负责人**: 后端开发
- **输出**: `core/prompt_engine/validators.py`
- **具体动作**:
  ```python
  class VariableValidator:
      def validate(self, schema: PromptSchema, variables: dict) -> ValidationResult:
          errors = []
          warnings = []
          
          for spec in schema.variables:
              value = variables.get(spec.name)
              if spec.required and value is None:
                  errors.append(f"Missing required variable: {spec.name}")
                  continue
              if spec.max_length and len(str(value)) > spec.max_length:
                  errors.append(f"Variable {spec.name} exceeds max_length {spec.max_length}")
          
          return ValidationResult(valid=len(errors)==0, errors=errors, warnings=warnings)
  ```
  1. 实现类型检查、required 检查、max_length 检查
  2. 支持自定义校验规则（正则、枚举值等）

#### 任务 3.2.2: 注入安全策略
- **负责人**: 后端开发 + 安全工程师
- **输出**: `core/prompt_engine/sanitizer.py`
- **具体动作**:
  1. 实现 `PromptSanitizer` 类：
     - `sanitize_string(value: str) -> str`: 控制字符清洗、长度截断
     - `escape_markdown(value: str) -> str`: Markdown 特殊字符转义
     - `detect_injection(value: str) -> InjectionRisk`: 启发式检测 prompt injection 模式（如 "ignore previous instructions"、多行系统指令等）
  2. 在 `generate_prompt()` 的变量准备阶段调用 sanitizer
  3. 高风险变量标记后进入日志，不阻断（避免误杀），但可配置为阻断
- **验收标准**:
  - [ ] 注入测试集（含 10 种常见 injection 模式）检测率 > 80%
  - [ ] 正常业务输入不误报（抽样 100 条验证）

#### 任务 3.2.3: 缺失变量阻断策略接入主链路
- **负责人**: 后端开发
- **输出**: PR
- **具体动作**:
  1. 在 `generate_prompt()` 的变量替换前增加校验步骤
  2. 校验失败时返回 400 错误，body 含缺失变量清单：
     ```json
     {
       "error": "MISSING_VARIABLES",
       "missing": ["application_number", "oa_text"],
       "message": "Required variables missing: application_number, oa_text"
     }
     ```
  3. 可选变量缺失时使用默认值，不阻断
- **验收标准**:
  - [ ] 缺失 required 变量时返回 400，不进入 LLM 调用
  - [ ] 缺失 optional 变量时使用默认值，正常返回

### W9: Prompt Inventory 与模板协议化收尾

#### 任务 3.3.1: Prompt Inventory 建立
- **负责人**: 提示词工程师
- **输出**: `PROMPT_INVENTORY.md`（自动化生成）
- **具体动作**:
  1. 扫描 `prompts/` 目录和 Neo4j 场景规则库，生成全量清单
  2. 每个条目包含：
     - ID / 版本 / 路径
     - 状态：production / staging / deprecated / draft
     - 关联场景（domain / task_type）
     - 变量列表
     - 负责人
  3. 建立 CI 检查：新增/修改提示词文件必须更新 Inventory
- **验收标准**:
  - [ ] Inventory 覆盖 100% 的生产使用模板
  - [ ] CI 检查生效，未更新 Inventory 的 PR 被阻断

#### 任务 3.3.2: 存量模板变量 Schema 补齐
- **负责人**: 提示词工程师
- **输出**: 更新后的场景规则（全部生产模板）
- **具体动作**:
  1. 遍历全部生产场景规则模板
  2. 提取所有占位符，补全 `VariableSpec`
  3. 标记 required / optional
  4. 更新 Neo4j 存储（或在独立 schema 表中存储）
- **验收标准**:
  - [ ] 100% 生产模板具备变量 schema
  - [ ] `validate()` 通过所有生产模板的校验

#### 任务 3.3.3: Phase 3 评审
- **Go/No-Go 标准**:
  - [ ] Jinja2 渲染器已接入主链路
  - [ ] 变量校验器拦截 100% 的 required 变量缺失（测试验证）
  - [ ] Prompt Inventory 自动化生成并通过 CI 校验
  - [ ] 注入安全策略通过安全评审

---

## 5. Phase 3.5: 稳定性保障周（W10）

**目标**: 不引入新功能，专注回归测试、性能基线、文档补齐、债务清理。

### 任务 3.5.1: 全链路回归测试
- **负责人**: QA
- **输出**: 回归测试报告
- **具体动作**:
  1. 跑全量单元测试 + 集成测试
  2. 针对提示词生成链路设计端到端测试用例（覆盖 10 个核心场景）
  3. 对比 Phase 1 基线：延迟、错误率、token 消耗
- **验收标准**:
  - [ ] 全量测试通过率 100%
  - [ ] P95 延迟不劣于 Phase 1 基线
  - [ ] 端到端测试覆盖全部核心场景

### 任务 3.5.2: 性能基线建立
- **负责人**: SRE + 后端开发
- **输出**: 性能基线文档
- **具体动作**:
  1. 压测主链路 API（QPS 从 10 逐步加到 100）
  2. 记录基线指标：
     - `prompt_generate_p50_latency_ms`
     - `prompt_generate_p95_latency_ms`
     - `prompt_generate_p99_latency_ms`
     - `prompt_generate_error_rate`
     - `fusion_additional_latency_p95_ms`
     - `avg_tokens_per_request`
  3. 建立性能退化告警阈值（如 P95 延迟增长 > 20% 触发告警）
- **验收标准**:
  - [ ] 性能基线文档已归档
  - [ ] 告警规则已配置

### 任务 3.5.3: 技术债务清理
- **负责人**: 后端开发
- **输出**: 债务清理 PR
- **具体动作**:
  1. 删除已标记 deprecated 且确认无调用的 dead code
  2. 补齐核心模块的 docstring
  3. 修复 lint 警告（ruff / mypy）
  4. 更新 `docs/architecture/prompt-system.md` 架构文档
- **验收标准**:
  - [ ] 代码覆盖率不下降
  - [ ] lint 检查 0 error
  - [ ] 架构文档与实际代码一致

### 任务 3.5.4: 运维手册补齐
- **负责人**: SRE
- **输出**: `docs/ops/prompt-system-runbook.md`
- **具体动作**:
  1. 编写故障排查手册：
     - 融合证据为空怎么办？
     - 缓存命中率骤降怎么办？
     - 某源降级如何快速恢复？
  2. 编写灰度操作手册：如何调整流量比例、如何紧急关闭融合
  3. 编写回滚操作手册
- **验收标准**:
  - [ ] 值班同学可仅凭 runbook 完成常见故障处理

---

## 6. Phase 4: 上下文预算与评估闭环（W11-W12）

**目标**: 实现 token 预算治理、三源融合证据动态裁剪、线上质量评估闭环。

### W11: Context Budget 分配器

#### 任务 4.1.1: 优先级槽位模型实现
- **负责人**: 后端开发
- **输出**: `core/prompt_engine/context_budget.py`
- **具体动作**:
  ```python
  @dataclass
  class Slot:
      priority: int  # 0=P0, 1=P1, 2=P2, 3=P3
      content: str
      estimated_tokens: int
      source: str
  
  class ContextBudgetAllocator:
      def allocate(self, slots: list[Slot], budget_tokens: int) -> list[Slot]:
          # 按优先级排序，贪心填充直到 budget 用完
          # P0 必须全部保留
          # P1-P3 按优先级和 estimated_tokens 填充
          # 同优先级按内容相关性或用户配置排序
  ```
  1. 实现优先级槽位模型
  2. 支持 `estimated_tokens` 的估算（可用 tiktoken 或近似字符数 / 4）
  3. 支持 `budget_tokens` 按 complexity 分层（simple: 3000, medium: 6000, complex: 10000）

#### 任务 4.1.2: 三源融合证据动态裁剪
- **负责人**: 后端开发
- **输出**: PR
- **具体动作**:
  1. 将融合证据块（legal_articles / graph_relations / wiki_background）作为 P1 槽位接入 Context Budget
  2. 根据剩余 budget 动态决定：
     - 每条证据是否保留
     - 保留时是否截断 summary（取前 N 字符）
     - 整个证据块是否降级为 "相关证据数量: X，详见知识库"
  3. 复杂度映射证据上限：
     - simple: max 3 条
     - medium: max 8 条
     - complex: max 12 条
- **验收标准**:
  - [ ] simple 任务的 system_prompt 总 token < 3000（抽样验证）
  - [ ] complex 任务保留全部关键证据，无 truncation 导致的信息丢失

#### 任务 4.1.3: Token 估算器集成
- **负责人**: 后端开发
- **输出**: PR
- **具体动作**:
  1. 集成 tiktoken（或项目已有的 tokenizer）用于精确估算
  2. 在 `generate_prompt()` 返回前估算 system_prompt + user_prompt 的总 token
  3. 超过 budget 时触发告警日志（但不阻断，用于观测）
- **验收标准**:
  - [ ] token 估算误差 < 10%（对比实际 API 消耗的 token）

### W12: 线上指标与回滚机制

#### 任务 4.2.1: 线上质量指标埋点
- **负责人**: 后端开发 + 数据分析师
- **输出**: 指标埋点 PR + Dashboard
- **具体动作**:
  1. 在 LLM 调用后（或用户反馈后）埋点以下指标：
     - `first_answer_acceptance_rate`: 用户未追问即接受的比例
     - `followup_rate`: 用户追问比例
     - `json_contract_pass_rate`: 输出符合 JSON schema 的比例（如适用）
     - `tool_call_success_rate`: 工具调用成功比例
     - `user_satisfaction_score`: 显式评分或隐式信号（如编辑距离、复制行为）
  2. 将指标接入现有 BI 系统
- **验收标准**:
  - [ ] 核心场景（OA 解读、创造性分析）100% 覆盖质量指标
  - [ ] Dashboard 支持按 prompt version 对比（A/B 分析）

#### 任务 4.2.2: Prompt Version Rollback 机制
- **负责人**: 后端开发
- **输出**: 回滚脚本 + 操作手册
- **具体动作**:
  1. 利用已有的 `__fusion_template_version` 机制扩展：
     - 每次场景规则模板更新时，自动生成新版本 hash
     - 保留最近 N 个版本的模板内容（存储于对象存储或数据库）
     - 支持通过 API 或配置快速回滚到指定 version
  2. 实现回滚 API：
     ```http
     POST /api/v1/prompt-system/rules/rollback
     {
       "rule_id": "patent.oa.analysis",
       "target_version": "patent.oa.analysis:abc123def456"
     }
     ```
  3. 回滚后自动清除相关缓存
- **验收标准**:
  - [ ] 回滚操作在 30 秒内生效
  - [ ] 回滚后缓存不返回旧版本内容
  - [ ] 回滚操作记录审计日志

#### 任务 4.2.3: A/B 测试能力
- **负责人**: 后端开发
- **输出**: A/B 配置模块
- **具体动作**:
  1. 在灰度配置基础上扩展 A/B 能力：
     - 同一场景支持两个版本的 prompt template
     - 按用户 hash 分流（50/50 或其他比例）
     - 自动对比两组的线上质量指标
  2. 支持"实验自动终止"：当某组的错误率显著高于另一组时，自动切回对照组
- **验收标准**:
  - [ ] 支持同时运行 2 个版本的场景规则
  - [ ] 指标对比自动产出（每日报告）

#### 任务 4.2.4: 项目结项评审
- **参与人**: 全团队 + 利益相关方
- **议程**:
  1. 12 周指标回顾（延迟、质量、覆盖率）
  2. 与基线对比的收益量化
  3. 遗留债务与后续计划
  4. 经验文档化
- **验收标准**:
  - [ ] 全阶段验收标准 100% 达成
  - [ ] 知识沉淀文档已归档

---

## 7. 验收标准总表

### Phase 1 验收

| # | 验收项 | 标准 | 验证方式 |
|---|---|---|---|
| 1.1 | 灰度开关 | 支持 domain / task_type / traffic_percentage / user_hash 分层 | 单元测试 + 配置验证 |
| 1.2 | 观测 Dashboard | 可实时查看 4 项核心指标 | 人工演示 |
| 1.3 | 告警规则 | 3 条告警可正常触发 | 注入测试数据验证 |
| 1.4 | 降级策略 | 单源故障不阻断，三源全故障正常返回 | 故障注入测试 |
| 1.5 | 灰度试点 | OA 解读 5% 流量运行 48h 无 P0 | 生产数据 |
| 1.6 | 紧急修复 | `evaluate_prompt_file()` 递归问题修复 | 单元测试 |

### Phase 2 验收

| # | 验收项 | 标准 | 验证方式 |
|---|---|---|---|
| 2.1 | 调用矩阵 | 100% 覆盖旧链路导入点 | `grep` + 人工审计 |
| 2.2 | Deprecated 标记 | 导入旧链路产生 DeprecationWarning | 单元测试 |
| 2.3 | 异步修复 | 异步方法不再被同步调用 | 静态分析 + 测试 |
| 2.4 | 资产迁移 | ≥2 个 v4 模板接入场景规则库 | 人工验证 + 测试 |
| 2.5 | 调用方迁移 | 非 deprecated 代码旧链路导入清零 | `grep` + CI |
| 2.6 | 压测通过 | QPS 不低于清理前基线 | 压测报告 |

### Phase 3 验收

| # | 验收项 | 标准 | 验证方式 |
|---|---|---|---|
| 3.1 | Jinja2 渲染器 | 接入主链路，StrictUndefined 生效 | 单元测试 |
| 3.2 | 变量校验器 | 100% 拦截 required 变量缺失 | 集成测试 |
| 3.3 | 注入安全 | 10 种 injection 模式检测率 > 80% | 安全测试 |
| 3.4 | Prompt Inventory | 自动化生成，CI 校验生效 | CI 验证 |
| 3.5 | Schema 补齐 | 100% 生产模板具备变量 schema | 脚本扫描 |

### Phase 3.5 验收

| # | 验收项 | 标准 | 验证方式 |
|---|---|---|---|
| 3.6 | 回归测试 | 全量测试 100% 通过 | CI 报告 |
| 3.7 | 性能基线 | P95 延迟不劣于 Phase 1 基线 | 压测报告 |
| 3.8 | 运维手册 | 值班同学可独立处理常见故障 | 演练 |

### Phase 4 验收

| # | 验收项 | 标准 | 验证方式 |
|---|---|---|---|
| 4.1 | Context Budget | simple 任务 token < 3000 | 抽样验证 |
| 4.2 | 证据裁剪 | 按 complexity 动态调整证据数量 | 单元测试 |
| 4.3 | 质量指标 | 核心场景 100% 覆盖 | Dashboard |
| 4.4 | 回滚机制 | 30 秒内生效，缓存同步清除 | 演练 |
| 4.5 | A/B 能力 | 支持两版本同时运行，自动对比 | 演示 |

---

## 8. 风险应对预案

| 风险 | 概率 | 影响 | 应对策略 |
|---|---|---|---|
| 灰度开启后延迟飙升 | 中 | 高 | W1 即实现降级策略，延迟 > 500ms 持续 5min 自动切流；预设 `traffic_percentage=0` 的紧急开关 |
| 融合证据污染模型输出 | 中 | 高 | W2 灰度试点时人工抽检 20 组；发现污染立即切流；增强 `verify_relevance` 过滤 |
| 旧链路迁移引发业务回归 | 高 | 高 | Phase 2 分周推进，每周只迁移 1-2 个模块；每次迁移后跑全量测试；保留回滚能力 |
| Jinja2 StrictUndefined 导致大量请求 400 | 低 | 中 | Phase 3 先在 staging 跑 1 周，收集缺失变量清单，补全 schema 后再上生产 |
| Token 成本失控 | 中 | 中 | Phase 4 的 Context Budget 优先实现 simple 任务裁剪；设定每日 token 预算上限告警 |
| Wiki 索引敏感导致缓存频繁失效 | 中 | 中 | W1 观测 `fusion_cache_hit_rate`，若 < 30% 则改用 content hash 替代 mtime 计算 revision |
| 团队资源不足导致延期 | 中 | 中 | 每个 Phase 设置缓冲周（Phase 3.5）；关键任务（灰度开关、降级策略）优先，非关键可降级 |

---

## 9. 资源需求

### 人力

| 角色 | 投入 | 职责 |
|---|---|---|
| 后端开发（主责） | 1 FTE | 灰度开关、主链路改造、渲染器、校验器、Context Budget |
| 提示词工程师 | 0.5 FTE | v4 资产迁移、变量 schema 定义、Prompt Inventory 维护 |
| SRE | 0.3 FTE | Dashboard、告警、压测、运维手册 |
| QA | 0.3 FTE | 回归测试、端到端测试、验收验证 |
| 安全工程师（兼职） | 0.1 FTE | 注入安全策略评审、渗透测试 |

### 基础设施

- 观测系统：复用现有 Prometheus / Grafana / ELK（无需新增）
- 存储：场景规则模板版本存储需对象存储或数据库表（预估 < 1GB）
- 计算：Jinja2 渲染和变量校验几乎无额外计算开销；Context Budget 的 token 估算需 tiktoken 库

### 外部依赖

- Neo4j 场景规则库：需支持 schema 字段扩展（或新建关联表）
- Wiki 索引：当前为全量轻量扫描，若后续升级为向量检索需额外资源（不在本计划范围内）

---

## 10. 附录：任务看板模板

建议用以下 Kanban 看板跟踪每日任务：

```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│   Backlog    │  In Progress │   In Review  │    Done      │
├──────────────┼──────────────┼──────────────┼──────────────┤
│ 任务 1.1.2   │ 任务 1.1.1   │ 任务 1.2.1   │ 任务 1.1.3   │
│ 任务 1.3.1   │              │              │              │
│ ...          │              │              │              │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

每个任务卡片格式：

```
[任务编号] 任务名称
负责人: @xxx
所属阶段: Phase X / Week Y
验收标准:
- [ ] 标准 1
- [ ] 标准 2
阻塞项: 无 / 依赖任务 Z
预估工时: Xh
```

---

## 变更日志

| 版本 | 日期 | 变更内容 |
|---|---|---|
| v1.0 | 2026-04-23 | 初始版本，基于校准后的研究报告拆解 |
