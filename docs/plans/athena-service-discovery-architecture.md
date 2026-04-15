# Athena API Gateway 服务发现系统架构设计

> **设计目标**: 构建高性能、高可用的分布式服务发现系统，支持多协议、智能负载均衡和动态配置管理
> **架构版本**: v2.0
> **设计时间**: 2026-02-20

---

## 🎯 系统概览

### 核心设计原则
1. **高可用性** - 无单点故障，多副本部署
2. **高性能** - 低延迟服务发现，高并发支持
3. **可扩展性** - 水平扩展，插件化架构
4. **多协议支持** - HTTP/gRPC/GraphQL 统一服务发现
5. **智能化** - 自适应负载均衡，智能故障检测

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │ HTTP Proxy  │  │ gRPC Proxy  │  │ GraphQL GW  │  │ LB Plugin│ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                    Service Discovery Core                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Service Registry Center                       │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │ │
│  │  │Registration │  │ Health Check│  │ Config Management  │ │ │
│  │  │   Service   │  │   Service   │  │      Service        │ │ │
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                     Plugin System Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │Discovery    │  │Health Check │  │Load Balance │  │Protocol │ │
│  │Plugins      │  │Plugins      │  │Plugins      │  │Plugins  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────────────┤
│                       Storage Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  Redis      │  │ PostgreSQL  │  │  Etcd       │  │ Memory  │ │
│  │ (Cache)     │  │ (Metadata)  │  │ (Config)    │  │ (Store) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ 服务注册中心架构

### 1. 核心组件设计

#### 1.1 服务注册服务 (Registration Service)

```python
# 服务注册核心接口
class ServiceRegistry:
    """服务注册中心核心接口"""
    
    async def register_service(self, service: ServiceInstance) -> bool:
        """注册新服务实例"""
        pass
    
    async def deregister_service(self, service_id: str) -> bool:
        """注销服务实例"""
        pass
    
    async def discover_services(self, service_name: str) -> List[ServiceInstance]:
        """发现服务实例列表"""
        pass
    
    async def update_service_metadata(self, service_id: str, metadata: Dict) -> bool:
        """更新服务元数据"""
        pass
```

**服务实例数据模型**:
```python
@dataclass
class ServiceInstance:
    # 基础信息
    service_id: str                    # 服务唯一标识
    service_name: str                  # 服务名称
    version: str                       # 服务版本
    namespace: str                     # 命名空间
    
    # 网络信息
    host: str                          # 服务主机
    port: int                          # 服务端口
    protocol: ProtocolType             # 协议类型 (HTTP/gRPC/GraphQL)
    endpoints: List[str]              # 服务端点列表
    
    # 健康信息
    health_status: HealthStatus        # 健康状态
    last_heartbeat: datetime          # 最后心跳时间
    health_check_url: str              # 健康检查地址
    
    # 负载均衡信息
    weight: int = 100                  # 权重
    tags: List[str] = field(default_factory=list)  # 标签
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    # 时间戳
    registration_time: datetime = field(default_factory=datetime.now)
    updated_time: datetime = field(default_factory=datetime.now)
```

#### 1.2 健康检查服务 (Health Check Service)

```python
class HealthChecker:
    """健康检查核心服务"""
    
    async def start_health_check(self, service_instance: ServiceInstance) -> None:
        """启动对服务实例的健康检查"""
        pass
    
    async def stop_health_check(self, service_id: str) -> None:
        """停止对服务实例的健康检查"""
        pass
    
    async def check_service_health(self, instance: ServiceInstance) -> HealthStatus:
        """执行单次健康检查"""
        pass
    
    async def get_service_health_summary(self, service_name: str) -> HealthSummary:
        """获取服务整体健康状态摘要"""
        pass
```

**健康检查配置**:
```python
@dataclass
class HealthCheckConfig:
    # 基础配置
    enabled: bool = True
    interval: int = 30                 # 检查间隔(秒)
    timeout: int = 5                   # 超时时间(秒)
    retries: int = 3                   # 重试次数
    
    # 检查类型
    check_type: HealthCheckType = HealthCheckType.HTTP
    http_path: str = "/health"         # HTTP检查路径
    grpc_service: str = ""             # gRPC服务名
    grpc_method: str = ""              # gRPC方法名
    
    # 高级配置
    expected_codes: List[int] = field(default_factory=lambda: [200])
    expected_body: str = ""            # 预期响应体
    headers: Dict[str, str] = field(default_factory=dict)
    
    # 故障处理
    failure_threshold: int = 3         # 连续失败阈值
    success_threshold: int = 2         # 连续成功阈值
    deregister_after: int = 300        # 失效后注销时间(秒)
```

#### 1.3 配置管理服务 (Configuration Management)

