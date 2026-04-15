# Athena API Gateway

🏛️ **统一微服务接入和API管理平台**

**服务类型**: Python + FastAPI  
**版本**: 1.0.0  
**端口**: 8080

## 简介

Athena API Gateway 是一个功能完整的微服务网关系统，提供统一的服务注册、路由管理、负载均衡和API代理功能。

## 🚀 核心特性

### 📋 服务管理
- **自动服务发现**: 微服务自动注册和发现
- **健康检查**: 定期健康检查和故障自动恢复
- **负载均衡**: 支持轮询和随机负载均衡策略
- **服务生命周期**: 完整的服务注册、更新、注销流程

### 🛣️ 路由管理
- **动态路由**: 支持运行时路由配置更新
- **路径匹配**: 灵活的路径匹配和前缀处理
- **HTTP方法支持**: 支持所有HTTP方法的路由
- **路由策略**: 超时控制、重试机制、速率限制

### 🔄 API代理
- **透明代理**: 透明的HTTP请求转发
- **请求/响应处理**: 完整的请求头和响应体处理
- **错误处理**: 统一的错误处理和响应
- **CORS支持**: 跨域资源共享支持

## 🛠️ 快速开始

### 1. 环境要求
- Python 3.8+
- pip (Python包管理器)
- curl (用于测试和健康检查)

### 2. 安装依赖
```bash
cd services/api-gateway
pip3 install -r requirements.txt
```

### 3. 启动完整演示
```bash
# 启动网关和示例服务
./demo.sh start

# 查看服务状态
./demo.sh status

# 运行功能测试
./demo.sh test

# 停止所有服务
./demo.sh stop
```

### 4. 手动启动
```bash
# 启动网关
./start_gateway.sh start

# 启动示例服务
python3 examples/user_service.py &
python3 examples/product_service.py &

# 配置路由
python3 configure_routes.py
```

服务将在 `http://localhost:8080` 启动

## 📁 项目结构

```
services/api-gateway/
├── athena_gateway.py          # 核心网关服务
├── start_gateway.sh            # 网关启动脚本
├── configure_routes.py        # 路由配置脚本
├── test_gateway.py            # 功能测试脚本
├── demo.sh                   # 完整演示脚本
├── requirements.txt           # Python依赖
├── README.md                 # 项目文档
└── examples/                 # 示例微服务
    ├── user_service.py        # 用户服务示例
    └── product_service.py     # 产品服务示例
```

## 📊 服务端点

### Gateway管理API
- `GET /` - 根端点
- `GET /health` - 健康检查
- `GET /docs` - API文档

### 认证管理API
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息
- `GET /api/v1/auth/users` - 获取用户列表 (管理员)
- `POST /api/v1/auth/users` - 创建用户 (管理员)
- `GET /api/v1/auth/api-keys` - 获取API密钥列表
- `POST /api/v1/auth/api-keys` - 创建API密钥
- `DELETE /api/v1/auth/api-keys/{id}` - 删除API密钥
- `GET /api/v1/auth/roles` - 获取角色列表
- `GET /api/v1/auth/permissions` - 获取权限列表

### 服务管理API
- `POST /api/v1/services/register` - 注册服务
- `GET /api/v1/services` - 获取所有服务
- `DELETE /api/v1/services/{service}/instances/{id}` - 注销服务

### 路由管理API
- `POST /api/v1/routes` - 添加路由
- `GET /api/v1/routes` - 获取所有路由

### 示例服务API (通过网关访问)
- `GET /api/users` - 获取所有用户
- `GET /api/users/{id}` - 获取指定用户
- `POST /api/users` - 创建用户
- `GET /api/products` - 获取所有产品
- `GET /api/products/{id}` - 获取指定产品
- `GET /api/categories` - 获取产品分类

## 🔧 配置说明

### 服务注册
```python
registration_data = {
    "service_name": "user-service",
    "instance_id": "unique-instance-id",
    "host": "localhost",
    "port": 8001,
    "protocol": "http",
    "health_endpoint": "/health",
    "metadata": {
        "version": "1.0.0",
        "description": "用户管理服务"
    },
    "tags": ["user", "management"]
}
```

