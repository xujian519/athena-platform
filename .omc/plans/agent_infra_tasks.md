# Agent-Infra (A1) 任务包

> 基础设施与观测智能体
> 负责范围: 灰度配置、降级策略、观测埋点、Dashboard、告警、热重载、运维手册
> 启动条件: 立即启动（W1）
> 并行关系: 与 Agent-Core (A2) 并行

---

## 上下文代码路径

| 文件 | 说明 |
|---|---|
| `core/api/prompt_system_routes.py:187-213` | 现有布尔开关 `is_legal_prompt_fusion_enabled()` |
| `core/api/prompt_system_routes.py:484-578` | 主链路融合注入点 |
| `core/legal_prompt_fusion/providers.py` | 三源 provider（Postgres / Neo4j / Wiki）|
| `core/legal_prompt_fusion/__init__.py` | 融合模块入口 |
| `core/legal_prompt_fusion/models.py` | 数据模型（SourceType 等）|

---

## 任务 1.1.1: 设计灰度配置 Schema

**输出**: `core/legal_prompt_fusion/rollout_config.py`

**具体要求**:
1. 实现 `FusionRolloutConfig` dataclass:
   - `global_enabled: bool = False`
   - `domain_whitelist: list[str] = []`
   - `task_type_whitelist: list[str] = []`
   - `traffic_percentage: int = 0` (0-100)
   - `user_id_hash_prefix: str = ""`
2. 实现 `should_enable(domain, task_type, user_id="") -> bool`:
   - 判断顺序: global_enabled → domain_whitelist → task_type_whitelist → traffic_percentage → user_id_hash_prefix
   - traffic_percentage: 对 request_id 或 user_id 做 hash，取模 100，小于 percentage 则命中
   - user_id_hash_prefix: 若不为空，user_id 的 hash 值以该前缀开头则命中
3. 配置支持热重载（通过文件监听或定时轮询 `config/prompt_fusion_rollout.yaml`）
4. 配置解析错误时不崩溃，保留上次有效配置，写入 error 日志
5. 完整的类型注解，通过 ruff/mypy

**验收检查清单**:
- [ ] 单元测试覆盖: global off / domain mismatch / task mismatch / traffic 0% / traffic 50% / user hash match
- [ ] 热重载: 修改配置文件后 10 秒内生效
- [ ] 错误恢复: 配置文件格式错误时保留旧配置

---

## 任务 1.1.3: 设计融合核心指标结构

**输出**: `core/legal_prompt_fusion/metrics.py`

**具体要求**:
1. 实现 `FusionMetrics` dataclass:
   - `request_id: str`
   - `domain: str`
   - `task_type: str`
   - `fusion_enabled: bool`
   - `latency_ms: float`
   - `evidence_count: int`
   - `evidence_by_source: dict[str, int]`
   - `cache_hit: bool`
   - `wiki_revision: str`
   - `template_version: str`
   - `source_degradation: list[str]`
   - `error: str | None`
2. 实现 `to_dict() -> dict` 和 `to_json() -> str` 方法
3. 字段类型注解完整（Python 3.11+ 可用 `str | None`）

---

## 任务 1.1.5: 单源异常自动降级

**输出**: PR（改动 `core/legal_prompt_fusion/providers.py`）

**具体要求**:
1. 三个 provider 类各自增加 try/except 包装:
   - `PostgresLegalRepository.retrieve(query, top_k)`
   - `Neo4jLegalRepository.retrieve(query, top_k)`
   - `WikiLegalRepository.retrieve(query, top_k)`
2. 异常捕获范围: 连接超时、查询错误、返回格式异常
3. 超时时限: 默认 200ms，可通过 `LEGAL_FUSION_SOURCE_TIMEOUT_MS` 环境变量配置
4. 降级行为: 返回空列表，记录 `source_degradation`，写入 warning 日志（含异常类型和消息）
5. 三源全部异常时: `HybridLegalRetriever` 返回空 evidence 列表，不抛错
6. 新增故障注入测试（mock provider 抛异常）

**验收检查清单**:
- [ ] 模拟 Postgres 故障: 请求成功，融合块含 Neo4j + Wiki 证据
- [ ] 模拟三源全部故障: 请求成功，融合块为空
- [ ] 降级事件写入 warning 日志

---

## 任务 1.1.6: 热重载配置实现

