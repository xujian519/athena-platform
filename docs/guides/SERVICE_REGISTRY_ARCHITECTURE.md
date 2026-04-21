# 服务注册中心架构设计

> **Phase 2 Week 2**
> **主题**: 服务注册中心 (Service Registry)
> **设计时间**: 2026-04-22

---

## 📋 设计目标

### 核心功能
1. **服务注册**: 服务启动时自动注册到注册中心
2. **健康检查**: 定期检查服务健康状态
3. **服务发现**: 客户端查询可用服务实例
4. **负载均衡**: 支持多种负载均衡策略
5. **故障剔除**: 自动剔除不健康的服务实例

### 非功能性需求
- **高可用**: 注册中心本身高可用（支持集群）
- **高性能**: 支持每秒1000+次查询
- **低延迟**: 服务发现延迟 < 10ms
- **一致性**: 服务状态最终一致性
- **易扩展**: 支持水平扩展

---

## 🏗️ 架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│              Service Registry Center                     │
│                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Service      │  │ Health       │  │ Service      │ │
│  │ Registration │  │ Checker      │  │ Discovery    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│         ↓                  ↓                  ↓          │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Service Registry Storage (Redis)          │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
         │                              │
    ┌────┴────┐                    ┌────┴────┐
    │ Services│                    │ Clients │
    └─────────┘                    └─────────┘
```

### 2. 核心组件

#### 2.1 服务注册表 (Service Registry)

**存储结构**:
```
service:instances:{service_name}
  Type: Hash
  Fields:
    - instance_id: {
        host: "localhost",
        port: 8001,
        status: "healthy",
        last_heartbeat: timestamp,
        metadata: {...}
      }
```

**数据结构**:
```python
@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str          # 实例ID
    service_name: str         # 服务名称
    host: str                 # 主机地址
    port: int                 # 端口
    status: ServiceStatus     # 服务状态
    last_heartbeat: datetime  # 最后心跳时间
    metadata: Dict[str, Any]  # 元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServiceInstance":
        """从字典创建"""
        return cls(**data)
```

#### 2.2 健康检查器 (Health Checker)

**检查类型**:
- **HTTP检查**: GET /health端点
- **TCP检查**: 端口连通性
- **心跳检查**: 服务主动上报

**检查策略**:
```python
@dataclass
class HealthCheckConfig:
    """健康检查配置"""
    check_type: Literal["http", "tcp", "heartbeat"]
    check_interval: int = 30      # 检查间隔（秒）
    check_timeout: int = 5        # 检查超时（秒）
    unhealthy_threshold: int = 3  # 不健康阈值
    healthy_threshold: int = 2    # 健康阈值

    # HTTP检查配置
    http_path: str = "/health"
    http_expected_status: int = 200

    # TCP检查配置
    tcp_port: Optional[int] = None
```

**健康状态**:
```python
class ServiceStatus(Enum):
    """服务状态"""
    HEALTHY = "healthy"       # 健康
    UNHEALTHY = "unhealthy"   # 不健康
    DRAINING = "draining"     # 流量排空（优雅下线）
    TERMINATED = "terminated" # 已终止
```

#### 2.3 服务发现 (Service Discovery)

**发现策略**:
- **随机选择**: Random
- **轮询**: Round Robin
- **最少连接**: Least Connection
- **一致性哈希**: Consistent Hash

**API接口**:
```python
class ServiceDiscovery:
    """服务发现接口"""

    async def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """注册服务实例"""

    async def deregister(
        self,
        service_name: str,
        instance_id: str
    ) -> bool:
        """注销服务实例"""

    async def heartbeat(
        self,
        service_name: str,
        instance_id: str
    ) -> bool:
        """发送心跳"""

    async def discover(
        self,
        service_name: str,
        strategy: LoadBalanceStrategy = LoadBalanceStrategy.ROUND_ROBIN
    ) -> Optional[ServiceInstance]:
        """发现服务实例"""

    async def get_all_instances(
        self,
        service_name: str,
        healthy_only: bool = True
    ) -> List[ServiceInstance]:
        """获取所有服务实例"""

    async def get_service_names(self) -> List[str]:
        """获取所有服务名称"""
```

---

## 🔄 工作流程

### 1. 服务注册流程

```
┌──────────┐            ┌──────────────┐
│ Service  │            │   Registry   │
└────┬─────┘            └──────┬───────┘
     │                          │
     │  1. Register Request     │
     │  (service_name, host,    │
     │   port, metadata)        │
     │─────────────────────────>│
     │                          │
     │                          │ 2. Store in Redis
     │                          │    service:instances:{name}
     │                          │
     │  3. Register Success     │
     │<─────────────────────────│
     │                          │
     │  4. Start Heartbeat      │
     │  (every 30s)             │
     │─────────────────────────>│
     │                          │
```

### 2. 健康检查流程

```
┌──────────┐            ┌──────────────┐
│ Service  │            │ Health Check │
└────┬─────┘            └──────┬───────┘
     │                          │
     │  1. Check Health         │
     │  (HTTP / TCP / Heartbeat)│
     │<─────────────────────────│
     │                          │
     │  2. Health Response      │
     │  (200 OK / Connection    │
     │   established)           │
     │─────────────────────────>│
     │                          │
     │                          │ 3. Update Status
     │                          │    healthy / unhealthy
     │                          │
     │                          │ 4. Check Threshold
     │                          │    unhealthy_count >= 3
     │                          │    => mark as UNHEALTHY
