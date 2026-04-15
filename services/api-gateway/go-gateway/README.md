# Athena API Gateway

基于Go语言实现的高性能API网关，为Athena智能工作平台提供统一的API入口、认证授权、限流控制和监控功能。

## 🚀 特性

### 核心功能
- **统一API入口**: 为所有后端服务提供统一的API访问点
- **HTTP服务器**: 基于Gin框架的高性能HTTP服务器
- **路由引擎**: 灵活的路由配置和代理机制
- **负载均衡**: 支持多实例负载均衡和故障转移

### 安全特性
- **JWT认证**: 完整的JWT令牌生成、验证和刷新机制
- **角色授权**: 基于角色的访问控制(RBAC)
- **API密钥**: 支持API密钥认证方式
- **安全中间件**: CORS、安全头、XSS防护等

### 性能特性
- **请求限流**: IP、用户、API密钥多维度限流
- **熔断器**: 服务故障时的自动熔断和恢复
- **连接池**: 数据库连接池优化
- **缓存策略**: Redis缓存支持

### 监控特性
- **Prometheus指标**: 完整的监控指标暴露
- **健康检查**: 服务健康状态监控
- **请求追踪**: 分布式请求追踪
- **性能监控**: 响应时间、错误率等关键指标

## 📁 项目结构

```
go-gateway/
├── cmd/gateway/           # 应用入口
│   └── main.go
├── internal/              # 内部包
│   ├── config/          # 配置管理
│   ├── database/        # 数据库连接
│   ├── gateway/         # 网关核心
│   ├── middleware/      # 中间件
│   ├── models/          # 数据模型
│   ├── monitoring/      # 监控系统
│   └── services/        # 服务管理
├── pkg/                 # 公共包
│   ├── logger/          # 日志系统
│   └── token/           # JWT令牌
├── config/               # 配置文件
│   └── config.yaml
├── tests/               # 测试文件
│   └── gateway_test.go
├── scripts/             # 部署脚本
│   └── deploy.sh
├── docker-compose.yml     # Docker编排
├── Dockerfile           # Docker镜像
└── go.mod              # Go模块
```

## 🛠️ 快速开始

### 环境要求
- Go 1.21+
- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 15+
- Redis 7+

### 本地开发

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd go-gateway
   ```

2. **安装依赖**
   ```bash
   go mod download
   ```

3. **启动基础服务**
   ```bash
   docker-compose up -d postgres redis
   ```

4. **运行网关**
   ```bash
   go run cmd/gateway/main.go -config config/config.yaml
   ```

### Docker部署

1. **构建镜像**
   ```bash
   docker build -t athena-gateway:latest .
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **检查服务状态**
   ```bash
   docker-compose ps
   curl http://localhost:8080/health
   ```

### 生产部署

```bash
# 使用部署脚本
./scripts/deploy.sh prod

# 或手动部署
./scripts/deploy.sh build
./scripts/deploy.sh docker
./scripts/deploy.sh start
```

## ⚙️ 配置

### 配置文件结构

主要配置文件位于 `config/config.yaml`：

```yaml
server:
  port: 8080
  host: "0.0.0.0"
  mode: "debug"          # debug, release, test
  read_timeout: 30
  write_timeout: 30
  idle_timeout: 60

database:
  host: "localhost"
  port: 5432
  user: "athena"
  password: "athena_password"
  db_name: "athena_gateway"
  ssl_mode: "disable"
  max_idle_conns: 10
  max_open_conns: 100
  max_lifetime: 3600

jwt:
  secret: "your-super-secret-jwt-key"
  expiration_time: 3600     # 秒
  refresh_time: 604800       # 秒 (7天)
  issuer: "athena-gateway"

rate_limit:
  enabled: true
  requests_per_minute: 100
  burst_size: 200
  whitelist_enabled: false
  whitelist: ["127.0.0.1"]

services:
  auth:
    url: "http://localhost:9001"
    timeout: 30
    retry_attempts: 3
    circuit_breaker:
      enabled: true
      threshold: 5
      timeout: 60
      reset_timeout: 300
      failure_rate: 0.5
```

### 环境变量

支持通过环境变量覆盖配置：

```bash
# 服务器配置
ATHENA_GATEWAY_SERVER_PORT=8080
ATHENA_GATEWAY_SERVER_HOST=0.0.0.0
ATHENA_GATEWAY_SERVER_MODE=release

# 数据库配置
ATHENA_GATEWAY_DATABASE_HOST=localhost
ATHENA_GATEWAY_DATABASE_PORT=5432
ATHENA_GATEWAY_DATABASE_USER=athena
ATHENA_GATEWAY_DATABASE_PASSWORD=your_password
ATHENA_GATEWAY_DATABASE_DB_NAME=athena_gateway

# JWT配置
ATHENA_GATEWAY_JWT_SECRET=your-super-secret-key
ATHENA_GATEWAY_JWT_EXPIRATION_TIME=3600

# Redis配置
ATHENA_GATEWAY_REDIS_HOST=localhost
ATHENA_GATEWAY_REDIS_PORT=6379
```

