# Athena Gateway Unified

> Athena工作平台统一网关 - 企业级API网关，提供服务发现、负载均衡、路由管理、健康检查和监控功能。

## ✨ 功能特性

### 核心功能
- **服务注册与发现**: 动态服务注册，自动健康检查
- **智能路由**: 支持精确匹配、通配符（`*`、`**`）、路径剥离
- **负载均衡**: 基于轮询的负载均衡算法
- **请求转发**: 高性能HTTP请求代理
- **依赖管理**: 服务依赖关系追踪

### 生产特性
- **优雅关机**: 两阶段关机机制（连接排空 + 资源清理）
- **日志轮转**: 基于大小的自动轮转和压缩
- **TLS/HTTPS**: 支持内置TLS和Nginx反向代理
- **多层认证**: IP白名单 + API Key + Bearer Token + Basic Auth
- **Prometheus指标**: 完整的监控指标导出

## 📦 系统支持

| 平台 | 状态 | 部署方式 | 文档 |
|------|------|----------|------|
| **macOS** | ✅ 完全支持 | launchd + shell脚本 | [DEPLOYMENT_MACOS.md](DEPLOYMENT_MACOS.md) |
| **Linux** | ✅ 完全支持 | systemd + shell脚本 | [DEPLOYMENT.md](DEPLOYMENT.md) |

## 🚀 快速开始

### 前置要求

- **Go**: 1.21+
- **系统**: macOS 11+ / Linux (Ubuntu 20.04+, CentOS 7+)
- **权限**: sudo/root (生产部署)

### 构建

```bash
cd gateway-unified
go build -o gateway ./cmd/gateway
```

### 本地开发运行

```bash
# 使用默认配置
./gateway

# 使用配置文件
GATEWAY_CONFIG=gateway-config.yaml ./gateway

# 使用环境变量
GATEWAY_PORT=9000 GATEWAY_LOG_LEVEL=debug ./gateway
```

### 健康检查

```bash
curl http://localhost:8005/health
```

## 🏭 生产环境部署

### macOS 部署

```bash
cd gateway-unified

# 一键部署（推荐）
sudo bash quick-deploy-macos.sh

# 查看状态
sudo /usr/local/athena-gateway/status.sh

# 查看日志
sudo /usr/local/athena-gateway/logs.sh
```

**详细文档**: [DEPLOYMENT_MACOS.md](DEPLOYMENT_MACOS.md)

### Linux 部署

```bash
cd gateway-unified

# 一键部署（推荐）
sudo bash quick-deploy.sh

# 查看状态
systemctl status athena-gateway

# 查看日志
journalctl -u athena-gateway -f
```

**详细文档**: [DEPLOYMENT.md](DEPLOYMENT.md)

## ⚙️ 配置说明

### 主配置文件 (config.yaml)

```yaml
server:
  port: 8005           # HTTP端口
  production: false    # 生产模式
  read_timeout: 30     # 读取超时(秒)
  write_timeout: 30    # 写入超时(秒)
  idle_timeout: 120    # 空闲超时(秒)

gateway:
  routes:
    - path: "/api/legal/*"
      strip_path: true
      target_service: "xiaona-legal"

services:
  discovery_type: "http"
  health_check_interval: 30s

logging:
  level: info          # debug, info, warn, error
  format: json         # json, text
  output: stdout       # stdout, file path

metrics:
  enabled: true
  port: 9090
  path: /metrics

tls:
  enabled: false       # 启用TLS
  cert_file: ""        # 证书文件路径
  key_file: ""         # 密钥文件路径
```

### 认证配置 (auth.yaml)

```yaml
# API Key 认证
api_keys:
  - "your-secure-api-key-here"

# Bearer Token 认证
bearer_tokens:
  - "your-secure-bearer-token-here"

# Basic Auth 认证
basic_auth:
  username: "admin"
  password: "your-secure-password-here"

# IP白名单
ip_whitelist:
  - "127.0.0.1"
  - "::1"
  - "10.0.0.0/8"
  - "172.16.0.0/12"
  - "192.168.0.0/16"
```

## 📡 API端点

### 健康检查
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/health` | 网关健康状态 |

### 服务管理
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/services/batch_register` | 批量注册服务 |
| GET | `/api/services/instances` | 查询所有服务实例 |
| GET | `/api/services/instances/:id` | 查询单个实例 |
| PUT | `/api/services/instances/:id` | 更新实例 |
| DELETE | `/api/services/instances/:id` | 删除实例 |

### 路由管理
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/routes` | 查询所有路由 |
| POST | `/api/routes` | 创建路由 |
| PATCH | `/api/routes/:id` | 更新路由 |
| DELETE | `/api/routes/:id` | 删除路由 |

### 依赖管理
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/dependencies` | 设置服务依赖 |
| GET | `/api/dependencies/:service` | 查询服务依赖 |

### 配置管理
| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/config/load` | 加载配置 |

## 🧪 测试

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/gateway -v

# 运行测试并显示覆盖率
go test -cover ./...

# 测试覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 📊 监控

### Prometheus 指标

网关默认在 `:9090/metrics` 导出Prometheus指标：

- `gateway_http_requests_total` - HTTP请求总数
- `gateway_http_request_duration_seconds` - 请求延迟
- `gateway_healthy_services` - 健康服务数
- `gateway_unhealthy_services` - 不健康服务数
- `gateway_active_connections` - 活动连接数

### Grafana 仪表板

导入 `grafana-dashboard.json` 获取预配置的监控仪表板。

## 🔐 安全检查

### macOS
```bash
sudo bash security-check-macos.sh
```

### Linux
```bash
sudo bash security-check.sh
```

## 🔧 管理命令

### macOS (launchd)
```bash
# 启动
sudo /usr/local/athena-gateway/start.sh
# 或
sudo launchctl load -w /Library/LaunchDaemons/com.athena.gateway.plist

