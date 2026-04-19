# 快速启动指南

## 🚀 一键启动可观测性环境

### 前置条件

- Docker 20.10+
- Docker Compose
- Git

### 启动步骤

```bash
# 1. 克隆项目（如果还没有）
git clone https://github.com/athena-workspace/core/gateway.git
cd gateway

# 2. 启动完整可观测性环境
docker-compose -f docker-compose.observability.yml up -d

# 3. 等待所有服务启动完成（约1-2分钟）
docker-compose -f docker-compose.observability.yml ps
```

### 服务访问地址

| 服务 | 地址 | 用户名 | 密码 | 描述 |
|------|------|--------|------|------|
| 🌐 API Gateway | http://localhost:8080 | - | - | 主要API服务 |
| 📊 Prometheus | http://localhost:9090 | - | - | 指标查询 |
| 📈 Grafana | http://localhost:3000 | admin | admin | 可视化仪表板 |
| 🔍 Jaeger | http://localhost:16686 | - | - | 分布式追踪 |

## 🧪 验证可观测性功能

### 1. 测试API网关

```bash
# 健康检查
curl http://localhost:8080/health

# 模拟API请求
curl -X GET http://localhost:8080/api/v1/users/123
curl -X POST http://localhost:8080/api/v1/orders -H "Content-Type: application/json" -d '{"test": "data"}'

# 触发错误请求
curl http://localhost:8080/nonexistent
```

### 2. 查看Prometheus指标

```bash
# 查看指标端点
curl http://localhost:8080/metrics

# 或直接访问Prometheus UI
# 打开 http://localhost:9090
# 在查询框中输入：rate(athena_gateway_http_requests_total[5m])
```

### 3. 查看Jaeger追踪

```bash
# 打开Jaeger UI
# http://localhost:16686

# 选择服务：athena-gateway
# 点击 "Find Traces" 查看追踪数据
```

### 4. 查看Grafana仪表板

```bash
# 登录Grafana
# http://localhost:3000
# 用户名：admin，密码：admin

# 导入预配置仪表板
# 左侧菜单 → Dashboards → Search → "Athena Gateway Overview"
```

## 🔧 自定义配置

### 修改采样率

编辑 `configs/config.observability.yaml`:

```yaml
monitoring:
  tracing:
    sampling:
      param: 0.05  # 改为5%采样率
```

重启服务：
```bash
docker-compose -f docker-compose.observability.yml restart gateway
```

### 添加自定义告警

编辑 `configs/alert_rules.yml`，添加新的告警规则：

```yaml
groups:
  - name: custom_alerts
    rules:
      - alert: CustomHighLatency
        expr: histogram_quantile(0.95, rate(athena_gateway_http_request_duration_seconds_bucket[5m])) > 1.0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "自定义高延迟告警"
          description: "95%延迟超过1秒"
```

重新加载Prometheus配置：
```bash
docker-compose -f docker-compose.observability.yml exec prometheus kill -HUP 1
```

## 📊 常用查询语句

### Prometheus查询

```promql
# 请求率
rate(athena_gateway_http_requests_total[5m])

# 错误率
rate(athena_gateway_http_errors_total[5m]) / rate(athena_gateway_http_requests_total[5m])

# P99延迟
histogram_quantile(0.99, rate(athena_gateway_http_request_duration_seconds_bucket[5m]))

# 内存使用
athena_gateway_go_memory_bytes{type="heap"} / 1024 / 1024
```

### Grafana仪表板变量

```json
{
  "name": "service",
  "type": "query",
  "datasource": "Prometheus",
  "query": "label_values(athena_gateway_http_requests_total, service)"
}
```

## 🚨 测试告警

### 手动触发告警

1. 生成高错误率：
```bash
for i in {1..100}; do
  curl -s http://localhost:8080/nonexistent > /dev/null
  sleep 0.1
done
```

2. 查看告警状态：
- Prometheus UI → Alerts
- 等待告警进入Firing状态

### 配置告警通知

在 `configs/alertmanager.yml` 中配置通知渠道（如Slack、邮件等）。

## 📈 性能测试

### 使用Apache Bench

```bash
# 压力测试
ab -n 1000 -c 10 http://localhost:8080/health

# 查看结果
# Prometheus → 查询指标变化
# Grafana → 观察仪表板更新
```

### 使用hey工具

```bash
# 安装hey
go install github.com/rakyll/hey@latest

# 并发测试
hey -n 1000 -c 20 -m GET http://localhost:8080/api/v1/users

# POST请求测试
hey -n 500 -c 5 -d '{"test":"data"}' -H "Content-Type: application/json" -m POST http://localhost:8080/api/v1/orders
```

## 🔍 故障排查

### 常见问题

1. **服务启动失败**
```bash
# 查看日志
docker-compose -f docker-compose.observability.yml logs gateway
docker-compose -f docker-compose.observability.yml logs prometheus
docker-compose -f docker-compose.observability.yml logs jaeger
```

2. **指标缺失**
```bash
# 检查指标端点
curl http://localhost:8080/metrics | head -20

# 检查Prometheus目标
curl http://localhost:9090/api/v1/targets | jq
```

3. **追踪数据缺失**
```bash
# 检查Jaeger服务
curl http://localhost:16686/api/services

# 检查OpenTelemetry配置
docker-compose logs gateway | grep -i tracing
```

4. **Grafana连接失败**
```bash
# 检查数据源
# Grafana UI → Configuration → Data Sources
# 确认Prometheus URL: http://prometheus:9090
```

### 重启服务

```bash
# 重启单个服务
docker-compose -f docker-compose.observability.yml restart gateway

# 重启所有服务
docker-compose -f docker-compose.observability.yml restart

# 完全重建
docker-compose -f docker-compose.observability.yml down
docker-compose -f docker-compose.observability.yml up -d --build
```

## 📚 进一步学习

- [详细配置文档](docs/OBSERVABILITY.md)
- [指标参考手册](docs/METRICS.md)
- [告警配置指南](docs/ALERTING.md)
- [性能优化建议](docs/PERFORMANCE.md)

---

**🎉 恭喜！您已成功启动Athena API Gateway的可观测性系统！**