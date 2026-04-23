# Athena工作平台项目结构

**最后更新**: 2025-12-13
**版本**: 1.0

## 目录结构概览

```
athena-working-platform/
├── 📁 services/                    # 微服务
│   ├── api-gateway/              # API网关 (8080)
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── router.py
│   │   │   └── security/
│   │   │       └── middleware.py
│   │   ├── requirements.txt
│   │   └── Dockerfile
│   │
│   ├── unified-identity/          # 统一身份认证 (8010)
│   │   ├── app/
│   │   │   ├── auth.py
│   │   │   ├── models.py
│   │   │   └── permissions.py
│   │   └── Dockerfile
│   │
│   ├── yunpat-agent/               # YunPat专利代理 (8020)
│   │   ├── app/
│   │   │   ├── agents/
│   │   │   ├── scrapers/
│   │   │   └── processors/
│   │   └── Dockerfile
│   │
│   ├── browser-automation/         # 浏览器自动化 (8030)
│   │   ├── app/
│   │   │   ├── browser.py
│   │   │   └── tasks/
│   │   └── Dockerfile
│   │
│   └── autonomous-control/         # 自主控制系统 (8040)
│       ├── app/
│       │   ├── controller.py
│       │   └── decision.py
│       └── Dockerfile
│
├── 📁 web/                        # 前端应用
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   ├── store/
│   │   └── router/
│   ├── package.json
│   └── vite.config.js
│
├── 📁 infrastructure/database/                   # 数据库相关
│   ├── migrations/                # 数据库迁移
│   ├── seeds/                     # 初始数据
│   └── dev/scripts/                   # 数据库脚本
│
├── 📁 dev/scripts/                     # 自动化脚本
│   ├── infrastructure/deploy/                    # 部署脚本
│   ├── infrastructure/database/                  # 数据库脚本
│   ├── security/                  # 安全脚本
│   ├── infrastructure/monitoring/                # 监控脚本
│   └── testing/                   # 测试脚本
│
├── 📁 config/                      # 配置文件
│   ├── ports.yaml                 # 端口配置
│   ├── environments/               # 环境配置
│   └── infrastructure/docker/                     # Docker配置
│
├── 📁 infrastructure/monitoring/                  # 监控配置
│   ├── prometheus/                # Prometheus配置
│   ├── grafana/                   # Grafana配置
│   └── alertmanager/              # 告警配置
│
├── 📁 security/                    # 安全配置
│   ├── infrastructure/docker/                     # 容器安全
│   ├── postgresql/                # 数据库安全
│   └── api/                       # API安全
│
├── 📁 docs/                        # 文档
│   ├── api/                        # API文档
│   ├── architecture/               # 架构文档
│   ├── guides/                     # 使用指南
│   └── reference/                  # 参考文档
│
├── 📁 dev/tests/                        # 测试
│   ├── unit/                       # 单元测试
│   ├── integration/                # 集成测试
│   └── e2e/                        # 端到端测试
│
├── 📁 optimization_work/            # 优化工作记录
│   ├── week1_code_quality/
│   ├── week2_refactoring/
│   ├── week3_documentation/
│   ├── week4_automation/
│   └── week5_security/
│
├── 📁 reports/                      # 报告
│   └── consistency_check_summary.md
│
├── 📄 docker-compose.yml             # 服务编排
├── 📄 docker-compose.dev.yml         # 开发环境
├── 📄 docker-compose.prod.yml        # 生产环境
├── 📄 docker-compose.monitoring.yml  # 监控服务
│
├── 📄 requirements.txt               # Python依赖
├── 📄 requirements-dev.txt           # 开发依赖
├── 📄 pyproject.toml                 # 项目配置
├── 📄 .env.example                  # 环境变量示例
├── 📄 .gitignore                    # Git忽略
├── 📄 .pre-commit-config.yaml        # Git钩子
└── 📄 README.md                     # 项目说明
```

## 服务说明

### 核心服务

