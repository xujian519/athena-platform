# Prometheus 和 Grafana 快速安装指南

**适用环境**: macOS / Linux
**更新日期**: 2026-01-27

---

## 📋 目录

1. [macOS 安装](#macos-安装)
2. [Linux 安装](#linux-安装)
3. [Docker 安装](#docker-安装)
4. [配置步骤](#配置步骤)
5. [验证安装](#验证安装)

---

## macOS 安装

### 使用 Homebrew（推荐）

```bash
# 1. 安装 Prometheus
brew install prometheus

# 2. 安装 Grafana
brew install grafana

# 3. 启动服务
brew services start prometheus
brew services start grafana

# 4. 验证安装
prometheus --version
grafana-cli --version
```

### 手动安装

```bash
# Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.darwin-amd64.tar.gz
tar xvfz prometheus-2.45.0.darwin-amd64.tar.gz
cd prometheus-2.45.0.darwin-amd64
./prometheus --config.file=documentation/examples/prometheus.yml

# Grafana
wget https://dl.grafana.com/oss/release/grafana-10.2.2.darwin-amd64.tar.gz
tar xvfz grafana-10.2.2.darwin-amd64.tar.gz
cd grafana-10.2.2
./bin/grafana-server web
```

---

## Linux 安装

### Ubuntu/Debian

```bash
# 1. 添加 Prometheus 仓库
sudo apt-get install -y prometheus

# 2. 添加 Grafana 仓库
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee /etc/apt/sources.list.d/grafana.list

# 3. 更新并安装
sudo apt-get update
sudo apt-get install -y grafana

# 4. 启动服务
sudo systemctl start prometheus
sudo systemctl start grafana
sudo systemctl enable prometheus
sudo systemctl enable grafana
```

### CentOS/RHEL

```bash
# 1. 添加 Grafana 仓库
sudo tee /etc/yum.repos.d/grafana.repo <<EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

# 2. 安装
sudo yum install -y prometheus grafana

# 3. 启动服务
sudo systemctl start prometheus
sudo systemctl start grafana
sudo systemctl enable prometheus
sudo systemctl enable grafana
```

---

## Docker 安装

### 使用 Docker Compose（最简单）

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: athena-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./config/monitoring/prometheus_alerts.yml:/etc/prometheus/prometheus_alerts.yml
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    container_name: athena-grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    restart: unless-stopped
    depends_on:
      - prometheus

volumes:
  prometheus-data:
  grafana-data:
```

启动服务：

```bash
# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 配置步骤

### 1. 验证 Prometheus 配置

```bash
# 运行验证脚本
./scripts/validate_prometheus_config.sh

# 或手动验证
promtool check config config/monitoring/prometheus.yml
promtool check rules config/monitoring/prometheus_alerts.yml
```

### 2. 启动 Prometheus

```bash
# 方式1: 使用启动脚本
./scripts/start_prometheus.sh

# 方式2: 手动启动（使用项目配置）
prometheus \
  --config.file=config/monitoring/prometheus.yml \
  --storage.tsdb.path=data/prometheus

# 方式3: Docker方式
docker-compose up -d prometheus
```

### 3. 访问 Prometheus

打开浏览器访问: http://localhost:9090

### 4. 配置 Grafana

#### 4.1 添加 Prometheus 数据源

1. 访问 http://localhost:3000
2. 登录（默认: admin/admin）
3. 点击 "Configuration" → "Data sources"
4. 点击 "Add data source"
5. 选择 "Prometheus"
6. 配置:
   - Name: `Prometheus`
   - URL: `http://localhost:9090`
   - Access: `Server (default)`
7. 点击 "Save & Test"

#### 4.2 导入仪表板

```bash
# 方式1: 使用导入脚本
./scripts/import_grafana_dashboard.sh

# 方式2: 手动导入
# 在 Grafana UI 中:
# 1. 点击 "+" → "Import dashboard"
# 2. 上传 config/monitoring/grafana_dashboard.json
# 3. 选择 Prometheus 数据源
# 4. 点击 "Import"
```

### 5. 启动 Athena 执行模块（带监控）

```python
from core.execution.config_loader import load_config
from core.execution.metrics import setup_metrics
from core.execution import EnhancedExecutionEngine

# 加载本地配置
config = load_config(config_path="config/local.yaml")

# 设置监控
metrics = setup_metrics(
    instance_id="local-01",
    version="2.0.0",
    metrics_port=9091  # 本地开发使用9091端口
)

# 创建执行引擎
engine = EnhancedExecutionEngine(
    agent_id="local_agent",
    config=config.execution_engine.__dict__
)

# 使用引擎...
# metrics 会自动收集执行指标
```

---

## 验证安装

### 1. 检查 Prometheus 状态

```bash
# 检查进程
ps aux | grep prometheus

# 检查端口
lsof -i :9090

# 检查Web UI
curl http://localhost:9090/-/healthy
```

### 2. 检查 Grafana 状态

```bash
# 检查进程
ps aux | grep grafana

# 检查端口
lsof -i :3000

# 检查API
curl http://localhost:3000/api/health
```

### 3. 检查告警规则

访问: http://localhost:9090/rules

应该能看到 `athena_execution_alerts` 和 `athena_execution_cluster_alerts` 规则组。

### 4. 检查监控目标

访问: http://localhost:9090/targets

应该能看到 `athena-execution` 任务。

### 5. 查看仪表板

访问: http://localhost:3000/d/athena-execution-monitoring

应该能看到完整的监控仪表板。

---

## 🔧 故障排除

### Prometheus 无法启动

```bash
# 检查配置文件
promtool check config config/monitoring/prometheus.yml

# 查看详细日志
prometheus --config.file=config/monitoring/prometheus.yml --log.level=debug
```

### Grafana 无法连接 Prometheus

1. 检查 Prometheus 是否运行: `curl http://localhost:9090`
2. 检查 Grafana 数据源配置
3. 查看 Grafana 日志: `tail -f /var/log/grafana/grafana.log`

### 没有指标数据

1. 确保执行模块正在运行
2. 检查 metrics 端点: `curl http://localhost:9091/metrics`
3. 检查 Prometheus 抓取配置

---

## 📊 快速命令参考

```bash
# 启动所有服务
./scripts/start_prometheus.sh &
brew services start grafana  # macOS
# 或
docker-compose up -d  # Docker

# 验证配置
./scripts/validate_prometheus_config.sh

# 导入仪表板
./scripts/import_grafana_dashboard.sh

# 查看日志
tail -f data/prometheus/*.log
tail -f /var/log/grafana/grafana.log

# 停止服务
brew services stop prometheus grafana  # macOS
# 或
docker-compose down  # Docker
```

---

## 📚 相关文档

- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
- [执行模块 API 文档](../02-references/EXECUTION_MODULE_API_V2.md)
- [生产环境配置](../../config/production.yaml)

---

**文档版本**: 1.0.0  
**最后更新**: 2026-01-27  
**维护者**: Athena AI系统
