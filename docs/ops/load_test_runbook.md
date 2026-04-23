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

### 1.3 告警与通知

| # | 检查项 | 操作 | 通过标准 |
|---|---|---|---|
| 11 | 生产告警静默 | 在告警平台创建静默规则（Maintenance Window） | 压测期间不触发 P1/P2 告警 |
| 12 | 相关人员通知 | 在团队频道发送压测预告 | 研发、运维、业务方已周知 |
| 13 | 压测时间窗口 | 确认非业务高峰期 | 避开 09:00-11:00、14:00-16:00 |

### 1.4 预检查 Checklist 签字

- [ ] 环境检查全部通过
- [ ] 数据与状态检查全部通过
- [ ] 告警静默已生效
- [ ] 团队通知已发送
- [ ] 回滚方案已确认

---

## 二、压测中观察（Observation）

### 2.1 实时指标 Dashboard

压测启动后，持续观察以下数据源：

| 数据源 | 地址 / 命令 | 关注指标 |
|---|---|---|
| Locust Web UI | `http://localhost:8089` | RPS、Failures、Response Time |
| 服务性能快照 | `curl ${HOST}/api/v1/prompt-system/monitoring/performance` | P95、P99、请求总量 |
| 缓存统计 | `curl ${HOST}/api/v1/prompt-system/cache/stats` | hit_rate、current_size |
| 容器/主机监控 | Grafana / Prometheus / `htop` | CPU、内存、网络 IO、磁盘 IO |
| 数据库监控 | Neo4j Browser / pgAdmin / Redis CLI | 连接数、慢查询、缓存命中率 |
| LLM 后端监控 | LLM 服务 Dashboard | 队列长度、Token 吞吐量、错误率 |

### 2.2 日志观察

```bash
# 实时跟踪服务端错误日志（根据实际部署调整）
tail -f /var/log/athena/prompt-system.log | grep -E "ERROR|WARN|❌|⚠️"

# 观察 5xx 错误
tail -f /var/log/athena/prompt-system.log | grep "status_code=5"

# 观察慢请求（>5s）
tail -f /var/log/athena/prompt-system.log | grep -E "processing_time_ms":[5-9][0-9]{3,}
```

### 2.3 关键阈值与熔断决策

| 指标 | 黄色警告 | 红色熔断 | 熔断动作 |
|---|---|---|---|
| 错误率 | ≥ 1% | ≥ 5% | 立即停止压测，保留现场 |
| P99 延迟 | ≥ 10s | ≥ 30s | 降级并发或停止压测 |
| CPU 使用率 | ≥ 70% | ≥ 90% | 观察是否持续 2min，是则停止 |
| 内存使用 | ≥ 80% | ≥ 95% | 立即停止，防止 OOM |
| LLM 队列深度 | ≥ 20 | ≥ 50 | 停止压测，通知 LLM 运维 |
| 数据库连接数 | ≥ 80% 上限 | ≥ 95% 上限 | 停止压测，检查连接泄漏 |

> **熔断原则**：一旦触及红色阈值，优先停止压测，保护生产环境，事后分析日志定位根因。

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
| 7 | 收集报告文件 | 将 `reports/load/` 下本次压测的 CSV + HTML 复制到归档目录 |
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

# 清理缓存
curl -X POST http://localhost:8000/api/v1/prompt-system/cache/clear

# 重置指标
curl -X POST http://localhost:8000/api/v1/prompt-system/monitoring/metrics/reset
```

### 5.3 修订记录

| 日期 | 版本 | 修订内容 | 修订人 |
|---|---|---|---|
| 2026-04-23 | v1.0 | 初始版本 | Agent-QA |
