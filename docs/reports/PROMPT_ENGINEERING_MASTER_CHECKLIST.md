# Athena Prompt Engineering 实施计划 — 主任务清单

> 基于 `PROMPT_ENGINEERING_IMPLEMENTATION_PLAN.md` 拆解
> 每条任务包含：ID、名称、智能体分配、依赖、输入、输出、验收检查清单

---

## 任务编号规则

```
[Phase].[周].[序号]
```

例如 `1.1.3` = Phase 1 / W1 / 第 3 个任务

---

## 智能体分配总览

| 智能体 | 代号 | 负责范围 | 启动周 | 并行度 |
|---|---|---|---|---|
| **Agent-Infra** | A1 | 灰度配置、降级策略、观测埋点、Dashboard、告警、运维手册 | W1 | 与 A2 并行 |
| **Agent-Core** | A2 | 主链路改造、紧急修复、灰度开关接入、缓存优化 | W1 | 与 A1 并行 |
| **Agent-Migrate** | A3 | 旧链路梳理、deprecated 标记、异步错配修复、资产迁移、调用方迁移 | W3 | 依赖 A2 |
| **Agent-Schema** | A4 | Jinja2 渲染器、变量 Schema、校验器、注入安全、Prompt Inventory | W7 | 依赖 A2，可与 A3 部分并行 |
| **Agent-Budget** | A5 | Context Budget、证据裁剪、质量指标、回滚、A/B | W11 | 依赖 A4 |
| **Agent-QA** | A6 | 测试用例、回归测试、性能压测、稳定性保障 | 贯穿 | 与所有智能体协作 |

---

## Phase 1: 灰度启用与观测（W1-W2）

### W1 任务

#### 任务 1.1.1: 设计灰度配置 Schema
- **ID**: `1.1.1`
- **智能体**: A1
- **依赖**: 无
- **输入**: `core/api/prompt_system_routes.py:212` 的 `is_legal_prompt_fusion_enabled()`
- **输出**: `core/legal_prompt_fusion/rollout_config.py`
- **工时**: 4h
- **检查清单**:
  - [ ] `FusionRolloutConfig` 类实现完整（global_enabled / domain_whitelist / task_type_whitelist / traffic_percentage / user_id_hash_prefix）
  - [ ] `should_enable()` 方法实现分层判断逻辑
  - [ ] 配置支持热重载（不重启服务生效）
  - [ ] 单元测试覆盖所有组合场景（global off / domain mismatch / task mismatch / traffic 0% / traffic 50% / user hash）
  - [ ] 类型注解完整，ruff/mypy 通过

#### 任务 1.1.2: 替换原有布尔开关
- **ID**: `1.1.2`
- **智能体**: A2
- **依赖**: `1.1.1`
- **输入**: `core/api/prompt_system_routes.py` 第 187-213 行
- **输出**: PR（改动范围控制在 `prompt_system_routes.py` 和配置模块）
- **工时**: 4h
- **检查清单**:
  - [ ] 删除纯环境变量判断，接入 `FusionRolloutConfig`
  - [ ] 保留环境变量向后兼容：`LEGAL_PROMPT_FUSION_ENABLED=true` 等价于 `global_enabled=true, traffic_percentage=100`
  - [ ] 新增配置文件 `config/prompt_fusion_rollout.yaml` 可覆盖环境变量
  - [ ] 代码审查通过
  - [ ] 单元测试通过（含向后兼容场景）

#### 任务 1.1.3: 设计融合核心指标结构
- **ID**: `1.1.3`
- **智能体**: A1
- **依赖**: 无
- **输入**: `core/legal_prompt_fusion/` 现有模块接口
- **输出**: `core/legal_prompt_fusion/metrics.py`
- **工时**: 3h
- **检查清单**:
  - [ ] `FusionMetrics` dataclass 包含全部字段（request_id / domain / task_type / fusion_enabled / latency_ms / evidence_count / evidence_by_source / cache_hit / wiki_revision / template_version / source_degradation / error）
  - [ ] 字段类型注解正确
  - [ ] 支持序列化为 JSON（用于日志/指标系统）

