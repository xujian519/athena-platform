# 认知与决策模块监控系统使用指南

## 📊 系统概述

本监控系统为Athena平台认知与决策模块提供完整的监控、告警和可视化解决方案。

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     应用层 (Application)                         │
│  认知模块 | 决策模块 | 超级推理 | Agent协作 | 记忆系统            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ├─> 指标导出器 (Port 9100)
                            │   core/monitoring/cognitive_metrics_exporter.py
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│              监控层 (Monitoring Stack)                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Prometheus  │  │   Grafana    │  │ Alertmanager │         │
│  │   :9090      │  │   :3000      │  │   :9093      │         │
│  │  时序数据库   │  │  可视化      │  │  告警管理    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 代码质量修复

执行代码质量修复脚本：

```bash
python3 scripts/fix_cognitive_decision_quality.py --all
```

**修复内容**：
- 移除重复的except块
- 修复空的except块
- 修复除零风险
- 添加缺失的导入
- 修复逻辑错误

### 2. 启动指标导出器

在终端运行：

```bash
python3 core/monitoring/cognitive_metrics_exporter.py
```

**验证指标导出**：
```bash
curl http://localhost:9100/metrics
```

### 3. 启动监控栈

**方式一：使用一键启动脚本（推荐）**

```bash
./scripts/start_monitoring_stack.sh
```

**方式二：手动启动**

```bash
cd config/docker
docker-compose -f docker-compose.monitoring-stack.yml up -d
```

### 4. 访问监控界面

| 服务 | URL | 凭据 |
|------|-----|------|
| Prometheus | http://localhost:9090 | 无需认证 |
| Grafana | http://localhost:3000 | admin/admin |
| Alertmanager | http://localhost:9093 | 无需认证 |
| 指标导出器 | http://localhost:9100/metrics | 无需认证 |

---

## 📈 Grafana仪表板

### 自动导入

使用Docker Compose启动的Grafana会自动导入仪表板：

