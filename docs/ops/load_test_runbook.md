# Prompt System 压测执行手册（Runbook）

> 本手册规范 Athena Prompt System 主链路 API 压测的完整流程，确保每次压测可重复、可观测、可恢复。

## 一、压测前检查（Pre-Check）

### 1.1 环境检查

| # | 检查项 | 命令 / 方法 | 通过标准 |
|---|---|---|---|
| 1 | 目标服务可访问 | `curl -f ${HOST}/api/v1/prompt-system/health` | HTTP 200，状态 `healthy` |
| 2 | 压测机网络连通 | `ping -c 3 ${HOST}` | 延迟 < 10ms，无丢包 |
| 3 | 压测机资源充足 | `htop` / `free -h` / `df -h` | CPU < 50%，内存 > 2G 空闲，磁盘 > 10G |
| 4 | Locust 版本正确 | `locust --version` | ≥ 2.15.0 |
| 5 | 数据集完整 | `ls tests/load/payloads/*.json` | 3 个 JSON 文件均存在且非空 |
| 6 | 脚本可执行 | `bash -n scripts/run_load_test.sh` | 无语法错误 |

### 1.2 数据与状态检查

| # | 检查项 | 命令 / 方法 | 通过标准 |
|---|---|---|---|
| 7 | 提示词缓存已清空 | `curl -X POST ${HOST}/api/v1/prompt-system/cache/clear` | 返回 `{"status":"success"}` |
| 8 | 性能指标已重置 | `curl -X POST ${HOST}/api/v1/prompt-system/monitoring/metrics/reset` | 返回 `{"status":"success"}` |
| 9 | 数据库连接正常 | `curl -f ${HOST}/api/v1/prompt-system/health/extended` | `neo4j`、`postgres`、`redis` 均为 `ok` |
| 10 | LLM 后端可用 | 查看 LLM 服务健康端点 | 状态正常，队列深度 < 5 |
| 11 | Prometheus 指标端点可访问 | `curl -f "${HOST}/api/v1/prompt-system/metrics?format=prometheus"` | HTTP 200，返回 Prometheus 文本 |

### 1.3 告警与通知

| # | 检查项 | 操作 | 通过标准 |
|---|---|---|---|
| 12 | 生产告警静默 | 在告警平台创建静默规则（Maintenance Window） | 压测期间不触发 P1/P2 告警 |
| 13 | 相关人员通知 | 在团队频道发送压测预告 | 研发、运维、业务方已周知 |
| 14 | 压测时间窗口 | 确认非业务高峰期 | 避开 09:00-11:00、14:00-16:00 |

### 1.4 预检查 Checklist 签字

- [ ] 环境检查全部通过
- [ ] 数据与状态检查全部通过
- [ ] 告警静默已生效
- [ ] 团队通知已发送
- [ ] 回滚方案已确认

---

## 二、压测执行（Execution）

### 2.1 实际执行步骤

按以下顺序执行，每步确认成功后再进入下一步：

**步骤 1：环境确认**
```bash
export HOST="http://localhost:8000"
curl -f "${HOST}/api/v1/prompt-system/health" || { echo "服务未就绪"; exit 1; }
```

**步骤 2：清空缓存并重置指标**
```bash
curl -X POST "${HOST}/api/v1/prompt-system/cache/clear"
curl -X POST "${HOST}/api/v1/prompt-system/monitoring/metrics/reset"
```

**步骤 3：执行基线压测（10 用户 → 50 用户 → 100 用户）**
```bash
# 低并发基线（10 用户，5 分钟）
./scripts/run_load_test.sh "${HOST}" 10 5m

# 中等并发基线（50 用户，10 分钟）
./scripts/run_load_test.sh "${HOST}" 50 10m

# 高并发基线（100 用户，10 分钟）
./scripts/run_load_test.sh "${HOST}" 100 10m
```

> **判停标准**：任意一步若触及「红色熔断阈值」（见 2.3），立即停止后续压测，保留现场并进入「四、应急响应」。

**步骤 4：采集 Prometheus 指标**
```bash
curl -s "${HOST}/api/v1/prompt-system/metrics?format=prometheus" > reports/load/prometheus_$(date +%Y%m%d_%H%M%S).txt
```

**步骤 5：采集性能快照**
```bash
curl -s "${HOST}/api/v1/prompt-system/monitoring/performance" | jq . > reports/load/performance_snapshot_$(date +%Y%m%d_%H%M%S).json
```

**步骤 6：采集缓存统计**
```bash
curl -s "${HOST}/api/v1/prompt-system/cache/stats" | jq . > reports/load/cache_stats_$(date +%Y%m%d_%H%M%S).json
```

### 2.2 实时指标 Dashboard

压测启动后，持续观察以下数据源：