#### 任务 1.1.4: 主链路埋点实现
- **ID**: `1.1.4`
- **智能体**: A2
- **依赖**: `1.1.3`
- **输入**: `core/api/prompt_system_routes.py` 的 `generate_prompt()` 第 484-578 行
- **输出**: PR
- **工时**: 4h
- **检查清单**:
  - [ ] 融合调用前后增加计时（`time.monotonic()`）
  - [ ] 记录每个源的返回数量和耗时
  - [ ] 记录缓存命中状态
  - [ ] 异常时记录 `source_degradation` 和 `error`
  - [ ] 指标异步发送，发送失败不阻断主链路（try/except + 日志）
  - [ ] 融合开启和关闭的请求都产生基线记录

#### 任务 1.1.5: 单源异常自动降级
- **ID**: `1.1.5`
- **智能体**: A1
- **依赖**: 无
- **输入**: `core/legal_prompt_fusion/providers.py`
- **输出**: PR
- **工时**: 4h
- **检查清单**:
  - [ ] Postgres / Neo4j / Wiki 三个 provider 各自增加异常捕获
  - [ ] 某源超时或异常时记录 `source_degradation`，返回空列表，不抛错
  - [ ] 三源全部异常时正常返回（融合块为空）
  - [ ] 单次 provider 调用超时默认 200ms（可配置）
  - [ ] 降级事件写入 warning 日志
  - [ ] 故障注入测试通过（模拟单源故障、双源故障、三源故障）

#### 任务 1.1.6: 热重载配置实现
- **ID**: `1.1.6`
- **智能体**: A1
- **依赖**: `1.1.1`
- **输入**: `config/prompt_fusion_rollout.yaml`
- **输出**: PR
- **工时**: 3h
- **检查清单**:
  - [ ] 配置文件修改后 10 秒内生效
  - [ ] 不重启服务即可切换灰度策略
  - [ ] 配置解析错误时不崩溃，保留上次有效配置
  - [ ] 配置变更写入 info 日志

### W2 任务

#### 任务 1.2.1: 指标收集 Pipeline 搭建
- **ID**: `1.2.1`
- **智能体**: A1
- **依赖**: `1.1.4`
- **输入**: 现有观测基础设施（Prometheus / Grafana / ELK）
- **输出**: 指标收集配置
- **工时**: 4h
- **检查清单**:
  - [ ] `FusionMetrics` 接入现有日志/指标系统
  - [ ] 聚合指标计算正确：evidence_hit_rate / avg_latency_ms / cache_hit_rate / source_degradation_rate
  - [ ] Dashboard 可实时查看（延迟 < 30s）
  - [ ] 支持按 domain / task_type / 时间范围过滤

#### 任务 1.2.2: 告警规则配置
- **ID**: `1.2.2`
- **智能体**: A1
- **依赖**: `1.2.1`
- **输入**: Dashboard 指标
- **输出**: 告警规则 YAML + 通知渠道配置
- **工时**: 3h
- **检查清单**:
  - [ ] FusionLatencyHigh（>500ms，5min）配置完成
  - [ ] FusionEvidenceLow（<60%，10min）配置完成
  - [ ] FusionCacheMissBurst（<30%，5min）配置完成
  - [ ] 告警通知渠道已配置（Slack / 钉钉 / 邮件）
  - [ ] 手动注入测试数据可触发告警

#### 任务 1.2.3: OA 解读场景 5% 灰度试点
- **ID**: `1.2.3`
- **智能体**: A2 + A6
- **依赖**: `1.1.2`, `1.1.5`, `1.2.1`
- **输入**: 生产环境
- **输出**: 灰度运行报告
- **工时**: 8h（含 24h 观察）
- **检查清单**:
  - [ ] 配置灰度：`domain=patent`, `task_type=office_action`, `traffic_percentage=5`
  - [ ] Dashboard 持续观察 24 小时
  - [ ] 人工抽检 20 条开启融合 vs 20 条未开启融合的响应
  - [ ] `fusion_avg_latency_ms` P95 < 300ms
  - [ ] 无 500 错误归因于融合模块
  - [ ] 无"融合证据块干扰模型输出格式"的案例
  - [ ] 产出灰度运行报告

