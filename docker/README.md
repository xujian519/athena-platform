# Athena工作平台 Docker 配置

本目录包含所有Docker相关配置文件。

## 目录结构

```
docker/
├── compose/                # Docker Compose 配置文件
│   ├── base.yml           # 基础服务配置
│   ├── development.yml    # 开发环境配置
│   ├── production.yml     # 生产环境配置
│   └── monitoring.yml     # 监控服务配置
├── Dockerfile             # 应用主镜像
├── Dockerfile.dev         # 开发环境镜像
└── .dockerignore          # Docker 忽略文件
```

## 配置文件说明

### 1. 基础服务 (base.yml)
包含所有基础服务配置：
- PostgreSQL 数据库
- Redis 缓存
- Qdrant 向量数据库
- Neo4j 图数据库

### 2. 开发环境 (development.yml)
开发环境特定配置：
- 热重载支持
- 调试端口开放
- 开发工具集成

### 3. 生产环境 (production.yml)
生产环境优化配置：
- 性能优化
- 安全加固
- 日志收集
- 监控集成

### 4. 监控服务 (monitoring.yml)
可选的监控服务：
- Prometheus 指标收集
- Grafana 可视化
- ELK 日志分析

## 使用方法

### 启动基础服务
```bash
docker-compose -f docker/compose/base.yml up -d
```

### 启动开发环境
```bash
docker-compose -f docker/compose/base.yml -f docker/compose/development.yml up -d
```

### 启动生产环境
```bash
docker-compose -f docker/compose/base.yml -f docker/compose/production.yml up -d
```

### 启动监控服务
```bash
docker-compose -f docker/compose/monitoring.yml up -d
```

## 端口分配

| 服务 | 开发环境 | 生产环境 | 说明 |
|------|---------|---------|------|
| PostgreSQL | 5432 | 5432 | 数据库 |
| Redis | 6379 | 6379 | 缓存 |
| Qdrant | 6333 | 6333 | 向量数据库 |
| Neo4j | 7474, 7687 | 7474, 7687 | 图数据库 |
| Athena | 8000 | 8000 | 主应用 |
| API Gateway | 8080 | 8080 | API网关 |
| Prometheus | - | 9090 | 监控 |
| Grafana | - | 3000 | 可视化 |

## 环境变量

创建 `.env` 文件配置环境变量：

```bash
# 数据库配置
POSTGRES_DB=patent_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Redis配置
REDIS_PASSWORD=your_redis_password

# 应用配置
ATHENA_ENV=development
LOG_LEVEL=INFO
```

## 注意事项

1. 生产环境部署前请修改默认密码
2. 确保Docker和Docker Compose版本兼容
3. 根据实际需求调整资源配置
4. 定期更新镜像到最新版本

## 故障排查

### 查看日志
```bash
docker-compose logs -f [service_name]
```

### 停止所有服务
```bash
docker-compose down
```

### 清理未使用的资源
```bash
docker system prune -f
```