| 数据源 | 地址 / 命令 | 关注指标 |
|---|---|---|
| Locust Web UI | `http://localhost:8089` | RPS、Failures、Response Time |
| 服务性能快照 | `curl ${HOST}/api/v1/prompt-system/monitoring/performance` | P95、P99、请求总量 |
| 缓存统计 | `curl ${HOST}/api/v1/prompt-system/cache/stats` | hit_rate、current_size |
| Prometheus 指标 | `curl "${HOST}/api/v1/prompt-system/metrics?format=prometheus"` | fusion_latency_seconds、fusion_cache_hits_total |
| 容器/主机监控 | Grafana / Prometheus / `htop` | CPU、内存、网络 IO、磁盘 IO |
| 数据库监控 | Neo4j Browser / pgAdmin / Redis CLI | 连接数、慢查询、缓存命中率 |
| LLM 后端监控 | LLM 服务 Dashboard | 队列长度、Token 吞吐量、错误率 |

### 2.3 关键阈值与熔断决策

| 指标 | 黄色警告 | 红色熔断 | 熔断动作 |
|---|---|---|---|
| 错误率 | ≥ 1% | ≥ 5% | 立即停止压测，保留现场 |
| P99 延迟 | ≥ 10s | ≥ 30s | 降级并发或停止压测 |
| CPU 使用率 | ≥ 70% | ≥ 90% | 观察是否持续 2min，是则停止 |
| 内存使用 | ≥ 80% | ≥ 95% | 立即停止，防止 OOM |
| LLM 队列深度 | ≥ 20 | ≥ 50 | 停止压测，通知 LLM 运维 |
| 数据库连接数 | ≥ 80% 上限 | ≥ 95% 上限 | 停止压测，检查连接泄漏 |
| 缓存命中率 | < 50% | < 30% | 检查缓存配置或预热逻辑 |

> **熔断原则**：一旦触及红色阈值，优先停止压测，保护生产环境，事后分析日志定位根因。

### 2.4 日志观察

```bash
# 实时跟踪服务端错误日志（根据实际部署调整）
tail -f /var/log/athena/prompt-system.log | grep -E "ERROR|WARN|❌|⚠️"

# 观察 5xx 错误
tail -f /var/log/athena/prompt-system.log | grep "status_code=5"

# 观察慢请求（>5s）
tail -f /var/log/athena/prompt-system.log | grep -E "processing_time_ms":[5-9][0-9]{3,}

# 观察融合指标（B5-PerfObs 新增）
tail -f /var/log/athena/prompt-system.log | grep "fusion_metrics"
```

---

## 三、压测后恢复（Recovery）

### 3.1 数据清理

| # | 操作项 | 命令 / 方法 | 确认标准 |
|---|---|---|---|
| 1 | 清理提示词缓存 | `curl -X POST ${HOST}/api/v1/prompt-system/cache/clear` | 返回 `success` |
| 2 | 重置性能指标 | `curl -X POST ${HOST}/api/v1/prompt-system/monitoring/metrics/reset` | 返回 `success` |
| 3 | 清理临时文件 | `rm -f /tmp/locust_*` | 无残留大文件 |

### 3.2 环境恢复

| # | 操作项 | 负责人 | 确认标准 |
|---|---|---|---|
| 4 | 取消告警静默 | 运维 / SRE | 告警平台显示静默已结束 |
| 5 | 恢复自动扩缩容 | 运维 / SRE | K8s HPA / 云厂商弹性策略恢复 |
| 6 | 通知团队压测结束 | 测试负责人 | 团队频道发送结果摘要 |

### 3.3 结果归档

| # | 操作项 | 说明 |
|---|---|---|
| 7 | 收集报告文件 | 将 `reports/load/` 下本次压测的 CSV + HTML + Prometheus 文本复制到归档目录 |
| 8 | 填写基线文档 | 将核心指标填入 `docs/reports/PERFORMANCE_BASELINE.md` |
| 9 | 记录异常与发现 | 在基线文档「关键结论与行动项」中登记问题 |
| 10 | 提交 Git 记录 | 将基线更新和 runbook 改进提交到版本库 |

### 3.4 恢复 Checklist 签字

- [ ] 缓存已清理
- [ ] 指标已重置
- [ ] 告警静默已取消
- [ ] 团队已通知
- [ ] 基线文档已更新
- [ ] 报告文件已归档

---

## 四、应急响应

### 4.1 压测导致服务异常

```bash
# 1. 立即停止 locust（Ctrl+C 或 kill）
# 2. 检查服务健康状态
curl -f ${HOST}/api/v1/prompt-system/health/extended | jq .

# 3. 如服务不健康，执行重启（根据部署方式）
# Docker Compose:
docker compose restart prompt-system

# Kubernetes:
kubectl rollout restart deployment/prompt-system -n athena

# 4. 清理缓存并复位指标
curl -X POST ${HOST}/api/v1/prompt-system/cache/clear
curl -X POST ${HOST}/api/v1/prompt-system/monitoring/metrics/reset
```

### 4.2 联系清单