```python
class ConfigManager:
    """动态配置管理服务"""
    
    async def get_service_config(self, service_name: str, version: str = None) -> Dict:
        """获取服务配置"""
        pass
    
    async def update_service_config(self, service_name: str, config: Dict) -> bool:
        """更新服务配置"""
        pass
    
    async def watch_config_changes(self, service_name: str, callback: Callable) -> None:
        """监听配置变更"""
        pass
    
    async def rollback_config(self, service_name: str, target_version: str) -> bool:
        """回滚配置"""
        pass
```

### 2. 数据存储设计

#### 2.1 多层存储架构

```
┌─────────────────────────────────────────────────────────┐
│                    存储层级架构                           │
├─────────────────────────────────────────────────────────┤
│  L1: 内存缓存 (Hot Layer)                                │
│  ├── 活跃服务实例 (10,000+)                              │
│  ├── 健康检查状态 (实时)                                 │
│  └── 路由表 (高频查询)                                   │
├─────────────────────────────────────────────────────────┤
│  L2: Redis 缓存 (Warm Layer)                           │
│  ├── 服务注册信息 (100,000+)                             │
│  ├── 配置数据 (动态变更)                                 │
│  └── 会话状态 (分布式)                                   │
├─────────────────────────────────────────────────────────┤
│  L3: PostgreSQL (Cold Layer)                           │
│  ├── 服务元数据 (持久化)                                 │
│  ├── 配置历史版本 (审计)                                 │
│  └── 操作日志 (可追溯)                                   │
├─────────────────────────────────────────────────────────┤
│  L4: Etcd (Configuration Layer)                         │
│  ├── 动态配置 (实时同步)                                 │
│  ├── 集群协调 (分布式锁)                                 │
│  └── 服务发现 (轻量级)                                   │
└─────────────────────────────────────────────────────────┘
```

#### 2.2 核心数据表设计

**服务实例表 (service_instances)**:
```sql
CREATE TABLE service_instances (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(255) NOT NULL,
    service_version VARCHAR(50) NOT NULL,
    namespace VARCHAR(100) NOT NULL DEFAULT 'default',
    
    -- 网络信息
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    protocol VARCHAR(20) NOT NULL CHECK (protocol IN ('HTTP', 'GRPC', 'GRAPHQL')),
    endpoints JSONB DEFAULT '[]',
    
    -- 健康信息
    health_status VARCHAR(20) NOT NULL DEFAULT 'UNKNOWN',
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    health_check_url VARCHAR(500),
    
    -- 负载均衡
    weight INTEGER DEFAULT 100,
    tags JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    
    -- 时间戳
    registration_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 索引
    UNIQUE(service_name, host, port),
    INDEX idx_service_name (service_name),
    INDEX idx_health_status (health_status),
    INDEX idx_last_heartbeat (last_heartbeat)
);
```

**服务配置表 (service_configs)**:
```sql
CREATE TABLE service_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    namespace VARCHAR(100) NOT NULL DEFAULT 'default',
    
    config_data JSONB NOT NULL,
    config_schema JSONB,
    description TEXT,
    
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(service_name, version),
    INDEX idx_service_name (service_name),
    INDEX idx_version (version)
);
```

### 3. 高可用性设计

#### 3.1 集群架构

```
┌─────────────────────────────────────────────────────────┐
│                   Service Discovery Cluster              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Registry   │  │  Registry   │  │  Registry   │     │
│  │  Node #1    │  │  Node #2    │  │  Node #3    │     │
│  │  (Leader)   │  │ (Follower)  │  │ (Follower)  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                     Coordination Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Etcd      │  │   Etcd      │  │   Etcd      │     │
│  │  Cluster    │  │  Cluster    │  │  Cluster    │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
├─────────────────────────────────────────────────────────┤
│                      Data Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ PostgreSQL  │  │   Redis     │  │   Memory    │     │
│  │  Primary    │  │  Cluster    │  │  Cache      │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────┘
```

#### 3.2 一致性保证

**Raft 协议实现**:
```python
class RaftConsensus:
    """基于Raft协议的分布式一致性"""
    
    def __init__(self, cluster_nodes: List[str]):
        self.nodes = cluster_nodes
        self.current_term = 0
        self.voted_for = None
        self.log = []
        self.commit_index = 0
        self.state = RaftState.FOLLOWER
    
    async def elect_leader(self) -> Optional[str]:
        """领导者选举"""
        pass
    
    async def replicate_log(self, entry: LogEntry) -> bool:
        """日志复制"""
        pass
    
    async def commit_entry(self, index: int) -> bool:
        """提交日志条目"""
        pass
```

---

## 🔍 健康检查机制设计

### 1. 多层次健康检查

#### 1.1 检查类型

