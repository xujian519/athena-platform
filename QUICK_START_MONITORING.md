# 🚀 Prometheus + Grafana监控 - 快速启动指南

## 前提条件

✅ Gateway已运行在端口9091（监控端口）  
✅ Docker Desktop已安装  
⚠️ **需要启动Docker Desktop**

---

## 📋 **启动步骤（3步）**

### 1️⃣ 启动Docker Desktop

打开 **Docker Desktop** 应用，等待启动完成

验证Docker运行：
```bash
docker ps
```

### 2️⃣ 启动监控服务

```bash
cd /Users/xujian/Athena工作平台
./scripts/start_docker_monitoring.sh start
```

### 3️⃣ 访问监控界面

**Prometheus**: http://localhost:9090  
**Grafana**: http://localhost:3000 (admin/admin)

---

## ✅ **验证监控正常**

### 在Prometheus中验证

1. 访问 http://localhost:9090
2. 点击 **Status** → **Targets**
3. 查找 **athena-gateway** 目标
4. 状态应为 **UP** (绿色)

### 在Grafana中查看仪表板

1. 访问 http://localhost:3000
2. 登录（admin/admin）
3. 点击左侧菜单 → **Dashboards**
4. 找到 **Athena** 文件夹
5. 打开 **Gateway WebSocket** 仪表板

### 查询Gateway指标

在Prometheus查询框中输入：
```promql
# 活跃连接数
websocket_active_sessions

# 消息速率
rate(websocket_messages_total[1m])

# P95延迟
histogram_quantile(0.95, websocket_message_duration_seconds)
```

---

## 🎯 **快速命令**

```bash
# 启动监控
./scripts/start_docker_monitoring.sh start

# 查看状态
./scripts/start_docker_monitoring.sh status

# 查看Prometheus日志
./scripts/start_docker_monitoring.sh logs prometheus

# 查看Grafana日志
./scripts/start_docker_monitoring.sh logs grafana

# 重启监控
./scripts/start_docker_monitoring.sh restart

# 停止监控
./scripts/start_docker_monitoring.sh stop
```

---

## 📊 **监控的指标**

| 指标类型 | 说明 |
|---------|------|
| **连接数** | websocket_sessions_total, websocket_active_sessions |
| **消息速率** | rate(websocket_messages_total[1m]) |
| **消息延迟** | histogram_quantile(0.95, websocket_message_duration_seconds) |
| **错误率** | rate(websocket_errors_total[5m]) |
| **Agent任务** | agent_tasks_total{agent="xiaona\|xiaonuo\|yunxi"} |
| **系统资源** | process_resident_memory_bytes, rate(process_cpu_seconds_total[1m]) |

---

## ⚠️ **故障排查**

### Docker未启动

```bash
# 启动Docker Desktop
open -a Docker

# 等待10秒后验证
docker ps
```

### Prometheus显示目标DOWN

1. 检查Gateway是否运行：
```bash
lsof -i :9091
```

2. 检查Gateway指标端点：
```bash
curl http://localhost:9091/metrics
```

3. 查看Prometheus日志：
```bash
./scripts/start_docker_monitoring.sh logs prometheus
```

### Grafana无法连接Prometheus

1. 检查Prometheus数据源：
   - 访问 http://localhost:3000
   - Configuration → Data Sources → Prometheus
   - 点击 "Test" 按钮

2. 检查Prometheus是否运行：
```bash
curl http://localhost:9090/api/v1/targets
```

---

## 📁 **配置文件位置**

| 配置 | 位置 |
|------|------|
| Prometheus配置 | `config/docker/prometheus/prometheus.yml` |
| Grafana数据源 | `config/docker/grafana/provisioning/datasources/prometheus.yml` |
| Grafana仪表板 | `config/docker/grafana/dashboards/Athena/gateway-websocket.json` |
| Gateway仪表板 | `gateway-unified/configs/grafana_dashboard.json` |

---

## 📖 **详细文档**

完整文档：[docs/DOCKER_MONITORING_SETUP.md](docs/DOCKER_MONITORING_SETUP.md)

---

## 🎉 **完成！**

监控服务启动后，你可以：

✅ 实时查看Gateway性能指标  
✅ 可视化WebSocket连接和消息  
✅ 监控错误率和延迟  
✅ 分析Agent任务统计  

**开始享受实时监控吧！** 🚀

---

**维护者**: 徐健 (xujian519@gmail.com)  
**创建日期**: 2026-04-20
