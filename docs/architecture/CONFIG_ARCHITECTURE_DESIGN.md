# Athena统一配置管理架构设计

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 设计阶段

---

## 📋 现状分析

### 当前配置问题

**问题1: 配置文件分散** 🔴
```
.env
.env.development
.env.production
.env.production.xiaonuo
.env.test
config/env/*.yml
core/config/*.py
services/*/config/*
```
- **数量**: 129个配置文件
- **位置**: 分散在多个目录
- **问题**: 难以管理和维护

**问题2: 配置重复** 🔴
- 数据库配置在多个文件中重复
- Redis配置分散
- LLM配置重复定义

**问题3: 配置加载不一致** 🔴
- 有的用环境变量
- 有的用YAML文件
- 有的用Python代码
- **结果**: 混乱且容易出错

**问题4: 缺少配置验证** 🔴
- 没有统一的配置验证
- 配置错误在运行时才暴露
- **风险**: 生产环境配置错误

---

## 🎯 设计目标

### 目标1: 配置文件数量 <50 🎯
- **当前**: 129个
- **目标**: <50个
- **减少**: 60%+

### 目标2: 统一配置架构 🎯
- **分层**: base → environments → services → env vars
- **继承**: 子配置覆盖父配置
- **验证**: 启动时验证配置

### 目标3: 易用性 🎯
- **单一入口**: `from core.config import settings`
- **类型安全**: Pydantic验证
- **自动完成**: IDE支持

### 目标4: 环境友好 🎯
- **开发**: .env.development
- **测试**: .env.test
- **生产**: .env.production

---

## 🏗️ 配置架构设计

### 配置分层结构

```
config/
├── base/                      # 基础配置（所有环境共享）
│   ├── database.yml          # 数据库基础配置
│   ├── redis.yml             # Redis基础配置
│   ├── llm.yml               # LLM基础配置
│   ├── gateway.yml           # Gateway基础配置
│   └── agents.yml            # Agent基础配置
│
├── environments/              # 环境配置
│   ├── development.yml       # 开发环境
│   ├── test.yml              # 测试环境
│   └── production.yml        # 生产环境
│
└── services/                  # 服务配置
    ├── gateway.yml           # Gateway服务配置
    ├── xiaona.yml            # 小娜服务配置
    ├── xiaonuo.yml           # 小诺服务配置
    └── yunxi.yml             # 云熙服务配置
```

### 配置加载顺序