| 角色 | 联系人 | 职责 |
|---|---|---|
| 测试负责人 | 待填写 | 压测执行、结果分析 |
| 研发负责人 | 待填写 | 代码问题定位、修复 |
| 运维 / SRE | 待填写 | 基础设施、告警、扩容 |
| LLM 后端负责人 | 待填写 | 模型服务、队列、Token 配额 |

---

## 五、附录

### 5.1 快速执行命令

```bash
# 一键执行 10 用户基线压测
./scripts/run_load_test.sh http://localhost:8000 10 5m

# 一键执行 50 用户基线压测
./scripts/run_load_test.sh http://localhost:8000 50 10m

# 一键执行 100 用户基线压测
./scripts/run_load_test.sh http://localhost:8000 100 10m

# 性能分析（cProfile）
python3 scripts/profile_generate_prompt.py
```

### 5.2 常用诊断命令

```bash
# 服务健康检查
curl -s http://localhost:8000/api/v1/prompt-system/health | jq .

# 扩展健康检查
curl -s http://localhost:8000/api/v1/prompt-system/health/extended | jq .

# 性能快照
curl -s http://localhost:8000/api/v1/prompt-system/monitoring/performance | jq .

# 缓存统计
curl -s http://localhost:8000/api/v1/prompt-system/cache/stats | jq .

# Prometheus 指标（纯文本格式，可直接被 Prometheus 抓取）
curl -s "http://localhost:8000/api/v1/prompt-system/metrics?format=prometheus"

# 清理缓存
curl -X POST http://localhost:8000/api/v1/prompt-system/cache/clear

# 重置指标
curl -X POST http://localhost:8000/api/v1/prompt-system/monitoring/metrics/reset
```

### 5.3 缓存优化建议

基于 `reports/performance_profile.txt` 的 cProfile 分析与代码路径审查，当前缓存机制存在以下优化空间：

#### A. 当前缓存机制分析

| 缓存层级 | 实现 | 命中率 | TTL | 瓶颈 |
|---|---|---|---|---|
| 提示词模板缓存 (`PromptTemplateCache`) | 内存 LRU + SHA256 键 | 中等 | 3600s | 键计算涉及全量变量 JSON 序列化 |
| 意图识别结果 | 无 | — | — | 每次请求重复 BGE-M3 编码 |
| 规则检索结果 | 无 | — | — | 每次请求重复 Neo4j Cypher 查询 |

#### B. 预加载高频提示词策略

**目标**：服务启动后 30 秒内将缓存命中率提升至 >85%。

**实施步骤**：

1. **定义高频组合清单**
   ```yaml
   # config/prompt_fusion_rollout.yaml 中增加 preload_rules 字段
   preload_rules:
     - domain: patent
       task_type: office_action
       phase: examination
     - domain: patent
       task_type: creativity_analysis
       phase: examination
     - domain: patent
       task_type: novelty_analysis
       phase: examination
   ```

2. **启动预加载脚本**
   ```python
   # 在 prompt_system_routes.py 或独立启动脚本中
   def _preload_hot_prompts():
       cache = get_prompt_cache()
       for rule in PRELOAD_RULES:
           # 使用典型变量构造缓存键并预生成提示词
           system_prompt, user_prompt = generate_for_rule(rule, TYPICAL_VARIABLES)
           cache.set(..., system_prompt=system_prompt, user_prompt=user_prompt)
   ```

3. **预热验证**
   ```bash
   curl -s http://localhost:8000/api/v1/prompt-system/cache/stats | jq '.hit_rate'
   # 预期：启动后立即 >80%
   ```

#### C. 其他优化建议

- **意图识别缓存**：对 `user_input` 做 SHA256 哈希，缓存 `ScenarioIdentifierOptimized` 输出（TTL 600s）。
- **规则缓存**：对 `domain+task_type` 组合缓存 `ScenarioRule` 对象（TTL 300s），避免重复 Neo4j 查询。
- **变量治理缓存**：对同一 `rule_id` 的 schema 做启动时预编译，避免每次请求重新构造 `VariableSpec` 列表。

### 5.4 判停标准（Success / Stop Criteria）

| 场景 | 判停标准 | 后续动作 |
|---|---|---|
| **成功完成** | 所有并发阶梯均通过，无红色阈值触发 | 归档报告，更新基线文档 |
| **黄色警告** | 某项指标触及黄色阈值，但未持续恶化 | 记录观察日志，继续压测但提高采样频率 |
| **红色熔断** | 任意指标触及红色阈值 | 立即停止 locust，保留现场，进入应急响应 |
| **渐进式降级** | P95/P99 随时间线性上升，错误率缓慢增长 | 提前终止当前阶梯，记录拐点并发数 |

### 5.5 修订记录

| 日期 | 版本 | 修订内容 | 修订人 |
|---|---|---|---|
| 2026-04-23 | v1.0 | 初始版本 | Agent-QA |
| 2026-04-23 | v1.1 | 补充实际执行步骤、判停标准、Prometheus 指标采集、缓存优化建议 | Agent-PerfObs |
