# Athena平台数据库资产说明

> **版本**: v1.0  
> **日期**: 2026-04-21  
> **说明**: Athena平台三大核心数据库资产

---

## 📊 数据库资产概览

Athena平台包含三个核心数据库，它们共同构成了平台的数字资产基础：

### 1. Athena主库（PostgreSQL）

**用途**: 系统数据和业务数据

**核心表**:
- 用户管理
- Agent配置
- 任务执行记录
- 系统配置

**连接信息**:
- 主机: localhost:5432
- 数据库: athena
- 用户: athena

**重要性**: ⭐⭐⭐⭐⭐

---

### 2. Patent专利库（PostgreSQL）

**用途**: 专利数据和检索系统

**核心表**:
- patents - 专利主表
- patents_vectors - 专利向量（语义检索）
- patents_citations - 专利引用
- patents_ipc - IPC分类

**连接信息**:
- 主机: localhost:5432
- 数据库: patent_db
- 用户: athena

**配置特性**:
- 全文检索索引
- 向量检索支持
- 引用关系追踪

**重要性**: ⭐⭐⭐⭐⭐

---

### 3. Neo4j法律世界模型

**用途**: 法律知识图谱

**核心实体**:
- 法律概念
- 案例节点
- 关系网络
- 推理规则

**连接信息**:
- 协议: bolt://
- 主机: localhost:7687
- 数据库: neo4j
- 用户: neo4j

**功能**:
- 法律知识推理
- 案例关联分析
- 语义关系查询

**重要性**: ⭐⭐⭐⭐⭐

---

## 🔧 统一配置管理

### 配置文件

**基础配置**:
- `config/base/athena.yml` - Athena主库配置
- `config/base/patent.yml` - Patent专利库配置
- `config/base/neo4j.yml` - Neo4j配置

**环境配置**:
- `config/environments/development.yml` - 开发环境
- `config/environments/test.yml` - 测试环境
- `config/environments/production.yml` - 生产环境

### 配置代码

**配置类**:
- `core/config/database_config.py` - 数据库配置管理
- `core/config/unified_settings.py` - 统一配置类

**使用示例**:
```python
from core.config.database_config import get_database_manager

# 获取数据库管理器
db_manager = get_database_manager()

# 访问三个数据库
athena_config = db_manager.get_athena_config()
patent_config = db_manager.get_patent_config()
neo4j_config = db_manager.get_neo4j_config()

# 获取连接URL
print(athena_config.url)
print(patent_config.url)
print(neo4j_config.bolt_url)
```

---

## ✅ 配置验证

### 验证结果

```bash
📊 Athena平台三大核心数据库资产:

1️⃣ Athena主库（系统数据）
   连接URL: postgresql://athena:***@localhost:5432/athena
   数据库: athena
   连接池: 20个连接

2️⃣ Patent专利库（专利数据）
   连接URL: postgresql://athena:***@localhost:5432/patent_db
   数据库: patent_db
   连接池: 10个连接

3️⃣ Neo4j法律世界模型（知识图谱）
   Bolt URL: bolt://neo4j:***@localhost:7687
   HTTP URL: http://localhost:7474
   数据库: neo4j
```

---

## 🎯 数据库管理最佳实践

### 1. 连接池管理

**Athena主库**:
- pool_size: 20
- max_overflow: 10
- 总连接数: 30

**Patent专利库**:
- pool_size: 10
- max_overflow: 20
- 总连接数: 30

### 2. 查询优化

**使用连接池**:
- 避免频繁创建连接
- 自动回收连接
- 连接复用

**批量操作**:
- 专利数据批量导入
- 向量检索批量处理
- 知识图谱批量查询

### 3. 数据安全

**备份策略**:
- 定期备份Patent专利库
- 备份Neo4j知识图谱
- 备份Athena主库

**访问控制**:
- 数据库密码加密存储
- 限制数据库访问权限
- 审计日志记录

---

## 📝 更新日志

### v1.0 (2026-04-21)

**新增**:
- ✅ 添加Patent专利库配置
- ✅ 添加Neo4j配置
- ✅ 创建DatabaseManager统一管理
- ✅ 更新配置架构文档

**改进**:
- ✅ 支持三个数据库的统一配置
- ✅ 环境变量覆盖
- ✅ 连接池配置

---

**文档版本**: v1.0  
**最后更新**: 2026-04-21  
**状态**: ✅ 数据库资产统一管理完成
