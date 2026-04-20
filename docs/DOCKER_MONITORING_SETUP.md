# 使用Docker启动Prometheus + Grafana监控

## 步骤1：启动Docker Desktop

1. 打开 **Docker Desktop** 应用
2. 等待Docker引擎启动（菜单栏图标变为活动状态）
3. 验证Docker运行：
```bash
docker ps
```

## 步骤2：启动Prometheus和Grafana

```bash
cd /Users/xujian/Athena工作平台

# 启动Prometheus和Grafana（后台）
docker-compose up -d prometheus grafana

# 查看运行状态
docker-compose ps
```

## 步骤3：验证服务运行

### Prometheus
```bash
# 访问Prometheus
open http://localhost:9090

# 或使用curl
curl http://localhost:9090/api/v1/targets
```

### Grafana
```bash
# 访问Grafana
open http://localhost:3000

# 默认登录
# 用户名: admin
# 密码: admin
```

## 步骤4：查看Gateway指标

### Prometheus中查看Gateway目标

1. 访问 http://localhost:9090
2. 点击 **Status** → **Targets**
3. 查看 **athena-gateway** 目标状态
4. 应该显示为 **UP** 状态

### 查询Gateway指标

在Prometheus查询框中输入：
```promql
# 查看活跃连接数
websocket_active_sessions

# 查看消息速率
rate(websocket_messages_total[1m])

# 查看P95延迟
histogram_quantile(0.95, websocket_message_duration_seconds)
```

### Grafana中查看仪表板

1. 访问 http://localhost:3000
2. 登录（admin/admin）
3. 点击左侧菜单 **+** → **Dashboard**
4. 查找 **Athena** 文件夹
5. 打开 **Gateway WebSocket** 仪表板

## 步骤5：验证Gateway监控端点

Gateway的Prometheus指标在：
```
http://localhost:9091/metrics
```

验证访问：
```bash
curl http://localhost:9091/metrics | head -20
```

应该看到类似：
```
# HELP websocket_sessions_total WebSocket总会话数
# TYPE websocket_sessions_total counter
websocket_sessions_total 123.0
...
```

## 常用命令

### 查看日志
```bash
# Prometheus日志
docker-compose logs -f prometheus

# Grafana日志
docker-compose logs -f grafana

# Gateway日志
tail -f gateway-unified/logs/gateway-error.log
```

### 重启服务
```bash
# 重启Prometheus
docker-compose restart prometheus

# 重启Grafana
docker-compose restart grafana

# 重启所有监控服务
docker-compose restart prometheus grafana
```

### 停止服务
```bash
# 停止监控服务
docker-compose stop prometheus grafana

# 完全停止并删除容器
docker-compose down
```

## 配置说明

### Prometheus配置
- **配置文件**: `config/docker/prometheus/prometheus.yml`
- **数据目录**: Docker volume `athena-prometheus-data`
- **抓取间隔**: 10秒（Gateway）
- **端口**: 9090

### Grafana配置
- **数据源**: Prometheus（自动配置）
- **仪表板目录**: `config/docker/grafana/dashboards/`
- **数据目录**: Docker volume `athena-grafana-data`
- **端口**: 3000

### Gateway配置
- **监控端口**: 9091
- **指标路径**: /metrics
- **配置文件**: `gateway-unified/config.yaml`

## 故障排查

### Prometheus无法连接Gateway

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
docker-compose logs prometheus | grep gateway
```

### Grafana无数据

1. 检查Prometheus数据源：
   - 访问 http://localhost:3000
   - Configuration → Data Sources → Prometheus
   - 点击 "Test" 按钮

2. 检查Prometheus是否抓取Gateway：
   - 访问 http://localhost:9090
   - Status → Targets
   - 查找 athena-gateway 目标

### 端口冲突

如果端口被占用：
```bash
# 查找占用进程
lsof -i :9090  # Prometheus
lsof -i :3000  # Grafana

# 停止占用进程或修改docker-compose.yml中的端口映射
```

## 数据持久化

Prometheus和Grafana的数据存储在Docker volumes中：
```bash
# 查看volumes
docker volume ls | grep athena

# 备份数据
docker run --rm -v athena-prometheus-data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz -C /data .
docker run --rm -v athena-grafana-data:/data -v $(pwd):/backup alpine tar czf /backup/grafana-backup.tar.gz -C /data .
```

## 下一步

监控运行后，可以：

1. **创建告警规则** - 在Prometheus中配置告警
2. **自定义仪表板** - 在Grafana中创建个性化面板
3. **设置通知** - 配置邮件或Slack通知
4. **长期监控** - 收集性能数据用于分析

## 参考文档

- [Prometheus查询指南](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana仪表板指南](https://grafana.com/docs/grafana/latest/dashboards/)
- [WebSocket监控配置](../gateway-unified/docs/GRAFANA_SETUP.md)

---

**维护者**: 徐健 (xujian519@gmail.com)
**最后更新**: 2026-04-20