```python
class HealthCheckType(Enum):
    HTTP = "http"                     # HTTP/HTTPS检查
    TCP = "tcp"                       # TCP连接检查  
    GRPC = "grpc"                     # gRPC健康检查
    GRAPHQL = "graphql"               # GraphQL健康查询
    SCRIPT = "script"                 # 自定义脚本检查
    PROMETHEUS = "prometheus"         # Prometheus指标检查

class HealthStatus(Enum):
    HEALTHY = "healthy"               # 健康
    UNHEALTHY = "unhealthy"           # 不健康
    UNKNOWN = "unknown"               # 未知
    DEGRADED = "degraded"             # 降级服务
    MAINTENANCE = "maintenance"       # 维护模式
```

#### 1.2 健康检查实现

```python
class HealthCheckExecutor:
    """健康检查执行器"""
    
    def __init__(self, config: HealthCheckConfig):
        self.config = config
        self.checkers = {
            HealthCheckType.HTTP: self._http_check,
            HealthCheckType.TCP: self._tcp_check,
            HealthCheckType.GRPC: self._grpc_check,
            HealthCheckType.GRAPHQL: self._graphql_check,
            HealthCheckType.SCRIPT: self._script_check,
            HealthCheckType.PROMETHEUS: self._prometheus_check,
        }
    
    async def execute_check(self, instance: ServiceInstance) -> HealthCheckResult:
        """执行健康检查"""
        checker = self.checkers.get(instance.protocol)
        if not checker:
            raise ValueError(f"Unsupported protocol: {instance.protocol}")
        
        start_time = time.time()
        try:
            result = await checker(instance)
            duration = time.time() - start_time
            
            return HealthCheckResult(
                status=HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY,
                duration=duration,
                message="Health check passed" if result else "Health check failed",
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheckResult(
                status=HealthStatus.UNHEALTHY,
                duration=time.time() - start_time,
                message=f"Health check error: {str(e)}",
                timestamp=datetime.now()
            )
    
    async def _http_check(self, instance: ServiceInstance) -> bool:
        """HTTP健康检查"""
        url = f"http://{instance.host}:{instance.port}{self.config.http_path}"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.config.timeout)) as session:
                async with session.get(url, headers=self.config.headers) as response:
                    return response.status in self.config.expected_codes
        except Exception:
            return False
    
    async def _grpc_check(self, instance: ServiceInstance) -> bool:
        """gRPC健康检查"""
        import grpc
        from grpc_health.v1 import health, health_pb2, health_pb2_grpc
        
        channel = grpc.insecure_channel(f"{instance.host}:{instance.port}")
        stub = health_pb2_grpc.HealthStub(channel)
        
        try:
            request = health_pb2.HealthCheckRequest(service=self.config.grpc_service)
            response = await stub.Check(request, timeout=self.config.timeout)
            return response.status == health_pb2.HealthCheckResponse.SERVING
        except Exception:
            return False
        finally:
            channel.close()
```

#### 1.3 智能故障检测

```python
class FailureDetector:
    """智能故障检测器"""
    
    def __init__(self, window_size: int = 100, threshold: float = 0.3):
        self.window_size = window_size
        self.threshold = threshold
        self.history = {}
    
    async def detect_failure(self, service_id: str, result: HealthCheckResult) -> bool:
        """检测服务故障"""
        if service_id not in self.history:
            self.history[service_id] = []
        
        # 维护滑动窗口
        self.history[service_id].append(result)
        if len(self.history[service_id]) > self.window_size:
            self.history[service_id].pop(0)
        
        # 计算故障率
        recent_results = self.history[service_id][-30:]  # 最近30次检查
        failure_count = sum(1 for r in recent_results if r.status != HealthStatus.HEALTHY)
        failure_rate = failure_count / len(recent_results)
        
        # 计算响应时间异常
        durations = [r.duration for r in recent_results]
        avg_duration = sum(durations) / len(durations)
        current_duration = result.duration
        
        # 故障判定逻辑
        if failure_rate > self.threshold:
            return True
        
        if current_duration > avg_duration * 2:  # 响应时间异常
            return True
        
        return False
```

### 2. 自适应健康检查

```python
class AdaptiveHealthChecker:
    """自适应健康检查器"""
    
    def __init__(self):
        self.check_intervals = {}
        self.min_interval = 5
        self.max_interval = 300
    
    def adapt_check_interval(self, service_id: str, health_history: List[HealthCheckResult]):
        """自适应调整检查间隔"""
        if len(health_history) < 10:
            return self.min_interval
        
        # 分析健康状态趋势
        recent_health = health_history[-10:]
        healthy_count = sum(1 for r in recent_health if r.status == HealthStatus.HEALTHY)
        health_ratio = healthy_count / len(recent_health)
        
        # 动态调整间隔
        if health_ratio >= 0.9:
            # 健康服务，降低检查频率
            new_interval = min(self.max_interval, self.check_intervals.get(service_id, self.min_interval) * 2)
        elif health_ratio >= 0.7:
            # 一般健康，保持当前间隔
            new_interval = self.check_intervals.get(service_id, self.min_interval)
        else:
            # 不健康服务，提高检查频率
            new_interval = max(self.min_interval, self.check_intervals.get(service_id, self.min_interval) // 2)
        
        self.check_intervals[service_id] = new_interval
        return new_interval
```