```

### 3. 服务发现流程

```
┌──────────┐            ┌──────────────┐
│ Client   │            │  Discovery   │
└────┬─────┘            └──────┬───────┘
     │                          │
     │  1. Discover Service     │
     │  (service_name)          │
     │─────────────────────────>│
     │                          │
     │                          │ 2. Query Redis
     │                          │    service:instances:{name}
     │                          │    status = healthy
     │                          │
     │                          │ 3. Load Balance
     │                          │    (Round Robin / Random)
     │                          │
     │  4. Return Instance      │
     │  (host, port)            │
     │<─────────────────────────│
     │                          │
     │  5. Call Service         │
     │──────────────────────────>│
```

---

## 💾 存储设计

### Redis数据结构

#### 1. 服务实例存储

```
Key: service:instances:{service_name}
Type: Hash
Fields:
  - {instance_id}: JSON字符串 {
      "instance_id": "xiaona-001",
      "service_name": "xiaona",
      "host": "localhost",
      "port": 8001,
      "status": "healthy",
      "last_heartbeat": "2026-04-22T10:00:00Z",
      "metadata": {
        "version": "2.0",
        "capabilities": ["patent_analysis", "legal_research"]
      }
    }

TTL: 300秒 (5分钟无心跳自动删除)
```

#### 2. 服务索引

```
Key: service:index
Type: Set
Members: ["xiaona", "xiaonuo", "gateway", "knowledge_graph"]

用途: 快速获取所有已注册的服务名称
```

#### 3. 健康检查状态

```
Key: service:health:{service_name}:{instance_id}
Type: String
Value: "healthy" | "unhealthy"
TTL: 60秒
```

---

## 🔧 API设计

### 1. 服务注册API

```python
POST /api/v1/services/register

Request:
{
  "service_name": "xiaona",
  "instance_id": "xiaona-001",
  "host": "localhost",
  "port": 8001,
  "metadata": {
    "version": "2.0",
    "capabilities": ["patent_analysis", "legal_research"]
  }
}

Response:
{
  "success": true,
  "instance_id": "xiaona-001",
  "registered_at": "2026-04-22T10:00:00Z"
}
```

### 2. 服务注销API

```python
DELETE /api/v1/services/{service_name}/{instance_id}

Response:
{
  "success": true,
  "deregistered_at": "2026-04-22T10:00:00Z"
}
```

### 3. 心跳API

```python
POST /api/v1/services/{service_name}/{instance_id}/heartbeat

Response:
{
  "success": true,
  "heartbeat_time": "2026-04-22T10:00:00Z"
}
```

### 4. 服务发现API

```python
GET /api/v1/services/{service_name}/discover?strategy=round_robin

Response:
{
  "success": true,
  "instance": {
    "instance_id": "xiaona-001",
    "host": "localhost",
    "port": 8001,
    "status": "healthy"
  }
}
```

### 5. 服务列表API

```python
GET /api/v1/services

Response:
{
  "success": true,
  "services": ["xiaona", "xiaonuo", "gateway", "knowledge_graph"]
}
```

---

## ⚖️ 负载均衡策略

### 1. Round Robin (轮询)

```python
class RoundRobinStrategy:
    """轮询策略"""

    def __init__(self):
        self.counter = 0

    def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择下一个实例"""
        if not instances:
            raise NoHealthyInstanceError()

        instance = instances[self.counter % len(instances)]
        self.counter += 1
        return instance
```

### 2. Random (随机)

```python
class RandomStrategy:
    """随机策略"""

    def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """随机选择实例"""
        if not instances:
            raise NoHealthyInstanceError()

        return random.choice(instances)
```

### 3. Least Connection (最少连接)

```python
class LeastConnectionStrategy:
    """最少连接策略"""

    def __init__(self):
        self.connections: Dict[str, int] = {}

    def select(self, instances: List[ServiceInstance]) -> ServiceInstance:
        """选择连接数最少的实例"""
        if not instances:
            raise NoHealthyInstanceError()

        return min(
            instances,
            key=lambda i: self.connections.get(i.instance_id, 0)
        )
```

---

## 🔐 安全设计

### 1. 认证

```python
# 服务注册需要API Key
X-API-Key: {service_api_key}

# 或使用JWT Token
Authorization: Bearer {jwt_token}
```

### 2. 授权

```python
# 服务只能注册/注销自己
# 客户端只能发现服务，不能注册
# 管理员可以查看所有服务
```

### 3. 加密

```python
# 服务间通信使用TLS
# API密钥加密存储
```

---

## 📊 监控指标

### 1. 服务指标

- 注册服务数量
- 健康实例数量
- 不健康实例数量
- 平均响应时间
- QPS (每秒查询数)

### 2. 健康检查指标

- 检查成功率
- 检查失败率
- 平均检查时间
- 超时率

### 3. 发现指标

- 发现请求总数
- 发现成功率
- 平均发现延迟
- 无健康实例错误数

---

## 🚀 实施计划

### Phase 1: 核心功能 (Day 1-3)
- [x] 设计架构文档
- [ ] 实现服务注册表
- [ ] 实现健康检查器
- [ ] 实现服务发现

### Phase 2: 高级功能 (Day 4-5)
- [ ] 实现负载均衡策略
- [ ] 实现监控指标
- [ ] 实现安全机制

### Phase 3: 集成测试 (Day 6-7)
- [ ] 注册现有服务
- [ ] 集成测试
- [ ] 性能测试
- [ ] 文档完善

---

**设计完成时间**: 2026-04-22
**设计人**: Claude Code (OMC模式)
**团队**: phase2-refactor
