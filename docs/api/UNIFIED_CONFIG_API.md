# 统一配置系统 API 参考文档

> **Phase 1 - 统一配置管理系统**
> **版本**: 1.0.0
> **更新时间**: 2026-04-21

---

## 目录

- [核心类](#核心类)
- [配置加载器](#配置加载器)
- [配置验证器](#配置验证器)
- [配置适配器](#配置适配器)
- [使用示例](#使用示例)
- [错误处理](#错误处理)

---

## 核心类

### UnifiedSettings

统一配置管理类，基于Pydantic Settings实现。

#### 类签名

```python
class UnifiedSettings(BaseSettings):
    """统一配置管理"""
```

#### 属性

| 属性名 | 类型 | 默认值 | 说明 |
|-------|------|--------|------|
| `environment` | Literal["development", "test", "production"] | "development" | 运行环境 |
| `database_host` | str | "localhost" | 数据库主机 |
| `database_port` | int | 5432 | 数据库端口 |
| `database_user` | str | "athena" | 数据库用户 |
| `database_password` | str | "athena123" | 数据库密码 |
| `database_name` | str | "athena" | 数据库名称 |
| `database_pool_size` | int | 20 | 连接池大小 |
| `database_max_overflow` | int | 10 | 连接池最大溢出 |
| `redis_host` | str | "localhost" | Redis主机 |
| `redis_port` | int | 6379 | Redis端口 |
| `redis_password` | str | "redis123" | Redis密码 |
| `redis_db` | int | 0 | Redis数据库 |
| `qdrant_host` | str | "localhost" | Qdrant主机 |
| `qdrant_port` | int | 6333 | Qdrant端口 |
| `qdrant_collection` | str | "athena" | Qdrant集合 |
| `llm_default_provider` | str | "anthropic" | 默认LLM提供商 |
| `llm_api_key` | Optional[str] | None | LLM API密钥 |
| `llm_model` | str | "claude-sonnet-4-6" | LLM模型 |
| `llm_temperature` | float | 0.7 | LLM温度 |
| `llm_max_tokens` | int | 4096 | LLM最大token数 |

#### 属性方法

##### database_url

```python
@property
def database_url(self) -> str:
    """获取数据库连接URL"""
    return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
```

**返回**: `str` - 数据库连接URL

**示例**:
```python
settings = UnifiedSettings()
print(settings.database_url)
# 输出: postgresql://athena:athena123@localhost:5432/athena
```

##### redis_url

```python
@property
def redis_url(self) -> str:
    """获取Redis连接URL"""
    return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
```

**返回**: `str` - Redis连接URL

##### qdrant_url

```python
@property
def qdrant_url(self) -> str:
    """获取Qdrant连接URL"""
    return f"http://{self.qdrant_host}:{self.qdrant_port}"
```

**返回**: `str` - Qdrant连接URL

#### 类方法

##### get_instance

```python
@classmethod
def get_instance(cls) -> "UnifiedSettings":
    """获取配置单例"""
```

**返回**: `UnifiedSettings` - 配置实例

**说明**: 使用单例模式，确保全局只有一个配置实例

**示例**:
```python
settings1 = UnifiedSettings.get_instance()
settings2 = UnifiedSettings.get_instance()
assert settings1 is settings2  # True
```

#### 使用示例

```python
from core.config.unified_settings import UnifiedSettings

# 方式1: 直接创建
settings = UnifiedSettings()

# 方式2: 使用单例
settings = UnifiedSettings.get_instance()

# 访问配置
print(f"数据库: {settings.database_url}")
print(f"Redis: {settings.redis_url}")
print(f"LLM: {settings.llm_default_provider}")

# 通过环境变量覆盖
# export DATABASE_HOST=prod-db.example.com
settings = UnifiedSettings()
print(settings.database_host)  # prod-db.example.com
```

---

## 配置加载器

### load_full_config

加载完整配置（支持继承）。

#### 函数签名

```python
def load_full_config(
    env: str = "development",
    service: Optional[str] = None
) -> Dict[str, Any]:
    """加载完整配置（支持继承）

    Args:
        env: 环境名称 (development/test/production)
        service: 服务名称 (可选)

    Returns:
        完整配置字典
    """
```

#### 参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `env` | str | "development" | 环境名称 |
| `service` | Optional[str] | None | 服务名称 |

#### 返回

`Dict[str, Any]` - 完整配置字典

#### 加载顺序

1. Base配置 (`config/base/*.yml`)
2. Environment配置 (`config/environments/{env}.yml`)
3. Service配置 (`config/services/{service}.yml`)
4. 环境变量 (优先级最高)

#### 示例

```python
from core.config.unified_config_loader import load_full_config

# 加载开发环境配置
config = load_full_config('development')

# 加载特定服务配置
config = load_full_config('development', 'xiaona')

# 访问配置
database_config = config.get('database', {})
service_config = config.get('service', {})
```

---

## 配置验证器

### ConfigValidator

配置验证器，使用Pydantic进行配置验证。

#### 类方法

##### validate_settings

```python
@staticmethod
def validate_settings(settings: UnifiedSettings) -> bool:
    """验证配置

    Args:
        settings: 配置实例

    Returns:
        是否验证通过
    """
```

#### 验证规则

1. **端口范围**: 1-65535
2. **生产环境**: 必须设置有效密码
3. **LLM温度**: 0.0-2.0
4. **连接池大小**: 必须 > 0

#### 示例

```python
from core.config.unified_settings import UnifiedSettings
from core.config.unified_validator import ConfigValidator

settings = UnifiedSettings()
is_valid = ConfigValidator.validate_settings(settings)

if not is_valid:
    print("配置验证失败")
```

---

## 配置适配器

### ConfigAdapter

配置适配器，用于迁移旧配置。

#### 静态方法

##### adapt_old_database_config

```python
@staticmethod
def adapt_old_database_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """适配旧数据库配置到新格式"""
```

**支持的旧格式**:
- `DATABASE_URL`: postgresql://user:pass@host:port/db
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`

##### adapt_old_redis_config

```python
@staticmethod
def adapt_old_redis_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """适配旧Redis配置到新格式"""
```

**支持的旧格式**:
- `REDIS_URL`: redis://[:password]@host:port/db
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_DB`

##### adapt_old_llm_config

```python
@staticmethod
def adapt_old_llm_config(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """适配旧LLM配置到新格式"""
```

**支持的旧格式**:
- `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`
- `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`

#### 示例

```python
from core.config.config_adapter import ConfigAdapter

# 迁移数据库配置
old_db_config = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/db"
}
new_db_config = ConfigAdapter.adapt_old_database_config(old_db_config)
```

---

## 使用示例

### 基础使用

```python
from core.config.unified_settings import UnifiedSettings

# 创建配置实例
settings = UnifiedSettings()

# 访问配置
db_url = settings.database_url
redis_url = settings.redis_url
llm_provider = settings.llm_default_provider
```

### 环境变量覆盖

```python
import os
from core.config.unified_settings import UnifiedSettings

# 设置环境变量
os.environ['DATABASE_HOST'] = 'prod-db.example.com'
os.environ['LLM_API_KEY'] = 'sk-...'

# 创建配置（自动读取环境变量）
settings = UnifiedSettings()
print(settings.database_host)  # prod-db.example.com
print(settings.llm_api_key)    # sk-...
```

### 服务特定配置

```python
from core.config.unified_config_loader import load_full_config

# 加载小娜服务配置
config = load_full_config('development', 'xiaona')

# 访问服务配置
service_name = config.get('service', {}).get('name')
service_type = config.get('service', {}).get('type')
```

### 配置迁移

```python
from core.config.config_adapter import ConfigAdapter

# 读取旧配置
old_config = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/old_db",
    "DB_HOST": "localhost",
    "DB_PORT": 5432
}

# 迁移到新格式
new_config = ConfigAdapter.adapt_old_database_config(old_config)
```

---

## 错误处理

### 常见错误

#### ValidationError

配置验证失败。

```python
from pydantic import ValidationError

try:
    settings = UnifiedSettings(database_port=99999)
except ValidationError as e:
    print(f"配置验证失败: {e}")
```

#### ConfigNotFoundError

配置文件未找到。

```python
from core.config.unified_config_loader import ConfigNotFoundError

try:
    config = load_full_config('invalid_env')
except ConfigNotFoundError as e:
    print(f"配置文件未找到: {e}")
```

### 错误处理示例

```python
from core.config.unified_settings import UnifiedSettings
from core.config.unified_validator import ConfigValidator
from pydantic import ValidationError

try:
    # 创建配置
    settings = UnifiedSettings()

    # 验证配置
    if not ConfigValidator.validate_settings(settings):
        raise ValueError("配置验证失败")

    # 使用配置
    db_url = settings.database_url

except ValidationError as e:
    print(f"配置验证错误: {e}")
except Exception as e:
    print(f"配置加载失败: {e}")
```

---

## 最佳实践

### 1. 使用单例模式

```python
# 推荐
settings = UnifiedSettings.get_instance()

# 不推荐
settings = UnifiedSettings()
```

### 2. 环境变量命名

```python
# 推荐：大写+下划线
os.environ['DATABASE_HOST'] = 'localhost'

# 不推荐：小写或连字符
os.environ['database_host'] = 'localhost'
```

### 3. 配置分层

```python
# Base配置：所有环境共享
# config/base/database.yml

# Environment配置：环境特定
# config/environments/production.yml

# Service配置：服务特定
# config/services/xiaona.yml
```

### 4. 敏感信息处理

```python
# 不要在配置文件中硬编码敏感信息
# 使用环境变量或密钥管理服务

os.environ['DATABASE_PASSWORD'] = 'secure_password'
settings = UnifiedSettings()
```

---

## 相关文档

- [配置架构设计](../guides/CONFIG_ARCHITECTURE.md)
- [配置迁移指南](../guides/CONFIG_MIGRATION_GUIDE.md)
- [环境配置指南](../guides/ENV_CONFIGURATION_GUIDE.md)

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-21
**维护者**: Claude Code (OMC模式)