#### 任务 1.2.4: 修复 `evaluate_prompt_file()` 递归问题
- **ID**: `1.2.4`
- **智能体**: A2
- **依赖**: 无
- **输入**: `core/ai/prompts/__init__.py` 第 155-165 行
- **输出**: Hotfix PR
- **工时**: 2h
- **检查清单**:
  - [ ] 修复递归调用（函数重命名或调整 import）
  - [ ] 调用 `evaluate_prompt_file("some.md")` 不再递归溢出
  - [ ] 单元测试通过
  - [ ] 回归测试通过

#### 任务 1.2.5: Phase 1 里程碑评审
- **ID**: `1.2.5`
- **智能体**: A1 + A2 + A6
- **依赖**: 全部 W1-W2 任务
- **输入**: 灰度数据、Dashboard、测试报告
- **输出**: 评审纪要
- **工时**: 2h
- **检查清单**:
  - [ ] 灰度运行 48h 无 P0 故障
  - [ ] `fusion_avg_latency_ms` P95 < 500ms
  - [ ] 降级策略通过故障注入测试
  - [ ] Phase 2 计划确认

---

## Phase 2: 主链路收口与旧链路清理（W3-W6）

### W3 任务

#### 任务 2.1.1: 全量调用矩阵梳理
- **ID**: `2.1.1`
- **智能体**: A3
- **依赖**: 无
- **输入**: 全仓库代码
- **输出**: `docs/reports/PROMPT_RUNTIME_MATRIX.md`
- **工时**: 6h
- **检查清单**:
  - [ ] `grep -rn` 扫描以下模块的全部导入和调用：progressive_loader / unified_prompt_manager / unified_prompt_manager_extended / unified_prompt_manager_production / integrated_prompt_generator / capability_integrated_prompt_generator
  - [ ] 按调用方（业务模块 / 测试 / 脚本）分类统计
  - [ ] 每个调用方标注：当前功能、迁移目标、预估工作量（高/中/低）
  - [ ] 调用矩阵覆盖 100% 的导入点

#### 任务 2.1.2: 标记 Deprecated
- **ID**: `2.1.2`
- **智能体**: A3
- **依赖**: `2.1.1`
- **输入**: 旧链路模块文件
- **输出**: PR（纯标记，不改逻辑）
- **工时**: 3h
- **检查清单**:
  - [ ] progressive_loader.py 顶部添加 DeprecationWarning
  - [ ] unified_prompt_manager.py 顶部添加 DeprecationWarning
  - [ ] unified_prompt_manager_extended.py 顶部添加 DeprecationWarning
  - [ ] unified_prompt_manager_production.py 顶部添加 DeprecationWarning
  - [ ] `core/ai/prompts/__init__.py` 导出列表注释 deprecated 状态
  - [ ] 导入 deprecated 模块时产生 `DeprecationWarning`
  - [ ] CI 不因此失败

#### 任务 2.1.3: 异步调用错配修复决策
- **ID**: `2.1.3`
- **智能体**: A3
- **依赖**: `2.1.1`
- **输入**: 定位到的错配代码点
- **输出**: `docs/decisions/ASYNC_FIX_DECISION.md`
- **工时**: 4h
- **检查清单**:
  - [ ] 定位全部同步调用异步方法的代码点（integrated_prompt_generator.py:212 / :276 / unified_prompt_manager_extended.py:209 / unified_prompt_manager_production.py:457）
  - [ ] 评估方案 A（加 await，全链 async 化）、方案 B（改为 sync 实现）、方案 C（废弃调用点，迁移至主链路）
  - [ ] 明确推荐方案及理由
  - [ ] 技术评审通过

### W4 任务

#### 任务 2.2.1: 执行异步错配修复
- **ID**: `2.2.1`
- **智能体**: A3
- **依赖**: `2.1.3`
- **输入**: 决策文档
- **输出**: PR
- **工时**: 8h
- **检查清单**:
  - [ ] 按决策方案修复全部错配点
  - [ ] 修复后异步方法不再被同步调用（静态分析验证）
  - [ ] 相关单元测试通过
  - [ ] 无新增 500 错误（集成测试）