# 停止
sudo /usr/local/athena-gateway/stop.sh
# 或
sudo launchctl unload -w /Library/LaunchDaemons/com.athena.gateway.plist

# 重启
sudo launchctl kickstart -k gui/$(id -u)/com.athena.gateway

# 查看状态
launchctl list | grep com.athena.gateway
```

### Linux (systemd)
```bash
# 启动
systemctl start athena-gateway

# 停止
systemctl stop athena-gateway

# 重启
systemctl restart athena-gateway

# 查看状态
systemctl status athena-gateway

# 查看日志
journalctl -u athena-gateway -f

# 开机自启
systemctl enable athena-gateway
```

## 📁 项目结构

```
gateway-unified/
├── cmd/
│   └── gateway/              # 主程序入口
│       └── main.go
├── internal/
│   ├── config/               # 配置管理
│   │   └── config.go
│   ├── gateway/              # 网关核心逻辑
│   │   └── gateway.go
│   ├── middleware/           # 中间件
│   │   ├── auth.go           # 认证中间件
│   │   └── metrics.go        # 指标中间件
│   ├── models/               # 数据模型
│   │   └── models.go
│   ├── router/               # 路由管理
│   │   └── router.go
│   ├── services/             # 服务发现
│   │   └── discovery.go
│   ├── logging/              # 日志系统
│   │   ├── logger.go
│   │   └── rotation.go       # 日志轮转
│   └── metrics/              # Prometheus指标
│       └── prometheus.go
├── deploy.sh                 # Linux部署脚本
├── deploy-macos.sh           # macOS部署脚本
├── quick-deploy.sh           # Linux一键部署
├── quick-deploy-macos.sh     # macOS一键部署
├── security-check.sh         # Linux安全检查
├── security-check-macos.sh   # macOS安全检查
├── uninstall.sh              # Linux卸载
├── uninstall-macos.sh        # macOS卸载
├── DEPLOYMENT.md             # Linux部署文档
├── DEPLOYMENT_MACOS.md       # macOS部署文档
├── CHANGELOG.md              # 开发日志
├── grafana-dashboard.json    # Grafana仪表板
├── gateway-config.yaml.example   # 配置模板
└── tls-config.yaml.example       # TLS配置模板
```

## 🌍 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GATEWAY_CONFIG` | 配置文件路径 | - |
| `GATEWAY_PORT` | 监听端口 | 8005 |
| `GATEWAY_PRODUCTION` | 生产模式 | false |
| `GATEWAY_READ_TIMEOUT` | 读取超时(秒) | 30 |
| `GATEWAY_WRITE_TIMEOUT` | 写入超时(秒) | 30 |
| `GATEWAY_IDLE_TIMEOUT` | 空闲超时(秒) | 120 |
| `GATEWAY_LOG_LEVEL` | 日志级别 | info |
| `GATEWAY_LOG_FORMAT` | 日志格式 | json |
| `GATEWAY_LOG_OUTPUT` | 日志输出 | stdout |
| `GATEWAY_METRICS_ENABLED` | 启用指标 | false |
| `GATEWAY_METRICS_PORT` | 指标端口 | 9090 |
| `GATEWAY_METRICS_PATH` | 指标路径 | /metrics |

## 📋 部署检查清单

### 部署前
- [ ] Go版本 >= 1.21
- [ ] 端口 8005、8443、9090 未被占用
- [ ] 有sudo/root权限

### 部署后（必须）
- [ ] 修改认证密钥 (`auth.yaml`)
- [ ] 配置SSL/TLS证书（生产环境）
- [ ] 验证防火墙规则
- [ ] 配置监控告警

### 验证
- [ ] 服务启动成功
- [ ] 健康检查通过
- [ ] 日志正常输出
- [ ] 指标正常导出

## 🐛 故障排查

### 服务无法启动

**macOS**:
```bash
# 查看服务状态
launchctl list | grep com.athena.gateway

# 查看日志
tail -50 /usr/local/athena-gateway/logs/gateway-error.log
```

**Linux**:
```bash
# 查看服务状态
systemctl status athena-gateway

# 查看日志
journalctl -u athena-gateway -n 50
```

### 端口被占用

```bash
# macOS/Linux
lsof -i :8005
lsof -i :8443
lsof -i :9090
```

### 权限错误

```bash
# macOS
sudo chown -R _athena:staff /usr/local/athena-gateway
sudo chmod 750 /usr/local/athena-gateway
sudo chmod 640 /usr/local/athena-gateway/config/*.yaml

# Linux
sudo chown -R athena:athena /opt/athena-gateway
sudo chmod 750 /opt/athena-gateway
sudo chmod 640 /opt/athena-gateway/config/*.yaml
```

## 📚 相关文档

- [开发日志](CHANGELOG.md)
- [macOS部署指南](DEPLOYMENT_MACOS.md)
- [Linux部署指南](DEPLOYMENT.md)
- [完整部署指南](DEPLOYMENT_COMPLETE.md)

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**版本**: v1.0.0-macos
**构建时间**: 2025-02-21
**维护者**: 徐健 (xujian519@gmail.com)
