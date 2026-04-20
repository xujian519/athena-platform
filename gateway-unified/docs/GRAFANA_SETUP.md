# Grafana监控仪表板配置指南

## 概述

Gateway + Prometheus + Grafana监控方案，提供实时性能监控和可视化。

## 架构

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│   Gateway       │────▶│ Prometheus   │────▶│  Grafana    │
│   :9091/metrics│     │   :9090      │     │   :3000     │
└─────────────────┘     └──────────────┘     └─────────────┘
    (指标源)              (数据收集)          (可视化)
```

## 快速开始

### 1. 检查依赖

确保已安装Prometheus和Grafana：

```bash
# 检查安装
prometheus --version
grafana-server --version

# 如果未安装
brew install prometheus
brew install grafana
```

### 2. 启动监控服务

```bash
cd /Users/xujian/Athena工作平台/gateway-unified
./scripts/start_monitoring.sh start
```

这会启动：
- Gateway (端口8005 + 监控端口9091)
- Prometheus (端口9090)
- Grafana (端口3000)

### 3. 访问Grafana

浏览器打开：http://localhost:3000

默认登录：
- 用户名：`admin`
- 密码：`admin`

## 配置Grafana数据源

### 步骤1：添加Prometheus数据源

1. 登录Grafana
2. 点击左侧齿轮图标 ⚙️ → Configuration → Data Sources
3. 点击 "Add data source"
4. 选择 "Prometheus"

### 步骤2：配置数据源

填写以下信息：

| 字段 | 值 |
|------|-----|
| Name | Prometheus |
| URL | http://localhost:9090 |
| Access | Server (default) |

### 步骤3：测试连接

点击 "Save & Test"，应该显示 "Data source is working"。

## 导入仪表板

### 方法1：通过JSON导入

1. 点击左侧 "+" → Import
2. 点击 "Import via panel json"
3. 粘贴 `configs/grafana_dashboard.json` 的内容
4. 点击 "Load"
5. 选择Prometheus数据源
6. 点击 "Import"

### 方法2：通过文件导入

1. 复制仪表板文件：
```bash
cp configs/grafana_dashboard.json data/grafana/dashboards/
```

2. 在Grafana中：
- 点击 "+" → Import
- 上传JSON文件

## 仪表板面板

导入的仪表板包含6个面板：

### 1. 连接数统计
- 总会话数
- 活跃会话数

### 2. 消息吞吐量
- 消息速率（1分钟）
- 5分钟平均速率

### 3. 消息延迟
- P50/P95/P99延迟
- 延迟分布

### 4. 错误率
- 错误速率
- 错误率百分比

### 5. Agent任务统计
- 小娜任务数
- 小诺任务数
- 云希任务数

### 6. 系统资源使用
- 内存占用（MB）
- CPU使用率

## 常用Prometheus查询

### 查看所有指标

```promql
up{job="athena-gateway"}
```

### 连接数

```promql
websocket_active_sessions
```

### 消息速率

```promql
rate(websocket_messages_total[1m])
```

### P95延迟

```promql
histogram_quantile(0.95, websocket_message_duration_seconds)
```

### 错误率

```promql
rate(websocket_errors_total[5m]) / rate(websocket_messages_total[5m])
```

## 管理命令

### 启动所有服务

```bash
./scripts/start_monitoring.sh start
```

### 停止所有服务

```bash
./scripts/start_monitoring.sh stop
```

### 重启所有服务

```bash
./scripts/start_monitoring.sh restart
```

### 查看服务状态

```bash
./scripts/start_monitoring.sh status
```

### 查看日志

```bash
./scripts/start_monitoring.sh logs
```

## 故障排查

### Grafana无法连接Prometheus

1. 检查Prometheus是否运行：
```bash
lsof -i :9090
```

2. 检查Prometheus日志：
```bash
tail -f /tmp/prometheus.log
```

3. 测试Prometheus：
```bash
curl http://localhost:9090/api/v1/targets
```

### 仪表板无数据

1. 检查Gateway监控端口：
```bash
curl http://localhost:9091/metrics
```

2. 检查Prometheus是否抓取Gateway：
```bash
curl http://localhost:9090/api/v1/targets
```

3. 查看Prometheus配置：
```bash
cat configs/prometheus-gateway.yml
```

### 端口冲突

如果端口被占用：

```bash
# 查找占用进程
lsof -i :9090  # Prometheus
lsof -i :9091  # Gateway监控
lsof -i :3000  # Grafana

# 杀死进程
kill -9 <PID>
```

## 自动启动

### 方法1：使用launchd（推荐）

创建启动服务（参考 `docs/SERVICE_SETUP.md`）

### 方法2：使用crontab

```bash
# 编辑crontab
crontab -e

# 添加启动任务
@reboot /Users/xujian/Athena工作平台/gateway-unified/scripts/start_monitoring.sh start
```

## 性能优化

### Prometheus数据保留

默认Prometheus保留15天数据。可在配置中调整：

```yaml
# prometheus-gateway.yml
storage:
  tsdb:
    retention.time: 30d  # 保留30天
```

### Grafana刷新间隔

建议：
- 实时监控：5-10秒
- 历史趋势：1-5分钟
- 长期统计：1小时+

### 采样间隔

当前配置：
- Prometheus抓取间隔：10秒
- Prometheus评估间隔：15秒

可根据需要调整 `configs/prometheus-gateway.yml`。

## 备份和恢复

### 备份Grafana配置

```bash
# 备份数据库
cp data/grafana/grafana.db data/grafana/grafana.db.backup

# 备份仪表板
tar -czf grafana-dashboards-$(date +%Y%m%d).tar.gz data/grafana/dashboards/
```

### 恢复Grafana配置

```bash
# 恢复数据库
cp data/grafana/grafana.db.backup data/grafana/grafana.db

# 重启Grafana
./scripts/start_monitoring.sh restart
```

## 注意事项

⚠️ **重要**：
- Prometheus数据存储在 `data/prometheus/` 目录
- Grafana数据存储在 `data/grafana/` 目录
- 定期备份配置和仪表板
- 监控磁盘使用情况

## 扩展阅读

- [Prometheus查询语言](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana仪表板指南](https://grafana.com/docs/grafana/latest/dashboards/)
- [WebSocket监控最佳实践](https://prometheus.io/docs/practices/naming/)

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
