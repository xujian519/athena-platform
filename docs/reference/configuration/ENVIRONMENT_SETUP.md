# Athena环境配置指南

## 📋 概述

Athena平台采用统一的环境配置管理方式，支持多环境切换（development、testing、staging、production）。

## 🗂️ 文件结构

```
Athena工作平台/
├── .env                      # 当前激活的环境配置（符号链接或副本）
├── .env.template             # 完整配置模板（包含所有可用配置项）
├── .env.development          # 开发环境配置
├── .env.testing              # 测试环境配置
├── .env.staging              # 预发布环境配置
├── .env.production           # 生产环境配置
├── .env.secrets              # 敏感信息（不提交到git）
├── .env.secrets.template     # 敏感信息模板
└── dev/scripts/
    ├── switch_env.sh         # 环境切换脚本
    └── activate_athena.sh    # 环境激活脚本
```

## 🚀 快速开始

### 1. 初始化环境

首次使用时，复制模板创建配置文件：

```bash
# 复制主配置模板
cp .env.template .env

# 编辑配置，填入实际值
vi .env
```

### 2. 切换环境

使用环境切换脚本：

```bash
# 切换到开发环境
./dev/scripts/switch_env.sh development

# 切换到测试环境
./dev/scripts/switch_env.sh testing

# 切换到生产环境
./dev/scripts/switch_env.sh production
```

### 3. 激活环境

激活Athena环境（加载环境变量）：

```bash
# 方式1: 使用激活脚本
source dev/scripts/activate_athena.sh

# 方式2: 直接加载.env
source .env
```

### 4. 验证环境

```bash
# 检查当前环境
echo $ATHENA_ENV

# 检查Python路径
echo $PYTHONPATH

# 运行测试验证
python dev/scripts/manage_environment.py check
```

## 🔧 配置项说明

### 基础配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ATHENA_ENV` | 环境类型 | development |
| `ATHENA_HOME` | 项目根目录 | /Users/xujian/Athena工作平台 |
| `PYTHONPATH` | Python路径 | ${ATHENA_HOME} |
| `DEBUG` | 调试模式 | false |
| `LOG_LEVEL` | 日志级别 | INFO |

### 数据库配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DB_HOST` | 数据库主机 | localhost |
| `DB_PORT` | 数据库端口 | 5432 |
| `DB_NAME` | 数据库名称 | athena_db |
| `DB_USER` | 数据库用户 | athena_user |
| `DB_PASSWORD` | 数据库密码 | - |

### Redis配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `REDIS_HOST` | Redis主机 | localhost |
| `REDIS_PORT` | Redis端口 | 6379 |
| `REDIS_DB` | Redis数据库 | 0 |

### AI模型配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `GLM_API_KEY` | GLM API密钥 | - |
| `OPENAI_API_KEY` | OpenAI API密钥 | - |
| `MODEL_PATH` | 模型存储路径 | ${ATHENA_HOME}/models |

### 服务端口配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `API_PORT` | 主API端口 | 8000 |
| `YUNPAT_PORT` | YunPat Agent端口 | 8020 |
| `CRAWLER_PORT` | 爬虫服务端口 | 8022 |

## 🛡️ 安全配置

### 敏感信息管理

敏感信息（API密钥、密码等）应存储在 `.env.secrets` 文件中：

```bash
# 复制模板
cp .env.secrets.template .env.secrets

# 编辑敏感信息
vi .env.secrets
```

### 环境特定安全

- **开发环境**: 可以使用默认/测试密钥
- **测试环境**: 使用测试专用密钥
- **生产环境**: 必须使用强密码和真实密钥

## 🔍 故障排查

### 问题1: 环境变量未生效

**症状**: 运行 `echo $ATHENA_ENV` 无输出

**解决**:
```bash
# 确保使用 source 命令
source .env

# 或使用激活脚本
source dev/scripts/activate_athena.sh
```

### 问题2: 找不到Python模块

**症状**: `ModuleNotFoundError: No module named 'core'`

**解决**:
```bash
# 检查PYTHONPATH
echo $PYTHONPATH

# 重新设置
export PYTHONPATH=/Users/xujian/Athena工作平台
```

### 问题3: 数据库连接失败

**症状**: `psycopg2.OperationalError: could not connect`

**解决**:
1. 检查数据库是否运行
2. 验证 `.env` 中的数据库配置
3. 确认数据库用户权限

## 📝 最佳实践

1. **永不提交敏感信息**: `.env.secrets` 和 `.env.docker.prod` 应在 `.gitignore` 中
2. **使用模板管理**: 所有配置变更先在 `.env.template` 中记录
3. **环境隔离**: 不同环境使用独立的数据库和配置
4. **版本控制**: 配置变更应通过PR审核
5. **密钥轮换**: 定期更新生产环境密钥

## 🔗 相关文档

- [统一配置模块](./UNIFIED_CONFIG.md)
- [环境管理工具](../dev/scripts/manage_environment.py)
- [部署指南](./DEPLOYMENT.md)