**优先级**（从低到高）:
1. **base/** - 基础配置
2. **environments/{ENV}.yml** - 环境配置
3. **services/{SERVICE}.yml** - 服务配置
4. **环境变量** - 运行时覆盖

**示例**:
```python
# 开发环境的Gateway服务
加载顺序:
1. config/base/gateway.yml        (基础配置)
2. config/environments/development.yml  (开发环境)
3. config/services/gateway.yml    (Gateway服务)
4. 环境变量 GATEWAY_PORT=8006     (运行时覆盖)
```

---

## 📐 配置架构详细设计

### 1. 基础配置层 (config/base/)

**职责**: 定义所有环境共享的配置

**文件列表**:
```yaml
# config/base/database.yml
database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600

# config/base/redis.yml
redis:
  db: 0
  socket_timeout: 5
  socket_connect_timeout: 5
  max_connections: 50

# config/base/llm.yml
llm:
  temperature: 0.7
  max_tokens: 4096
  timeout: 60
  retry: 3

# config/base/gateway.yml
gateway:
  workers: 4
  log_level: info
  timeout: 30

# config/base/agents.yml
agents:
  timeout: 300
  max_retries: 3
  log_level: debug
```

### 2. 环境配置层 (config/environments/)

**职责**: 定义特定环境的配置

**文件列表**:
```yaml
# config/environments/development.yml
environment:
  name: development
  debug: true

database:
  host: localhost
  port: 5432
  user: athena
  password: athena123
  name: athena_dev

redis:
  host: localhost
  port: 6379
  password: redis123

llm:
  provider: anthropic
  model: claude-sonnet-4-6

# config/environments/test.yml
environment:
  name: test
  debug: true

database:
  host: localhost
  port: 5432
  user: athena
  password: athena123
  name: athena_test

# config/environments/production.yml
environment:
  name: production
  debug: false

database:
  host: ${DATABASE_HOST}  # 从环境变量读取
  port: 5432
  user: ${DATABASE_USER}
  password: ${DATABASE_PASSWORD}
  name: athena

redis:
  host: ${REDIS_HOST}
  port: 6379
  password: ${REDIS_PASSWORD}

llm:
  provider: ${LLM_PROVIDER}
  api_key: ${LLM_API_KEY}
  model: ${LLM_MODEL}
```

### 3. 服务配置层 (config/services/)

**职责**: 定义特定服务的配置

**文件列表**:
```yaml
# config/services/gateway.yml
gateway:
  host: 0.0.0.0
  port: 8005
  routes:
    - path: /api/legal/*
      service: xiaona
    - path: /api/coordination/*
      service: xiaonuo

# config/services/xiaona.yml
xiaona:
  agent_type: legal
  model: claude-sonnet-4-6
  temperature: 0.7
  capabilities:
    - patent_analysis
    - legal_research
    - case_retrieval

# config/services/xiaonuo.yml
xiaonuo:
  agent_type: coordinator
  model: claude-opus-4-6
  temperature: 0.5
  auto_spawn: true

# config/services/yunxi.yml
yunxi:
  agent_type: ip_management
  model: claude-sonnet-4-6
  temperature: 0.6
```

---

## 🔧 配置加载器设计

### 核心配置类

```python
# core/config/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from typing import Literal
import yaml
from pathlib import Path

class Settings(BaseSettings):
    """统一配置管理类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # 忽略额外的环境变量
    )

    # 环境配置
    environment: Literal["development", "test", "production"] = "development"
    debug: bool = False

    # 数据库配置
    database_host: str = "localhost"
    database_port: int = 5432
    database_user: str = "athena"
    database_password: str = "athena123"
    database_name: str = "athena"
    database_pool_size: int = 20
    database_max_overflow: int = 10

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.database_user}:{self.database_password}@"
            f"{self.database_host}:{self.database_port}/{self.database_name}"
        )

    # Redis配置
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "redis123"
    redis_db: int = 0
    redis_max_connections: int = 50

    @property
    def redis_url(self) -> str:
        return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # LLM配置
    llm_provider: Literal["openai", "anthropic", "deepseek", "glm"] = "anthropic"
    llm_api_key: str = ""
    llm_model: str = "claude-sonnet-4-6"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    llm_timeout: int = 60
    llm_retry: int = 3

    # Gateway配置
    gateway_host: str = "0.0.0.0"
    gateway_port: int = 8005
    gateway_workers: int = 4
    gateway_log_level: str = "info"

    # Agent配置
    agent_timeout: int = 300
    agent_max_retries: int = 3
    agent_log_level: str = "debug"

    # 配置验证
    @validator("llm_api_key")
    def validate_llm_api_key(cls, v):
        if not v or len(v) < 10:
            raise ValueError("LLM API key must be at least 10 characters")
        return v

    @validator("database_url")
    def validate_database_url(cls, v):
        if not v.startswith("postgresql://"):
            raise ValueError("Invalid database URL")
        return v

    # 从YAML文件加载
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "Settings":
        """从YAML文件加载配置"""
        with open(yaml_path) as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)

    # 加载完整配置（base → environment → service → env）
    @classmethod
    def load(cls, environment: str = None, service: str = None) -> "Settings":
        """加载完整配置（支持继承）"""
        config = {}

        # 1. 加载基础配置
        base_dir = Path("config/base")
        if base_dir.exists():
            for yaml_file in base_dir.glob("*.yml"):
                with open(yaml_file) as f:
                    config.update(yaml.safe_load(f))

        # 2. 加载环境配置
        env = environment or cls._get_environment()
        env_file = Path(f"config/environments/{env}.yml")
        if env_file.exists():
            with open(env_file) as f:
                config.update(yaml.safe_load(f))

        # 3. 加载服务配置（可选）
        if service:
            service_file = Path(f"config/services/{service}.yml")
            if service_file.exists():
                with open(service_file) as f:
                    config.update(yaml.safe_load(f))

        # 4. 环境变量会自动覆盖（Pydantic机制）
        return cls(**config)

    @staticmethod
    def _get_environment() -> str:
        """从环境变量获取当前环境"""
        import os
        return os.getenv("ATHENA_ENV", "development")

    # 单例模式
    _instance = None

    @classmethod
    def get_instance(cls) -> "Settings":
        """获取配置单例"""
        if cls._instance is None:
            cls._instance = cls.load()
        return cls._instance

# 全局配置实例
settings = Settings.get_instance()
```

### 配置加载器

```python
# core/config/loader.py
from typing import Dict, Any
import yaml
from pathlib import Path

def load_config(
    environment: str = "development",
    service: str = None
) -> Dict[str, Any]:
    """加载配置（支持继承）"""
    config = {}

    # 1. 加载基础配置
    base_dir = Path("config/base")
    if base_dir.exists():
        for yaml_file in base_dir.glob("*.yml"):
            with open(yaml_file) as f:
                config.update(yaml.safe_load(f))

    # 2. 加载环境配置
    env_file = Path(f"config/environments/{environment}.yml")
    if env_file.exists():
        with open(env_file) as f:
            config.update(yaml.safe_load(f))

    # 3. 加载服务配置（可选）
    if service:
        service_file = Path(f"config/services/{service}.yml")
        if service_file.exists():
            with open(service_file) as f:
                config.update(yaml.safe_load(f))

    return config
```

---

## 📝 使用示例

### 基础使用

```python
# 导入配置
from core.config.settings import settings

# 访问配置
db_url = settings.database_url
redis_url = settings.redis_url
llm_model = settings.llm_model

# 判断环境
if settings.debug:
    print("开发模式")
```

### 加载特定环境

```python
from core.config.settings import Settings

# 加载开发环境
dev_settings = Settings.load(environment="development")

# 加载生产环境
prod_settings = Settings.load(environment="production")

# 加载特定服务配置
gateway_settings = Settings.load(
    environment="production",
    service="gateway"
)
```

### 环境变量覆盖

```bash
# 运行时覆盖配置
export DATABASE_HOST=prod-db.example.com
export REDIS_HOST=prod-redis.example.com
export LLM_MODEL=claude-opus-4-6

# 启动服务
python3 scripts/xiaonuo_unified_startup.py
```

---

## 🎯 配置迁移计划

### 阶段1: 创建新配置结构 (Day 1-2)

**任务**:
1. 创建config/base/目录
2. 创建config/environments/目录
3. 创建config/services/目录
4. 编写配置架构文档（本文档）

### 阶段2: 实现配置工具 (Day 3-4)

**任务**:
1. 创建core/config/settings.py
2. 创建core/config/loader.py
3. 创建core/config/validator.py
4. 编写单元测试

### 阶段3: 迁移现有配置 (Day 5)

**任务**:
1. 分析现有配置文件（129个）
2. 迁移到新的配置结构
3. 使用适配器兼容旧配置
4. 运行测试验证

### 阶段4: 清理旧配置 (Day 6-7)

**任务**:
1. 删除重复的配置文件
2. 更新配置文档
3. 部署到测试环境
4. 观察48小时

---

## ✅ 验证标准

### 功能验证
- [ ] 配置文件数量从129减少到<50
- [ ] 配置分层结构清晰
- [ ] 配置继承机制工作正常
- [ ] 环境变量覆盖正常

### 质量验证
- [ ] 单元测试覆盖率 >70%
- [ ] 所有服务正常启动
- [ ] 配置验证工作正常
- [ ] 文档完整准确

### 性能验证
- [ ] 配置加载时间 <100ms
- [ ] 内存占用无明显增加
- [ ] 服务启动时间无明显增加

---

## 📊 预期成果

### 配置文件数量

| 类型 | 迁移前 | 迁移后 | 减少 |
|------|--------|--------|------|
| **基础配置** | 分散 | 5个 | - |
| **环境配置** | 7个 | 3个 | 57% |
| **服务配置** | 分散 | 4个 | - |
| **总计** | 129个 | <50个 | **60%+** |

### 配置管理改善

| 维度 | 改善 |
|------|------|
| **可维护性** | ⬆️ 大幅提升 |
| **可读性** | ⬆️ 结构清晰 |
| **可验证性** | ⬆️ 启动时验证 |
| **易用性** | ⬆️ 单一入口 |

---

**文档版本**: v1.0
**最后更新**: 2026-04-21
**状态**: ✅ 配置架构设计完成

**下一步**: 实现配置管理工具（Day 3-4）
