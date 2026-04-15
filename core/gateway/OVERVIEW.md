# Athena API Gateway - 项目总览

## 🚀 快速开始

### 本地开发
```bash
# 克隆项目
git clone <repository-url>
cd core/gateway

# 初始化项目
make init

# 启动开发环境
./scripts/dev-start.sh start local

# 或使用Docker启动
./scripts/dev-start.sh start docker
```

### 运行测试
```bash
# 运行所有测试
./scripts/test.sh all

# 快速测试（仅单元测试）
./scripts/test.sh quick

# 生成覆盖率报告
make coverage
```

### 构建和部署
```bash
# 构建二进制文件
make build

# 构建Docker镜像
make docker-build

# 部署到开发环境
ENVIRONMENT=dev ./scripts/deploy.sh deploy
```

## 📁 项目结构

```
gateway/
├── 📄 README.md                  # 项目说明文档
├── 📄 Makefile                  # 构建脚本
├── 📄 go.mod                   # Go模块定义
├── 📄 main.go                  # 主程序入口
├── 📄 Dockerfile                # 生产Docker镜像
├── 📄 Dockerfile.dev            # 开发Docker镜像
├── 📄 docker-compose.yml        # 生产环境编排
├── 📄 docker-compose.dev.yml    # 开发环境编排
├── 📄 .golangci.yml           # 代码质量配置
├── 📄 .pre-commit-config.yaml  # Git钩子配置
├── 📁 internal/                 # 内部包
│   ├── 📁 config/              # 配置管理
│   │   ├── 📄 config.go
│   │   ├── 📄 loader.go
│   │   └── 📄 validator.go
│   ├── 📁 handler/            # HTTP处理器
│   ├── 📁 router/             # 路由管理
│   ├── 📁 auth/               # 认证授权
│   ├── 📁 proxy/              # 代理转发
│   ├── 📁 limiter/            # 限流控制
│   ├── 📁 security/           # 安全防护
│   ├── 📁 monitoring/         # 监控观测
│   ├── 📁 cache/              # 缓存系统
│   └── 📁 utils/              # 工具函数
├── 📁 pkg/                     # 公共包
│   ├── 📁 client/             # 客户端SDK
│   ├── 📁 errors/             # 错误定义
│   └── 📁 logger/             # 日志包
├── 📁 configs/                 # 配置文件
│   ├── 📄 config.yaml         # 默认配置
│   ├── 📄 config.dev.yaml     # 开发环境
│   └── 📄 config.prod.yaml    # 生产环境
├── 📁 scripts/                 # 脚本工具
│   ├── 📄 dev-start.sh       # 开发启动脚本
│   ├── 📄 deploy.sh          # 部署脚本
│   └── 📄 test.sh           # 测试脚本
├── 📁 tests/                   # 测试文件
│   ├── 📁 integration/       # 集成测试
│   ├── 📁 unit/              # 单元测试
│   ├── 📁 e2e/               # 端到端测试
│   └── 📁 benchmark/         # 性能测试
├── 📁 deployments/             # 部署配置
│   ├── 📁 docker/            # Docker部署
│   ├── 📁 k8s/              # Kubernetes部署
│   └── 📁 helm/             # Helm图表
├── 📁 docs/                    # 文档
├── 📁 examples/                # 示例代码
└── 📁 .github/                 # GitHub配置
    └── 📁 workflows/         # CI/CD流水线
```

## ⚙️ 配置管理

### 环境配置
- **开发环境**: `configs/config.dev.yaml` + `.env.dev`
- **生产环境**: `configs/config.prod.yaml` + `.env.prod`
- **默认配置**: `configs/config.yaml`

### 主要配置项
- **服务配置**: 端口、超时、缓冲区大小
- **Redis配置**: 连接池、超时、重试策略
- **认证配置**: JWT密钥、令牌过期时间
- **限流配置**: 策略、阈值、分布式限流
- **代理配置**: 超时、重试、熔断器、负载均衡
- **监控配置**: Prometheus、链路追踪
- **安全配置**: CORS、CSRF、IP白名单

## 🐳 Docker化部署

### 本地开发
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 查看日志
docker-compose -f docker-compose.dev.yml logs -f gateway
```

### 生产部署
```bash
# 构建镜像
docker build -t athena-gateway:latest .

# 启动生产环境
docker-compose up -d

# 检查服务状态
docker-compose ps
```

## 🧪 测试策略

### 测试类型
- **单元测试**: 测试单个函数和模块
- **集成测试**: 测试组件间协作
- **端到端测试**: 测试完整业务流程
- **性能测试**: 基准测试和压力测试
- **安全测试**: 漏洞扫描和依赖检查

### 测试命令
```bash
# 运行所有测试
make test

