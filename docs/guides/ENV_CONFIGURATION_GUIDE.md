# 环境配置说明

> **最后更新**: 2026-04-21
> **第1阶段 Day 6: 统一环境配置**

---

## 📁 配置文件结构

### 配置文件清单

| 文件 | 用途 | 行数 | 状态 |
|------|------|------|------|
| `.env` | 基础环境配置（所有环境共享） | 290行 | ✅ 已存在 |
| `.env.development` | 开发环境特定配置 | 7行 | ✅ 已重命名 |
| `.env.test` | 测试环境特定配置 | 10行 | ✅ 已存在 |
| `.env.production` | 生产环境特定配置 | 90行 | ✅ 已存在 |

### 配置文件说明

#### 1. `.env` - 基础环境配置
**用途**: 所有环境共享的基础配置

**包含内容**:
- 数据库连接配置
- Redis配置
- Qdrant向量数据库配置
- Neo4j图数据库配置
- AI模型API密钥
- MCP服务配置
- 通信服务配置
- 监控配置
- 日志配置
- 安全配置（CORS、JWT等）

#### 2. `.env.development` - 开发环境配置
**用途**: 开发环境特定配置

**特点**:
- 覆盖基础配置中的开发环境特定值
- 7行简洁配置

#### 3. `.env.test` - 测试环境配置
**用途**: 测试环境特定配置

**特点**:
- 测试数据库配置
- 测试环境开关

#### 4. `.env.production` - 生产环境配置
**用途**: 生产环境特定配置

**特点**:
- 生产级安全配置
- 生产数据库配置
- 性能优化配置
- 90行完整配置

---

## 🔧 配置加载机制

### 配置继承

使用 `config/env_loader.py` 进行配置加载：

```python
from config.env_loader import load_env, get_env

# 加载开发环境配置
dev_config = load_env("development")
print(f"开发环境配置: {len(dev_config)} 个变量")

# 加载生产环境配置
prod_config = load_env("production")
print(f"生产环境配置: {len(prod_config)} 个变量")
```

### 加载顺序

1. **基础配置**: 加载 `.env`
2. **环境配置**: 加载 `.env.{environment}`
3. **合并**: 环境特定配置覆盖基础配置

```python
# 示例
# .env: DEBUG=true
# .env.development: DEBUG=false
# 结果: DEBUG=false (环境配置覆盖基础配置)
```

---

## 📝 配置管理最佳实践

### 1. 配置文件分层

```
.env                    # 基础配置（所有环境共享）
├─ .env.development     # 开发环境覆盖
├─ .env.test            # 测试环境覆盖
└─ .env.production      # 生产环境覆盖
```

### 2. 配置优先级

```
环境变量 > .env.{environment} > .env
```

### 3. 安全配置

**敏感信息**（密码、密钥）处理：
- ✅ 使用环境变量
- ✅ 永不提交到Git
- ✅ 生产环境使用强密码
- ✅ 定期轮换密钥

### 4. 配置验证

使用配置加载器验证配置：

```bash
# 验证开发环境配置
python3 config/env_loader.py development

# 验证生产环境配置
python3 config/env_loader.py production
```

---

## 🔄 变更历史

### 2026-04-21 - 第1阶段 Day 6统一

**已删除**:
- ❌ `.env.prod` (3行，内容已整合到.env.production)

**已重命名**:
- ✅ `.env.dev` → `.env.development`

**新增功能**:
- ✅ `config/env_loader.py` - 配置加载器
- ✅ 配置继承机制
- ✅ 配置验证功能

**统一后的配置文件**:
- `.env` (290行) - 基础配置
- `.env.development` (7行) - 开发环境
- `.env.test` (10行) - 测试环境
- `.env.production` (90行) - 生产环境

---

## 🎯 下一步优化

### 短期 (第2阶段)
- [ ] 使用Pydantic Settings管理配置
- [ ] 添加配置验证
- [ ] 添加配置文档生成

### 长期 (第3-4阶段)
- [ ] 配置文件迁移到YAML格式
- [ ] 配置中心化管理
- [ ] 配置版本管理

---

**文档创建时间**: 2026-04-21
**执行阶段**: 第1阶段 Day 6
**维护者**: 徐健 (xujian519@gmail.com)
