# Athena服务注册中心架构设计

> **版本**: v1.0
> **日期**: 2026-04-21
> **状态**: 设计阶段

---

## 📋 现状分析

### 当前服务发现机制

**现有配置**: `config/service_discovery.json`

**问题**:
1. 🔴 **静态配置** - 手动维护服务列表
2. 🔴 **无健康检查** - 不知道服务是否在线
3. 🔴 **无负载均衡** - 无法智能选择服务实例
4. 🔴 **无服务发现** - 新服务需要手动注册

---

## 🎯 设计目标

### 目标1: 动态服务注册 🎯
- 服务启动时自动注册
- 服务关闭时自动注销
- 支持服务元数据

### 目标2: 健康检查 🎯
- 定期检查服务健康状态
- 自动剔除不健康服务
- 支持自定义健康检查端点

### 目标3: 服务发现 🎯
- 按服务名称查询
- 按服务类型查询
- 按标签查询

### 目标4: 负载均衡 🎯
- 支持多种负载均衡算法
- 自动选择最优服务实例
- 失败重试

---

## 🏗️ 服务注册架构

### 架构分层

```
┌─────────────────────────────────────────────────────────┐
│                  服务注册中心 (Registry)                  │
│  ┌────────────────────────────────────────────────────┐ │
│  │           服务注册表 (Service Registry)            │ │
│  │  - 服务信息 (name, type, host, port, tags)        │ │
│  │  - 健康状态 (status, last_check, metrics)         │ │
│  │  - 元数据 (metadata)                              │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │           健康检查器 (Health Checker)              │ │
│  │  - 定期检查服务健康状态                            │ │
│  │  - 自动更新服务状态                                │ │
│  │  - 剔除不健康服务                                  │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │           服务发现API (Discovery API)              │ │
│  │  - 按名称查询                                      │ │
│  │  - 按类型查询                                      │ │
│  │  - 按标签查询                                      │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────┐ │
│  │           负载均衡器 (Load Balancer)               │ │
│  │  - 轮询 (Round Robin)                              │ │
│  │  - 响应时间加权 (Response Time)                    │ │
│  │  - 最少连接 (Least Connections)                    │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
         │
         │ HTTP/WebSocket
         │
    ┌────┴────┐
    │ 服务实例  │
    │ Gateway  │
    │ Xiaona   │
    │ Xiaonuo  │
    │ Yunxi    │
    └─────────┘
```

---

## 📐 数据模型设计

### 服务信息 (ServiceInfo)

```python
class ServiceInfo(BaseModel):
    """服务信息"""
    
    # 基本信息
    id: str                          # 服务ID（唯一）
    name: str                        # 服务名称
    type: str                        # 服务类型
    version: str                     # 服务版本
    
    # 网络信息
    host: str                        # 主机地址
    port: int                        # 端口号
    protocol: str = "http"           # 协议（http/https/ws）
    
    # 健康检查
    health_check_url: str            # 健康检查URL
    health_check_interval: int = 30  # 健康检查间隔（秒）
    health: ServiceHealth            # 健康状态
    
    # 负载均衡
    weight: int = 1                  # 权重
    response_time: float = 0.0       # 响应时间（ms）
    active_connections: int = 0      # 活动连接数
    
    # 元数据
    tags: List[str] = []             # 标签
    metadata: Dict[str, str] = {}    # 元数据
```

### 健康状态 (ServiceHealth)

```python
class ServiceHealth(BaseModel):
    """服务健康状态"""
    
    status: ServiceStatus            # 服务状态
    last_check: datetime             # 最后检查时间
    error_message: Optional[str]     # 错误信息
    metrics: Dict[str, float] = {}   # 性能指标
```

### 服务状态 (ServiceStatus)

```python
class ServiceStatus(str, Enum):
    """服务状态枚举"""
    STARTING = "starting"            # 启动中
    RUNNING = "running"              # 运行中
    DEGRADED = "degraded"            # 降级运行
    STOPPING = "stopping"            # 停止中
    STOPPED = "stopped"              # 已停止
    ERROR = "error"                  # 错误
```

---

## 🔧 核心组件设计

### 1. 服务注册表 (ServiceRegistry)

**职责**:
- 存储服务信息
- 管理服务生命周期
- 提供服务查询接口

**API**:
```python
class ServiceRegistry:
    """服务注册表"""
    
    def register(self, service: ServiceInfo) -> bool:
        """注册服务"""
        
    def deregister(self, service_id: str) -> bool:
        """注销服务"""
        
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """获取服务"""
        
    def find_services(
        self,
        name: str = None,
        service_type: str = None,
        tags: List[str] = None
    ) -> List[ServiceInfo]:
        """查找服务"""
        
    def update_health(
        self,
        service_id: str,
        health: ServiceHealth
    ) -> bool:
        """更新健康状态"""
```

