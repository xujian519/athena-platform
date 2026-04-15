# Athena API Gateway 可观测性系统

> 基于OpenTelemetry、Prometheus、Jaeger和Grafana的企业级可观测性解决方案

**版本**: 1.0.0
**更新时间**: 2026-02-20

## 📋 目录

- [🎯 系统概述](#-系统概述)
- [🏗️ 架构设计](#️-架构设计)
- [📊 监控指标](#-监控指标)
- [🔍 分布式追踪](#-分布式追踪)
- [🚨 告警配置](#-告警配置)
- [📈 可视化仪表板](#-可视化仪表板)
- [🚀 快速启动](#-快速启动)
- [⚙️ 配置说明](#️-配置说明)
- [🔧 运维指南](#-运维指南)

---

## 🎯 系统概述

Athena API Gateway可观测性系统提供全方位的监控、追踪和分析能力，包括：

### 核心能力
- **📊 实时监控**: 基于Prometheus的多维度指标收集
- **🔍 分布式追踪**: OpenTelemetry + Jaeger的端到端追踪
- **📈 可视化分析**: Grafana仪表板的直观数据展示
- **🚨 智能告警**: 基于阈值的自动化告警机制
- **📋 性能分析**: 详细的性能指标和趋势分析

### 技术栈
- **指标收集**: Prometheus
- **分布式追踪**: OpenTelemetry + Jaeger
- **数据可视化**: Grafana
- **告警管理**: AlertManager
- **容器化**: Docker + Docker Compose

---

## 🏗️ 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Athena API Gateway                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │ HTTP请求处理 │ │ 追踪中间件   │ │ 指标收集中间件       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    可观测性数据流                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   指标数据   │ │   追踪数据   │ │     日志数据         │   │
│  │   Prometheus │ │   Jaeger    │ │     结构化日志       │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据存储与分析                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │  Grafana    │ │ AlertManager│ │    性能分析报告      │   │
│  │  仪表板     │ │   告警系统   │ │                     │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 数据流设计

1. **请求处理流程**
   ```
   HTTP请求 → 追踪中间件 → 指标收集中间件 → 业务处理 → 响应
   ```

2. **数据收集流程**
   ```
   Gateway → OpenTelemetry → Jaeger
   Gateway → Prometheus → Grafana
   Gateway → 结构化日志 → 日志聚合
   ```

3. **告警流程**
   ```
   Prometheus → AlertManager → 通知渠道 → 运维团队
   ```

---

## 📊 监控指标

### HTTP指标

| 指标名称 | 类型 | 标签 | 描述 |
|---------|------|------|------|
| `athena_gateway_http_requests_total` | Counter | method, path, status, service, user_agent | HTTP请求总数 |
| `athena_gateway_http_request_duration_seconds` | Histogram | method, path, service | 请求持续时间 |
| `athena_gateway_http_request_size_bytes` | Histogram | method, path | 请求大小 |
| `athena_gateway_http_response_size_bytes` | Histogram | method, path, status | 响应大小 |
| `athena_gateway_http_errors_total` | Counter | method, path, status, error_type | 错误总数 |

### 认证指标

| 指标名称 | 类型 | 标签 | 描述 |
|---------|------|------|------|
| `athena_gateway_auth_requests_total` | Counter | status, auth_type, user_type | 认证请求总数 |
| `athena_gateway_auth_duration_seconds` | Histogram | auth_type | 认证处理时间 |

### 代理指标

| 指标名称 | 类型 | 标签 | 描述 |
|---------|------|------|------|
| `athena_gateway_proxy_requests_total` | Counter | service, method, status | 代理请求总数 |
| `athena_gateway_proxy_duration_seconds` | Histogram | service, method | 代理请求时间 |
| `athena_gateway_proxy_retries_total` | Counter | service, reason | 代理重试次数 |

### 系统指标

| 指标名称 | 类型 | 标签 | 描述 |
|---------|------|------|------|
| `athena_gateway_go_goroutines` | Gauge | - | Goroutine数量 |
| `athena_gateway_go_memory_bytes` | Gauge | type | 内存使用量 |
| `athena_gateway_go_gc_duration_seconds` | Histogram | gc_type | GC持续时间 |

### 熔断器指标

| 指标名称 | 类型 | 标签 | 描述 |
|---------|------|------|------|
| `athena_gateway_circuitbreaker_state` | Gauge | service, breaker_name | 熔断器状态 |

---

## 🔍 分布式追踪

### OpenTelemetry配置

```yaml
monitoring:
  tracing:
    enabled: true
    service_name: "athena-gateway"
    service_version: "1.0.0"
    environment: "development"
    jaeger:
      endpoint: "http://jaeger:14268/api/traces"
      insecure: true
    sampling:
      type: "probabilistic"
      param: 0.1  # 10% 采样率
```

### 追踪中间件

自动为每个HTTP请求创建span，包含：
- 请求方法、路径、状态码
- 请求/响应大小
- 处理时间
- 错误信息（如果有）
- 服务标识

### 追踪上下文传播

支持向下游服务传播追踪上下文：
- W3C Trace Context格式
- Baggage支持
- 跨服务链路追踪

---

## 🚨 告警配置

### 告警规则

#### 业务告警

1. **高错误率告警**
   ```yaml
   - alert: HighErrorRate
     expr: rate(athena_gateway_http_errors_total[5m]) > 0.05
     for: 5m
     severity: critical
   ```

2. **高延迟告警**
   ```yaml
   - alert: HighLatency
     expr: histogram_quantile(0.99, rate(athena_gateway_http_request_duration_seconds_bucket[5m])) > 2.0
     for: 5m
     severity: warning
   ```

#### 系统告警

1. **高内存使用**
   ```yaml
   - alert: HighMemoryUsage
     expr: athena_gateway_go_memory_bytes{type="heap"} / 1024 / 1024 > 512
     for: 10m
     severity: warning
   ```

2. **服务不可用**
   ```yaml
   - alert: GatewayDown
     expr: up{job="athena-gateway"} == 0
     for: 1m
     severity: critical
   ```

### 告警通知

支持多种通知渠道：
- 邮件通知
- Slack集成
- 钉钉机器人
- Webhook自定义

---

## 📈 可视化仪表板

### Grafana仪表板

#### 1. Gateway Overview仪表板

包含面板：
- **请求速率**: 实时QPS监控
- **响应时间**: P50, P95, P99延迟分布
- **错误率**: 各类错误统计
- **状态码分布**: 饼图展示
- **内存使用**: 堆内存、栈内存监控
- **Goroutine数量**: 实时监控

#### 2. Performance Analysis仪表板

包含面板：
- **慢请求分析**: 基于百分位的延迟分析
- **错误趋势**: 错误率变化趋势
- **吞吐量分析**: 峰值和平均值统计
- **资源使用率**: CPU、内存使用趋势

#### 3. Service Dependency仪表板

包含面板：
- **下游服务延迟**: 各服务响应时间
- **熔断器状态**: 实时熔断器状态
- **重试统计**: 重试次数和成功率
- **服务健康度**: 综合健康评分

---

## 🚀 快速启动

### 使用Docker Compose启动

```bash
# 1. 克隆项目
git clone https://github.com/athena-workspace/core/gateway.git
cd gateway

# 2. 启动完整可观测性环境
docker-compose -f docker-compose.observability.yml up -d

# 3. 查看服务状态
docker-compose -f docker-compose.observability.yml ps
```

### 访问地址

| 服务 | 地址 | 描述 |
|------|------|------|
| Gateway | http://localhost:8080 | API网关主服务 |
| Prometheus | http://localhost:9090 | 指标查询 |
| Grafana | http://localhost:3000 | 可视化仪表板 |
| Jaeger | http://localhost:16686 | 分布式追踪 |
| Redis | localhost:6379 | 缓存服务 |

### 默认凭据

- **Grafana**: admin / admin
- **Redis**: 无密码（开发环境）

---

## ⚙️ 配置说明

### 环境变量配置

```bash
# 服务配置
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8080

# 追踪配置
TRACING_ENABLED=true
TRACING_SERVICE_NAME=athena-gateway
TRACING_JAEGER_ENDPOINT=http://jaeger:14268/api/traces
TRACING_SAMPLE_RATE=0.1

# 指标配置
METRICS_ENABLED=true
METRICS_PATH=/metrics

# 日志配置
LOG_LEVEL=info
LOG_FORMAT=json
```

### 完整配置示例

参考 `configs/config.observability.yaml` 文件，包含：
- 服务器配置
- Redis配置
- 认证配置
- 代理配置
- 监控配置
- 安全配置

---

## 🔧 运维指南

### 性能调优

1. **指标收集优化**
   ```yaml
   # 适当调整采样率
   monitoring:
     tracing:
       sampling:
         param: 0.05  # 生产环境建议5%采样率
   ```

2. **内存使用优化**
   ```yaml
   # 调整批处理大小
   tracing:
     batch_timeout: "10s"
     max_export_batch_size: 1024
   ```

### 故障排查

1. **服务不可用**
   ```bash
   # 检查服务状态
   curl http://localhost:8080/health
   
   # 查看日志
   docker-compose logs gateway
   ```

2. **指标缺失**
   ```bash
   # 检查指标端点
   curl http://localhost:8080/metrics
   
   # 验证Prometheus配置
   curl http://localhost:9090/api/v1/targets
   ```

3. **追踪数据缺失**
   ```bash
   # 检查Jaeger服务
   curl http://localhost:16686/api/services
   
   # 验证追踪配置
   docker-compose logs jaeger
   ```

### 监控最佳实践

1. **设置合理阈值**
   - 错误率 < 5%
   - P99延迟 < 2秒
   - 内存使用 < 80%

2. **配置分级告警**
   - Critical: 服务不可用
   - Warning: 性能下降
   - Info: 业务指标异常

3. **定期维护**
   - 清理历史数据
   - 更新仪表板
   - 优化告警规则

---

## 📚 相关文档

- [OpenTelemetry官方文档](https://opentelemetry.io/docs/)
- [Prometheus配置指南](https://prometheus.io/docs/prometheus/latest/configuration/)
- [Grafana仪表板配置](https://grafana.com/docs/grafana/latest/dashboards/)
- [Jaeger使用指南](https://www.jaegertracing.io/docs/)

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进可观测性系统：

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 发起Pull Request

---

**🔗 Athena API Gateway - 企业级可观测性，让系统运行尽在掌握！**