---

## ⚖️ 负载均衡算法设计

### 1. 智能负载均衡器

```python
class LoadBalancer:
    """智能负载均衡器"""
    
    def __init__(self, algorithm: LoadBalanceAlgorithm):
        self.algorithm = algorithm
        self.metrics_collector = MetricsCollector()
        self.health_manager = HealthManager()
    
    async def select_instance(self, request_context: RequestContext) -> Optional[ServiceInstance]:
        """选择服务实例"""
        # 获取可用服务实例
        available_instances = await self._get_healthy_instances(request_context.service_name)
        
        if not available_instances:
            raise NoAvailableInstanceError(f"No healthy instances for {request_context.service_name}")
        
        # 应用负载均衡算法
        selected_instance = await self.algorithm.select(
            instances=available_instances,
            context=request_context,
            metrics=await self.metrics_collector.get_metrics(),
            health_status=await self.health_manager.get_health_summary()
        )
        
        return selected_instance
    
    async def _get_healthy_instances(self, service_name: str) -> List[ServiceInstance]:
        """获取健康的服务实例"""
        all_instances = await self.service_registry.discover_services(service_name)
        return [
            instance for instance in all_instances 
            if instance.health_status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED]
        ]
```

### 2. 多算法支持

```python
class LoadBalanceAlgorithm(ABC):
    """负载均衡算法基类"""
    
    @abstractmethod
    async def select(
        self, 
        instances: List[ServiceInstance], 
        context: RequestContext,
        metrics: ServiceMetrics,
        health_status: HealthSummary
    ) -> ServiceInstance:
        """选择服务实例"""
        pass

class WeightedRoundRobinAlgorithm(LoadBalanceAlgorithm):
    """加权轮询算法"""
    
    def __init__(self):
        self.current_weights = {}
    
    async def select(self, instances, context, metrics, health_status) -> ServiceInstance:
        """加权轮询选择"""
        total_weight = sum(instance.weight for instance in instances)
        
        for instance in instances:
            self.current_weights[instance.service_id] = (
                self.current_weights.get(instance.service_id, 0) + instance.weight
            )
            
            if self.current_weights[instance.service_id] >= total_weight:
                self.current_weights[instance.service_id] -= total_weight
                return instance
        
        # 如果没有实例被选中，返回权重最高的实例
        return max(instances, key=lambda x: x.weight)

class LeastConnectionsAlgorithm(LoadBalanceAlgorithm):
    """最少连接算法"""
    
    async def select(self, instances, context, metrics, health_status) -> ServiceInstance:
        """选择连接数最少的实例"""
        connection_counts = await metrics.get_connection_counts()
        
        instance_with_least_connections = min(
            instances,
            key=lambda instance: connection_counts.get(instance.service_id, 0)
        )
        
        return instance_with_least_connections

class ResponseTimeBasedAlgorithm(LoadBalanceAlgorithm):
    """基于响应时间的算法"""
    
    async def select(self, instances, context, metrics, health_status) -> ServiceInstance:
        """基于响应时间选择最优实例"""
        response_times = await metrics.get_response_times()
        
        # 计算加权响应时间（考虑健康状态）
        weighted_times = {}
        for instance in instances:
            base_time = response_times.get(instance.service_id, 1000)  # 默认1秒
            
            # 根据健康状态调整权重
            if instance.health_status == HealthStatus.HEALTHY:
                health_factor = 1.0
            elif instance.health_status == HealthStatus.DEGRADED:
                health_factor = 1.5
            else:
                health_factor = 10.0  # 严重惩罚
            
            weighted_times[instance.service_id] = base_time * health_factor
        
        # 选择响应时间最短的实例
        best_instance = min(
            instances,
            key=lambda instance: weighted_times.get(instance.service_id, float('inf'))
        )
        
        return best_instance

class ConsistentHashAlgorithm(LoadBalanceAlgorithm):
    """一致性哈希算法"""
    
    def __init__(self, virtual_nodes: int = 150):
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
    
    async def select(self, instances, context, metrics, health_status) -> ServiceInstance:
        """一致性哈希选择"""
        # 构建哈希环
        self._build_hash_ring(instances)
        
        # 计算请求的哈希值
        hash_key = self._hash_request(context)
        
        # 在环上找到下一个节点
        instance = self._find_next_instance(hash_key)
        
        return instance
    
    def _build_hash_ring(self, instances: List[ServiceInstance]):
        """构建一致性哈希环"""
        self.ring.clear()
        
        for instance in instances:
            for i in range(self.virtual_nodes):
                virtual_key = f"{instance.service_id}:{i}"
                hash_value = self._hash(virtual_key)
                self.ring[hash_value] = instance
        
        self.sorted_keys = sorted(self.ring.keys())
    
    def _find_next_instance(self, hash_key: int) -> ServiceInstance:
        """在环上找到下一个实例"""
        if not self.sorted_keys:
            raise ValueError("No instances available")
        
        # 二分查找
        idx = bisect.bisect_right(self.sorted_keys, hash_key)
        if idx == len(self.sorted_keys):
            idx = 0
        
        return self.ring[self.sorted_keys[idx]]
```

