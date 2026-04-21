# Athena安全配置指南

## 概述

本指南详细说明如何安全配置Athena工作平台，包括环境变量设置、密钥生成和安全最佳实践。

## 🚨 紧急安全通知

**重要发现和修复**：
- ✅ 已修复 **16处** 硬编码密码问题
- ✅ 已创建统一的环境变量配置管理模块
- ✅ 已更新 `.env.example` 文件
- ⚠️ **请立即按照本指南配置生产环境**

## 1. 环境变量配置

### 1.1 必需的环境变量

#### 数据库密码
```bash
# 生成安全密码（16个字符）
openssl rand -base64 16

# 添加到 .env 文件
DB_PASSWORD=<生成的密码>
```

#### JWT密钥
```bash
# 生成JWT密钥（32字节，64个十六进制字符）
openssl rand -hex 32

# 添加到 .env 文件
JWT_SECRET=<生成的密钥>
JWT_SECRET_KEY=<生成的密钥>
```

#### Neo4j密码
```bash
# 生成Neo4j密码
openssl rand -base64 12

# 添加到 .env 文件
NEO4J_PASSWORD=<生成的密码>
```

### 1.2 可选的环境变量

#### Redis密码
```bash
# 生产环境强烈建议设置
REDIS_PASSWORD=<生成的密码>
```

#### AI模型API密钥
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# 智谱AI
ZHIPU_API_KEY=...

# DeepSeek
DEEPSEEK_API_KEY=sk-...
```

## 2. 配置步骤

### 2.1 创建 .env 文件

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
nano .env
```

### 2.2 生成所有必需的密钥

```bash
# 生成数据库密码
echo "DB_PASSWORD=$(openssl rand -base64 16)" >> .env

# 生成JWT密钥
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# 生成Neo4j密码
echo "NEO4J_PASSWORD=$(openssl rand -base64 12)" >> .env

# 生成Redis密码（可选）
echo "REDIS_PASSWORD=$(openssl rand -base64 16)" >> .env
```

### 2.3 验证配置

```bash
# 运行安全验证
python3 -c "
from core.security.env_config import validate_security_config
result = validate_security_config()
if result['valid']:
    print('✅ 安全配置验证通过')
else:
    print('❌ 安全配置存在问题:')
    if result['missing']:
        print(f'  缺失的环境变量: {result[\"missing\"]}')
    if result['weak']:
        print(f'  弱密钥: {result[\"weak\"]}')
"
```

## 3. 已修复的文件清单

### 3.1 核心认证模块
- ✅ `core/auth/authentication.py` - JWT密钥已改为从环境变量读取
- ✅ `shared/auth/auth_middleware.py` - JWT和Redis密码已改为从环境变量读取

### 3.2 数据库连接
- ✅ `tools/patent_archive_updater.py` - 数据库密码已修复
- ✅ `tools/simple_fee_importer.py` - 数据库密码已修复
- ✅ `tools/update_patents_from_fees.py` - 数据库密码已修复
- ✅ `tools/check_database_structure.py` - 数据库密码已修复
- ✅ `tools/patent_archive_ollama_importer_v2.py` - 数据库密码已修复
- ✅ `tools/patent_archive_multimodal_importer.py` - 数据库密码已修复
- ✅ `tools/patent_archive_ollama_importer_v3.py` - 数据库密码已修复
- ✅ `tools/fee_payment_importer.py` - 数据库密码已修复
- ✅ `tools/patent_excel_parser.py` - 数据库密码已修复

### 3.3 知识图谱
- ✅ `knowledge_graph/neo4j_graph_engine.py` - Neo4j密码已改为从环境变量读取

### 3.4 服务模块
- ✅ `services/multimodal/multimodal_api_server.py` - 数据库密码已修复
- ✅ `services/multimodal/hybrid_api_gateway.py` - 数据库密码已修复
- ✅ `services/platform-integration-service/browser_integration_service.py` - 智谱API密钥已修复
- ✅ `services/scripts/xiaonuo_browser_control.py` - 智谱API密钥已修复
- ✅ `services/common-tools-service/browser_automation_tool.py` - 智谱API密钥已修复
- ✅ `services/ai-models/glm-full-suite/glm_unified_client.py` - 智谱API密钥已修复
- ✅ `services/ai-models/deepseek-integration/deepseek_patent_simplified.py` - DeepSeek密钥已修复
- ✅ `services/ai-models/deepseek-integration/deepseek_coder_service.py` - DeepSeek密钥已修复

## 4. 使用统一配置模块

### 4.1 导入配置模块

```python
from core.security.env_config import (
    get_env_var,
    get_database_url,
    get_redis_url,
    get_jwt_secret,
    get_api_key,
    get_neo4j_config,
    get_qdrant_config,
    Config
)
```

### 4.2 使用示例

