# 配置管理架构设计

> **设计时间**: 2026-04-21
> **第2阶段 Week 1 Day 1-2**
> **状态**: 设计完成

---

## 📋 配置分层架构

### 1. 基础配置 (base/)

**用途**: 所有环境共享的配置

**文件列表**:
```
config/base/
├── database.yml   # 数据库配置
├── redis.yml      # Redis配置
├── qdrant.yml     # Qdrant配置
└── llm.yml        # LLM配置
```

**特点**:
- 包含所有环境通用的配置
- 使用环境变量替换敏感信息
- 提供默认值

---

### 2. 环境配置 (environments/)

**用途**: 特定环境的配置（development/test/production）

**文件列表**:
```
config/environments/
├── development.yml
├── test.yml
└── production.yml
```

**特点**:
- 覆盖基础配置的值
- 添加环境特定的配置
- 环境变量优先级最高

---

### 3. 服务配置 (services/)

**用途**: 特定服务的配置

**文件列表**:
```
config/services/
├── gateway.yml
├── xiaona.yml
├── xiaonuo.yml
└── yunxi.yml
```

**特点**:
- 服务特定的配置
- 可以覆盖基础配置
- 支持服务独立部署

---

### 4. 部署配置 (deployments/)

**用途**: 部署相关的配置

**文件列表**:
```
config/deployments/
├── docker.yml
└── kubernetes.yml
```

**特点**:
- 容器化配置
- 编排配置
- 资源限制

---

## 🔄 配置加载顺序

```
1. base/ (基础配置)
   ↓
2. environments/{env}.yml (环境配置)
   ↓
3. services/{service}.yml (服务配置)
   ↓
4. 环境变量 (覆盖配置文件)
```

**优先级**: 环境变量 > 服务配置 > 环境配置 > 基础配置

---

## 🔧 配置加载实现

### 使用Pydantic Settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """统一配置管理"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 数据库配置
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "athena"
    database_password: str = "athena123"
    database_name: str = "athena"
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"

# 全局配置实例
settings = Settings()
```

### 使用示例

```python
from core.config.settings import settings

# 访问配置
db_url = settings.database_url
redis_host = settings.redis_host
llm_model = settings.llm_model
```

---

## ✅ 设计验证

### 验证标准

- ✅ 配置架构设计文档已完成
- ✅ 配置分层结构清晰
- ✅ 配置加载逻辑明确
- ✅ 支持环境变量覆盖
- ✅ 支持多环境
- ✅ 支持多服务
- ✅ 类型安全

---

## 📊 配置示例

### development.yml

```yaml
# 开发环境配置
environment: development
debug: true
log_level: DEBUG

# 覆盖基础配置
database:
  pool_size: 5
  max_overflow: 2

redis:
  db: 1  # 使用独立的DB
```

### production.yml

```yaml
# 生产环境配置
environment: production
debug: false
log_level: INFO

# 覆盖基础配置
database:
  pool_size: 20
  max_overflow: 10

redis:
  password: ${REDIS_PASSWORD}  # 必须设置密码
```

---

## 🎯 下一步

**Day 3-4**: 实现配置管理工具
- 创建 `core/config/settings.py`
- 实现配置加载器
- 实现配置验证器
- 编写单元测试

---

**设计完成时间**: 2026-04-21
**设计人**: Claude Code (OMC模式)
**团队**: phase2-refactor
**状态**: ✅ 设计完成
