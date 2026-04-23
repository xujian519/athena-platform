# WebSocket控制平面 - 性能、监控与安全实施报告

> **完成日期**: 2026-04-20
> **状态**: ✅ 全部完成
> **包含**: 性能测试套件、Prometheus/Grafana监控集成、TLS/SSL安全支持

---

## 📊 执行摘要

在完成WebSocket控制平面核心功能的基础上，进一步实施了生产级的关键改进：

1. ✅ **性能测试套件** - 完整的性能测试框架
2. ✅ **Prometheus监控集成** - 实时监控和Grafana仪表板
3. ✅ **TLS/SSL安全支持** - 加密通信支持
4. ✅ **完整文档** - 使用指南和最佳实践

---

## 🎯 实施内容

### 1. 性能测试套件

**文件**: `tests/performance/test_websocket_performance.py`

**测试项目**:

#### 测试1: 并发连接测试
- 目标: 100个并发连接
- 指标: 连接成功率、平均连接时间

#### 测试2: 消息吞吐量测试
- 目标: 10个客户端，每客户端100条消息
- 指标: 总消息数、吞吐量（条/秒）

#### 测试3: 消息延迟测试
- 目标: 100条测试消息
- 指标: 平均延迟、P50/P95/P99延迟

#### 测试4: 资源占用测试
- 目标: 50个客户端，每客户端50条消息
- 指标: CPU使用率、内存占用

**运行方式**:
```bash
# 确保Gateway正在运行
cd /Users/xujian/Athena工作平台/gateway-unified
./bin/gateway

# 运行性能测试（新终端）
cd /Users/xujian/Athena工作平台
python3 tests/performance/test_websocket_performance.py
```

---

### 2. Prometheus监控集成

#### 2.1 Prometheus配置

**文件**: `configs/prometheus.yml`

**配置内容**:
- 抓取间隔: 15秒
- Gateway监控: `localhost:9090/metrics`
- WebSocket控制平面监控
- 系统监控（可选）

#### 2.2 Grafana仪表板

**文件**: `configs/grafana_dashboard.json`

**仪表板面板**:

1. **连接数统计**
   - 总会话数
   - 活跃会话数

2. **消息吞吐量**
   - 消息速率（1分钟）
   - 5分钟平均速率

3. **消息延迟**
   - P50/P95/P99延迟
   - 延迟分布直方图

4. **错误率**
   - 错误速率
   - 错误率百分比

5. **Agent任务统计**
   - 小娜任务数
   - 小诺任务数
   - 云希任务数

6. **系统资源使用**
   - 内存占用（MB）
   - CPU使用率

#### 2.3 WebSocket Prometheus指标

**文件**: `internal/metrics/websocket_metrics.go`

**新增指标**:

```go
// 会话指标
websocket_sessions_total          // 总会话数
websocket_active_sessions        // 活跃会话数

// 消息指标
websocket_messages_total          // 消息总数（按类型、Agent）
websocket_message_duration_seconds  // 消息处理延迟

// 错误指标
websocket_errors_total             // 错误总数（按类型）

// Agent任务指标
agent_tasks_total                  // Agent任务总数（按Agent、类型、状态）
agent_task_duration_seconds      // 任务处理时长

// Canvas Host指标
canvas_render_total                // Canvas渲染总数
canvas_render_duration_seconds    // Canvas渲染时长

// Gateway请求指标
gateway_request_duration_seconds  // 请求处理时长
gateway_requests_total             // 请求总数（按端点、方法、状态）
```

**使用方式**:
```python
from core.agents.websocket_adapter import WebSocketClient

# 使用指标辅助器
metrics = WebSocketMetricsHelper()
metrics.RecordSessionCreated()
metrics.RecordMessage("task", "xiaona")
metrics.RecordMessageDuration(0.05)
```

---

### 3. TLS/SSL安全支持

#### 3.1 证书生成

**文件**: `scripts/generate_tls_certs.sh`

**功能**:
- 自动生成2048位RSA私钥
- 生成自签名证书（有效期365天）
- 配置SAN（主题备用名称）
- 支持localhost和127.0.0.1

**运行方式**:
```bash
cd /Users/xujian/Athena工作平台/gateway-unified
bash scripts/generate_tls_certs.sh
```

**生成的文件**:
```
certs/
├── server.crt    # 证书文件
└── server.key     # 私钥文件
```

#### 3.2 TLS配置

**配置文件**: `config.yaml`

```yaml
tls:
  enabled: true
  cert_file: /Users/xujian/Athena工作平台/gateway-unified/certs/server.crt
  key_file: /Users/xujian/Athena工作平台/gateway-unified/certs/server.key
```

#### 3.3 WSS支持

