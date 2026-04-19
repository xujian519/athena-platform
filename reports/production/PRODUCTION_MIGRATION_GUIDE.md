# 🔧 生产环境硬编码密码修复指南

> 📅 创建时间: 2025-12-29
> 🎯 目标: 迁移硬编码密码到环境变量
> 👤 执行人: 徐健

---

## 📋 问题概述

生产环境中有多个文件硬编码了数据库密码,主要问题:

```
❌ Nebula图数据库密码: "nebula" (20+处)
❌ PostgreSQL密码: "xiaonuo@Athena", "xj781102" (10+处)
❌ 其他敏感配置: 若干
```

**安全风险**:
- 密码明文存储在代码中
- 版本控制系统中暴露密码
- 无法为不同环境使用不同配置
- 密码轮换困难

---

## ✅ 解决方案

### 1. 新增文件

#### `production/.env.example`
环境变量配置模板,包含所有需要配置的敏感信息。

**使用方法**:
```bash
# 复制模板
cd /Users/xujian/Athena工作平台/production
cp .env.example .env

# 编辑.env文件,填写实际密码
vim .env
```

**关键配置**:
```bash
# 数据库密码(必填,否则会报错)
POSTGRES_PASSWORD=your_secure_postgres_password_here
NEBULA_PASSWORD=your_secure_nebula_password_here

# 其他配置有默认值,可选
POSTGRES_HOST=localhost
NEBULA_HOST=localhost
...
```

#### `production/config.py`
安全配置加载器,从环境变量读取配置。

**特性**:
- ✅ 从环境变量加载配置
- ✅ 支持多个.env文件位置
- ✅ 配置验证(必需的密码未设置会报错)
- ✅ 提供便捷的配置获取函数

**使用方法**:
```python
# 方式1: 使用全局配置实例
from production.config import get_config

config = get_config()
password = config.postgres_password
nebula_pwd = config.nebula_password

# 方式2: 使用便捷函数
from production.config import get_postgres_config, get_nebula_config

postgres_cfg = get_postgres_config()
nebula_cfg = get_nebula_config()
```

---

## 🔄 迁移步骤

### 第一步: 准备.env文件

```bash
# 1. 复制配置模板
cd /Users/xujian/Athena工作平台/production
cp .env.example .env

# 2. 编辑.env文件,设置实际密码
vim .env
```

**在.env中设置**:
```bash
# 设置当前硬编码的密码(用于兼容)
POSTGRES_PASSWORD=xiaonuo@Athena
NEBULA_PASSWORD=nebula

# ⚠️ 生产环境部署时,请改为强密码!
# POSTGRES_PASSWORD=your_very_strong_password_here
# NEBULA_PASSWORD=your_very_strong_password_here
```

### 第二步: 修复代码文件

#### 示例1: 修复Nebula连接

**修复前** (`production/scripts/nebula_graph_builder.py:42`):
```python
class NebulaGraphBuilder:
    def __init__(self, hosts=[("localhost", 9669)], user="root", password="nebula"):
        self.password = "nebula"  # ❌ 硬编码
```

**修复后**:
```python
from production.config import get_nebula_config

class NebulaGraphBuilder:
    def __init__(self):
        config = get_nebula_config()
        self.hosts = [(config['host'], config['port'])]
        self.user = config['user']
        self.password = config['password']  # ✅ 从环境变量读取
```

#### 示例2: 修复PostgreSQL连接

**修复前** (`production/scripts/patent_full_text/phase2/config.py:55`):
```python
class DatabaseConfig:
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "athena"
    postgres_password: str = "xiaonuo@Athena"  # ❌ 硬编码
```

**修复后**:
```python
from production.config import get_config

class DatabaseConfig:
    def __init__(self):
        config = get_config()
        self.postgres_host = config.postgres_host
        self.postgres_port = config.postgres_port
        self.postgres_user = config.postgres_user
        self.postgres_password = config.postgres_password  # ✅ 从环境变量读取
```

### 第三步: 验证配置

```bash
# 测试配置加载
cd /Users/xujian/Athena工作平台/production
python3 config.py

# 应该看到:
# ✅ 配置加载成功
#    环境: production
#    PostgreSQL: localhost:5432
#    Nebula: localhost:9669
#    ...
```

---

## 📝 需要修复的文件列表

### 高优先级 (核心服务)

#### Nebula图数据库相关 (20个文件)
```
production/scripts/patent_rules_system/nebula_graph_builder_real.py
production/scripts/patent_rules_system/nebula_graph_builder_sync.py
production/scripts/import_knowledge_graph.py
production/scripts/import_trademark_laws_to_legal_db.py
production/scripts/patent_full_text/phase3/db_integration.py
production/scripts/patent_full_text/phase3/kg_builder_v2.py
production/scripts/patent_full_text/phase3/production_config.py
production/scripts/patent_full_text/phase3/start_full_pipeline.py
production/scripts/patent_full_text/phase2/kg_builder.py
production/scripts/patent_full_text/phase2/config.py
production/scripts/patent_full_text/phase2/postgresql_updater.py
production/scripts/patent_full_text/phase2/pipeline.py
production/scripts/nebula_graph_builder.py
production/scripts/check_nebula_data.py
production/scripts/patent_guideline/patent_guideline_retriever.py
... (以及其他包含nebula密码的文件)
```

