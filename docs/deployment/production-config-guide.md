# Athena工作平台 - 生产环境配置部署指南

> 版本: 1.0.0
> 更新时间: 2024-12-24
> 适用环境: 生产环境 (Production)

## 目录

1. [概述](#概述)
2. [配置文件说明](#配置文件说明)
3. [快速开始](#快速开始)
4. [详细配置步骤](#详细配置步骤)
5. [配置验证](#配置验证)
6. [安全建议](#安全建议)
7. [常见问题](#常见问题)
8. [附录](#附录)

---

## 概述

本指南说明如何为Athena工作平台配置生产环境。Athena平台采用统一的环境变量配置方式，支持多环境管理（开发、测试、预发布、生产）。

### 配置文件结构

```
Athena工作平台/
├── .env.production.unified    # 统一生产环境配置（新建）
├── .env.staging               # 预发布环境配置
├── .env.development           # 开发环境配置
├── .env.testing               # 测试环境配置
├── .env.template              # 配置模板
├── config/
│   └── config_loader.py       # 配置加载模块
└── dev/scripts/
    └── validate_env.py        # 环境验证脚本
```

---

## 配置文件说明

### 1. `.env.production.unified` - 统一生产环境配置

新建的**生产环境专用配置文件**，包含所有配置项的分类说明。

**特点：**
- 包含27个配置分类，覆盖所有功能模块
- 每个配置项都有详细注释
- 提供默认值和安全建议
- 包含部署前检查清单

**适用场景：**
- 首次部署生产环境
- 需要全面了解所有配置选项
- 作为其他环境配置的参考

### 2. `.env.template` - 配置模板

通用配置模板，适用于所有环境。

**使用方法：**
```bash
# 复制模板并重命名
cp .env.template .env.production

# 编辑配置文件
vim .env.production
```

### 3. `config/config_loader.py` - 配置加载模块

Python配置加载器，提供：
- 多环境配置加载
- 类型安全的配置对象
- 配置验证功能
- 敏感信息脱敏

**使用示例：**
```python
from config.config_loader import ConfigLoader, get_config

# 加载生产环境配置
config = ConfigLoader.load(env="production")

# 或使用全局配置
config = get_config()

# 访问配置
db_url = config.database.url
redis_url = config.redis.url
```

### 4. `dev/scripts/validate_env.py` - 环境验证脚本

验证环境配置的正确性和安全性。

**使用方法：**
```bash
# 验证生产环境配置
python dev/scripts/validate_env.py --env production

# 严格模式（警告视为错误）
python dev/scripts/validate_env.py --env production --strict

# 只验证特定分类
python dev/scripts/validate_env.py --env production --check database,security

# 输出JSON格式
python dev/scripts/validate_env.py --env production --output json

# 生成安全密码
python dev/scripts/validate_env.py --generate-password
```

---

## 快速开始

### 步骤1: 复制配置文件

```bash
# 进入项目目录
cd /Users/xujian/Athena工作平台

# 复制生产环境配置模板
cp .env.production.unified .env.production.local

# 编辑配置文件
vim .env.production.local
```

### 步骤2: 修改必需配置项

**最小必需配置：**

```bash
# 基础配置
ATHENA_ENV=production
DEBUG=false
LOG_LEVEL=WARNING

# 数据库配置
POSTGRES_HOST=your-db-host.internal
POSTGRES_PORT=5432
POSTGRES_USER=athena_prod
POSTGRES_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD
POSTGRES_DB=athena_production

# Redis配置
REDIS_HOST=your-redis-host.internal
REDIS_PORT=6379
REDIS_PASSWORD=CHANGE_THIS_TO_STRONG_REDIS_PASSWORD

# 安全配置
JWT_SECRET_KEY=CHANGE_THIS_TO_SECURE_RANDOM_STRING_MIN_64_CHARS
CORS_ORIGINS=https://your-domain.com
```

### 步骤3: 生成安全密钥

```bash
# 使用验证脚本生成安全密码
python dev/scripts/validate_env.py --generate-password

# 输出示例：
# 生成的安全密码（32字符）:
# aB3$xK9#mP2@qL7&nR5!tW8^yV6%cS4*dF1

# 使用生成的密码替换配置中的占位符
```

### 步骤4: 验证配置

```bash
# 验证配置文件
python dev/scripts/validate_env.py --env production --config .env.production.local

# 如果通过验证，输出：
# ✅ 验证结果: 通过（无错误，但有警告）
```

### 步骤5: 启动应用

```bash
# 加载配置并启动
export ATHENA_ENV=production
python -m athena.main
```

---

## 详细配置步骤

### 1. 基础环境配置

```bash
# 环境类型
ATHENA_ENV=production
ENVIRONMENT=production

# 平台路径
ATHENA_HOME=/app/athena
PYTHONPATH=/app/athena

# 调试模式（生产环境必须关闭）
DEBUG=false

# 日志级别（WARNING或ERROR）
LOG_LEVEL=WARNING

# 服务器配置
HOST=0.0.0.0
PORT=8000
WORKERS=8

# 时区
TZ=Asia/Shanghai
```

**配置说明：**

| 配置项 | 说明 | 生产环境建议值 |
|--------|------|----------------|
| `DEBUG` | 调试模式 | `false`（必须） |
| `LOG_LEVEL` | 日志级别 | `WARNING` 或 `ERROR` |
| `WORKERS` | 工作进程数 | `CPU核心数 * 2 + 1` |
| `TZ` | 时区 | 根据服务器位置设置 |

### 2. 数据库配置

```bash
# PostgreSQL主数据库
POSTGRES_HOST=your-db-cluster.internal
POSTGRES_PORT=5432
POSTGRES_USER=athena_prod_user
POSTGRES_PASSWORD=your_strong_password_here
POSTGRES_DB=athena_production

# 连接池配置
POSTGRES_POOL_SIZE=50
POSTGRES_MAX_OVERFLOW=100
POSTGRES_POOL_TIMEOUT=30
POSTGRES_POOL_RECYCLE=3600
POSTGRES_POOL_PRE_PING=true

# 只读副本（可选）
POSTGRES_READ_REPLICA_HOST=your-db-read-replica.internal
POSTGRES_READ_REPLICA_ENABLED=true
```

**安全建议：**

1. **密码强度：**
   - 最少16个字符
   - 包含大小写字母、数字、特殊字符
   - 使用密码生成工具

2. **连接池大小：**
   - 计算公式：`pool_size = (CPU核心数 * 2) + 有效磁盘数`
   - 生产环境建议：`50-100`

3. **主从复制：**
   - 生产环境强烈建议配置只读副本
   - 读操作自动路由到副本

### 3. Redis配置

```bash
# Redis主配置
REDIS_HOST=your-redis-cluster.internal
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# Redis集群模式（高可用）
REDIS_CLUSTER_MODE=true
REDIS_CLUSTER_NODES=redis-node1:6379,redis-node2:6379,redis-node3:6379

# Redis Sentinel配置
REDIS_SENTINEL_ENABLED=true
REDIS_SENTINEL_MASTER_NAME=athena-master
REDIS_SENTINEL_NODES=sentinel1:26379,sentinel2:26379,sentinel3:26379
```

**高可用方案：**

| 方案 | 适用场景 | 配置复杂度 |
|------|----------|-----------|
| 单实例 | 开发/测试 | 低 |
| 主从复制 | 小型生产 | 中 |
| Redis Cluster | 大型生产 | 高 |
| Redis Sentinel | 高可用生产 | 中 |

### 4. 向量数据库配置

```bash
# Qdrant配置（自托管）
QDRANT_HOST=your-qdrant-cluster.internal
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=athena_vectors_production

# Qdrant Cloud（推荐）
QDRANT_cloud_URL=https://your-cluster.qdrant.io
QDRANT_CLOUD_API_KEY=your_cloud_api_key

# 向量搜索配置
VECTOR_DIMENSION=768
VECTOR_SIMILARITY_THRESHOLD=0.75
VECTOR_SEARCH_LIMIT=100
```

**选择建议：**
- 小规模部署：使用自托管Qdrant
- 大规模/高可用：使用Qdrant Cloud

### 5. AI模型配置

```bash
# GLM模型（智谱AI）
GLM_API_KEY=your_glm_api_key
GLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
GLM_MODEL=glm-4

# DeepSeek模型（推荐用于中文）
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=deepseek-chat

# OpenAI模型（可选）
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# Gemini模型（可选）
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-pro
```

**模型选择建议：**

| 使用场景 | 推荐模型 | 原因 |
|----------|----------|------|
| 中文主要 | GLM-4 / DeepSeek | 中文理解更好 |
| 多语言 | GPT-4 | 支持语言多 |
| 成本敏感 | DeepSeek | 性价比高 |
| 本地部署 | BGE-M3 | 无需API调用 |

### 6. 安全配置

```bash
# JWT配置
JWT_SECRET_KEY=your_secure_random_key_min_64_chars_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=30

# 加密配置
ENCRYPTION_KEY=your_32_char_encryption_key_here
ENCRYPTION_ALGORITHM=AES-256-GCM

# CORS配置（限制域名）
CORS_ORIGINS=https://your-domain.com,https://app.your-domain.com
CORS_ALLOW_CREDENTIALS=true

# API安全
API_KEY_REQUIRED=true
API_RATE_LIMIT_ENABLED=true
API_RATE_LIMIT_PER_MINUTE=100

# SSL/TLS配置
SSL_ENABLED=true
SSL_CERT_PATH=/etc/ssl/certs/athena.crt
SSL_KEY_PATH=/etc/ssl/private/athena.key
```

**安全检查清单：**

- [ ] JWT密钥长度 >= 64字符
- [ ] 加密密钥长度 >= 32字符
- [ ] CORS来源已限制为具体域名
- [ ] SSL/TLS已启用
- [ ] API限流已启用
- [ ] Session Cookie设置了Secure和HttpOnly

### 7. 存储配置

```bash
# 文件上传路径
UPLOAD_PATH=/app/athena/uploads
TEMP_PATH=/app/athena/temp
CACHE_PATH=/app/athena/cache
MAX_UPLOAD_SIZE=104857600  # 100MB

# 阿里云OSS（推荐）
OSS_ENABLED=true
OSS_ACCESS_KEY_ID=your_oss_access_key
OSS_ACCESS_KEY_SECRET=your_oss_secret
OSS_BUCKET=athena-production
OSS_ENDPOINT=oss-cn-hangzhou.aliyuncs.com

# AWS S3（备选）
AWS_S3_ENABLED=false
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_REGION=cn-north-1
AWS_S3_BUCKET=athena-backup
```

### 8. 监控配置

```bash
# 日志配置
LOG_PATH=/app/athena/logs
LOG_LEVEL=WARNING
LOG_FORMAT=json
LOG_MAX_BYTES=104857600  # 100MB
LOG_BACKUP_COUNT=30

# Prometheus监控
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090

# Sentry错误监控
SENTRY_ENABLED=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production

# Grafana可视化
GRAFANA_ENABLED=true
GRAFANA_PORT=3001
GRAFANA_USERNAME=admin
GRAFANA_PASSWORD=your_grafana_password
```

### 9. 告警配置

```bash
# 告警开关
ALERT_ENABLED=true
ALERT_SEVERITY_THRESHOLD=warning

# 邮件告警
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USERNAME=alerts@your-domain.com
SMTP_PASSWORD=your_email_password
ALERT_EMAIL_TO=admin@your-domain.com,oncall@your-domain.com

# Webhook告警（Slack/钉钉/企业微信）
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=your-token
WEWORK_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-key
```

### 10. 微服务配置

```bash
# YunPat Agent服务
YUNPAT_URL=https://yunpat.your-domain.com
YUNPAT_PORT=8020
YUNPAT_DEFAULT_LLM=deepseek-chat

# 小诺服务
XIANUO_URL=https://xiaonuo.your-domain.com
XIANUO_PORT=8021

# 爬虫服务
CRAWLER_URL=https://crawler.your-domain.com
CRAWLER_PORT=8022

# 其他微服务...
```

---

## 配置验证

### 使用验证脚本

```bash
# 基础验证
python dev/scripts/validate_env.py --env production

# 详细输出
python dev/scripts/validate_env.py --env production --verbose

# 严格模式
python dev/scripts/validate_env.py --env production --strict

# 验证特定分类
python dev/scripts/validate_env.py --env production --check database,security

# JSON输出（用于CI/CD）
python dev/scripts/validate_env.py --env production --output json
```

### 验证输出示例

```
======================================================================
Athena环境变量验证报告 - PRODUCTION环境
======================================================================
验证时间: 2024-12-24T10:30:00

【验证摘要】
  总计: 45 项
  ✅ 通过: 38 项
  ⚠️  警告: 5 项
  ❌ 错误: 2 项

✅ 验证结果: 通过（无错误，但有警告）

【详细结果】

【基础配置】
  ✅ 环境类型: 当前环境: production
  ✅ DEBUG模式: DEBUG模式配置正确
  ⚠️  日志级别: 生产环境不建议使用DEBUG级别日志
     当前值: DEBUG
     期望值: WARNING 或 ERROR
     💡 建议: 生产环境建议设置 LOG_LEVEL=WARNING

【数据库】
  ✅ POSTGRES_HOST: 配置有效
  ✅ POSTGRES_PORT: 数据库端口配置
  ❌ POSTGRES_PASSWORD: 使用了弱密码或默认值
     当前值: chang***
     💡 建议: 请使用强密码（至少16个字符，包含大小写字母、数字和特殊字符）

【安全】
  ✅ JWT_SECRET_KEY: 密钥强度符合要求
  ⚠️  CORS_ORIGINS: 生产环境不应允许所有来源的CORS请求
     当前值: *
     期望值: 具体的域名列表
     💡 建议: 生产环境必须限制CORS来源域名
```

---

## 安全建议

### 1. 密钥管理

**最佳实践：**

```bash
# ❌ 不好的做法
POSTGRES_PASSWORD=password123

# ✅ 好的做法
POSTGRES_PASSWORD=aB3$xK9#mP2@qL7&nR5!tW8^yV6%cS4*dF1
```

**生成安全密码：**

```bash
# 使用验证脚本生成
python dev/scripts/validate_env.py --generate-password --password-length 32

# 使用OpenSSL
openssl rand -base64 32

# 使用Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. 密钥存储

**推荐方案优先级：**

1. **密钥管理系统（最佳）**
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault
   - 阿里云KMS

2. **环境变量（推荐）**
   - 通过容器编排系统注入
   - 避免写入配置文件

3. **加密配置文件（备选）**
   - 使用加密工具（如sops）
   - 将加密文件提交到版本控制

### 3. 访问控制

```bash
# 设置配置文件权限
chmod 600 .env.production.local

# 确保只有所有者可读写
ls -la .env.production.local
# 输出: -rw------- 1 athena athena ...

# 避免在日志中输出敏感信息
export LOG_LEVEL=WARNING  # 不要使用DEBUG
```

### 4. 密钥轮换

**定期轮换计划：**

| 密钥类型 | 轮换频率 |
|----------|----------|
| 数据库密码 | 每90天 |
| API密钥 | 每180天 |
| JWT密钥 | 每30天 |
| 加密密钥 | 每365天 |

---

## 常见问题

### Q1: 生产环境必须配置哪些环境变量？

**必需变量：**

```bash
# 基础配置
ATHENA_ENV=production
DEBUG=false

# 数据库
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_DB

# 安全
JWT_SECRET_KEY

# 至少一个AI模型
GLM_API_KEY 或 DEEPSEEK_API_KEY 或 OPENAI_API_KEY
```

### Q2: 如何在Kubernetes中管理配置？

**使用ConfigMap和Secret：**

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: athena-config
data:
  ATHENA_ENV: "production"
  DEBUG: "false"
  LOG_LEVEL: "WARNING"
---
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: athena-secrets
type: Opaque
stringData:
  POSTGRES_PASSWORD: "your-password"
  JWT_SECRET_KEY: "your-secret"
```

**在Pod中引用：**

```yaml
spec:
  containers:
  - name: athena
    envFrom:
    - configMapRef:
        name: athena-config
    - secretRef:
        name: athena-secrets
```

### Q3: 如何在不同环境间切换配置？

```python
# 方法1: 通过环境变量
export ATHENA_ENV=production
python app.py

# 方法2: 通过命令行参数
python app.py --env production

# 方法3: 通过配置文件
cp .env.production .env.local
python app.py
```

### Q4: 验证脚本报告错误如何处理？

**常见错误及解决方案：**

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| JWT密钥长度不足 | 密钥太短 | 使用 >= 64字符的密钥 |
| CORS允许所有来源 | 配置了`*` | 限制为具体域名 |
| DEBUG模式开启 | 生产环境开启DEBUG | 设置 `DEBUG=false` |
| 数据库连接失败 | 配置错误或网络问题 | 检查主机、端口、密码 |

### Q5: 如何使用密钥管理系统？

**AWS Secrets Manager示例：**

```python
import boto3
import json

def get_config():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='athena-production')
    secret = json.loads(response['SecretString'])

    # 更新环境变量
    os.environ.update(secret)
    return ConfigLoader.load()
```

---

## 附录

### A. 配置文件完整示例

参见 `.env.production.unified` 文件。

### B. 配置加载API文档

**主要类和函数：**

```python
# ConfigLoader类
ConfigLoader.load(env: str = None) -> AthenaConfig
ConfigLoader.validate(config: AthenaConfig, strict: bool = False) -> List[str]
ConfigLoader.print_config(config: AthenaConfig, hide_secrets: bool = True)

# 便捷函数
get_config(env: str = None, reload: bool = False) -> AthenaConfig
init_config(env: str = None) -> AthenaConfig
is_production() -> bool
get_database_url() -> str
```

### C. 环境验证脚本选项

```bash
选项:
  --env {development,staging,production,testing}
                        指定要验证的环境
  --strict              严格模式（将警告也视为错误）
  --output {text,json}  输出格式
  --check CATEGORY      指定要验证的分类（逗号分隔）
  --verbose, -v         显示详细信息
  --generate-password   生成安全的随机密码
  --password-length N   生成密码的长度（默认: 32）
```

### D. 故障排查清单

**部署前检查：**

- [ ] 所有密码和密钥已替换为强密码
- [ ] 数据库连接信息已更新
- [ ] Redis连接信息已更新
- [ ] API密钥已配置
- [ ] CORS域名已限制为生产域名
- [ ] SSL证书路径已配置
- [ ] 监控和告警已启用
- [ ] 备份策略已配置
- [ ] 日志级别已设置为WARNING或ERROR
- [ ] DEBUG模式已关闭

---

## 相关文档

- [配置模板](/.env.template)
- [配置加载模块源码](/config/config_loader.py)
- [环境验证脚本源码](/dev/scripts/validate_env.py)
- [系统架构文档](/docs/architecture.md)
- [部署指南](/docs/infrastructure/infrastructure/deployment/README.md)

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0.0 | 2024-12-24 | 初始版本，包含统一配置系统 |

---

**文档维护者：** Athena团队
**最后更新：** 2024-12-24