**WebSocket Secure URL**:
```
wss://localhost:8005/ws
```

**Python客户端配置**:
```python
client = WebSocketClient(
    gateway_url="wss://localhost:8005/ws",  # 使用wss
    ssl_verify=True  # 验证证书（生产环境）
)
```

---

## 📈 预期性能指标

### 性能目标

| 指标 | 目标值 | 测试方法 |
|-----|-------|---------|
| 并发连接数 | 1,000+ | 并发连接测试 |
| 消息延迟 | <50ms (P95) | 延迟测试 |
| 消息吞吐量 | 10,000+ 条/秒 | 吞吐量测试 |
| 内存占用 | <500MB | 资源占用测试 |
| 错误率 | <0.1% | 持续运行监控 |

### 监控告警规则（建议）

| 指标 | 阈值 | 级别 |
|-----|------|------|
| 错误率 | >1% | Warning |
| 错误率 | >5% | Critical |
| P95延迟 | >100ms | Warning |
| P95延迟 | >200ms | Critical |
| 内存占用 | >1GB | Warning |
| 内存占用 | >2GB | Critical |

---

## 🚀 使用指南

### 快速启动（带监控）

```bash
# 1. 启动Prometheus
prometheus --config.file=configs/prometheus.yml

# 2. 启动Grafana
grafana-server

# 3. 启动Gateway
./bin/gateway

# 4. 访问仪表板
open http://localhost:3000
```

### 导入Grafana仪表板

1. 登录Grafana (默认: admin/admin)
2. 进入 Configuration → Data Sources
3. 添加Prometheus数据源: `http://localhost:9090`
4. 进入 Dashboards → Import
5. 粘贴 `configs/grafana_dashboard.json` 内容
6. 点击Import

### 运行性能测试

```bash
# 确保Gateway正在运行
cd /Users/xujian/Athena工作平台/gateway-unified
./bin/gateway

# 运行性能测试
python3 tests/performance/test_websocket_performance.py
```

### 启用TLS

```bash
# 1. 生成证书
bash scripts/generate_tls_certs.sh

# 2. 更新配置
vim config.yaml
# 设置 tls.enabled = true

# 3. 启动Gateway
./bin/gateway

# 4. 使用WSS连接
wss://localhost:8005/ws
```

---

## 📁 新增文件清单

### 性能测试
```
tests/performance/
└── test_websocket_performance.py    (~370行) - 性能测试脚本
```

### 监控集成
```
configs/
├── prometheus.yml                  - Prometheus配置
└── grafana_dashboard.json          - Grafana仪表板

internal/metrics/
└── websocket_metrics.go             (~270行) - WebSocket指标
```

### TLS/SSL
```
scripts/
└── generate_tls_certs.sh            - 证书生成脚本

certs/
├── server.crt                       - TLS证书
└── server.key                       - TLS私钥
```

### 文档
```
docs/reports/
└── WEBSOCKET_CONTROL_PLANE_PERFORMANCE_SECURITY_20260420.md
```

---

## 💡 最佳实践

### 性能优化

1. **连接池复用** - 复用WebSocket连接，避免频繁建立连接
2. **消息批量处理** - 批量发送消息，减少网络往返
3. **异步处理** - 使用asyncio异步处理消息
4. **资源限制** - 限制最大并发连接数

### 监控告警

1. **关键指标监控** - 关注延迟、错误率、资源使用
2. **告警阈值设置** - 根据实际情况调整阈值
3. **告警通知** - 配置邮件、Slack等通知渠道
4. **定期审查** - 定期审查监控数据和告警规则

### 安全加固

1. **使用TLS** - 生产环境必须使用WSS
2. **证书管理** - 定期更新证书，使用CA签发证书
3. **访问控制** - 配置IP白名单、API密钥认证
4. **日志脱敏** - 敏感信息不记录到日志

---

## 🎊 总结

成功完成了WebSocket控制平面的**生产级改进**：

✅ **性能测试** - 完整的性能测试框架
✅ **监控集成** - Prometheus + Grafana实时监控
✅ **安全加固** - TLS/SSL加密通信
✅ **完整文档** - 使用指南和最佳实践

### 技术栈

- **性能测试**: Python + asyncio + websockets + psutil
- **监控**: Prometheus + Grafana
- **安全**: OpenSSL + TLS 1.2

### 下一步

1. **生产部署** - 部署到生产环境
2. **压力测试** - 长时间稳定性测试
3. **灰度切流** - 逐步切换流量
4. **持续优化** - 根据监控数据持续优化

---

**维护者**: 徐健 (xujian519@gmail.com)  
**完成日期**: 2026-04-20  
**状态**: ✅ **WebSocket控制平面生产级改进全部完成！**