#### 任务 2.2.2: v4 资产转化为场景规则模板
- **ID**: `2.2.2`
- **智能体**: A3 + A4
- **依赖**: 无
- **输入**: prompts/ 中的 v4 模板
- **输出**: Neo4j 场景规则模板（3 个）
- **工时**: 12h
- **检查清单**:
  - [ ] hitl_protocol_v4_constraint_repeat.md → 作为 safety 基础块接入全部场景
  - [ ] cap04_inventive_v2_with_whenToUse.md → 创造性分析场景规则
  - [ ] task_2_1_oa_analysis_v2_with_parallel.md → OA 解读场景规则
  - [ ] Markdown 内容转化为 system_prompt_template / user_prompt_template
  - [ ] 补充变量占位符（当前用 `{var}`，后续 Phase 3 升级）
  - [ ] 写入 Neo4j 规则库
  - [ ] 3 个模板可通过 `retrieve_rule()` 正常检索
  - [ ] `substitute_variables()` 替换后输出与原 Markdown 语义一致
  - [ ] 人工验证 5 条请求的 system_prompt 质量不低于原静态模板

### W5 任务

#### 任务 2.3.1: 低风险调用方迁移
- **ID**: `2.3.1`
- **智能体**: A3
- **依赖**: `2.1.2`
- **输入**: 调用矩阵
- **输出**: PR
- **工时**: 6h
- **检查清单**:
  - [ ] 清理"仅导入但未实际使用"的代码点
  - [ ] 将测试中的旧链路调用替换为主链路 API 调用或 mock
  - [ ] 每次改动后跑全量测试
  - [ ] 全量测试通过

#### 任务 2.3.2: 中风险调用方迁移
- **ID**: `2.3.2`
- **智能体**: A3
- **依赖**: `2.3.1`
- **输入**: 核心业务代理的 get_system_prompt()
- **输出**: PR
- **工时**: 10h
- **检查清单**:
  - [ ] 选取 2-3 个核心业务代理
  - [ ] Python 字符串模板替换为对主链路 `generate_prompt()` 的调用，或提取为 Markdown 接入场景规则库
  - [ ] 自动化 diff 或人工抽检：迁移后输出与原输出差异 < 5%
  - [ ] 业务模块单元测试通过

### W6 任务

#### 任务 2.4.1: 主链路唯一化验证
- **ID**: `2.4.1`
- **智能体**: A6
- **依赖**: `2.3.2`
- **输入**: 全仓库代码
- **输出**: 测试报告
- **工时**: 8h
- **检查清单**:
  - [ ] 非测试/非 deprecated 代码中已无 progressive_loader 和 unified_prompt_manager* 的导入（grep 验证）
  - [ ] 全量集成测试通过（含提示词生成链路）
  - [ ] 压测主链路 API：QPS、延迟、错误率不低于清理前基线

#### 任务 2.4.2: Phase 2 里程碑评审
- **ID**: `2.4.2`
- **智能体**: A3 + A6
- **依赖**: 全部 W3-W6 任务
- **输入**: 测试报告、压测报告
- **输出**: 评审纪要
- **工时**: 2h
- **检查清单**:
  - [ ] 旧链路已标记 deprecated 且无新增调用
  - [ ] 主链路已承载 100% 生产流量
  - [ ] v4 资产 ≥2 个已接入场景规则库
  - [ ] 异步调用错配已修复

---

## Phase 3: 变量治理与模板协议化（W7-W9）

### W7 任务

#### 任务 3.1.1: Jinja2 渲染器实现
- **ID**: `3.1.1`
- **智能体**: A4
- **依赖**: 无
- **输入**: Jinja2 库
- **输出**: `core/prompt_engine/renderer.py`
- **工时**: 4h
- **检查清单**:
  - [ ] `PromptRenderer` 类实现，使用 `Environment(loader=BaseLoader(), undefined=StrictUndefined, autoescape=False)`
  - [ ] `render(template: str, variables: dict) -> str` 方法
  - [ ] 支持自定义过滤器（default、truncate）
  - [ ] 缺失变量时抛出 `UndefinedError`，不静默通过
  - [ ] 单元测试覆盖正常渲染、缺失变量、过滤器、复杂嵌套

