# Athena API Gateway

企业级API网关，为Athena工作平台提供统一的API入口、认证、路由和监控功能。

## 🏗️ 架构概述

Athena API Gateway是基于Gin框架构建的高性能、可扩展的API网关，提供：

- 🔐 **统一认证**: JWT token认证和权限控制
- 🛣️ **智能路由**: 请求路由和负载均衡
- 📊 **监控日志**: 结构化日志和请求追踪
- ⚙️ **配置管理**: 动态配置和热重载
- 🏥 **健康检查**: 服务健康状态监控
- 🔄 **优雅关闭**: 零停机部署支持

## 📁 项目结构

```
api-gateway/
├── cmd/                     # 应用程序入口
│   └── server/
│       └── main.go         # 主程序入口
├── internal/                # 内部包（不对外暴露）
│   ├── auth/               # 认证相关
│   ├── config/             # 配置管理
│   ├── handlers/           # HTTP处理器
│   ├── logging/            # 日志系统
│   └── middleware/         # 中间件
├── pkg/                    # 公共包（可对外暴露）
│   ├── response/           # 响应格式化
│   └── server/             # 服务器封装
├── configs/                # 配置文件
├── deployments/            # 部署配置
│   ├── docker/            # Docker配置
│   └── k8s/               # Kubernetes配置
├── tests/                  # 测试文件
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
├── scripts/               # 脚本工具
└── docs/                  # 文档
```

## 🚀 快速开始

### 环境要求

- Go 1.21+
- Docker (可选)
- Kubernetes (可选)

### 本地开发

```bash
# 克隆项目
cd api-gateway

# 安装依赖
go mod tidy

# 运行服务
go run cmd/server/main.go

# 或使用配置文件
go run cmd/server/main.go --config configs/config.yaml
```

### Docker部署

```bash
# 构建镜像
docker build -t athena-gateway:latest -f deployments/docker/Dockerfile .

# 运行容器
docker run -p 8080:8080 -v $(pwd)/configs:/app/configs athena-gateway:latest
```

## 🔧 配置说明

配置文件位于 `configs/config.yaml`，支持以下配置项：

- **server**: 服务器配置（端口、超时等）
- **auth**: 认证配置（JWT密钥、过期时间等）
- **logging**: 日志配置（级别、格式等）
- **upstream**: 上游服务配置

## 📖 API文档

### 认证端点

- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新token
- `POST /api/v1/auth/logout` - 用户登出

### 健康检查

- `GET /health` - 基本健康检查
- `GET /health/ready` - 就绪检查
- `GET /health/live` - 存活检查

### 管理端点

- `GET /api/v1/admin/status` - 系统状态
- `GET /api/v1/admin/metrics` - 系统指标

## 🧪 测试

```bash
# 运行所有测试
go test ./...

# 运行单元测试
go test ./tests/unit/...

# 运行集成测试
go test ./tests/integration/...

# 生成测试覆盖率报告
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out
```

## 📊 监控

API网关提供多种监控方式：

- **结构化日志**: 请求/响应日志
- **健康检查**: 服务状态监控
- **指标收集**: 性能指标统计
- **分布式追踪**: 请求链路追踪

## 🔒 安全

- JWT token认证
- CORS跨域配置
- 请求限流
- 输入验证和清理
- 安全头设置

## 🚀 部署

### Docker Compose

```bash
docker-compose -f deployments/docker/docker-compose.yml up -d
```

### Kubernetes

```bash
kubectl apply -f deployments/k8s/
```

## 🤝 贡献

1. Fork 项目
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 🆘 支持

如有问题，请提交Issue或联系开发团队。

---

**🌸 Athena工作平台 - 星河智汇，光耀知途** 💕