### 3. 自适应负载均衡

```python
class AdaptiveLoadBalancer:
    """自适应负载均衡器"""
    
    def __init__(self):
        self.algorithms = {
            "round_robin": WeightedRoundRobinAlgorithm(),
            "least_connections": LeastConnectionsAlgorithm(),
            "response_time": ResponseTimeBasedAlgorithm(),
            "consistent_hash": ConsistentHashAlgorithm()
        }
        self.performance_history = {}
    
    async def select_algorithm(self, service_name: str, metrics: ServiceMetrics) -> str:
        """自动选择最优算法"""
        if service_name not in self.performance_history:
            self.performance_history[service_name] = {}
        
        # 评估各算法性能
        algorithm_scores = {}
        for algo_name, algorithm in self.algorithms.items():
            score = await self._evaluate_algorithm_performance(
                algorithm, service_name, metrics
            )
            algorithm_scores[algo_name] = score
        
        # 选择得分最高的算法
        best_algorithm = max(algorithm_scores.items(), key=lambda x: x[1])[0]
        return best_algorithm
    
    async def _evaluate_algorithm_performance(
        self, 
        algorithm: LoadBalanceAlgorithm, 
        service_name: str, 
        metrics: ServiceMetrics
    ) -> float:
        """评估算法性能"""
        # 综合评估指标：响应时间、错误率、吞吐量
        service_metrics = await metrics.get_service_metrics(service_name)
        
        response_time_score = self._normalize_score(service_metrics.avg_response_time, 0, 10000)
        error_rate_score = self._normalize_score(service_metrics.error_rate, 0, 1)
        throughput_score = self._normalize_score(service_metrics.throughput, 0, 10000)
        
        # 加权评分
        total_score = (
            response_time_score * 0.4 +     # 响应时间权重40%
            error_rate_score * 0.3 +        # 错误率权重30%
            throughput_score * 0.3          # 吞吐量权重30%
        )
        
        return total_score
    
    def _normalize_score(self, value: float, min_val: float, max_val: float) -> float:
        """归一化评分到0-100"""
        if value <= min_val:
            return 100.0
        if value >= max_val:
            return 0.0
        
        normalized = 1.0 - (value - min_val) / (max_val - min_val)
        return normalized * 100.0
```

---

## 📋 请求上下文与指标收集

### 1. 请求上下文

```python
@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str
    user_id: Optional[str]
    session_id: Optional[str]
    service_name: str
    method: str
    path: str
    headers: Dict[str, str]
    query_params: Dict[str, str]
    timestamp: datetime
    client_ip: str
    user_agent: str
    
    # 负载均衡相关
    previous_attempts: List[str] = field(default_factory=list)
    preferred_instance: Optional[str] = None
    stickiness_cookie: Optional[str] = None
```

### 2. 指标收集系统

```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.request_metrics = {}
        self.instance_metrics = {}
        self.circuit_breaker_states = {}
    
    async def record_request(
        self, 
        service_name: str, 
        instance_id: str, 
        response_time: float, 
        status_code: int
    ):
        """记录请求指标"""
        timestamp = datetime.now()
        
        # 更新实例指标
        if instance_id not in self.instance_metrics:
            self.instance_metrics[instance_id] = InstanceMetrics()
        
        metrics = self.instance_metrics[instance_id]
        metrics.total_requests += 1
        metrics.total_response_time += response_time
        
        if status_code >= 500:
            metrics.error_count += 1
        
        metrics.last_request_time = timestamp
        metrics.avg_response_time = metrics.total_response_time / metrics.total_requests
        
        # 维护时间窗口数据
        self._update_time_window_metrics(instance_id, timestamp, response_time, status_code)
    
    async def get_connection_counts(self) -> Dict[str, int]:
        """获取当前连接数"""
        # 实时连接数统计
        connection_counts = {}
        for instance_id, metrics in self.instance_metrics.items():
            connection_counts[instance_id] = metrics.active_connections
        
        return connection_counts
    
    async def get_response_times(self) -> Dict[str, float]:
        """获取平均响应时间"""
        response_times = {}
        for instance_id, metrics in self.instance_metrics.items():
            response_times[instance_id] = metrics.avg_response_time
        
        return response_times

@dataclass
class InstanceMetrics:
    """实例指标"""
    total_requests: int = 0
    total_response_time: float = 0.0
    error_count: int = 0
    active_connections: int = 0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    
    # 时间窗口指标
    requests_5min: int = 0
    errors_5min: int = 0
    avg_response_5min: float = 0.0
```

