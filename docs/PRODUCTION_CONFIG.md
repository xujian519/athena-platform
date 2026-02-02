# 生产环境配置管理规范

**版本**: 1.0.0
**更新时间**: 2024-12-24
**状态**: 生产标准

---

## 🎯 核心原则

**统一配置源**: 生产环境统一使用 `.env.production.local` 作为唯一配置文件

> ⚠️ **重要**: 所有生产部署必须使用 `.env.production.local`，其他配置文件仅作参考或备份

---

## 📁 配置文件说明

### ✅ 当前使用的配置文件

| 文件名 | 大小 | 状态 | 用途 |
|--------|------|------|------|
| `.env.production.local` | 22KB | ✅ **生效中** | 生产环境唯一配置源 |
| `.env.production.unified` | 22KB | 🟡 备份 | 与local相同，保留同步 |
| `.env.production.backup` | 22KB | 🟡 备份 | 自动备份，紧急恢复用 |

### ❌ 已废弃的配置文件

| 文件名 | 状态 | 原因 |
|--------|------|------|
| `.env.production` | ❌ **已废弃** | 配置不完整（仅38行），不应使用 |
| `config/production.yaml` | ❌ **已废弃** | 与ENV不同步，容易混淆 |
| `config/environments/production.yaml` | ❌ **已废弃** | 格式不统一，维护困难 |
| `services/*/config/production.yaml` | ❌ **已废弃** | 分散配置，难以管理 |

---

## 🚀 部署配置规范

### 标准部署流程

```bash
# 1. 确认配置文件存在
ls -la .env.production.local

# 2. 验证配置完整性
python dev/scripts/validate_env.py --env .env.production.local

# 3. 加载配置启动服务
docker-compose --env-file .env.production.local up -d

# 或使用Python直接加载
export $(cat .env.production.local | xargs) && python main.py
```

### Docker Compose 配置

```yaml
# docker-compose.yml 标准写法
version: '3.8'
services:
  athena-platform:
    env_file:
      - .env.production.local  # ✅ 唯一配置源
    # 不要使用其他.env文件
```

### Python 配置加载

```python
# config_loader.py 标准写法
from dotenv import load_dotenv
import os

# ✅ 正确：加载生产配置
load_dotenv('.env.production.local')

# ❌ 错误：不要使用
# load_dotenv('.env.production')  # 配置不完整
# load_dotenv('config/production.yaml')  # 格式不同
```

---

## 🔧 配置文件结构

### .env.production.local 标准结构

```bash
# =============================================================================
# Athena工作平台 - 统一生产环境配置文件
# =============================================================================
# 版本: 1.0.0
# 更新时间: 2024-12-24

# 1. 基础环境配置
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# 2. 数据库配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=athena_production
# ... 更多配置

# 3. API服务配置
API_HOST=0.0.0.0
API_PORT=8000
# ... 更多配置

# 总计：719行完整配置
```

---

## 📋 配置更新流程

### 日常更新流程

```bash
# 1. 编辑配置文件
vim .env.production.local

# 2. 验证配置语法
python dev/scripts/validate_env.py --env .env.production.local

# 3. 创建备份
cp .env.production.local .env.production.backup.$(date +%Y%m%d_%H%M%S)

# 4. 重启服务使配置生效
docker-compose --env-file .env.production.local restart
```

### 紧急回滚流程

```bash
# 如果配置更新出现问题，立即回滚
cp .env.production.backup .env.production.local
docker-compose --env-file .env.production.local restart
```

---

## ⚠️ 安全注意事项

### 敏感信息管理

```yaml
禁止事项:
  ❌ 将 .env.production.local 提交到Git仓库
  ❌ 在代码中硬编码密钥和密码
  ❌ 通过邮件或即时通讯传输配置文件

推荐做法:
  ✅ 使用 .gitignore 排除配置文件
  ✅ 使用密钥管理系统（AWS Secrets Manager / HashiCorp Vault）
  ✅ 定期轮换密钥和访问令牌
```

### 文件权限

```bash
# 设置严格的文件权限
chmod 600 .env.production.local
chmod 600 .env.production.backup
chmod 600 .env.production.unified

# 验证权限
ls -la .env.production*
```

---

## 🔍 配置验证

### 自动化检查

```bash
# 运行一致性检查
python dev/scripts/services_consistency_check.py

# 检查配置完整性
python dev/scripts/validate_env.py --env .env.production.local --strict
```

### 检查清单

- [ ] 配置文件存在：`.env.production.local`
- [ ] 文件权限正确：`chmod 600`
- [ ] 配置完整：719行，无缺失项
- [ ] 无敏感信息泄露
- [ ] 备份文件已更新
- [ ] Git忽略规则已配置

---

## 📊 配置迁移记录

### 历史变更

| 日期 | 操作 | 说明 |
|------|------|------|
| 2024-12-24 | 统一配置 | 将12个分散配置文件统一为 `.env.production.local` |
| 2024-12-24 | 创建备份 | 生成 `.env.production.backup` |
| 2024-12-24 | 文档化 | 创建本配置规范文档 |

### 废弃配置处理

```bash
# 已废弃的配置文件（仅供参考，不要删除）
.env.production                    # 38行不完整配置
config/production.yaml             # YAML格式配置
config/environments/production.yaml
services/*/config/production.yaml  # 分散的服务配置
```

---

## 🆘 故障排查

### 常见问题

**Q1: 服务启动失败，提示配置项缺失**
```bash
# 解决方案：检查是否加载了正确的配置文件
echo $ENVIRONMENT  # 应该输出：production
docker-compose config | grep env_file  # 确认使用 .env.production.local
```

**Q2: 配置更新后不生效**
```bash
# 解决方案：完全重启服务
docker-compose --env-file .env.production.local down
docker-compose --env-file .env.production.local up -d
```

**Q3: 找不到某个配置项**
```bash
# 解决方案：验证配置文件完整性
grep -r "CONFIG_KEY" .env.production.local
# 如果不存在，从 .env.production.template 恢复
```

---

## 📞 支持和联系

- **配置问题**: 联系DevOps团队
- **部署问题**: 查看部署文档
- **紧急问题**: 使用 `.env.production.backup` 立即回滚

---

**文档维护**: DevOps团队
**最后审核**: 2024-12-24
**下次审核**: 2025-01-24

---

> 💡 **提示**: 定期检查配置文件的一致性，确保所有部署使用相同的配置源。
