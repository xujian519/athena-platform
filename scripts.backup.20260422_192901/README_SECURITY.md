# Athena安全配置脚本使用指南

本目录包含Athena平台的安全配置和验证脚本。

## 📋 脚本列表

### 1. setup_security_env.sh ⭐ 推荐使用

**用途**: 快速生成和配置所有必需的安全环境变量

**使用方法**:
```bash
# 从项目根目录运行
./scripts/setup_security_env.sh
```

**功能**:
- ✅ 自动生成所有安全密钥（数据库、JWT、Neo4j、Redis等）
- ✅ 创建/更新 .env 文件
- ✅ 自动备份现有的 .env 文件
- ✅ 设置正确的文件权限（600）
- ✅ 自动验证配置

**输出示例**:
```
============================================================================
Athena安全环境变量配置
============================================================================

============================================================================
检查依赖工具
============================================================================
✅ 依赖检查通过

============================================================================
生成安全密钥
============================================================================
✅ DB_PASSWORD: x7mK...2pQ9
✅ JWT_SECRET: a1b2c3d4...e5f6g7h8
✅ NEO4J_PASSWORD: n3oJ...4jPq
✅ REDIS_PASSWORD: r5dS...6tUv

============================================================================
写入环境变量文件
============================================================================
✅ .env 文件已创建

🎉 安全环境变量配置完成！
```

---

### 2. verify_security_config.py

**用途**: 验证安全配置是否正确

**使用方法**:
```bash
# 从项目根目录运行
python3 scripts/verify_security_config.py
```

**功能**:
- ✅ 检查所有必需的环境变量是否已设置
- ✅ 验证密钥长度是否符合要求
- ✅ 检测是否使用了不安全的默认值
- ✅ 扫描代码中是否还有硬编码密钥
- ✅ 验证 .env 文件权限
- ✅ 生成详细的验证报告

**输出示例**:
```
================================================================================
Athena安全配置验证报告
================================================================================

✅ 通过检查 (3 项):
  ✅ DB_PASSWORD (数据库密码)
  ✅ JWT_SECRET (JWT密钥)
  ✅ NEO4J_PASSWORD (Neo4j密码)

⚠️  警告 (1 项):
  ⚠️  REDIS_PASSWORD (Redis密码) 未设置（推荐配置）

================================================================================
🎉 安全配置完美！所有检查都通过了。
================================================================================
```

---

### 3. fix_hardcoded_passwords.py

**用途**: 自动扫描并修复代码中的硬编码密码

**使用方法**:
```bash
# 从项目根目录运行
python3 scripts/fix_hardcoded_passwords.py
```

**功能**:
- 🔍 扫描所有Python文件
- 🔍 识别硬编码的密码和API密钥
- 🔧 自动替换为环境变量调用
- 📝 生成修复报告

**注意事项**:
- 此脚本会修改代码文件
- 建议在运行前提交代码或创建备份
- 修复后需要验证代码能否正常运行

---

## 🚀 快速开始

### 场景1: 全新安装

如果您是第一次配置Athena平台：

```bash
# 1. 运行自动配置脚本
./scripts/setup_security_env.sh

# 2. 验证配置（脚本会自动运行，也可以手动运行）
python3 scripts/verify_security_config.py

# 3. 添加可选的API密钥（如需要）
nano .env
# 编辑添加 OPENAI_API_KEY、ZHIPU_API_KEY 等

# 4. 启动服务
docker-compose -f config/docker/docker-compose.unified-databases.yml up -d
```

### 场景2: 已有项目，需要添加安全配置

```bash
# 1. 运行配置脚本（会自动备份现有.env文件）
./scripts/setup_security_env.sh

# 2. 检查生成的配置
cat .env

# 3. 如需调整某些值，手动编辑
nano .env

# 4. 验证配置
python3 scripts/verify_security_config.py
```

### 场景3: 检查现有配置的安全性

```bash
# 仅运行验证脚本
python3 scripts/verify_security_config.py
```

---

## 📝 手动配置步骤

如果您想手动配置环境变量：

### 1. 创建 .env 文件

```bash
cp .env.example .env
```

### 2. 生成安全密钥

