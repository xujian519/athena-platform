# Phase 1 & 2 快速开始指南

> **Athena工作平台 - 渐进式重构**
> **Phase 1**: 统一配置管理系统
> **Phase 2**: 服务注册中心
> **更新时间**: 2026-04-21

---

## 目录

- [5分钟快速入门](#5分钟快速入门)
- [配置系统使用](#配置系统使用)
- [服务注册使用](#服务注册使用)
- [常见场景](#常见场景)
- [故障排除](#故障排除)

---

## 5分钟快速入门

### 1. 配置系统快速开始

```python
# 导入配置类
from core.config.unified_settings import UnifiedSettings

# 创建配置实例
settings = UnifiedSettings()

# 使用配置
print(f"数据库: {settings.database_url}")
print(f"Redis: {settings.redis_url}")
print(f"LLM提供商: {settings.llm_default_provider}")
```

### 2. 服务注册快速开始

```python
import asyncio
from core.service_registry import (
    get_registry,
    ServiceRegistration
)

async def main():
    # 获取注册中心
    registry = get_registry()

    # 注册服务
    registration = ServiceRegistration(
        service_name="my_service",
        instance_id="my-service-001",
        host="localhost",
        port=8888
    )

    await registry.register_service(registration)

    # 发现服务
    instance = await registry.discover_service("my_service")
    print(f"服务地址: {instance.address}")

asyncio.run(main())
```

---

## 配置系统使用

### 基础配置

#### 1. 查看当前配置

```python
from core.config.unified_settings import UnifiedSettings

settings = UnifiedSettings()

# 数据库配置
print(f"主机: {settings.database_host}")
print(f"端口: {settings.database_port}")
print(f"数据库: {settings.database_name}")

# Redis配置
print(f"Redis: {settings.redis_url}")

# LLM配置
print(f"提供商: {settings.llm_default_provider}")
print(f"模型: {settings.llm_model}")
```

#### 2. 通过环境变量覆盖配置

```bash
# 设置环境变量
export DATABASE_HOST=prod-db.example.com
export DATABASE_PORT=5433
export LLM_API_KEY=sk-your-key-here

# 运行应用
python3 your_app.py
```

或者在代码中：

```python
import os
os.environ['DATABASE_HOST'] = 'prod-db.example.com'

from core.config.unified_settings import UnifiedSettings
settings = UnifiedSettings()
print(settings.database_host)  # prod-db.example.com
```

#### 3. 加载特定环境的配置

```python
from core.config.unified_config_loader import load_full_config

# 开发环境
dev_config = load_full_config('development')

# 生产环境
prod_config = load_full_config('production')

# 测试环境
test_config = load_full_config('test')
```

#### 4. 加载服务特定配置

```python
# 加载小娜服务配置
xiaona_config = load_full_config('development', 'xiaona')

# 访问服务配置
service_info = xiaona_config.get('service', {})
print(f"服务名: {service_info.get('name')}")
print(f"版本: {service_info.get('version')}")
```

---

### 高级配置

#### 1. 自定义配置验证

```python
from core.config.unified_settings import UnifiedSettings
from core.config.unified_validator import ConfigValidator

# 创建配置
settings = UnifiedSettings()

# 验证配置
if ConfigValidator.validate_settings(settings):
    print("配置验证通过")
else:
    print("配置验证失败")
```

#### 2. 迁移旧配置

```python
from core.config.config_adapter import ConfigAdapter

# 旧配置
old_config = {
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/olddb",
    "REDIS_URL": "redis://:password@localhost:6379/0"
}

# 迁移到新格式
new_db_config = ConfigAdapter.adapt_old_database_config(old_config)
new_redis_config = ConfigAdapter.adapt_old_redis_config(old_config)
```

---

## 服务注册使用

### 基础使用

#### 1. 注册服务

```python
import asyncio
from core.service_registry import get_registry, ServiceRegistration

async def register_my_service():
    registry = get_registry()

    registration = ServiceRegistration(
        service_name="xiaona",
        instance_id="xiaona-001",
        host="localhost",
        port=8001,
        metadata={
            "version": "2.0",
            "type": "agent"
        }
    )

    success = await registry.register_service(registration)
    if success:
        print("服务注册成功")

asyncio.run(register_my_service())
```

#### 2. 发现服务

```python
import asyncio
from core.service_registry import get_discovery

async def discover_service():
    discovery = get_discovery()

    # 发现服务
    instance = await discovery.discover("xiaona")

    if instance:
        print(f"服务地址: {instance.address}")
        print(f"服务状态: {instance.status.value}")

asyncio.run(discover_service())
```

#### 3. 发送心跳

```python
import asyncio
from core.service_registry import get_discovery

async def heartbeat_loop():
    discovery = get_discovery()

    while True:
        # 发送心跳
        await discovery.heartbeat("xiaona", "xiaona-001")

        # 等待30秒
        await asyncio.sleep(30)

asyncio.run(heartbeat_loop())
```

---

### 高级使用

#### 1. 使用负载均衡

```python
from core.service_registry import (
    get_discovery,
    LoadBalanceStrategy
)

async def call_service_with_load_balancing():
    discovery = get_discovery()

    # 轮询策略
    instance1 = await discovery.discover(
        "xiaona",
        strategy=LoadBalanceStrategy.ROUND_ROBIN
    )

    # 随机策略
    instance2 = await discovery.discover(
        "xiaona",
        strategy=LoadBalanceStrategy.RANDOM
    )

    # 最少连接策略
    instance3 = await discovery.discover(
        "xiaona",
        strategy=LoadBalanceStrategy.LEAST_CONNECTION
    )
```

#### 2. 获取所有实例

```python
async def get_all_instances():
    discovery = get_discovery()

    # 获取所有实例（包括不健康的）
    all_instances = await discovery.get_all_instances(
        "xiaona",
        healthy_only=False
    )

    # 只获取健康实例
    healthy_instances = await discovery.get_all_instances(
        "xiaona",
        healthy_only=True
    )

    for instance in healthy_instances:
        print(f"{instance.instance_id} @ {instance.address}")
```

#### 3. 健康检查

```python
from core.service_registry import get_registry

async def check_service_health():
    registry = get_registry()

    # 检查所有服务
    result = await registry.check_health()

    print(f"检查总数: {result['total_checked']}")
    print(f"健康: {result['healthy']}")
    print(f"不健康: {result['unhealthy']}")

    # 检查特定服务
    result = await registry.check_health("xiaona")
```

---

## 常见场景

### 场景1: 启动微服务

```python
import asyncio
import aiohttp
from core.service_registry import get_registry, ServiceRegistration

async def start_microservice():
    # 1. 注册服务
    registry = get_registry()

    registration = ServiceRegistration(
        service_name="xiaona",
        instance_id="xiaona-001",
        host="localhost",
        port=8001
    )

    await registry.register_service(registration)

    # 2. 启动心跳任务
    async def heartbeat():
        while True:
            await registry.send_heartbeat("xiaona", "xiaona-001")
            await asyncio.sleep(30)

    asyncio.create_task(heartbeat())

    # 3. 启动HTTP服务
    app = aiohttp.web.Application()
    # ... 添加路由

    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, 'localhost', 8001)
    await site.start()

    print("服务已启动: http://localhost:8001")

    # 4. 保持运行
    try:
        await asyncio.Event().wait()
    finally:
        # 5. 优雅下线
        await registry.deregister_service("xiaona", "xiaona-001")
        await runner.cleanup()

asyncio.run(start_microservice())
```

---

### 场景2: 服务间调用

```python
import asyncio
import aiohttp
from core.service_registry import get_discovery

async def call_xiaona_service():
    discovery = get_discovery()

    # 1. 发现服务
    instance = await discovery.discover("xiaona")

    if not instance:
        print("服务不可用")
        return

    # 2. 调用服务
    url = f"http://{instance.address}/api/analyze"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"text": "测试"}) as resp:
            result = await resp.json()
            print(f"结果: {result}")

asyncio.run(call_xiaona_service())
```

---

### 场景3: 监控服务状态

```python
import asyncio
from core.service_registry import get_registry

async def monitor_services():
    registry = get_registry()

    while True:
        # 获取统计信息
        stats = await registry.get_registry_statistics()

        print(f"""
        服务监控:
        - 总服务数: {stats['total_services']}
        - 总实例数: {stats['total_instances']}
        - 健康实例: {stats['healthy_instances']}
        - 不健康实例: {stats['unhealthy_instances']}
        """)

        # 显示每个服务的详情
        for service_name, service_stats in stats['services'].items():
            print(f"""
            {service_name}:
            - 总实例: {service_stats['total_instances']}
            - 健康: {service_stats['healthy_instances']}
            - 不健康: {service_stats['unhealthy_instances']}
            """)

        # 等待60秒
        await asyncio.sleep(60)

asyncio.run(monitor_services())
```

---

### 场景4: 配置切换

```python
from core.config.unified_settings import UnifiedSettings
from core.config.unified_config_loader import load_full_config
import os

# 开发环境
os.environ['ENVIRONMENT'] = 'development'
dev_settings = UnifiedSettings()

# 生产环境
os.environ['ENVIRONMENT'] = 'production'
prod_settings = UnifiedSettings()

# 或使用加载器
dev_config = load_full_config('development')
prod_config = load_full_config('production')
```

---

## 故障排除

### 配置问题

#### 问题1: 配置文件未找到

**错误信息**:
```
ConfigNotFoundError: 配置文件未找到
```

**解决方案**:
1. 检查配置文件是否存在
```bash
ls -la config/base/
ls -la config/environments/
```

2. 确认文件名正确
```python
# 正确
config = load_full_config('development')

# 错误
config = load_full_config('dev')  # 应该是 'development'
```

---

#### 问题2: 环境变量不生效

**问题**: 设置了环境变量但没有生效

**解决方案**:
1. 确认环境变量名称正确（大写+下划线）
```bash
# 正确
export DATABASE_HOST=localhost

# 错误
export database_host=localhost
export DATABASE-HOST=localhost
```

2. 在导入配置类前设置环境变量
```python
import os
os.environ['DATABASE_HOST'] = 'localhost'

from core.config.unified_settings import UnifiedSettings
settings = UnifiedSettings()
```

---

#### 问题3: 配置验证失败

**错误信息**:
```
ValidationError: 配置验证失败
```

**解决方案**:
1. 检查端口范围 (1-65535)
2. 检查LLM温度 (0.0-2.0)
3. 生产环境必须设置密码

```python
# 错误示例
settings = UnifiedSettings(
    database_port=99999,  # 超出范围
    llm_temperature=3.0   # 超出范围
)

# 正确示例
settings = UnifiedSettings(
    database_port=5432,
    llm_temperature=0.7
)
```

---

### 服务注册问题

#### 问题1: 服务注册失败

**错误信息**:
```
ConnectionError: Redis连接失败
```

**解决方案**:
1. 确认Redis服务正在运行
```bash
# 检查Redis状态
docker-compose ps redis

# 或使用ping
redis-cli ping
```

2. 或使用内存存储（测试环境）
```python
from core.service_registry.storage_memory import InMemoryServiceRegistryStorage
from core.service_registry import ServiceRegistryCenter

storage = InMemoryServiceRegistryStorage()
registry = ServiceRegistryCenter(storage=storage)
```

---

#### 问题2: 服务发现失败

**错误信息**:
```
NoHealthyInstanceError: 没有可用的健康实例
```

**解决方案**:
1. 检查服务是否已注册
```python
services = await discovery.get_service_names()
print(f"已注册服务: {services}")
```

2. 检查服务健康状态
```python
instances = await discovery.get_all_instances(
    "xiaona",
    healthy_only=False  # 包括不健康的实例
)

for instance in instances:
    print(f"{instance.instance_id}: {instance.status.value}")
```

3. 检查心跳是否正常发送
```python
# 确保定期发送心跳
await discovery.heartbeat("xiaona", "xiaona-001")
```

---

#### 问题3: 心跳超时

**问题**: 服务被标记为不健康

**解决方案**:
1. 确保心跳间隔小于超时时间
```python
# 心跳间隔: 30秒
# 超时时间: 300秒（默认）

async def heartbeat_loop():
    while True:
        await discovery.heartbeat("xiaona", "xiaona-001")
        await asyncio.sleep(30)  # 小于300秒
```

2. 或增加超时时间
```python
from core.service_registry import HealthCheckConfig

config = HealthCheckConfig(
    check_type="heartbeat",
    heartbeat_timeout=600  # 10分钟
)
```

---

## 最佳实践

### 1. 配置管理

- ✅ 使用环境变量管理敏感信息
- ✅ 不同环境使用不同配置文件
- ✅ 定期备份配置文件
- ✅ 使用版本控制管理配置（排除敏感信息）

### 2. 服务注册

- ✅ 启动时自动注册服务
- ✅ 定期发送心跳（推荐30秒）
- ✅ 优雅下线时注销服务
- ✅ 使用唯一实例ID（包含UUID或主机名）

### 3. 服务发现

- ✅ 使用负载均衡策略
- ✅ 处理服务不可用的情况
- ✅ 实现重试机制
- ✅ 缓存服务实例（短时间）

### 4. 监控告警

- ✅ 定期检查服务健康状态
- ✅ 监控注册中心统计信息
- ✅ 设置异常告警
- ✅ 记录服务注册/注销事件

---

## 相关文档

- [统一配置系统API](../api/UNIFIED_CONFIG_API.md)
- [服务注册中心API](../api/SERVICE_REGISTRY_API.md)
- [配置架构设计](../guides/CONFIG_ARCHITECTURE.md)
- [服务注册架构设计](../guides/SERVICE_REGISTRY_ARCHITECTURE.md)
- [全面验证报告](../reports/PHASE1_PHASE2_COMPREHENSIVE_VERIFICATION_REPORT_20260421.md)

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-21
**维护者**: Claude Code (OMC模式)