#### 1. API网关 (api-gateway:8080)
- **职责**: 统一API入口、路由、限流、认证
- **技术栈**: FastAPI + Uvicorn
- **关键特性**:
  - 请求路由和负载均衡
  - API密钥验证
  - 限流和熔断保护
  - CORS处理

#### 2. 统一身份认证 (unified-identity:8010)
- **职责**: 用户认证、授权、会话管理
- **技术栈**: FastAPI + JWT
- **关键特性**:
  - 多因素认证支持
  - RBAC权限控制
  - OAuth2集成
  - 会话管理

#### 3. YunPat专利代理 (yunpat-agent:8020)
- **职责**: 专利数据采集、处理、分析
- **技术栈**: Scrapy + Celery
- **关键特性**:
  - 多源专利数据采集
  - 智能数据清洗
  - 并发处理
  - 失败重试

#### 4. 浏览器自动化 (browser-automation:8030)
- **职责**: 网页自动化、截图、交互
- **技术栈**: Selenium + Playwright
- **关键特性**:
  - 多浏览器支持
  - 并行执行
  - 截图管理
  - 报告生成

#### 5. 自主控制系统 (autonomous-control:8040)
- **职责**: 智能决策、任务调度
- **技术栈**: Python + Redis + Celery
- **关键特性**:
  - 任务优先级管理
  - 智能调度算法
  - 状态跟踪
  - 故障恢复

### 支撑服务

#### 监控服务
- **Prometheus** (9090): 指标收集
- **Grafana** (3000): 可视化仪表盘
- **AlertManager** (9093): 告警管理
- **Node Exporter** (9100): 系统指标

### 数据服务
- **PostgreSQL** (5432): 主数据库
- **Redis** (6379): 缓存和队列
- **Qdrant** (6333): 向量搜索

## 部署模式

### 开发环境
```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d
```

### 生产环境
```bash
# 启动生产环境
docker-compose -f docker-compose.prod.yml up -d
```

### 监控部署
```bash
# 启动监控服务
docker-compose -f docker-compose.monitoring.yml up -d
```

## 开发工作流

### 1. 开发分支策略
- `main`: 主分支，生产代码
- `develop`: 开发分支，集成功能
- `feature/*`: 功能分支
- `hotfix/*`: 热修复分支

### 2. 代码质量检查
```bash
# 预提交检查
pre-commit run --all-files

# 手动质量检查
./dev/scripts/quality/check-quality.sh
```

### 3. 测试流程
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest dev/tests/unit/
pytest dev/tests/integration/
```

## 环境变量

### 必需的环境变量
```bash
# 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=athena_patent
POSTGRES_USER=athena_admin
POSTGRES_PASSWORD=your_password

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# JWT配置
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=HS256

# 监控配置
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000
```

## 配置管理

### 环境配置优先级
1. 环境变量
2. .env文件
3. 配置文件
4. 默认值

### 配置文件结构
```
config/
├── environments/
│   ├── development.yaml
│   ├── staging.yaml
│   └── production.yaml
└── default.yaml
```

## 数据流向

```
用户请求 → API网关 → 认证服务 → 业务服务 → 数据库
                ↓
            ←← 监控/日志 ←← ←←←←←←←←←
```

## 扩展指南

### 添加新服务
1. 创建服务目录: `services/new-service/`
2. 实现服务接口
3. 添加Dockerfile
4. 更新docker-compose配置
5. 添加监控配置

### 添加新功能
1. 创建功能分支
2. 开发功能代码
3. 编写测试
4. 更新文档
5. 提交合并请求

## 安全考虑

- API网关统一入口
- 身份认证和授权
- 数据传输加密
- 定期安全扫描
- 容器安全配置

## 维护指南

### 日志位置
- 应用日志: `/var/log/athena/`
- 数据库日志: `/var/log/postgresql/`
- 访问日志: `/var/log/infrastructure/infrastructure/nginx/`

### 备份策略
- 数据库: 每日自动备份
- 代码: Git版本控制
- 配置: 文档管理

### 监控指标
- 应用性能指标
- 系统资源使用
- 错误率统计
- 用户活跃度