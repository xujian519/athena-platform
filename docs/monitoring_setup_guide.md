# Athena Gateway监控告警系统配置指南

> **文档版本**: v1.0
> **编制日期**: 2026-04-18
> **适用范围**: Athena统一网关 (gateway-unified)
> **维护者**: 徐健 (xujian519@gmail.com)

---

## 目录

- [系统架构](#系统架构)
- [Prometheus配置](#prometheus配置)
- [Grafana仪表板](#grafana仪表板)
- [Alertmanager告警](#alertmanager告警)
- [链路追踪](#链路追踪)
- [验证清单](#验证清单)

---

## 系统架构

Athena统一网关监控告警系统采用四层架构：

```
┌─────────────────────────────────────────────────────────────┐
│                    Athena Gateway (8005)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │   指标收集层                                            │  │
│  │   - Prometheus Counter/Histogram/Gauge               │  │
│  │   - OpenTelemetry Tracer                             │  │
│  │   - JSON结构化日志                                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────┴────┐         ┌─────┴─────┐        ┌────┴────┐
    ↓         ↓         ↓           ↓        ↓         ↓
 Prometheus  Grafana  Alertmanager  Jaeger  日志聚合器  OTel Collector
  (9090)    (3000)    (9093)      (16686)  (可选)      (4318)
```

---

## Prometheus配置

### 1. 配置文件位置

- **主配置**: `gateway-unified/configs/prometheus/prometheus.yml`
- **告警规则**: `gateway-unified/configs/prometheus/alerts/athena_alerts.yml`

### 2. Prometheus主配置

创建 `prometheus.yml`:

```yaml
# Prometheus全局配置
global:
  scrape_interval: 15s        # 抓取间隔
  evaluation_interval: 15s    # 规则评估间隔
  external_labels:
    cluster: 'athena-gateway'
    environment: 'production'

# 告警管理器配置
alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - 'localhost:9093'

# 告警规则文件
rule_files:
  - 'alerts/athena_alerts.yml'

# 抓取目标配置
scrape_configs:
  # 网关主服务指标
  - job_name: 'gateway-unified'
    static_configs:
      - targets: ['localhost:8005']
        labels:
          service: 'gateway-unified'
          component: 'core'

  # 监控服务器指标 (Prometheus metrics端点)
  - job_name: 'gateway-monitoring'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'gateway-monitoring'
          component: 'metrics'

  # MCP服务器指标
  - job_name: 'mcp_servers'
    static_configs:
      - targets: ['localhost:3003']  # 本地搜索引擎
        labels:
          service: 'local-search-engine'
      - targets: ['localhost:7860']  # Mineru解析器
        labels:
          service: 'mineru-parser'

  # 知识图谱服务 (Neo4j metrics)
  - job_name: 'knowledge-graph'
    static_configs:
      - targets: ['localhost:8100']
        labels:
          service: 'knowledge-graph'

  # 向量数据库 (Qdrant metrics)
  - job_name: 'vector-db'
    static_configs:
      - targets: ['localhost:6333']
        labels:
          service: 'qdrant'
```

### 3. 启动Prometheus

**方法1: Docker (推荐)**

```bash
# 创建Prometheus配置目录
mkdir -p /Users/xujian/Athena工作平台/monitoring/prometheus

# 复制配置文件
cp gateway-unified/configs/prometheus/prometheus.yml \
   /Users/xujian/Athena工作平台/monitoring/prometheus/

# 启动Prometheus
docker run -d \
  --name prometheus \
  --network host \
  -v /Users/xujian/Athena工作平台/monitoring/prometheus:/etc/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --web.listen-address=:9090
```

**方法2: 二进制安装**

```bash
# 下载Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.darwin-amd64.tar.gz
tar xvfz prometheus-2.45.0.darwin-amd64.tar.gz

# 启动
cd prometheus-2.45.0.darwin-amd64
./prometheus --config.file=gateway-unified/configs/prometheus/prometheus.yml
```

### 4. 验证Prometheus指标

```bash
# 检查Prometheus UI
open http://localhost:9090

# 查询指标
curl http://localhost:9090/api/v1/query?query=up

# 查看网关指标
curl http://localhost:9090/api/v1/query?query=athena_gateway_proxy_requests_total

# 验证告警规则
promtool check rules gateway-unified/configs/prometheus/alerts/athena_alerts.yml
```

---

## Grafana仪表板

### 1. 安装Grafana

**Docker方式 (推荐)**

```bash
docker run -d \
  --name grafana \
  --network host \
  -e GF_SECURITY_ADMIN_PASSWORD=admin123 \
  grafana/grafana:latest
```

**访问Grafana**: http://localhost:3000 (admin/admin123)

### 2. 添加Prometheus数据源

1. 登录Grafana
2. 导航: **Configuration** → **Data Sources** → **Add data source**
3. 选择 **Prometheus**
4. 配置:
   - **Name**: Prometheus
   - **URL**: http://localhost:9090
   - **Access**: Server (default)
5. 点击 **Save & Test**

### 3. 导入Athena网关仪表板

**方法1: 通过JSON文件导入**

1. 导航: **Create** → **Import**
2. 点击 **Upload JSON file**
3. 选择 `gateway-unified/configs/grafana/dashboards/athena_gateway_dashboard.json`
4. 选择 **Prometheus** 数据源
5. 点击 **Import**

**方法2: 通过导入ID** (如果已发布到Grafana.com)

```bash
# 导航: Create → Import
# 输入仪表板ID: <待发布>
# 点击 Load
```

### 4. 仪表板面板说明

| 面板名称 | 指标 | 说明 |
|---------|------|------|
| 总请求QPS | `rate(athena_gateway_proxy_requests_total[1m])` | 每秒请求数 |
| 错误率趋势 | `rate(errors) / rate(requests)` | 5xx错误率百分比 |
| P50/P95/P99延迟 | `histogram_quantile(...)` | 延迟百分位数 |
| 路由分布 | `sum by (service) (rate(...))` | 各服务请求占比 |
| 向量搜索延迟 | `histogram_quantile(0.95, ...{service="vector-search"})` | 向量搜索P95延迟 |
| KG查询延迟 | `histogram_quantile(0.95, ...{service="knowledge-graph"})` | 知识图谱P95延迟 |
| RAG命中率 | `hits / (hits + misses)` | 缓存命中率 |
| 工具调用次数 | `sum by (service) (rate(...{service=~"tool.*|mcp.*"}))` | 工具调用频率 |
| MCP服务器状态 | `up{job="mcp_servers"}` | MCP服务器在线状态 |
| 熔断器状态 | `count(circuitbreaker_state{state="open"})` | 打开的熔断器数量 |
| 缓存命中率 | `hits / (hits + misses)` | 缓存命中率百分比 |
| 限流触发次数 | `rate(ratelimit_checks_total{status="rejected"})` | 每秒限流拒绝数 |

---

## Alertmanager告警

### 1. 安装Alertmanager

```bash
docker run -d \
  --name alertmanager \
  --network host \
  -v /Users/xujian/Athena工作平台/monitoring/alertmanager:/etc/alertmanager \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml
```

### 2. 配置Alertmanager

创建 `alertmanager.yml`:

```yaml
# 全局配置
global:
  resolve_timeout: 5m

# 告警路由配置
route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  # 子路由
  routes:
    # 关键告警 → 钉钉/Slack
    - match:
        severity: critical
      receiver: 'critical-alerts'
      continue: true

    # 警告告警 → 邮件
    - match:
        severity: warning
      receiver: 'warning-alerts'

# 接收者配置
receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'  # 自定义Webhook

  - name: 'critical-alerts'
    # 钉钉告警
    webhook_configs:
      - url: 'YOUR_DINGTALK_WEBHOOK_URL'
        send_resolved: true

  - name: 'warning-alerts'
    # 邮件告警
    email_configs:
      - to: 'xujian519@gmail.com'
        from: 'alertmanager@athena-gateway.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'YOUR_EMAIL'
        auth_password: 'YOUR_PASSWORD'

# 抑制规则
inhibit_rules:
  # 如果网关已下线，抑制其他所有告警
  - source_match:
      alertname: 'GatewayDown'
    target_match_re:
      alertname: '.*'
    equal: ['instance']
```

### 3. 测试告警规则

```bash
# 验证告警规则语法
promtool check rules gateway-unified/configs/prometheus/alerts/athena_alerts.yml

# 查看当前活跃告警
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# 手动触发测试告警（修改规则临时降低阈值）
# 编辑 athena_alerts.yml，将 GatewayHighErrorRate 阈值改为 0.001
# 重启Prometheus后等待2分钟观察告警
```

---

## 链路追踪

### 1. 安装Jaeger

```bash
# 使用Docker快速启动Jaeger All-in-One
docker run -d \
  --name jaeger \
  --network host \
  -e COLLECTOR_OTLP_ENABLED=true \
  jaegertracing/all-in-one:latest
```

**访问Jaeger UI**: http://localhost:16686

### 2. 配置OpenTelemetry Collector (可选)

如果需要使用OTel Collector而非直连Jaeger：

```yaml
# otel-collector-config.yaml
receivers:
  otlp:
    protocols:
      http:
        endpoint: 0.0.0.0:4318
      grpc:
        endpoint: 0.0.0.0:4317

processors:
  batch:

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger]
```

启动OTel Collector:

```bash
docker run -d \
  --name otel-collector \
  --network host \
  -v /path/to/otel-collector-config.yaml:/etc/otel-collector/config.yaml \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector/config.yaml
```

### 3. 验证链路追踪

```bash
# 检查Jaeger UI
open http://localhost:16686

# 查询Trace
# 在Jaeger UI中选择服务 "gateway-unified"
# 点击 "Find Traces" 查看最近追踪

# 验证Trace上下文传递
curl -v http://localhost:8005/api/v1/kg/query \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' \
  2>&1 | grep -i "traceparent"
```

### 4. 查看Trace示例

在Jaeger UI中，一个典型的请求Trace结构：

```
[POST /api/v1/kg/query]
  │
  ├─ [Auth Span] 认证检查 (2ms)
  ├─ [Route Span] 路由匹配 (1ms)
  ├─ [Proxy Span] 反向代理 (45ms)
  │   ├─ [LB Span] 负载均衡选择 (1ms)
  │   ├─ [CB Span] 熔断器检查 (1ms)
  │   └─ [HTTP Span] 后端请求 (40ms)
  │       ├─ [Embed Span] 向量化 (15ms)
  │       ├─ [Search Span] 向量搜索 (20ms)
  │       └─ [KG Span] 知识图谱查询 (5ms)
  └─ [Cache Span] 缓存写入 (2ms)
```

---

## 验证清单

### 1. Prometheus验证

- [ ] Prometheus服务正常运行 (http://localhost:9090)
- [ ] 网关指标端点可访问 (http://localhost:9090/metrics)
- [ ] 所有scrape目标状态为UP
- [ ] 告警规则加载成功 (`promtool check rules` 通过)
- [ ] 查询 `athena_gateway_proxy_requests_total` 有数据

### 2. Grafana验证

- [ ] Grafana服务正常运行 (http://localhost:3000)
- [ ] Prometheus数据源连接成功
- [ ] Athena网关仪表板导入成功
- [ ] 所有面板正常显示数据（非"No Data"）
- [ ] 仪表板自动刷新 (默认5秒)

### 3. Alertmanager验证

- [ ] Alertmanager服务正常运行 (http://localhost:9093)
- [ ] 告警规则加载到Prometheus
- [ ] 测试告警能正常触发
- [ ] 告警能正确路由到接收者
- [ ] 告警恢复后能正确发送 `resolved` 通知

### 4. 链路追踪验证

- [ ] Jaeger服务正常运行 (http://localhost:16686)
- [ ] OpenTelemetry已初始化 (查看网关启动日志)
- [ ] Trace数据成功发送到Jaeger
- [ ] 在Jaeger UI能查到Trace记录
- [ ] Trace包含完整的Span树 (认证→路由→代理→后端)

### 5. 日志验证

- [ ] 网关日志格式为JSON结构化
- [ ] 日志包含 `timestamp`, `level`, `service` 字段
- [ ] 日志包含 `trace_id`, `span_id` 字段（启用链路追踪后）
- [ ] 日志可通过 `request_id` 关联
- [ ] 敏感信息已脱敏（API Key、Token等）

---

## 故障排查

### Prometheus无数据

**症状**: Prometheus UI显示 "No data"

**排查步骤**:

1. 检查scrape目标状态:
   ```bash
   curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health, lastError}'
   ```

2. 检查网关metrics端点:
   ```bash
   curl http://localhost:9090/metrics | grep athena_gateway
   ```

3. 检查Prometheus配置:
   ```bash
   promtool check config gateway-unified/configs/prometheus/prometheus.yml
   ```

### Grafana仪表板无数据

**症状**: 导入仪表板后所有面板显示 "No Data"

**排查步骤**:

1. 验证Prometheus数据源:
   - Grafana → Configuration → Data Sources → Prometheus
   - 点击 "Test" 检查连接状态

2. 手动查询Prometheus:
   ```bash
   # 在Grafana Explore中执行
   athena_gateway_proxy_requests_total
   ```

3. 检查时间范围:
   - 确保仪表板时间范围设置为 "Last 1 hour" 或更大

### 告警未触发

**症状**: 触发条件已满足但告警未触发

**排查步骤**:

1. 检查告警规则状态:
   ```bash
   curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | select(.name=="GatewayHighErrorRate")'
   ```

2. 检查告警持续时间 (`for` 条件):
   - 告警需要持续满足条件超过 `for` 指定时间才会触发

3. 检查Alertmanager配置:
   ```bash
   curl http://localhost:9093/api/v1/status | jq '.data.config'
   ```

### 链路追踪无数据

**症状**: Jaeger UI无Trace记录

**排查步骤**:

1. 检查网关启动日志:
   ```bash
   # 查找 "OpenTelemetry初始化成功" 日志
   docker logs gateway-unified | grep OpenTelemetry
   ```

2. 检查OTLP exporter配置:
   ```go
   // 确认 collectorEndpoint 配置正确
   otlptracehttp.WithEndpoint("localhost:4318")
   ```

3. 验证Jaeger接收端点:
   ```bash
   curl http://localhost:14268/api/traces \
     -X POST -d '{}' \
     -H "Content-Type: application/json"
   ```

---

## 性能优化建议

### Prometheus优化

1. **调整抓取间隔**: 生产环境建议15s，开发环境可30s
2. **配置数据保留**:
   ```yaml
   prometheus.yml:
     storage:
      tsdb:
        retention.time: 15d  # 保留15天数据
   ```
3. **启用远程存储** (长期存储方案)

### Grafana优化

1. **仪表板刷新频率**: 关键面板5s，非关键面板30s或1m
2. **查询优化**: 避免高基数查询 (如 `by (user_id)` )
3. **使用变量**: 减少重复仪表板数量

### 告警优化

1. **告警分组**: 合理设置 `group_wait` 和 `group_interval` 避免告警风暴
2. **告警抑制**: 使用 `inhibit_rules` 避免重复告警
3. **告警静默**: 维护期间使用 `silence` 规则

---

## 附录

### A. 监控指标完整列表

详见 `gateway-unified/internal/metrics/definitions.go`

### B. 告警规则完整列表

详见 `gateway-unified/configs/prometheus/alerts/athena_alerts.yml`

### C. Grafana仪表板JSON

详见 `gateway-unified/configs/grafana/dashboards/athena_gateway_dashboard.json`

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-18