#### 任务 3.1.2: 变量 Schema 定义
- **ID**: `3.1.2`
- **智能体**: A4
- **依赖**: 无
- **输入**: 现有模板变量分析
- **输出**: `core/prompt_engine/schema.py`
- **工时**: 4h
- **检查清单**:
  - [ ] `VariableSpec` dataclass 包含：name / type / required / source / default / description / max_length
  - [ ] `PromptSchema` dataclass 包含：variables / template_version
  - [ ] 为 W4 迁移的 3 个场景规则模板编写 schema
  - [ ] 类型枚举：string / int / float / bool / list / dict

#### 任务 3.1.3: 场景规则模板语法升级
- **ID**: `3.1.3`
- **智能体**: A4
- **依赖**: `3.1.1`
- **输入**: Neo4j 中的场景规则模板
- **输出**: 更新后的场景规则
- **工时**: 6h
- **检查清单**:
  - [ ] system_prompt_template / user_prompt_template 中的 `{var}` 替换为 `{{ var }}`
  - [ ] 增加 `| default('暂无')` 等过滤器
  - [ ] 更新 `substitute_variables()` 支持 Jinja2（或新建 `Jinja2ScenarioRule` 子类，逐步切换）
  - [ ] 模板渲染结果与原 `{var}` 替换结果一致（对比测试 100% pass）
  - [ ] `StrictUndefined` 在缺失变量时抛出 `UndefinedError`

### W8 任务

#### 任务 3.2.1: 变量校验器实现
- **ID**: `3.2.1`
- **智能体**: A4
- **依赖**: `3.1.2`
- **输入**: `core/prompt_engine/schema.py`
- **输出**: `core/prompt_engine/validators.py`
- **工时**: 4h
- **检查清单**:
  - [ ] `VariableValidator` 类实现
  - [ ] 类型检查、required 检查、max_length 检查
  - [ ] 支持自定义校验规则（正则、枚举值）
  - [ ] 返回 `ValidationResult(valid, errors, warnings)`
  - [ ] 单元测试覆盖所有校验类型

#### 任务 3.2.2: 注入安全策略
- **ID**: `3.2.2`
- **智能体**: A4
- **依赖**: 无
- **输入**: 安全测试用例
- **输出**: `core/prompt_engine/sanitizer.py`
- **工时**: 6h
- **检查清单**:
  - [ ] `PromptSanitizer` 类实现
  - [ ] `sanitize_string()`: 控制字符清洗、长度截断
  - [ ] `escape_markdown()`: Markdown 特殊字符转义
  - [ ] `detect_injection()`: 启发式检测 prompt injection 模式
  - [ ] 在 `generate_prompt()` 变量准备阶段调用 sanitizer
  - [ ] 高风险变量标记后进入日志，不阻断（可配置为阻断）
  - [ ] 注入测试集（10 种常见 injection 模式）检测率 > 80%
  - [ ] 正常业务输入不误报（抽样 100 条验证）

#### 任务 3.2.3: 缺失变量阻断策略接入主链路
- **ID**: `3.2.3`
- **智能体**: A4
- **依赖**: `3.2.1`
- **输入**: `core/api/prompt_system_routes.py` 的 `generate_prompt()`
- **输出**: PR
- **工时**: 4h
- **检查清单**:
  - [ ] 变量替换前增加校验步骤
  - [ ] 缺失 required 变量时返回 400，body 含缺失变量清单
  - [ ] 缺失 optional 变量时使用默认值，正常返回
  - [ ] 不进入 LLM 调用（节省 token）
  - [ ] 集成测试覆盖缺失变量场景

### W9 任务