1. 登录Grafana (http://localhost:3000)
2. 导航到 Dashboards → Athena
3. 打开 "Athena 认知与决策模块监控仪表板"

### 手动导入

如果需要手动导入：

```bash
python3 scripts/import_grafana_dashboard.py --manual
```

或使用Grafana Web UI：
1. 登录Grafana
2. 点击 "+" → "Import"
3. 上传文件: `config/monitoring/grafana/cognitive_decision_dashboard.json`

### 仪表板面板

仪表板包含10个核心监控面板：

| # | 面板名称 | 指标说明 |
|---|----------|----------|
| 1 | 认知与决策处理延迟 (P95) | 95分位延迟，显示性能瓶颈 |
| 2 | 代码覆盖率 | 各模块测试覆盖率 |
| 3 | 技术债务分布 | 按严重程度分类的技术债务 |
| 4 | 请求速率 (QPS) | 每秒请求数 |
| 5 | 错误率趋势 | 各模块错误率变化 |
| 6 | 语法错误状态 | 当前语法错误数量 |
| 7 | Agent任务队列 | 任务队列长度 |
| 8 | 内存使用趋势 | 超级推理引擎内存占用 |
| 9 | LLM响应延迟 | LLM API调用延迟 |
| 10 | 记忆缓存命中率 | 缓存系统效率 |

---

## 🚨 告警规则

### 告警规则组

系统包含7个告警规则组，共20+条告警规则：

#### 1. 认知模块告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| HighCognitiveLatency | Warning | P95延迟 > 5秒 |
| CriticalCognitiveLatency | Critical | P95延迟 > 30秒 |
| HighCognitiveConfidence | Warning | 置信度 > 95% |

#### 2. 决策模块告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| HighDecisionErrorRate | Warning | 错误率 > 5% |
| CriticalDecisionErrorRate | Critical | 错误率 > 15% |
| DecisionQueueBacklog | Warning | 队列长度 > 100 |

#### 3. 超级推理引擎告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| SuperReasoningHighMemory | Warning | 内存 > 1GB |
| SuperReasoningTimeout | Warning | 推理时间 > 5分钟 |

#### 4. LLM集成告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| HighLLMLatency | Warning | P95延迟 > 60秒 |
| LLMHighFailureRate | Critical | 失败率 > 10% |
| HighTokenUsage | Warning | Token速率 > 10000/秒 |

#### 5. Agent协作告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| AgentTaskBacklog | Warning | 队列长度 > 50 |
| AgentFailureRate | Warning | 失败率 > 10% |
| AgentTimeoutRate | Warning | 超时率 > 5% |

#### 6. 记忆系统告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| MemoryCacheLowHit | Warning | 命中率 < 70% |
| VectorSearchHighLatency | Warning | P95延迟 > 2秒 |

#### 7. 质量门禁告警

| 告警名称 | 严重级别 | 触发条件 |
|----------|----------|----------|
| TechnicalDebtHigh | Warning | 技术债务 > 50个 |
| TestCoverageLow | Warning | 覆盖率 < 70% |
| SyntaxErrorsPresent | Critical | 存在语法错误 |

### 配置告警通知

编辑 `config/docker/alertmanager.yml` 配置邮件或Webhook通知：

```yaml
receivers:
  - name: 'critical-alerts'
    email_configs:
      - to: 'your-email@example.com'
        from: 'alertmanager@athena-platform.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

---

## 📊 Prometheus指标

### 核心指标

#### 认知模块指标

```promql
# 认知处理延迟
cognitive_processing_duration_seconds

# 认知请求总数
cognitive_requests_total

# 认知错误总数
cognitive_errors_total

# 认知置信度
cognitive_confidence
```

#### 决策模块指标

```promql
# 决策处理延迟
decision_processing_duration_seconds

# 决策请求总数
decision_requests_total

# 决策错误总数
decision_errors_total

# 决策队列长度
decision_queue_length
```

#### 超级推理指标

```promql
# 超级推理延迟
super_reasoning_duration_seconds

# 超级推理内存使用
super_reasoning_memory_bytes

# 超级推理步骤数
super_reasoning_steps_total
```

### 常用查询

#### 计算错误率

```promql
sum(rate(cognitive_errors_total[5m])) / sum(rate(cognitive_requests_total[5m]))
```

#### 计算P95延迟

```promql
histogram_quantile(0.95, rate(cognitive_processing_duration_seconds_bucket[5m]))
```

#### 计算缓存命中率

```promql
rate(memory_cache_hits_total[5m]) / (rate(memory_cache_hits_total[5m]) + rate(memory_cache_misses_total[5m]))
```

---

## 🔧 管理命令

### 查看服务状态

```bash
docker-compose -f config/docker/docker-compose.monitoring-stack.yml ps
```

### 查看日志

```bash
# 所有服务日志
docker-compose -f config/docker/docker-compose.monitoring-stack.yml logs -f

# 特定服务日志
docker-compose -f config/docker/docker-compose.monitoring-stack.yml logs -f prometheus
docker-compose -f config/docker/docker-compose.monitoring-stack.yml logs -f grafana
```

### 停止服务

```bash
docker-compose -f config/docker/docker-compose.monitoring-stack.yml down
```

### 重启服务

```bash
docker-compose -f config/docker/docker-compose.monitoring-stack.yml restart
```

### 更新配置

修改配置文件后重启服务：

```bash
# Prometheus配置
docker-compose -f config/docker/docker-compose.monitoring-stack.yml exec prometheus kill -HUP 1

# 完全重启
docker-compose -f config/docker/docker-compose.monitoring-stack.yml restart
```

---

## 🛠️ 故障排查

### 端口被占用

检查端口占用：

```bash
lsof -i :3000  # Grafana
lsof -i :9090  # Prometheus
lsof -i :9100  # 指标导出器
```

解决方案：
1. 停止占用端口的进程
2. 或修改 `docker-compose.monitoring-stack.yml` 中的端口映射

### Grafana无法连接Prometheus

检查Prometheus数据源配置：

1. 登录Grafana
2. Configuration → Data Sources → Prometheus
3. 确认URL为 `http://prometheus:9090`
4. 点击 "Save & Test"

### 仪表板无数据

检查清单：
1. ✅ 指标导出器是否运行 (http://localhost:9100/metrics)
2. ✅ Prometheus是否抓取指标 (http://localhost:9090/targets)
3. ✅ Grafana数据源是否正常
4. ✅ 仪表板时间范围是否正确

### 告警不触发

检查清单：
1. ✅ 告警规则是否加载 (http://localhost:9090/alerts)
2. ✅ 规则条件是否满足
3. ✅ Alertmanager是否运行 (http://localhost:9093)
4. ✅ 通知配置是否正确

---

## 📁 文件结构

```
Athena工作平台/
├── core/monitoring/
│   └── cognitive_metrics_exporter.py    # 指标导出器
├── config/
│   ├── docker/
│   │   ├── docker-compose.monitoring-stack.yml  # 监控栈配置
│   │   ├── alertmanager.yml                      # Alertmanager配置
│   │   ├── grafana/
│   │   │   ├── provisioning/
│   │   │   │   ├── datasources/prometheus.yml    # 数据源配置
│   │   │   │   └── dashboards/dashboard.yml      # 仪表板配置
│   │   │   └── dashboards/
│   │   │       └── cognitive_decision_dashboard.json
│   │   └── prometheus/
│   │       └── cognitive_decision_alerts.yml     # 告警规则
│   └── monitoring/
│       ├── prometheus.yml                        # Prometheus主配置
│       └── grafana/
│           └── cognitive_decision_dashboard.json # 仪表板JSON
├── scripts/
│   ├── fix_cognitive_decision_quality.py        # 代码质量修复
│   ├── import_grafana_dashboard.py              # 仪表板导入工具
│   └── start_monitoring_stack.sh                # 监控栈启动脚本
└── docs/quality/
    └── cognitive_decision_monitoring_guide.md   # 本文档
```

---

## 🎯 最佳实践

### 1. 定期检查监控

建议每周检查一次：
- 仪表板中的异常指标
- 告警历史记录
- 系统性能趋势

### 2. 及时处理告警

告警处理优先级：
1. **Critical**: 立即处理（如语法错误、严重错误率）
2. **Warning**: 当天处理（如性能下降、资源不足）

### 3. 持续优化阈值

根据实际情况调整告警阈值，避免误报和漏报。

### 4. 定期备份数据

Prometheus数据备份：

```bash
docker cp athena-prometheus:/prometheus ./prometheus-backup
```

Grafana配置备份：

```bash
docker cp athena-grafana:/var/lib/grafana ./grafana-backup
```

---

## 📞 支持与反馈

如有问题或建议，请联系：
- 项目仓库: [Athena工作平台](https://github.com/your-repo)
- 邮件: xujian519@gmail.com

---

*文档版本: v1.0*
*更新日期: 2026-01-25*
*Athena Platform Team*