---

## 🔄 动态配置管理

### 1. 配置热更新机制

```python
class ConfigWatcher:
    """配置监听器"""
    
    def __init__(self, etcd_client: EtcdClient):
        self.etcd = etcd_client
        self.watchers = {}
        self.callbacks = {}
    
    async def watch_service_config(self, service_name: str, callback: Callable[[Dict], None]):
        """监听服务配置变更"""
        key = f"/service-config/{service_name}"
        
        # 创建监听器
        watch_id = self.etcd.add_watch_callback(
            key=key,
            callback=lambda event: self._on_config_change(event, callback)
        )
        
        self.watchers[service_name] = watch_id
        self.callbacks[service_name] = callback
    
    def _on_config_change(self, event: EtcdEvent, callback: Callable[[Dict], None]):
        """配置变更处理"""
        if event.type == EventType.PUT:
            try:
                config = json.loads(event.value.decode('utf-8'))
                asyncio.create_task(self._safe_callback(callback, config))
            except Exception as e:
                logger.error(f"Failed to parse config change: {e}")
    
    async def _safe_callback(self, callback: Callable[[Dict], None], config: Dict):
        """安全执行回调"""
        try:
            await callback(config)
        except Exception as e:
            logger.error(f"Config callback failed: {e}")
```

### 2. 配置版本管理

```python
class ConfigVersionManager:
    """配置版本管理器"""
    
    def __init__(self, storage: ConfigStorage):
        self.storage = storage
    
    async def create_version(
        self, 
        service_name: str, 
        config: Dict, 
        description: str = "", 
        created_by: str = ""
    ) -> str:
        """创建配置版本"""
        version = self._generate_version()
        
        config_record = ConfigRecord(
            service_name=service_name,
            version=version,
            config_data=config,
            description=description,
            created_by=created_by,
            created_at=datetime.now()
        )
        
        await self.storage.save_config(config_record)
        
        # 更新当前活跃版本
        await self.storage.set_active_version(service_name, version)
        
        return version
    
    async def rollback_to_version(self, service_name: str, target_version: str) -> bool:
        """回滚到指定版本"""
        config_record = await self.storage.get_config(service_name, target_version)
        if not config_record:
            return False
        
        # 创建回滚记录
        rollback_version = await self.create_version(
            service_name=service_name,
            config=config_record.config_data,
            description=f"Rollback to version {target_version}",
            created_by="system"
        )
        
        return True
    
    def _generate_version(self) -> str:
        """生成版本号"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.token_hex(4)
        return f"v{timestamp}_{random_suffix}"
```

---

## 📱 多协议支持架构

### 1. 协议适配器设计

```python
class ProtocolAdapter(ABC):
    """协议适配器基类"""
    
    @abstractmethod
    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册服务"""
        pass
    
    @abstractmethod
    async def discover_services(self, service_name: str) -> List[ServiceInstance]:
        """发现服务"""
        pass
    
    @abstractmethod
    async def health_check(self, instance: ServiceInstance) -> HealthCheckResult:
        """健康检查"""
        pass

class HTTPProtocolAdapter(ProtocolAdapter):
    """HTTP协议适配器"""
    
    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册HTTP服务"""
        # 验证HTTP端点可访问性
        health_url = f"http://{instance.host}:{instance.port}/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(health_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status == 200:
                        return await self._persist_registration(instance)
                    return False
        except Exception as e:
            logger.error(f"HTTP service registration failed: {e}")
            return False

class GRPCProtocolAdapter(ProtocolAdapter):
    """gRPC协议适配器"""
    
    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册gRPC服务"""
        import grpc
        from grpc_health.v1 import health_pb2_grpc
        
        try:
            channel = grpc.insecure_channel(f"{instance.host}:{instance.port}")
            stub = health_pb2_grpc.HealthStub(channel)
            
            # 验证gRPC服务可访问性
            request = health_pb2.HealthCheckRequest(service="")
            response = stub.Check(request, timeout=5)
            
            if response.status == health_pb2.HealthCheckResponse.SERVING:
                return await self._persist_registration(instance)
            return False
        except Exception as e:
            logger.error(f"gRPC service registration failed: {e}")
            return False
        finally:
            channel.close()

class GraphQLProtocolAdapter(ProtocolAdapter):
    """GraphQL协议适配器"""
    
    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册GraphQL服务"""
        # GraphQL服务通常通过HTTP端点暴露
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"http://{instance.host}:{instance.port}/graphql",
                    json={"query": query},
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data.get("errors"):
                            return await self._persist_registration(instance)
                    return False
        except Exception as e:
            logger.error(f"GraphQL service registration failed: {e}")
            return False
```

### 2. 协议转换层