# 运行特定测试
make test-unit          # 单元测试
make test-integration   # 集成测试
make benchmark         # 性能测试

# 生成覆盖率报告
make coverage
```

## 🔧 开发工具链

### 代码质量
- **格式化**: `go fmt`, `gofmt`
- **静态分析**: `go vet`, `golangci-lint`
- **安全扫描**: `gosec`, `trivy`
- **依赖管理**: `go mod tidy`

### Git钩子
- **Pre-commit**: 代码格式化、静态检查
- **Pre-push**: 测试执行、覆盖率检查
- **Commitizen**: 提交信息规范化

### CI/CD流水线
- **代码检查**: 格式化、静态分析、安全扫描
- **测试执行**: 单元测试、集成测试、端到端测试
- **构建部署**: 多平台构建、Docker镜像、K8s部署
- **发布管理**: 版本标签、GitHub Release

## 📊 监控和观测

### 指标收集
- **Prometheus**: 应用指标、系统指标
- **Jaeger**: 分布式链路追踪
- **Grafana**: 可视化仪表板

### 日志管理
- **结构化日志**: JSON格式、分级记录
- **日志聚合**: 集中收集、索引查询
- **告警通知**: 异常检测、即时通知

### 健康检查
- **服务健康**: HTTP健康检查端点
- **依赖检查**: Redis、数据库连接状态
- **资源监控**: CPU、内存、网络使用率

## 🔒 安全特性

### 认证授权
- **JWT认证**: 无状态令牌验证
- **RBAC权限**: 基于角色的访问控制
- **API密钥**: 服务间认证机制

### 防护措施
- **CORS配置**: 跨域请求控制
- **CSRF防护**: 跨站请求伪造防护
- **限流保护**: 防止DDoS攻击
- **IP白名单**: 访问源控制

### 安全扫描
- **代码扫描**: 静态安全分析
- **依赖检查**: 第三方库漏洞检测
- **容器扫描**: 镜像安全漏洞扫描

## 🚀 性能优化

### 网关性能
- **连接池**: Redis连接复用
- **缓存策略**: 多级缓存优化
- **负载均衡**: 智能流量分发
- **熔断器**: 故障隔离保护

### 资源使用
- **内存优化**: 对象池、垃圾回收调优
- **CPU优化**: 并发处理、goroutine管理
- **网络优化**: 连接复用、压缩传输

## 📚 API文档

### Swagger文档
- **自动生成**: 基于代码注解生成
- **交互式测试**: 在线API测试工具
- **版本管理**: 多版本API支持

### 开发文档
- **API指南**: 请求格式、响应格式
- **配置说明**: 参数详解、示例配置
- **故障排查**: 常见问题解决方案

## 🔄 版本发布

### 版本管理
- **语义化版本**: MAJOR.MINOR.PATCH
- **自动化发布**: 基于Git标签触发
- **多平台构建**: Linux、macOS、Windows

### 部署流程
- **环境隔离**: 开发、测试、生产环境
- **灰度发布**: 渐进式功能发布
- **回滚机制**: 快速故障恢复

## 🛠️ 故障排查

### 常见问题
1. **服务启动失败**: 检查配置文件、端口占用
2. **连接超时**: 检查网络连接、防火墙设置
3. **认证失败**: 检查JWT密钥、令牌过期时间
4. **限流触发**: 检查限流配置、客户端请求频率

### 调试工具
- **日志分析**: 结构化日志查询
- **链路追踪**: 请求链路可视化
- **性能分析**: CPU、内存使用分析

## 🤝 贡献指南

### 开发流程
1. **分支管理**: 功能分支、Pull Request
2. **代码审查**: 自动化检查 + 人工审查
3. **测试要求**: 单元测试、集成测试
4. **提交规范**: Commitizen规范

### 代码规范
- **Go规范**: 遵循官方编码规范
- **命名约定**: 清晰、一致的命名
- **注释要求**: 必要的函数和包注释

## 📞 支持和维护

### 技术支持
- **问题反馈**: GitHub Issues
- **功能请求**: 功能讨论区
- **安全报告**: 私有渠道报告

### 维护计划
- **定期更新**: 依赖包更新、安全补丁
- **性能优化**: 持续性能调优
- **功能增强**: 基于用户反馈的功能迭代

---

**🔗 Athena API Gateway - 连接智能未来**