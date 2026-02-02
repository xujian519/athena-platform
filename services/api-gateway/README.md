# Athena API Gateway

**服务类型**: Node.js + Express.js
**版本**: 1.0.0
**端口**: 8080

## 简介

Athena API网关是整个Athena智能工作平台的统一入口，负责请求路由、认证授权、限流控制等核心功能。

## 技术栈

- **Node.js** 18+
- **Express.js** 4.18.2
- **TypeScript** (支持类型检查)
- **JWT** 身份认证
- **Redis** 缓存和会话存储

## 快速开始

### 1. 安装依赖

```bash
# 安装Node.js依赖
npm install

# 或使用yarn
yarn install
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 启动服务

```bash
# 生产模式启动
npm start

# 开发模式启动（自动重启）
npm run dev

# 构建生产版本
npm run build
```

服务将在 `http://localhost:8080` 启动

## 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| NODE_ENV | development | 运行环境 |
| PORT | 8080 | 服务端口 |
| JWT_SECRET | - | JWT签名密钥（必需） |
| REDIS_URL | redis://localhost:6379 | Redis连接地址 |
| API_TIMEOUT | 30000 | API超时时间(ms) |
| RATE_LIMIT_WINDOW | 15 | 限流时间窗口(分钟) |
| RATE_LIMIT_MAX | 100 | 窗口内最大请求数 |

## API路由

### 核心路由

```javascript
// 健康检查
GET /health

// 网关信息
GET /gateway/info

// 路由列表
GET /gateway/routes
```

### 后端服务代理

```javascript
// AI服务代理
/api/v1/ai/* -> http://localhost:9001

// 智能体服务代理
/api/v1/agents/* -> http://localhost:9002

// 数据服务代理
/api/v1/data/* -> http://localhost:9003
```

### 认证相关

```javascript
// 登录
POST /auth/login

// 刷新Token
POST /auth/refresh

// 登出
POST /auth/logout
```

## 中间件

### 1. 认证中间件
- JWT Token验证
- 用户身份提取
- 权限检查

### 2. 限流中间件
- 基于IP的限流
- 基于用户的限流
- 动态限流策略

### 3. 日志中间件
- 请求日志记录
- 响应时间统计
- 错误日志追踪

### 4. 安全中间件
- CORS配置
- 安全头设置
- XSS防护

## 配置管理

### 路由配置
路由配置在 `config/routes.json`:

```json
{
  "routes": [
    {
      "path": "/api/v1/ai",
      "target": "http://localhost:9001",
      "methods": ["GET", "POST", "PUT", "DELETE"],
      "auth": true,
      "rateLimit": {
        "window": 15,
        "max": 100
      }
    }
  ]
}
```

### 白名单配置
IP白名单在 `config/whitelist.json`:

```json
{
  "ips": ["127.0.0.1", "::1"],
  "ranges": ["192.168.0.0/16"]
}
```

## 监控和日志

### 健康检查
```bash
curl http://localhost:8080/health
```

响应：
```json
{
  "status": "healthy",
  "timestamp": "2023-12-13T23:06:00.000Z",
  "uptime": 3600,
  "version": "1.0.0"
}
```

### Prometheus指标
- `/metrics` 端点暴露Prometheus格式的指标
- 包含请求数、响应时间、错误率等

### 日志格式
```json
{
  "timestamp": "2023-12-13T23:06:00.000Z",
  "level": "info",
  "message": "Request processed",
  "method": "GET",
  "url": "/api/v1/test",
  "status": 200,
  "duration": 45,
  "ip": "127.0.0.1",
  "user": "user123"
}
```

## 开发指南

### 添加新路由

1. 在 `src/routes/` 目录下创建路由文件
2. 在 `config/routes.json` 中添加路由配置
3. 重启服务

```javascript
// src/routes/example.js
const express = require('express');
const router = express.Router();

router.get('/example', (req, res) => {
  res.json({ message: 'Example route' });
});

module.exports = router;
```

### 添加中间件

```javascript
// src/middleware/custom.js
const customMiddleware = (req, res, next) => {
  // 自定义逻辑
  next();
};

module.exports = customMiddleware;
```

## 测试

### 运行测试
```bash
# 运行所有测试
npm test

# 监视模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage
```

### API测试
```bash
# 健康检查
curl http://localhost:8080/health

# 带认证的请求
curl -H "Authorization: Bearer <token>" \
     http://localhost:8080/api/v1/protected
```

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t athena-api-gateway .

# 运行容器
docker run -d \
  -p 8080:8080 \
  -e NODE_ENV=production \
  -e JWT_SECRET=your-secret \
  --name athena-gateway \
  athena-api-gateway
```

### Docker Compose

```yaml
version: '3.8'
services:
  api-gateway:
    build: .
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=production
      - JWT_SECRET=${JWT_SECRET}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

### PM2部署

```bash
# 安装PM2
npm install -g pm2

# 启动服务
pm2 start src/index.js --name "athena-gateway"

# 查看状态
pm2 status

# 查看日志
pm2 logs athena-gateway
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   lsof -i :8080

   # 杀死进程
   kill -9 <PID>
   ```

2. **Redis连接失败**
   - 检查Redis是否运行
   - 验证REDIS_URL配置

3. **JWT无效**
   - 检查JWT_SECRET配置
   - 确保Token未过期

### 调试模式

```bash
# 启用调试日志
DEBUG=athena:* npm start
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交变更
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License

## 联系方式

- 团队：Athena AI Team
- 邮箱：athena@example.com
- 文档：[Athena Platform Docs](https://docs.athena.com)

---

**注意**: 这是Node.js项目，不需要Python的requirements.txt文件。依赖管理通过package.json和package-lock.json进行。