## 🔌 API文档

### 认证API

#### 用户登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "123",
    "username": "testuser",
    "email": "user@example.com",
    "roles": ["user"]
  }
}
```

#### 刷新令牌
```http
POST /api/v1/auth/refresh
Authorization: Bearer <refresh_token>
```

#### 用户登出
```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

### 受保护的API

需要认证的API使用Bearer Token认证：

```http
GET /api/v1/users/profile
Authorization: Bearer <access_token>
```

### API密钥认证

使用API密钥进行认证：

```http
GET /api/v1/protected/resource
X-API-Key: <api_key>
```

## 📊 监控

### Prometheus指标

网关暴露以下Prometheus指标：

- `gateway_http_requests_total` - HTTP请求总数
- `gateway_http_request_duration_seconds` - HTTP请求持续时间
- `gateway_auth_total` - 认证请求数
- `gateway_rate_limit_total` - 限流触发次数
- `gateway_service_health` - 服务健康状态
- `gateway_proxy_latency_seconds` - 代理请求延迟

访问指标：`http://localhost:9090/metrics`

### 健康检查

- **健康状态**: `GET /health`
- **就绪状态**: `GET /ready`
- **存活状态**: `GET /live`

### Grafana仪表板

访问Grafana：`http://localhost:3000`
- 默认用户名：admin
- 默认密码：admin123

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
go test -v ./...

# 运行特定测试
go test -v ./internal/gateway

# 运行基准测试
go test -bench=. ./...

# 生成测试覆盖率
go test -cover ./...
```

### 测试覆盖

测试包括：
- 中间件功能测试
- 认证授权测试
- 限流功能测试
- 服务代理测试
- 配置加载测试
- 数据库连接测试

## 🚀 部署脚本

### 脚本功能

部署脚本 `scripts/deploy.sh` 提供以下功能：

```bash
# 检查依赖
./scripts/deploy.sh check

# 构建应用
./scripts/deploy.sh build

# 构建Docker镜像
./scripts/deploy.sh docker

# 启动服务
./scripts/deploy.sh start

# 停止服务
./scripts/deploy.sh stop

# 查看日志
./scripts/deploy.sh logs

# 健康检查
./scripts/deploy.sh health

# 部署开发环境
./scripts/deploy.sh dev

# 部署生产环境
./scripts/deploy.sh prod

# 备份数据
./scripts/deploy.sh backup

# 清理资源
./scripts/deploy.sh cleanup
```

## 🔧 开发指南

### 添加新中间件

1. 在 `internal/middleware/` 目录创建新文件
2. 实现中间件函数
3. 在网关中注册中间件

示例：
```go
func CustomMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        // 中间件逻辑
        c.Next()
    }
}
```

### 添加新服务

1. 在配置文件中添加服务配置
2. 实现服务客户端
3. 添加路由代理规则

### 添加新指标

1. 在 `internal/monitoring/monitoring.go` 中定义指标
2. 在相关代码中记录指标
3. 在文档中说明新指标

## 🐛 故障排除

### 常见问题

**问题**: 端口被占用
```bash
# 查看端口占用
lsof -i :8080

# 杀死进程
kill -9 <PID>
```

**问题**: 数据库连接失败
```bash
# 检查数据库状态
docker-compose logs postgres

# 测试连接
docker-compose exec postgres psql -U athena -d athena_gateway
```

**问题**: Redis连接失败
```bash
# 检查Redis状态
docker-compose logs redis

# 测试连接
docker-compose exec redis redis-cli ping
```

**问题**: 认证失败
- 检查JWT密钥配置
- 验证令牌格式
- 检查令牌过期时间

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f athena-gateway

# 查看所有服务日志
docker-compose logs -f

# 查看最近日志
docker-compose logs --tail=100 athena-gateway
```

## 📈 性能优化

### 数据库优化
- 使用连接池
- 实现查询缓存
- 优化慢查询
- 设置合适的索引

### 缓存策略
- Redis热点数据缓存
- 会话数据缓存
- API响应缓存
- 静态资源缓存

### 并发处理
- 合理设置工作协程数
- 使用缓冲通道
- 避免阻塞操作
- 实现优雅关闭

## 🔒 安全考虑

### 认证安全
- 强密码策略
- JWT密钥轮换
- 令牌过期管理
- 多因素认证支持

### 网络安全
- HTTPS强制
- 安全头设置
- CORS配置
- 输入验证

### 数据安全
- 敏感数据加密
- 审计日志
- 访问控制
- 数据备份

## 📝 更新日志

### v1.0.0 (2024-01-01)
- ✅ 初始版本发布
- ✅ 基础网关功能
- ✅ JWT认证系统
- ✅ 请求限流功能
- ✅ 监控系统集成
- ✅ Docker部署支持

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 编写测试用例
5. 确保测试通过
6. 提交Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 📞 支持

如有问题或建议，请：

1. 查看文档和FAQ
2. 搜索已有Issues
3. 创建新的Issue
4. 联系维护团队

---

**Athena API Gateway** - 为智能工作平台提供强大、安全、高性能的API网关服务。