### 2. 健康检查器 (HealthChecker)

**职责**:
- 定期检查服务健康状态
- 自动更新服务状态
- 剔除不健康服务

**API**:
```python
class HealthChecker:
    """健康检查器"""
    
    async def check_service(
        self,
        service: ServiceInfo
    ) -> ServiceHealth:
        """检查单个服务"""
        
    async def check_all_services(self) -> Dict[str, ServiceHealth]:
        """检查所有服务"""
        
    async def start_background_check(self) -> None:
        """启动后台检查"""
```

### 3. 服务发现API (DiscoveryAPI)

**职责**:
- 提供服务查询接口
- 负载均衡
- 失败重试

**API**:
```python
class DiscoveryAPI:
    """服务发现API"""
    
    async def discover(
        self,
        service_name: str,
        load_balance: str = "round_robin"
    ) -> Optional[ServiceInfo]:
        """发现服务（带负载均衡）"""
        
    async def discover_all(
        self,
        service_name: str
    ) -> List[ServiceInfo]:
        """发现所有服务实例"""
        
    async def discover_by_type(
        self,
        service_type: str
    ) -> List[ServiceInfo]:
        """按类型发现服务"""
        
    async def discover_by_tags(
        self,
        tags: List[str]
    ) -> List[ServiceInfo]:
        """按标签发现服务"""
```

---

## 🔄 服务注册流程

### 服务启动流程

```
1. 服务启动
   ↓
2. 创建ServiceInfo
   ↓
3. 调用Registry.register(service)
   ↓
4. 健康检查器开始监控
   ↓
5. 服务可用
```

### 服务关闭流程

```
1. 服务关闭
   ↓
2. 调用Registry.deregister(service_id)
   ↓
3. 健康检查器停止监控
   ↓
4. 服务从注册表移除
```

### 健康检查流程

```
1. 定时器触发（默认30秒）
   ↓
2. 遍历所有服务
   ↓
3. 调用健康检查URL
   ↓
4. 解析响应状态
   ↓
5. 更新服务状态
   ↓
6. 剔除不健康服务（连续3次失败）
```

---

## 📊 负载均衡算法

### 1. 轮询 (Round Robin)

**原理**: 按顺序轮流选择服务实例

**适用**: 服务实例性能相近

### 2. 响应时间加权 (Response Time)

**原理**: 优先选择响应时间短的服务

**适用**: 服务实例性能差异大

### 3. 最少连接 (Least Connections)

**原理**: 优先选择活动连接数少的服务

**适用**: 长连接场景

### 4. 随机 (Random)

**原理**: 随机选择服务实例

**适用**: 简单场景

---

## 🗂️ 持久化存储

### 存储选项

**选项1: 内存存储** (默认)
- 优点: 快速
- 缺点: 重启丢失

**选项2: Redis存储**
- 优点: 持久化、分布式
- 缺点: 需要Redis

**选项3: 数据库存储**
- 优点: 持久化、可查询
- 缺点: 较慢

### Redis存储结构

```
Key: athena:services:{service_id}
Value: JSON(ServiceInfo)

Key: athena:services:name:{service_name}
Value: Set(service_ids)

Key: athena:services:type:{service_type}
Value: Set(service_ids)

Key: athena:services:tag:{tag}
Value: Set(service_ids)
```

---

## 🚀 使用示例

### 服务注册

```python
from core.service_registry import ServiceRegistry, ServiceInfo

# 创建服务信息
service = ServiceInfo(
    id="xiaona-001",
    name="xiaona",
    type="agent",
    version="1.0.0",
    host="localhost",
    port=8001,
    health_check_url="http://localhost:8001/health",
    tags=["legal", "patent"]
)

# 注册服务
registry = ServiceRegistry()
registry.register(service)
```

### 服务发现

```python
from core.service_registry import DiscoveryAPI

# 发现服务
api = DiscoveryAPI()
service = await api.discover("xiaona")

if service:
    print(f"发现服务: {service.name}")
    print(f"地址: {service.host}:{service.port}")
```

### 健康检查

```python
from core.service_registry import HealthChecker

# 检查所有服务
checker = HealthChecker()
health_status = await checker.check_all_services()

for service_id, health in health_status.items():
    print(f"{service_id}: {health.status}")
```

---

## ✅ 实施计划

### Day 8-10: 设计服务注册架构
- 设计数据模型
- 设计API接口
- 编写架构文档

### Day 11-12: 实现服务注册工具
- 实现ServiceRegistry
- 实现HealthChecker
- 实现DiscoveryAPI
- 编写单元测试

### Day 13-14: 集成服务注册
- 集成Gateway服务注册
- 集成Agent服务注册
- 清理旧的service_discovery.json

---

**文档版本**: v1.0
**最后更新**: 2026-04-21
**状态**: ✅ 架构设计完成

**下一步**: 实现服务注册工具（Day 11-12）