### 路由配置
```python
route_config = {
    "path": "/api/users/*",
    "service_name": "user-service",
    "methods": ["GET", "POST", "PUT", "DELETE"],
    "strip_prefix": True,
    "timeout": 30,
    "retries": 3,
    "rate_limit": {"requests_per_minute": 100},
    "auth_required": False,
    "cors_enabled": True
}
```

## 📈 监控和日志

### 日志文件
- `logs/gateway.log` - 网关运行日志
- `logs/gateway_stdout.log` - 标准输出日志
- `logs/gateway_stderr.log` - 错误输出日志

### 健康检查
```bash
# Gateway健康状态
curl http://localhost:8080/health

# 服务注册状态
curl http://localhost:8080/api/v1/services

# 路由配置状态
curl http://localhost:8080/api/v1/routes
```

## 🧪 测试

### 运行完整测试套件
```bash
# 基础功能测试
python3 test_gateway.py

# 认证功能测试
python3 test_auth.py

# 运行所有测试
./demo.sh test
```

### 认证测试示例
```bash
# 用户登录
curl -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 使用JWT令牌访问API
TOKEN=$(curl -s -X POST http://localhost:8080/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/v1/auth/me

# 使用API密钥访问API
curl -H "X-API-Key: athena-test-key-12345" \
  http://localhost:8080/api/users
```

### 手动测试示例
```bash
# 测试用户服务 (需要认证)
curl -H "X-API-Key: athena-test-key-12345" http://localhost:8080/api/users

# 测试产品服务 (需要认证)
curl -H "X-API-Key: athena-test-key-12345" http://localhost:8080/api/products

# 测试错误处理
curl http://localhost:8080/api/nonexistent
```

## 🔄 部署模式

### 开发环境
```bash
./demo.sh start
```

### 生产环境
```bash
# 使用环境变量配置
export GATEWAY_PORT=8080
export LOG_LEVEL=INFO

# 启动服务
./start_gateway.sh start
```

### Docker部署 (规划中)
```bash
# 构建镜像
docker build -t athena-gateway .

# 运行容器
docker run -p 8080:8080 athena-gateway
```

## 🔒 安全特性

### 认证和授权
- ✅ JWT令牌验证
- ✅ API密钥管理
- ✅ 基于角色的访问控制 (RBAC)
- ✅ 权限精细化控制
- ✅ 用户管理界面

### 安全中间件
- ✅ 双重认证机制 (JWT + API Key)
- ✅ 权限检查中间件
- ✅ CORS跨域控制
- ✅ 安全头设置
- 请求速率限制 (计划中)
- 请求大小限制 (计划中)

## 📈 性能特性

### 负载均衡
- 轮询策略 (Round Robin)
- 随机策略 (Random)
- 最少连接策略 (Least Connections - 计划中)

### 缓存机制
- 路由配置缓存
- 服务实例缓存
- 响应缓存 (计划中)

## 🛠️ 扩展功能

### 已实现
- ✅ 服务注册和发现
- ✅ 动态路由配置
- ✅ 健康检查和负载均衡
- ✅ 请求代理和转发
- ✅ 错误处理和日志
- ✅ 配置持久化

### 已实现
- ✅ JWT认证中间件
- ✅ API密钥管理
- ✅ 用户和角色管理
- ✅ 权限控制系统

### 开发中
- 🔄 请求速率限制
- 🔄 监控指标收集
- 🔄 集群模式支持

### 计划中
- 📋 服务网格集成
- 📋 分布式配置管理
- 📋 链路追踪支持
- 📋 优雅关闭和重启
- 📋 API版本管理

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: athena@example.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/athena/api-gateway/issues)
- 📖 文档: [Athena文档中心](https://docs.athena.example.com)

---

**🏛️ Athena API Gateway** - 让微服务管理变得简单高效!

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: athena@example.com
- 🐛 问题反馈: [GitHub Issues](https://github.com/athena/api-gateway/issues)
- 📖 文档: [Athena文档中心](https://docs.athena.example.com)

---

**🏛️ Athena API Gateway** - 让微服务管理变得简单高效!