```python
class ProtocolTranslationLayer:
    """协议转换层"""
    
    def __init__(self):
        self.translators = {
            "http_to_grpc": HTTPToGRPCTranslator(),
            "grpc_to_http": GRPCToHTTPTranslator(),
            "graphql_to_http": GraphQLToHTTPTranslator(),
            "http_to_graphql": HTTPToGraphQLTranslator(),
        }
    
    async def translate_request(
        self, 
        source_protocol: str, 
        target_protocol: str, 
        request: Any
    ) -> Any:
        """请求协议转换"""
        translator_key = f"{source_protocol}_to_{target_protocol}"
        translator = self.translators.get(translator_key)
        
        if not translator:
            raise ValueError(f"No translator found for {translator_key}")
        
        return await translator.translate_request(request)
    
    async def translate_response(
        self, 
        source_protocol: str, 
        target_protocol: str, 
        response: Any
    ) -> Any:
        """响应协议转换"""
        translator_key = f"{source_protocol}_to_{target_protocol}"
        translator = self.translators.get(translator_key)
        
        if not translator:
            raise ValueError(f"No translator found for {translator_key}")
        
        return await translator.translate_response(response)
```

---

## 🔌 插件系统集成架构

### 1. 插件接口定义

```python
class ServiceDiscoveryPlugin(ABC):
    """服务发现插件基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict) -> bool:
        """初始化插件"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """关闭插件"""
        pass

class HealthCheckPlugin(ServiceDiscoveryPlugin):
    """健康检查插件"""
    
    @abstractmethod
    async def check_health(self, instance: ServiceInstance) -> HealthCheckResult:
        """执行健康检查"""
        pass

class LoadBalancePlugin(ServiceDiscoveryPlugin):
    """负载均衡插件"""
    
    @abstractmethod
    async def select_instance(
        self, 
        instances: List[ServiceInstance], 
        context: RequestContext
    ) -> ServiceInstance:
        """选择服务实例"""
        pass
```

### 2. 插件管理器

```python
class PluginManager:
    """插件管理器"""
    
    def __init__(self):
        self.plugins = {}
        self.plugin_configs = {}
        self.plugin_dependencies = {}
    
    async def load_plugin(self, plugin_class: Type[ServiceDiscoveryPlugin], config: Dict) -> bool:
        """加载插件"""
        try:
            plugin_instance = plugin_class()
            await plugin_instance.initialize(config)
            
            self.plugins[plugin_instance.name] = plugin_instance
            self.plugin_configs[plugin_instance.name] = config
            
            logger.info(f"Plugin {plugin_instance.name} loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to load plugin: {e}")
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        if plugin_name not in self.plugins:
            return False
        
        try:
            await self.plugins[plugin_name].shutdown()
            del self.plugins[plugin_name]
            del self.plugin_configs[plugin_name]
            
            logger.info(f"Plugin {plugin_name} unloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[ServiceDiscoveryPlugin]:
        """获取插件实例"""
        return self.plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: Type[ServiceDiscoveryPlugin]) -> List[ServiceDiscoveryPlugin]:
        """按类型获取插件列表"""
        return [
            plugin for plugin in self.plugins.values() 
            if isinstance(plugin, plugin_type)
        ]
```

---

## 🚀 部署架构设计

### 1. Kubernetes 部署

```yaml
# Service Discovery Cluster Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: athena-service-discovery
  namespace: athena-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: athena-service-discovery
  template:
    metadata:
      labels:
        app: athena-service-discovery
    spec:
      containers:
      - name: service-discovery
        image: athena/service-discovery:v2.0
        ports:
        - containerPort: 8080
        - containerPort: 8081
        env:
        - name: NODE_ENV
          value: "production"
        - name: REDIS_URL
          value: "redis://redis-cluster:6379"
        - name: POSTGRES_URL
          value: "postgresql://user:pass@postgres:5432/service_discovery"
        - name: ETCD_ENDPOINTS
          value: "etcd-0:2379,etcd-1:2379,etcd-2:2379"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

---
# Service Discovery Service
apiVersion: v1
kind: Service
metadata:
  name: athena-service-discovery
  namespace: athena-system
spec:
  selector:
    app: athena-service-discovery
  ports:
  - name: http
    port: 8080
    targetPort: 8080
  - name: grpc
    port: 8081
    targetPort: 8081
  type: ClusterIP

---
# ConfigMap for Service Discovery
apiVersion: v1
kind: ConfigMap
metadata:
  name: service-discovery-config
  namespace: athena-system
data:
  config.yaml: |
    service_discovery:
      health_check:
        default_interval: 30
        default_timeout: 5
        failure_threshold: 3
      load_balancing:
        default_algorithm: "weighted_round_robin"
        adaptive_enabled: true
      storage:
        redis:
          enabled: true
          cluster_mode: true
        postgresql:
          enabled: true
          connection_pool_size: 20
        etcd:
          enabled: true
          watch_timeout: 30
```

