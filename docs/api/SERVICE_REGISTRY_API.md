# 服务注册中心 API 参考文档

> **Phase 2 - 服务注册中心**
> **版本**: 1.0.0
> **更新时间**: 2026-04-21

---

## 目录

- [数据模型](#数据模型)
- [服务注册](#服务注册)
- [健康检查](#健康检查)
- [服务发现](#服务发现)
- [统一注册中心](#统一注册中心)
- [使用示例](#使用示例)
- [错误处理](#错误处理)

---

## 数据模型

### ServiceInstance

服务实例数据模型。

#### 类签名

```python
@dataclass
class ServiceInstance:
    """服务实例"""
```

#### 属性

| 属性名 | 类型 | 说明 |
|-------|------|------|
| `instance_id` | str | 实例ID（唯一） |
| `service_name` | str | 服务名称 |
| `host` | str | 主机地址 |
| `port` | int | 端口 |
| `status` | ServiceStatus | 服务状态 |
| `last_heartbeat` | datetime | 最后心跳时间 |
| `metadata` | Dict[str, Any] | 元数据 |
| `created_at` | datetime | 创建时间 |
| `updated_at` | datetime | 更新时间 |

#### 属性方法

##### address

```python
@property
def address(self) -> str:
    """获取服务地址"""
    return f"{self.host}:{self.port}"
```

##### is_healthy

```python
def is_healthy(self) -> bool:
    """判断服务是否健康"""
    return self.status == ServiceStatus.HEALTHY
```

##### is_expired

```python
def is_expired(self, timeout_seconds: int = 300) -> bool:
    """判断服务是否超时"""
```

#### 方法

##### to_dict

```python
def to_dict(self) -> Dict[str, Any]:
    """转换为字典"""
```

##### to_json

```python
def to_json(self) -> str:
    """转换为JSON字符串"""
```

##### touch

```python
def touch(self):
    """更新心跳时间"""
```

---

### ServiceStatus

服务状态枚举。

```python
class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"       # 健康
    UNHEALTHY = "unhealthy"   # 不健康
    DRAINING = "draining"     # 流量排空
    TERMINATED = "terminated" # 已终止
```

---

### LoadBalanceStrategy

负载均衡策略枚举。

```python
class LoadBalanceStrategy(Enum):
    """负载均衡策略"""
    ROUND_ROBIN = "round_robin"       # 轮询
    RANDOM = "random"                 # 随机
    LEAST_CONNECTION = "least_connection"  # 最少连接
    CONSISTENT_HASH = "consistent_hash"    # 一致性哈希
```

---

### HealthCheckConfig

健康检查配置。

```python
@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    check_type: Literal["http", "tcp", "heartbeat"] = "heartbeat"
    check_interval: int = 30      # 检查间隔（秒）
    check_timeout: int = 5        # 检查超时（秒）
    unhealthy_threshold: int = 3  # 不健康阈值
    healthy_threshold: int = 2    # 健康阈值

    # HTTP检查配置
    http_path: str = "/health"
    http_expected_status: int = 200
    http_method: str = "GET"

    # TCP检查配置
    tcp_port: Optional[int] = None

    # 心跳检查配置
    heartbeat_timeout: int = 300
```

---

## 服务注册

### ServiceDiscovery

服务发现和注册接口。

#### 方法

##### register

```python
async def register(
    self,
    service_name: str,
    instance_id: str,
    host: str,
    port: int,
    metadata: Optional[dict] = None,
    ttl: int = 300
) -> bool:
    """注册服务

    Args:
        service_name: 服务名称
        instance_id: 实例ID
        host: 主机地址
        port: 端口
        metadata: 元数据
        ttl: 过期时间（秒）

    Returns:
        是否注册成功
    """
```

**示例**:
```python
from core.service_registry import get_discovery

discovery = get_discovery()
success = await discovery.register(
    service_name="xiaona",
    instance_id="xiaona-001",
    host="localhost",
    port=8001,
    metadata={
        "version": "2.0",
        "type": "agent"
    }
)
```

---

##### deregister

```python
async def deregister(
    self,
    service_name: str,
    instance_id: str
) -> bool:
    """注销服务

    Args:
        service_name: 服务名称
        instance_id: 实例ID

    Returns:
        是否注销成功
    """
```

**示例**:
```python
success = await discovery.deregister(
    service_name="xiaona",
    instance_id="xiaona-001"
)
```

---

##### heartbeat

```python
async def heartbeat(
    self,
    service_name: str,
    instance_id: str
) -> bool:
    """发送心跳

    Args:
        service_name: 服务名称
        instance_id: 实例ID

    Returns:
        是否成功
    """
```

**示例**:
```python
# 定期发送心跳（推荐30秒一次）
import asyncio

async def heartbeat_loop():
    while True:
        await discovery.heartbeat("xiaona", "xiaona-001")
        await asyncio.sleep(30)
```

---

## 健康检查

### HealthChecker

健康检查器。

#### 方法

##### check_instance

```python
async def check_instance(
    self,
    instance: ServiceInstance,
    config: Optional[HealthCheckConfig] = None
) -> HealthCheckResult:
    """检查单个实例

    Args:
        instance: 服务实例
        config: 健康检查配置

    Returns:
        检查结果
    """
```

**返回**:
```python
class HealthCheckResult:
    def __init__(
        self,
        healthy: bool,
        message: str = "",
        response_time_ms: float = 0
    ):
        self.healthy = healthy
        self.message = message
        self.response_time_ms = response_time_ms
```

---

##### check_all_instances

```python
async def check_all_instances(
    self,
    service_name: Optional[str] = None
) -> Dict[str, HealthCheckResult]:
    """检查所有实例

    Args:
        service_name: 服务名称（可选）

    Returns:
        实例键 -> 检查结果
    """
```

**示例**:
```python
from core.service_registry import get_health_checker

checker = get_health_checker()
results = await checker.check_all_instances()

for instance_key, result in results.items():
    status = "✅" if result.healthy else "❌"
    print(f"{status} {instance_key}: {result.message}")
```

---

## 服务发现

### ServiceDiscovery

服务发现接口（续）。

#### 方法

##### discover

```python
async def discover(
    self,
    service_name: str,
    strategy: Optional[LoadBalanceStrategy] = None,
    healthy_only: bool = True
) -> Optional[ServiceInstance]:
    """发现服务

    Args:
        service_name: 服务名称
        strategy: 负载均衡策略
        healthy_only: 是否只返回健康实例

    Returns:
        服务实例或None
    """
```

**示例**:
```python
# 使用轮询策略
instance = await discovery.discover(
    "xiaona",
    strategy=LoadBalanceStrategy.ROUND_ROBIN
)

# 使用随机策略
instance = await discovery.discover(
    "xiaona",
    strategy=LoadBalanceStrategy.RANDOM
)

# 调用服务
if instance:
    url = f"http://{instance.address}/api/endpoint"
    response = requests.get(url)
```

---

##### get_all_instances

```python
async def get_all_instances(
    self,
    service_name: str,
    healthy_only: bool = True
) -> List[ServiceInstance]:
    """获取所有服务实例

    Args:
        service_name: 服务名称
        healthy_only: 是否只返回健康实例

    Returns:
        服务实例列表
    """
```

**示例**:
```python
instances = await discovery.get_all_instances("xiaona")

for instance in instances:
    print(f"{instance.instance_id} @ {instance.address} - {instance.status.value}")
```

---

##### get_service_names

```python
async def get_service_names(self) -> List[str]:
    """获取所有服务名称

    Returns:
        服务名称列表
    """
```

**示例**:
```python
services = await discovery.get_service_names()
print(f"已注册服务: {', '.join(services)}")
```

---

## 统一注册中心

### ServiceRegistryCenter

统一服务注册中心，整合所有功能。

#### 方法

##### register_service

```python
async def register_service(
    self,
    registration: ServiceRegistration,
    ttl: int = 300
) -> bool:
    """注册服务

    Args:
        registration: 服务注册信息
        ttl: 过期时间（秒）

    Returns:
        是否注册成功
    """
```

**示例**:
```python
from core.service_registry import (
    get_registry,
    ServiceRegistration,
    HealthCheckConfig
)

registry = get_registry()

registration = ServiceRegistration(
    service_name="xiaona",
    instance_id="xiaona-001",
    host="localhost",
    port=8001,
    metadata={"version": "2.0"},
    health_check_config=HealthCheckConfig(
        check_type="http",
        check_interval=30
    )
)

await registry.register_service(registration)
```

---

##### discover_service

```python
async def discover_service(
    self,
    service_name: str,
    strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN,
    healthy_only: bool = True
) -> Optional[ServiceInstance]:
    """发现服务

    Args:
        service_name: 服务名称
        strategy: 负载均衡策略
        healthy_only: 是否只返回健康实例

    Returns:
        服务实例或None
    """
```

---

##### get_service_statistics

```python
async def get_service_statistics(self, service_name: str) -> dict:
    """获取服务统计信息

    Args:
        service_name: 服务名称

    Returns:
        统计信息字典
    """
```

**返回**:
```python
{
    "service_name": "xiaona",
    "total_instances": 2,
    "healthy_instances": 2,
    "unhealthy_instances": 0,
    "instances": [
        {
            "instance_id": "xiaona-001",
            "address": "localhost:8001",
            "status": "healthy",
            "last_heartbeat": "2026-04-21T10:00:00Z"
        }
    ]
}
```

---

##### get_registry_statistics

```python
async def get_registry_statistics(self) -> dict:
    """获取注册中心统计信息

    Returns:
        统计信息字典
    """
```

**返回**:
```python
{
    "total_services": 5,
    "total_instances": 5,
    "healthy_instances": 5,
    "unhealthy_instances": 0,
    "services": {
        "xiaona": {...},
        "xiaonuo": {...}
    }
}
```

---

##### check_health

```python
async def check_health(self, service_name: Optional[str] = None) -> dict:
    """执行健康检查

    Args:
        service_name: 服务名称（可选）

    Returns:
        检查结果字典
    """
```

---

## 使用示例

### 基础使用

```python
import asyncio
from core.service_registry import get_registry

async def main():
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

### 带健康检查的注册

```python
from core.service_registry import (
    ServiceRegistration,
    HealthCheckConfig
)

registration = ServiceRegistration(
    service_name="xiaona",
    instance_id="xiaona-001",
    host="localhost",
    port=8001,
    metadata={"version": "2.0"},
    health_check_config=HealthCheckConfig(
        check_type="http",
        check_interval=30,
        check_timeout=5,
        http_path="/health",
        http_expected_status=200
    )
)
```

---

### 使用负载均衡

```python
from core.service_registry import LoadBalanceStrategy

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

---

### 启动后台健康检查

```python
from core.service_registry import get_registry

registry = get_registry()

# 启动后台健康检查
registry.start_health_check()

# 主循环
try:
    while True:
        # 应用逻辑
        await asyncio.sleep(1)
finally:
    # 停止健康检查
    registry.stop_health_check()
```

---

## 错误处理

### NoHealthyInstanceError

没有健康实例异常。

```python
from core.service_registry import NoHealthyInstanceError

try:
    instance = await discovery.discover("unhealthy_service")
except NoHealthyInstanceError:
    print("没有可用的健康实例")
```

---

### ServiceNotFoundError

服务未找到异常。

```python
# 获取不存在的服务
instances = await discovery.get_all_instances("non_existent_service")
if not instances:
    print("服务不存在")
```

---

## 最佳实践

### 1. 服务注册

```python
# 推荐：启动时自动注册
async def start_service():
    registry = get_registry()

    registration = ServiceRegistration(
        service_name="xiaona",
        instance_id=f"xiaona-{uuid.uuid4()}",
        host=get_host_ip(),
        port=8001,
        metadata={"version": "2.0"}
    )

    await registry.register_service(registration)
```

---

### 2. 心跳维护

```python
# 推荐：后台任务定期发送心跳
async def heartbeat_task():
    registry = get_registry()

    while True:
        try:
            await registry.send_heartbeat("xiaona", "xiaona-001")
            await asyncio.sleep(30)  # 30秒一次
        except asyncio.CancelledError:
            break
```

---

### 3. 优雅下线

```python
# 推荐：优雅下线流程
async def graceful_shutdown():
    registry = get_registry()

    # 1. 标记为DRAINING状态
    instance = await registry.get_instance("xiaona", "xiaona-001")
    instance.status = ServiceStatus.DRAINING
    await registry.update_instance(instance)

    # 2. 等待现有请求完成
    await wait_for_requests_complete()

    # 3. 注销服务
    await registry.deregister_service("xiaona", "xiaona-001")
```

---

### 4. 错误重试

```python
# 推荐：服务发现时重试
async def discover_with_retry(service_name, max_retries=3):
    for i in range(max_retries):
        instance = await discovery.discover(service_name)
        if instance:
            return instance
        await asyncio.sleep(2 ** i)  # 指数退避
    return None
```

---

## 相关文档

- [服务注册架构设计](../guides/SERVICE_REGISTRY_ARCHITECTURE.md)
- [Week 2完成报告](../reports/P2_WEEK2_DAY2_3_COMPLETION_REPORT_20260421.md)
- [全面验证报告](../reports/PHASE1_PHASE2_COMPREHENSIVE_VERIFICATION_REPORT_20260421.md)

---

**文档版本**: 1.0.0
**最后更新**: 2026-04-21
**维护者**: Claude Code (OMC模式)