#### 数据库连接
```python
from sqlalchemy import create_engine
from core.security.env_config import get_database_url

# 使用环境变量构建的数据库URL
engine = create_engine(get_database_url())
```

#### Neo4j连接
```python
from core.security.env_config import get_neo4j_config

config = get_neo4j_config()
driver = GraphDatabase.driver(
    config["uri"],
    auth=(config["username"], config["password"])
)
```

#### API密钥获取
```python
from core.security.env_config import get_api_key

# 获取OpenAI API密钥
openai_key = get_api_key("OPENAI")

# 获取智谱AI密钥
zhipu_key = get_api_key("ZHIPU")
```

## 5. 安全最佳实践

### 5.1 密码强度要求
- 数据库密码：至少8个字符
- JWT密钥：至少32个字符（推荐64个）
- Redis密码：至少16个字符（生产环境）
- Neo4j密码：至少8个字符

### 5.2 密钥生成命令
```bash
# 数据库密码（16字符）
openssl rand -base64 16

# JWT密钥（64字符十六进制）
openssl rand -hex 32

# 通用安全密钥（32字符）
openssl rand -base64 32

# UUID格式密钥
uuidgen
```

### 5.3 文件权限
```bash
# 设置.env文件权限（仅所有者可读写）
chmod 600 .env

# 验证权限
ls -la .env
# 应显示: -rw------- (600)
```

### 5.4 Git忽略配置
确保 `.gitignore` 包含：
```
# 环境变量文件
.env
.env.local
.env.*.local

# 敏感配置文件
*.secret
*.key
secrets/
```

## 6. 生产环境部署检查清单

### 6.1 配置检查
- [ ] 所有密码已设置为强密码（非默认值）
- [ ] JWT_SECRET已设置为至少32个字符的随机值
- [ ] DB_PASSWORD已设置为强密码
- [ ] NEO4J_PASSWORD已设置
- [ ] REDIS_PASSWORD已设置（生产环境）
- [ ] 所有API密钥已配置

### 6.2 文件检查
- [ ] .env文件权限设置为600
- [ ] .env文件未被提交到Git
- [ ] .env.example已更新（不含真实密钥）

### 6.3 功能验证
```bash
# 运行安全配置验证
python3 -c "
from core.security.env_config import validate_security_config
import json
result = validate_security_config()
print(json.dumps(result, indent=2, ensure_ascii=False))
"

# 测试数据库连接
python3 -c "
from core.security.env_config import get_database_url
print('数据库URL:', get_database_url())
"

# 测试Neo4j配置
python3 -c "
from core.security.env_config import get_neo4j_config
config = get_neo4j_config()
print('Neo4j URI:', config['uri'])
print('Neo4j 用户名:', config['username'])
"
```

## 7. 故障排查

### 7.1 常见错误

#### 错误：环境变量未设置
```
SecurityConfigError: 环境变量 DB_PASSWORD 未设置
```
**解决方案**：在 `.env` 文件中添加对应的环境变量

#### 错误：密钥长度不足
```
SecurityConfigError: 环境变量 JWT_SECRET 的值长度必须至少为 32 个字符
```
**解决方案**：使用 `openssl rand -hex 32` 生成更长的密钥

#### 错误：导入失败
```
ModuleNotFoundError: No module named 'core.security.env_config'
```
**解决方案**：确保 `core/security/env_config.py` 文件存在，并添加正确的路径

### 7.2 调试命令
```bash
# 检查环境变量是否加载
python3 -c "import os; print('DB_PASSWORD:', os.getenv('DB_PASSWORD', 'NOT SET'))"

# 验证配置模块
python3 -c "from core.security.env_config import Config; print(Config.DATABASE_URL)"
```

## 8. 迁移指南

### 8.1 从硬编码密码迁移

**之前的代码**：
```python
engine = create_engine("postgresql://postgres:xj781102@localhost:5432/athena")
```

**迁移后的代码**：
```python
from core.security.env_config import get_database_url
engine = create_engine(get_database_url())
```

### 8.2 从配置文件迁移

**之前的代码**：
```python
import yaml
with open('config.yaml') as f:
    config = yaml.safe_load(f)
password = config['database']['password']
```

**迁移后的代码**：
```python
from core.security.env_config import get_env_var
password = get_env_var('DB_PASSWORD')
```

## 9. 相关文档

- [环境变量配置](/.env.example)
- [安全审计报告](/SECURITY_AUDIT_REPORT.md)
- [部署指南](/DEPLOYMENT_GUIDE.md)
- [API文档](/docs/API.md)

## 10. 支持和反馈

如遇到安全问题或需要帮助，请联系：
- 📧 邮箱: xujian519@gmail.com
- 📋 Issue: GitHub Issues

---

**最后更新**: 2026-01-26
**版本**: 1.0.0
**状态**: ✅ 生产就绪