### 2. Standalone 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  service-discovery:
    image: athena/service-discovery:v2.0
    ports:
      - "8080:8080"
      - "8081:8081"
    environment:
      - NODE_ENV=production
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://postgres:password@postgres:5432/service_discovery
      - ETCD_ENDPOINTS=etcd:2379
    depends_on:
      - redis
      - postgres
      - etcd
    restart: unless-stopped
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=service_discovery
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./migration/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped

  etcd:
    image: quay.io/coreos/etcd:v3.5.9
    ports:
      - "2379:2379"
      - "2380:2380"
    environment:
      - ETCD_NAME=etcd
      - ETCD_DATA_DIR=/etcd-data
      - ETCD_LISTEN_CLIENT_URLS=http://0.0.0.0:2379
      - ETCD_ADVERTISE_CLIENT_URLS=http://etcd:2379
      - ETCD_LISTEN_PEER_URLS=http://0.0.0.0:2380
      - ETCD_INITIAL_ADVERTISE_PEER_URLS=http://etcd:2380
      - ETCD_INITIAL_CLUSTER=etcd=http://etcd:2380
      - ETCD_INITIAL_CLUSTER_TOKEN=etcd-cluster
      - ETCD_INITIAL_CLUSTER_STATE=new
    volumes:
      - etcd_data:/etcd-data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
  etcd_data:
```

---

## 📊 监控与可观测性

### 1. 指标收集

```python
class ObservabilityManager:
    """可观测性管理器"""
    
    def __init__(self):
        self.metrics_registry = PrometheusMetricsRegistry()
        self.tracer = JaegerTracer()
        self.logger = StructuredLogger()
    
    async def record_service_discovery_metrics(self):
        """记录服务发现指标"""
        # Prometheus指标
        service_discovery_requests = self.metrics_registry.counter(
            'service_discovery_requests_total',
            'Total service discovery requests',
            ['service_name', 'status']
        )
        
        discovery_latency = self.metrics_registry.histogram(
            'service_discovery_duration_seconds',
            'Service discovery request duration',
            ['service_name']
        )
        
        active_instances = self.metrics_registry.gauge(
            'service_instances_active',
            'Number of active service instances',
            ['service_name', 'status']
        )
        
        # 分布式追踪
        with self.tracer.start_span("service_discovery") as span:
            span.set_tag("service_name", "athena-gateway")
            span.set_tag("operation", "discover_services")
            
            # 记录指标
            service_discovery_requests.labels(
                service_name="athena-gateway", 
                status="success"
            ).inc()
            
            discovery_latency.labels(service_name="athena-gateway").observe(0.05)
            
            active_instances.labels(
                service_name="user-service",
                status="healthy"
            ).set(5)
```

### 2. 告警规则

```yaml
# Prometheus告警规则
groups:
- name: service_discovery_alerts
  rules:
  - alert: ServiceDiscoveryHighLatency
    expr: histogram_quantile(0.95, rate(service_discovery_duration_seconds_bucket[5m])) > 1
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Service discovery latency is high"
      description: "95th percentile latency is {{ $value }}s"

  - alert: ServiceInstanceDown
    expr: service_instances_active{status="healthy"} == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "All instances of service {{ $labels.service_name }} are down"
      description: "No healthy instances available for service {{ $labels.service_name }}"

  - alert: HealthCheckFailureRate
    expr: rate(health_check_failures_total[5m]) > 0.1
    for: 3m
    labels:
      severity: warning
    annotations:
      summary: "Health check failure rate is high"
      description: "Health check failure rate is {{ $value }} failures/sec"
```

---

## 🎯 总结与展望

### 核心特性总结

1. **高可用架构**: 多节点部署，Raft一致性协议，无单点故障
2. **智能负载均衡**: 多算法支持，自适应选择，实时性能评估
3. **全面健康检查**: 多协议支持，自适应频率，智能故障检测
4. **动态配置管理**: 热更新，版本控制，配置回滚
5. **插件化架构**: 可扩展设计，统一接口，生命周期管理
6. **多协议支持**: HTTP/gRPC/GraphQL统一服务发现
7. **完善可观测性**: 指标收集，分布式追踪，智能告警

### 技术优势

- **性能优异**: 内存缓存 + Redis多层存储，毫秒级响应
- **可靠性高**: 多副本部署，自动故障转移，数据一致性保证
- **扩展性强**: 水平扩展，插件化架构，支持自定义扩展
- **运维友好**: 完整监控指标，自动告警，便捷部署

### 未来演进方向

1. **AI增强**: 机器学习驱动的负载均衡和故障预测
2. **边缘计算**: 支持边缘节点的服务发现和负载均衡
3. **服务网格**: 与Istio等服务网格深度集成
4. **多云支持**: 跨云厂商的统一服务发现
5. **零信任安全**: 基于身份的服务访问控制

---

**设计完成时间**: 2026-02-20  
**文档版本**: v1.0  
**作者**: Athena AI Team