#### 任务 3.3.1: Prompt Inventory 自动化
- **ID**: `3.3.1`
- **智能体**: A4
- **依赖**: `3.1.2`
- **输入**: `prompts/` 目录 + Neo4j 场景规则库
- **输出**: `scripts/generate_prompt_inventory.py` + `PROMPT_INVENTORY.md`
- **工时**: 6h
- **检查清单**:
  - [ ] 扫描脚本覆盖 prompts/ 目录和 Neo4j 场景规则库
  - [ ] 每个条目包含：ID / 版本 / 路径 / 状态 / 关联场景 / 变量列表 / 负责人
  - [ ] 状态枚举：production / staging / deprecated / draft
  - [ ] CI 检查：新增/修改提示词文件必须更新 Inventory
  - [ ] CI 检查生效，未更新 Inventory 的 PR 被阻断

#### 任务 3.3.2: 存量模板变量 Schema 补齐
- **ID**: `3.3.2`
- **智能体**: A4
- **依赖**: `3.1.2`
- **输入**: 全部生产场景规则模板
- **输出**: 更新后的场景规则 + schema 存储
- **工时**: 8h
- **检查清单**:
  - [ ] 遍历全部生产场景规则模板
  - [ ] 提取所有占位符，补全 `VariableSpec`
  - [ ] 标记 required / optional
  - [ ] 更新 Neo4j 存储（或新建 schema 关联表）
  - [ ] 100% 生产模板具备变量 schema
  - [ ] `validate()` 通过所有生产模板的校验

#### 任务 3.3.3: Phase 3 里程碑评审
- **ID**: `3.3.3`
- **智能体**: A4 + A6
- **依赖**: 全部 W7-W9 任务
- **输入**: 测试报告、Inventory、schema 覆盖率
- **输出**: 评审纪要
- **工时**: 2h
- **检查清单**:
  - [ ] Jinja2 渲染器已接入主链路
  - [ ] 变量校验器拦截 100% 的 required 变量缺失（测试验证）
  - [ ] Prompt Inventory 自动化生成并通过 CI 校验
  - [ ] 注入安全策略通过安全评审

---

## Phase 3.5: 稳定性保障周（W10）

#### 任务 3.5.1: 全链路回归测试
- **ID**: `3.5.1`
- **智能体**: A6
- **依赖**: `3.3.2`
- **输入**: 全量测试套件 + 端到端测试用例
- **输出**: 回归测试报告
- **工时**: 8h
- **检查清单**:
  - [ ] 全量单元测试 + 集成测试通过率 100%
  - [ ] 提示词生成链路端到端测试用例覆盖 10 个核心场景
  - [ ] 对比 Phase 1 基线：延迟、错误率、token 消耗无劣化

#### 任务 3.5.2: 性能基线建立
- **ID**: `3.5.2`
- **智能体**: A6 + A1
- **依赖**: `1.2.1`
- **输入**: 压测环境
- **输出**: 性能基线文档
- **工时**: 6h
- **检查清单**:
  - [ ] 压测主链路 API：QPS 从 10 逐步加到 100
  - [ ] 记录：p50 / p95 / p99 延迟、错误率、fusion_additional_latency_p95、avg_tokens_per_request
  - [ ] 建立性能退化告警阈值（P95 延迟增长 > 20% 触发）
  - [ ] 性能基线文档已归档

#### 任务 3.5.3: 技术债务清理
- **ID**: `3.5.3`
- **智能体**: A3
- **依赖**: 无
- **输入**: 全仓库代码
- **输出**: 债务清理 PR
- **工时**: 6h
- **检查清单**:
  - [ ] 删除已标记 deprecated 且确认无调用的 dead code
  - [ ] 补齐核心模块 docstring
  - [ ] 修复 lint 警告（ruff / mypy）
  - [ ] 更新 `docs/architecture/prompt-system.md`
  - [ ] 代码覆盖率不下降
  - [ ] lint 检查 0 error