**输出**: PR（改动 `core/legal_prompt_fusion/rollout_config.py`，新增 `config/prompt_fusion_rollout.yaml`）

**具体要求**:
1. 配置文件格式:
   ```yaml
   global_enabled: false
   domain_whitelist:
     - patent
   task_type_whitelist:
     - office_action
     - novelty_analysis
   traffic_percentage: 5
   user_id_hash_prefix: ""
   ```
2. 使用文件轮询（每 10 秒检查 mtime）或 watchdog 实现热重载
3. 配置变更时写入 info 日志: "Config reloaded: global_enabled=false, traffic_percentage=5"
4. 首次加载失败时使用默认空配置（全关）

---

## 任务 1.2.1: 指标收集 Pipeline 搭建

**输出**: 指标收集配置（接入现有观测系统）

**具体要求**:
1. 将 `FusionMetrics` 数据接入现有日志系统（ELK / Loki）:
   - 以结构化 JSON 日志输出
2. 若项目使用 Prometheus，定义以下指标:
   - `fusion_requests_total` (counter, labels: domain, task_type, fusion_enabled)
   - `fusion_latency_seconds` (histogram, labels: domain, task_type)
   - `fusion_evidence_count` (histogram, labels: domain, source_type)
   - `fusion_cache_hits_total` (counter, labels: domain)
   - `fusion_source_degradations_total` (counter, labels: source_type)
3. Grafana Dashboard 面板:
   - Panel 1: `fusion_evidence_hit_rate = sum(fusion_evidence_count > 0) / sum(fusion_requests_total{fusion_enabled="true"})`
   - Panel 2: `fusion_avg_latency_ms = avg(fusion_latency_seconds) * 1000`
   - Panel 3: `fusion_cache_hit_rate = sum(fusion_cache_hits_total) / sum(fusion_requests_total)`
   - Panel 4: `fusion_source_degradation_rate = sum(fusion_source_degradations_total) / sum(fusion_requests_total)`
4. 支持按 domain / task_type / 时间范围过滤

---

## 任务 1.2.2: 告警规则配置

**输出**: 告警规则 YAML + 通知渠道配置

**具体要求**:
1. 三条告警规则:
   ```yaml
   - alert: FusionLatencyHigh
     expr: histogram_quantile(0.95, fusion_latency_seconds) > 0.5
     for: 5m
     severity: warning
     annotations:
       summary: "Fusion latency P95 > 500ms"
       action: "降低 traffic_percentage 或检查 Wiki 索引"
   
   - alert: FusionEvidenceLow
     expr: rate(fusion_evidence_count[10m]) / rate(fusion_requests_total{fusion_enabled="true"}[10m]) < 0.6
     for: 10m
     severity: warning
     annotations:
       summary: "Fusion evidence hit rate < 60%"
       action: "检查 Wiki 索引状态和 PostgreSQL schema"
   
   - alert: FusionCacheMissBurst
     expr: rate(fusion_cache_hits_total[5m]) / rate(fusion_requests_total[5m]) < 0.3
     for: 5m
     severity: critical
     annotations:
       summary: "Fusion cache hit rate < 30%"
       action: "检查 wiki_revision 计算是否过于敏感"
   ```
2. 通知渠道配置到现有告警系统（Slack / 钉钉 / PagerDuty）
3. 通过手动注入测试数据验证告警可触发

---

## 任务 3.5.4: 运维手册补齐（W10）

**输出**: `docs/ops/prompt-system-runbook.md`

**具体要求**:
1. 故障排查手册:
   - 融合证据为空 → 检查 Wiki 索引状态、PostgreSQL 连接、Neo4j 查询日志
   - 缓存命中率骤降 → 检查 wiki_revision 是否因文件 mtime 抖动频繁变化
   - 某源降级 → 查看 `source_degradation` 日志，手动测试该源连接
   - 延迟飙升 → 检查 `fusion_latency_seconds` 分位值，定位慢源
2. 灰度操作手册:
   - 如何调整 `config/prompt_fusion_rollout.yaml` 的 traffic_percentage
   - 如何紧急关闭融合（global_enabled=false）
   - 如何按 domain 或 task_type 单独开启/关闭
3. 回滚操作手册:
   - 如何调用回滚 API（参考 A5 的任务 4.2.2）
   - 如何手动清除缓存
4. 值班演练: 由非开发人员按 runbook 处理 3 个模拟故障