```bash
# 数据库密码
echo "DB_PASSWORD=$(openssl rand -base64 16)" >> .env

# JWT密钥
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env

# Neo4j密码
echo "NEO4J_PASSWORD=$(openssl rand -base64 12)" >> .env

# Redis密码（可选）
echo "REDIS_PASSWORD=$(openssl rand -base64 16)" >> .env
```

### 3. 设置文件权限

```bash
chmod 600 .env
```

### 4. 验证配置

```bash
python3 scripts/verify_security_config.py
```

---

## 🔍 密钥要求

### 必需的环境变量

| 变量名 | 用途 | 最小长度 | 生成命令 |
|--------|------|----------|----------|
| DB_PASSWORD | 数据库密码 | 8字符 | `openssl rand -base64 16` |
| JWT_SECRET | JWT签名密钥 | 32字符 | `openssl rand -hex 32` |
| JWT_SECRET_KEY | JWT备用密钥 | 32字符 | `openssl rand -hex 32` |
| NEO4J_PASSWORD | Neo4j密码 | 8字符 | `openssl rand -base64 12` |

### 推荐的环境变量

| 变量名 | 用途 | 最小长度 | 生成命令 |
|--------|------|----------|----------|
| REDIS_PASSWORD | Redis密码 | 16字符 | `openssl rand -base64 16` |
| ENCRYPTION_KEY | 加密密钥 | 32字符 | `openssl rand -base64 32` |

---

## ⚠️ 常见问题

### Q1: 脚本提示"未找到 openssl 命令"

**解决方案**:
```bash
# macOS
brew install openssl

# Ubuntu/Debian
sudo apt-get install openssl

# CentOS/RHEL
sudo yum install openssl
```

### Q2: 验证脚本显示"环境变量未设置"

**解决方案**:
1. 检查 .env 文件是否存在
2. 确认环境变量已添加到 .env 文件
3. 重启终端或重新加载环境变量

### Q3: .env 文件权限警告

**解决方案**:
```bash
chmod 600 .env
```

### Q4: 数据库连接失败

**解决方案**:
1. 确认数据库密码与 .env 中的 DB_PASSWORD 一致
2. 检查数据库是否正在运行
3. 验证数据库配置（主机、端口）

### Q5: JWT密钥长度不足警告

**解决方案**:
```bash
# 生成更长的JWT密钥（64字符）
echo "JWT_SECRET=$(openssl rand -hex 32)" >> .env
```

---

## 🔒 安全最佳实践

### 1. 密钥管理

- ✅ 使用强密码（至少8个字符）
- ✅ 定期轮换密钥
- ✅ 不要在代码中硬编码密钥
- ✅ 不要将 .env 文件提交到版本控制

### 2. 文件权限

- ✅ .env 文件权限设置为 600
- ✅ 确保只有文件所有者可读写

### 3. 生产环境

- ✅ 使用专门的密钥管理服务（如 HashiCorp Vault）
- ✅ 启用数据库连接加密
- ✅ 使用HTTPS/TLS加密通信
- ✅ 定期审计访问日志

### 4. 开发环境

- ✅ 使用与生产环境不同的密钥
- ✅ 在 .env.local 中配置本地开发变量
- ✅ 不要在生产环境使用开发密钥

---

## 📚 相关文档

- [安全配置指南](../SECURITY_CONFIG_GUIDE.md) - 详细的安全配置说明
- [环境变量示例](../.env.example) - 完整的环境变量模板
- [修复完成报告](../HARDCODED_PASSWORD_FIX_COMPLETION_REPORT.md) - 硬编码密码修复报告

---

## 💡 提示

1. **首次使用**: 强烈建议使用 `setup_security_env.sh` 脚本
2. **定期验证**: 运行 `verify_security_config.py` 确保配置安全
3. **备份重要**: 在修改配置前备份现有的 .env 文件
4. **查看日志**: 如遇问题，查看脚本的详细输出

---

## 🆘 获取帮助

如果遇到问题：

1. 查看脚本输出的错误信息
2. 阅读 [SECURITY_CONFIG_GUIDE.md](../SECURITY_CONFIG_GUIDE.md)
3. 运行 `python3 scripts/verify_security_config.py` 获取详细诊断
4. 联系：xujian519@gmail.com

---

**最后更新**: 2026-01-26
**版本**: 1.0.0