#### 任务 3.5.4: 运维手册补齐
- **ID**: `3.5.4`
- **智能体**: A1
- **依赖**: `1.2.2`
- **输入**: 运维经验
- **输出**: `docs/ops/prompt-system-runbook.md`
- **工时**: 4h
- **检查清单**:
  - [ ] 故障排查手册（融合证据为空、缓存命中率骤降、源降级恢复）
  - [ ] 灰度操作手册（调整流量比例、紧急关闭融合）
  - [ ] 回滚操作手册
  - [ ] 值班同学演练通过（可独立处理常见故障）

---

## Phase 4: 上下文预算与评估闭环（W11-W12）

### W11 任务

#### 任务 4.1.1: 优先级槽位模型实现
- **ID**: `4.1.1`
- **智能体**: A5
- **依赖**: `3.1.1`
- **输入**: Jinja2 渲染器 + 现有模板结构
- **输出**: `core/prompt_engine/context_budget.py`
- **工时**: 6h
- **检查清单**:
  - [ ] `Slot` dataclass 包含：priority / content / estimated_tokens / source
  - [ ] `ContextBudgetAllocator` 类实现贪心填充算法
  - [ ] P0 必选槽位全部保留
  - [ ] P1-P3 按优先级和 estimated_tokens 填充
  - [ ] 支持按 complexity 分层预算（simple:3000 / medium:6000 / complex:10000）
  - [ ] token 估算使用 tiktoken 或字符数/4 近似，误差 < 10%

#### 任务 4.1.2: 三源融合证据动态裁剪
- **ID**: `4.1.2`
- **智能体**: A5
- **依赖**: `4.1.1`, `1.1.5`
- **输入**: 融合证据块生成逻辑
- **输出**: PR
- **工时**: 6h
- **检查清单**:
  - [ ] 融合证据块作为 P1 槽位接入 Context Budget
  - [ ] 根据剩余 budget 动态决定：保留/截断 summary/降级为数量提示
  - [ ] 复杂度映射证据上限：simple max 3 / medium max 8 / complex max 12
  - [ ] simple 任务 system_prompt 总 token < 3000（抽样验证）
  - [ ] complex 任务保留全部关键证据，无 truncation 导致信息丢失

#### 任务 4.1.3: Token 估算器集成
- **ID**: `4.1.3`
- **智能体**: A5
- **依赖**: `4.1.1`
- **输入**: tiktoken 或现有 tokenizer
- **输出**: PR
- **工时**: 3h
- **检查清单**:
  - [ ] 集成 tiktoken 用于精确估算
  - [ ] `generate_prompt()` 返回前估算 system_prompt + user_prompt 总 token
  - [ ] 超过 budget 时触发告警日志（不阻断）
  - [ ] token 估算误差 < 10%（对比实际 API 消耗）

### W12 任务

#### 任务 4.2.1: 线上质量指标埋点
- **ID**: `4.2.1`
- **智能体**: A5 + A1
- **依赖**: `1.2.1`
- **输入**: 用户反馈数据 + LLM 调用结果
- **输出**: 指标埋点 PR + Dashboard
- **工时**: 6h
- **检查清单**:
  - [ ] first_answer_acceptance_rate（用户未追问即接受的比例）
  - [ ] followup_rate（用户追问比例）
  - [ ] json_contract_pass_rate（输出符合 JSON schema 的比例）
  - [ ] tool_call_success_rate（工具调用成功比例）
  - [ ] user_satisfaction_score（显式评分或隐式信号）
  - [ ] 核心场景（OA 解读、创造性分析）100% 覆盖质量指标
  - [ ] Dashboard 支持按 prompt version 对比（A/B 分析）

#### 任务 4.2.2: Prompt Version Rollback 机制
- **ID**: `4.2.2`
- **智能体**: A5
- **依赖**: `1.1.3`（template_version 机制）
- **输入**: 现有版本联动机制
- **输出**: 回滚 API + 脚本 + 手册
- **工时**: 6h
- **检查清单**:
  - [ ] 每次场景规则模板更新自动生成新版本 hash
  - [ ] 保留最近 N 个版本的模板内容（对象存储或数据库）
  - [ ] 实现回滚 API：`POST /api/v1/prompt-system/rules/rollback`
  - [ ] 回滚后自动清除相关缓存
  - [ ] 回滚操作在 30 秒内生效
  - [ ] 回滚后缓存不返回旧版本内容
  - [ ] 回滚操作记录审计日志