#### PostgreSQL相关 (10个文件)
```
production/scripts/patent_full_text/quick_test.py
production/scripts/patent_full_text/phase2/config.py
production/scripts/patent_full_text/phase2/postgresql_updater.py
production/scripts/patent_full_text/phase2/pipeline.py
production/scripts/check_storage_system.py
... (以及其他包含postgres密码的文件)
```

---

## 🛠️ 批量修复脚本

创建批量修复脚本来加速迁移:

```bash
#!/bin/bash
# batch_fix_passwords.sh

echo "🔧 批量修复硬编码密码"

# 1. 备份所有包含硬编码密码的文件
grep -rl "password.*=.*\"nebula\"" production/ | while read file; do
    cp "$file" "$file.hardcoded_backup"
    echo "✅ 已备份: $file"
done

# 2. 添加配置导入到每个文件
grep -rl "password.*=.*\"nebula\"" production/ | while read file; do
    # 检查是否已有import
    if ! grep -q "from production.config import" "$file"; then
        # 在第一个import之前添加
        sed -i '1i from production.config import get_config' "$file"
        echo "✅ 已添加导入: $file"
    fi
done

echo "✅ 批量修复完成!"
echo "⚠️  请手动修改每个文件,将硬编码密码替换为config调用"
```

---

## 🎯 实施建议

### 方案A: 渐进式迁移 (推荐)

**阶段1** (本周):
1. 创建.env文件并设置密码
2. 修复核心服务文件(5-10个)
3. 测试验证

**阶段2** (下周):
1. 修复剩余Nebula相关文件
2. 修复PostgreSQL相关文件
3. 全面测试

**阶段3** (第三周):
1. 删除备份文件
2. 更新文档
3. 建立CI/CD检查

### 方案B: 一次性迁移 (快速但有风险)

1. 一次性修复所有文件
2. 全面测试
3. 部署

**风险**: 可能引入错误,需要仔细测试

---

## ⚠️ 注意事项

### 1. 不要将.env提交到版本控制

**创建 `.gitignore`**:
```bash
# 确保.env不被提交
echo ".env" >> /Users/xujian/Athena工作平台/.gitignore
echo "production/.env" >> /Users/xujian/Athena工作平台/.gitignore
```

### 2. 生产环境密码强度

**密码要求**:
- 至少16个字符
- 包含大小写字母、数字、特殊字符
- 不要使用字典词汇
- 每个环境使用不同密码

**示例**:
```bash
# ❌ 弱密码
POSTGRES_PASSWORD=nebula
POSTGRES_PASSWORD=xiaonuo@Athena

# ✅ 强密码
POSTGRES_PASSWORD=A7$f9xK2@mP5qL8#nR3
```

### 3. 密码轮换

**建议**:
- 每3个月轮换一次密码
- 使用密码管理器生成强密码
- 轮换后更新.env文件
- 重启相关服务

### 4. 备份文件清理

**确认迁移成功后,删除备份**:
```bash
find production/ -name "*.hardcoded_backup" -delete
```

---

## 📊 进度跟踪

### 待修复文件统计

```
Nebula密码:     20个文件
PostgreSQL密码: 10个文件
其他配置:       5个文件
-----------------------
总计:           35个文件
```

### 修复状态

- [ ] 创建.env文件
- [ ] 测试config.py
- [ ] 修复Nebula相关文件 (20个)
- [ ] 修复PostgreSQL相关文件 (10个)
- [ ] 修复其他配置文件 (5个)
- [ ] 全面测试
- [ ] 清理备份文件

---

## 🔗 相关资源

**已创建**:
- `production/.env.example` - 配置模板
- `production/config.py` - 配置加载器
- 本文档 - 迁移指南

**参考**:
- `PRODUCTION_ISSUES_REPORT.md` - 生产环境问题报告
- `check_production_issues.py` - 检查脚本

---

## 📞 帮助

如有问题,请参考:
1. 测试配置加载: `python3 production/config.py`
2. 查看配置模板: `cat production/.env.example`
3. 检查硬编码位置: `python3 check_production_issues.py`

---

> ⚠️ **重要**: 在生产环境部署前,务必确保所有硬编码密码都已迁移到环境变量!

> ✅ **成功标准**: 所有文件都使用`from production.config import get_config`读取密码,不再有硬编码密码!

> 🚀 **下一步**: 完成密码迁移后,建议配置密钥管理系统(如HashiCorp Vault)进一步提升安全性。
