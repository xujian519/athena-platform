# Athena平台 - 追踪数据可视化指南

> **版本**: 1.0
> **更新日期**: 2026-04-24
> **作者**: Athena平台团队

---

## 目录

1. [快速开始](#快速开始)
2. [仪表板说明](#仪表板说明)
3. [告警规则](#告警规则)
4. [常见问题](#常见问题)
5. [高级用法](#高级用法)

---

## 快速开始

### 1. 启动追踪环境

```bash
# 完整启动（包含Docker服务）
./scripts/setup_tracing_dashboard.sh

# 如果服务已在运行，仅配置Grafana
./scripts/setup_tracing_dashboard.sh --skip-start

# 仅验证服务状态
./scripts/setup_tracing_dashboard.sh --verify-only
```

### 2. 访问可视化界面

| 服务 | 地址 | 凭据 |
|------|------|------|
| **Grafana仪表板** | http://localhost:3001/d/athena-tracing-overview | admin/admin |
| **Grafana首页** | http://localhost:3001 | admin/admin |
| **Jaeger UI** | http://localhost:16686 | 无需认证 |
| **Elasticsearch** | http://localhost:9200 | 无需认证 |

### 3. 查看追踪数据

#### 方式一：Grafana仪表板（推荐）

1. 打开Grafana仪表板
2. 选择时间范围（右上角）
3. 查看各项指标趋势

#### 方式二：Jaeger UI（详细追踪）

1. 打开Jaeger UI
2. 在"Service"下拉菜单中选择服务（如`xiaona-agent`, `xiaonuo-agent`）
3. 点击"Find Traces"
4. 点击具体Trace查看完整调用链

---

## 仪表板说明

### 📊 系统概览

#### 请求量趋势 (QPS)

- **含义**: 系统每秒处理的请求数量
- **正常范围**: 根据业务量而定
- **异常判断**: 突然下降可能表示服务异常

#### 延迟分布 (P50/P95/P99)

- **P50**: 中位数延迟，50%请求的响应时间
- **P95**: 95分位延迟，仅5%请求超过此值
- **P99**: 99分位延迟，仅1%请求超过此值

**性能基准**:
- 绿色: < 100ms
- 黄色: 100-500ms
- 红色: > 500ms

#### 错误率

- **含义**: 返回错误状态码的请求比例
- **正常范围**: < 1%
- **异常判断**: 持续升高表示服务问题

### 🤖 Agent性能

#### Agent平均响应时间

显示各Agent的平均处理时间，可识别：
- 响应慢的Agent
- 性能回归问题

#### Agent请求量分布

显示各Agent的请求占比，可了解：
- 热门Agent
- 负载分布情况

### ⚙️ 操作分析

#### 最慢的操作 (Top 10)

显示耗时最长的操作，有助于：
- 识别性能瓶颈
- 优化慢查询

#### 操作频率趋势

显示各操作的调用频率变化，可发现：
- 异常调用模式
- 流量突增

---

## 告警规则

### 高延迟告警

**条件**: P95延迟 > 100ms 持续5分钟

**响应**:
1. 检查Agent负载
2. 查看慢操作列表
3. 分析数据库/LLM调用

### 高错误率告警

**条件**: 错误率 > 1% 持续5分钟

**响应**:
1. 查看错误日志
2. 检查依赖服务状态
3. 分析失败请求的Trace

### 流量突降告警

**条件**: QPS下降 > 50% 持续2分钟

**响应**:
1. 检查Gateway状态
2. 验证网络连接
3. 查看系统日志

---

## 常见问题

### Q1: Grafana无法连接数据源

**症状**: 仪表板显示"No data"

**解决方案**:
```bash
# 1. 检查服务状态
docker-compose -f docker-compose.tracing.yml ps

# 2. 检查Elasticsearch
curl http://localhost:9200/_cluster/health

# 3. 检查Jaeger
curl http://localhost:16686

# 4. 重启Grafana
docker-compose -f docker-compose.tracing.yml restart grafana
```

### Q2: 追踪数据不显示

**症状**: Jaeger/Grafana无数据

**解决方案**:
```bash
# 1. 确认应用已启动追踪
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"

# 2. 检查OTEL Collector日志
docker-compose -f docker-compose.tracing.yml logs -f otel-collector

# 3. 发送测试请求
python -c "
from core.tracing import get_tracer
tracer = get_tracer('test')
with tracer.start_as_current_span('test-span'):
    print('Test trace sent')
"
```

### Q3: Elasticsearch磁盘空间不足

**症状**: 追踪数据写入失败

**解决方案**:
```bash
# 1. 清理旧数据
curl -X DELETE "localhost:9200/otel-traces-$(date -v-7d +%Y-%m-%d)*"

# 2. 设置索引保留策略
curl -X PUT "localhost:9200/_ilm/policy/otel-traces-policy" \
  -H 'Content-Type: application/json' -d '{
  "policy": {
    "phases": {
      "hot": {"actions": {}},
      "delete": {"min_age": "7d", "actions": {"delete": {}}}
    }
  }
}'
```

---

## 高级用法

### 自定义仪表板

1. 在Grafana中点击"+" → "New dashboard"
2. 添加面板并配置查询
3. 保存并分享

### 添加告警通知

1. 进入Grafana → Alerting → Notification channels
2. 添加通知渠道（Webhook/Email/Slack）
3. 在仪表板面板中配置告警规则

### 导出追踪数据

```bash
# 导出特定时间范围的追踪
curl -X POST "localhost:16686/api/traces?service=xiaona-agent&limit=100" \
  -o traces.json

# 查询Elasticsearch
curl -X GET "localhost:9200/otel-traces-*/_search?pretty" \
  -H 'Content-Type: application/json' -d '{
  "query": {"match_all": {}},
  "size": 10
}'
```

---

## 相关文档

- [分布式追踪架构设计](../architecture/DISTRIBUTED_TRACING_ARCHITECTURE.md)
- [OpenTelemetry集成指南](../opentelemetry/INTEGRATION_GUIDE.md)
- [性能分析工具链](../performance/PERFORMANCE_ANALYSIS_TOOLCHAIN.md)

---

**更新日志**:
- 2026-04-24: 初始版本