#### 任务 4.2.3: A/B 测试能力
- **ID**: `4.2.3`
- **智能体**: A5
- **依赖**: `1.1.1`（灰度配置）
- **输入**: 灰度配置模块
- **输出**: A/B 配置模块
- **工时**: 4h
- **检查清单**:
  - [ ] 同一场景支持两个版本的 prompt template
  - [ ] 按用户 hash 分流（50/50 或其他比例）
  - [ ] 自动对比两组的线上质量指标
  - [ ] 支持"实验自动终止"：错误率显著高于对照组时自动切回

#### 任务 4.2.4: 项目结项评审
- **ID**: `4.2.4`
- **智能体**: A1 + A2 + A3 + A4 + A5 + A6
- **依赖**: 全部任务
- **输入**: 12 周指标回顾
- **输出**: 结项报告
- **工时**: 4h
- **检查清单**:
  - [ ] 全阶段验收标准 100% 达成
  - [ ] 与基线对比的收益量化
  - [ ] 遗留债务与后续计划
  - [ ] 知识沉淀文档已归档

---

## 依赖图（简化）

```
Phase 1
├── 1.1.1 (A1) ──┬── 1.1.2 (A2) ──┬── 1.2.3 (A2+A6)
├── 1.1.3 (A1) ──┤                  │
├── 1.1.4 (A2) ──┤                  │
├── 1.1.5 (A1) ──┤                  │
├── 1.1.6 (A1) ──┤                  │
├── 1.2.1 (A1) ──┤                  │
├── 1.2.2 (A1) ──┘                  │
├── 1.2.4 (A2) ─────────────────────┘
└── 1.2.5 (评审)

Phase 2 (依赖 Phase 1)
├── 2.1.1 (A3) ──┬── 2.1.2 (A3) ──┬── 2.3.1 (A3) ──┬── 2.4.1 (A6)
├── 2.1.3 (A3) ──┤                  │                  │
├── 2.2.1 (A3) ──┤                  │                  │
├── 2.2.2 (A3+A4)┤                  │                  │
└── 2.3.2 (A3) ──┘                  │                  │
                                    └── 2.4.2 (评审)

Phase 3 (依赖 Phase 2)
├── 3.1.1 (A4) ──┬── 3.1.3 (A4) ──┬── 3.2.3 (A4) ──┬── 3.3.1 (A4)
├── 3.1.2 (A4) ──┤                  │                  ├── 3.3.2 (A4)
├── 3.2.1 (A4) ──┤                  │                  └── 3.3.3 (评审)
└── 3.2.2 (A4) ──┘                  │

Phase 3.5
├── 3.5.1 (A6)
├── 3.5.2 (A6+A1)
├── 3.5.3 (A3)
└── 3.5.4 (A1)

Phase 4 (依赖 Phase 3)
├── 4.1.1 (A5) ──┬── 4.1.2 (A5) ──┬── 4.2.1 (A5+A1)
├── 4.1.3 (A5)   │                  ├── 4.2.2 (A5)
└──              │                  ├── 4.2.3 (A5)
                 │                  └── 4.2.4 (评审)
                 │
                 └── W11 核心路径
```

---

## 智能体启动顺序

### 第一波（W1，立即并行启动）

```
A1 (Agent-Infra)    ──┐
                       ├──→ 并行开发，每日同步
A2 (Agent-Core)     ──┘
```

### 第二波（W3，依赖第一波完成）

```
A3 (Agent-Migrate)  ──→ 串行启动，依赖 A2 的主链路改造完成
```

### 第三波（W7，与 A3 部分并行）

```
A4 (Agent-Schema)   ──→ 依赖 A2，可与 A3 后半段并行
```

### 第四波（W11，依赖第三波）

```
A5 (Agent-Budget)   ──→ 依赖 A4 完成
```

### 贯穿全程

```
A6 (Agent-QA)       ──→ 与所有智能体协作，W10 集中发力
```
