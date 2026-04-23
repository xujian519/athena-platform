# 企业级多智能体协作架构 - 接口定义文档

## 1. 核心接口定义

### 1.1 小诺智能编排器接口

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class RequestStatus(Enum):
    """请求状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class IntentType(Enum):
    """意图类型枚举"""
    PATENT_WRITING = "patent_writing"
    PATENT_SEARCH = "patent_search"
    TECHNOLOGY_ANALYSIS = "technology_analysis"
    DOCUMENT_GENERATION = "document_generation"
    CONSULTATION = "consultation"

@dataclass
class UserRequest:
    """用户请求"""
    request_id: str
    user_id: str
    timestamp: datetime
    content: str
    request_type: str
    priority: int = 1
    context: Dict[str, Any] = None
    metadata: Dict[str, Any] = None

@dataclass
class Intent:
    """用户意图"""
    intent_type: IntentType
    confidence: float
    entities: Dict[str, Any]
    context: Dict[str, Any]
    extracted_keywords: List[str]
    estimated_complexity: float

@dataclass
class Task:
    """任务"""
    task_id: str
    name: str
    description: str
    required_capabilities: List[str]
    estimated_duration: int  # 秒
    dependencies: List[str] = None
    parameters: Dict[str, Any] = None

@dataclass
class TaskPlan:
    """任务计划"""
    plan_id: str
    tasks: List[Task]
    dependencies: Dict[str, List[str]]
    execution_order: List[str]
    estimated_total_time: int
    parallel_groups: List[List[str]]

@dataclass
class AgentAssignment:
    """智能体分配"""
    task_id: str
    agent_id: str
    agent_instance: str
    estimated_start_time: datetime
    estimated_end_time: datetime
    resource_allocation: Dict[str, Any]

@dataclass
class AgentExecutionPlan:
    """智能体执行计划"""
    plan_id: str
    assignments: List[AgentAssignment]
    execution_strategy: str
    fallback_strategies: List[str]

@dataclass
class OrchestratorResponse:
    """编排器响应"""
    request_id: str
    status: RequestStatus
    result: Dict[str, Any]
    execution_summary: Dict[str, Any]
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

class IXiaonuoOrchestrator(ABC):
    """小诺智能编排器接口"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化编排器"""
        pass
    
    @abstractmethod
    async def process_request(self, request: UserRequest) -> OrchestratorResponse:
        """处理用户请求"""
        pass
    
    @abstractmethod
    async def get_request_status(self, request_id: str) -> RequestStatus:
        """获取请求状态"""
        pass
    
    @abstractmethod
    async def cancel_request(self, request_id: str) -> bool:
        """取消请求"""
        pass
    
    @abstractmethod
    async def get_execution_metrics(self) -> Dict[str, Any]:
        """获取执行指标"""
        pass
```

### 1.2 标准化智能体接口

```python
@dataclass
class AgentCapability:
    """智能体能力"""
    name: str
    category: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    performance_metrics: Dict[str, float]
    supported_languages: List[str]
    max_concurrent_tasks: int

@dataclass
class AgentMetadata:
    """智能体元数据"""
    agent_id: str
    name: str
    version: str
    description: str
    capabilities: List[AgentCapability]
    resource_requirements: Dict[str, Any]
    health_check_interval: int
    supported_message_types: List[str]

class AgentStatus(Enum):
    """智能体状态"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    SHUTTING_DOWN = "shutting_down"

class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class AgentInstance:
    """智能体实例"""
    instance_id: str
    agent_id: str
    host: str
    port: int
    status: AgentStatus
    health_status: HealthStatus
    current_load: float
    max_capacity: int
    last_heartbeat: datetime
    capabilities: List[str]

@dataclass
class MessageContext:
    """消息上下文"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    correlation_id: Optional[str]
    timestamp: datetime
    source: str
    destination: str

@dataclass
class AgentMessage:
    """智能体消息"""
    message_id: str
    message_type: str
    payload: Dict[str, Any]
    context: MessageContext
    priority: int = 1
    ttl: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class ProcessingResult:
    """处理结果"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    processing_time: float = 0.0
    metrics: Dict[str, Any] = None

class IStandardAgent(ABC):
    """标准化智能体接口"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化智能体"""
        pass
    
    @abstractmethod
    async def process_message(self, message: AgentMessage) -> ProcessingResult:
        """处理消息"""
        pass
    
    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """健康检查"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[AgentCapability]:
        """获取能力列表"""
        pass
    
    @abstractmethod
    async def get_metadata(self) -> AgentMetadata:
        """获取元数据"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> bool:
        """关闭智能体"""
        pass
    
    @abstractmethod
    async def update_config(self, config: Dict[str, Any]) -> bool:
        """更新配置"""
        pass
```

### 1.3 原子工具接口

```python
@dataclass
class ToolParameter:
    """工具参数"""
    name: str
    type: str
    description: str
    required: bool = True
    default_value: Any = None
    validation_rules: Dict[str, Any] = None

@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

@dataclass
class ToolMetadata:
    """工具元数据"""
    tool_id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tags: List[str]
    parameters: List[ToolParameter]
    return_schema: Dict[str, Any]
    dependencies: List[str]
    resource_requirements: Dict[str, Any]
    license: str

@dataclass
class ToolExecutionRequest:
    """工具执行请求"""
    tool_id: str
    parameters: Dict[str, Any]
    execution_context: Dict[str, Any]
    timeout: int = 300
    priority: int = 1

class IAtomicTool(ABC):
    """原子工具接口"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化工具"""
        pass
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> ToolResult:
        """执行工具"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> bool:
        """清理资源"""
        pass
    
    @abstractmethod
    def get_metadata(self) -> ToolMetadata:
        """获取工具元数据"""
        pass
    
    @abstractmethod
    async def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        pass
    
    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """获取参数和返回值schema"""
        pass

class IAtomicToolRegistry(ABC):
    """原子工具注册中心接口"""
    
    @abstractmethod
    async def register_tool(self, tool: IAtomicTool) -> bool:
        """注册工具"""
        pass
    
    @abstractmethod
    async def unregister_tool(self, tool_id: str) -> bool:
        """注销工具"""
        pass
    
    @abstractmethod
    async def get_tool(self, tool_id: str) -> Optional[IAtomicTool]:
        """获取工具实例"""
        pass
    
    @abstractmethod
    async def list_tools(self, category: Optional[str] = None) -> List[ToolMetadata]:
        """列出工具"""
        pass
    
    @abstractmethod
    async def execute_tool(self, request: ToolExecutionRequest) -> ToolResult:
        """执行工具"""
        pass
    
    @abstractmethod
    async def search_tools(self, query: str) -> List[ToolMetadata]:
        """搜索工具"""
        pass
```

### 1.4 统一通信协议接口

```python
@dataclass
class MessageRoute:
    """消息路由"""
    route_id: str
    source_agent: str
    target_agent: str
    target_instance: str
    transport_channel: str
    estimated_latency: int
    reliability: float

@dataclass
class TransportConfig:
    """传输配置"""
    channel_type: str
    connection_params: Dict[str, Any]
    security_config: Dict[str, Any]
    timeout_config: Dict[str, Any]
    retry_config: Dict[str, Any]

class IMessageRouter(ABC):
    """消息路由器接口"""
    
    @abstractmethod
    async def route_message(self, message: AgentMessage) -> MessageRoute:
        """路由消息"""
        pass
    
    @abstractmethod
    async def update_routing_table(self, routes: List[MessageRoute]) -> bool:
        """更新路由表"""
        pass
    
    @abstractmethod
    async def get_route_info(self, target_agent: str) -> List[MessageRoute]:
        """获取路由信息"""
        pass

class IAsyncTransport(ABC):
    """异步传输接口"""
    
    @abstractmethod
    async def send_message(self, route: MessageRoute, message: bytes) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def receive_message(self, channel: str, timeout: int = 30) -> Optional[bytes]:
        """接收消息"""
        pass
    
    @abstractmethod
    async def create_channel(self, config: TransportConfig) -> str:
        """创建通道"""
        pass
    
    @abstractmethod
    async def close_channel(self, channel: str) -> bool:
        """关闭通道"""
        pass

class IMessageSerializer(ABC):
    """消息序列化接口"""
    
    @abstractmethod
    async def serialize(self, message: AgentMessage) -> bytes:
        """序列化消息"""
        pass
    
    @abstractmethod
    async def deserialize(self, data: bytes) -> AgentMessage:
        """反序列化消息"""
        pass
    
    @abstractmethod
    async def get_schema_version(self) -> str:
        """获取schema版本"""
        pass

class IUnifiedCommunicationProtocol(ABC):
    """统一通信协议接口"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化协议"""
        pass
    
    @abstractmethod
    async def send_message(self, message: AgentMessage) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    async def receive_message(self, timeout: int = 30) -> Optional[AgentMessage]:
        """接收消息"""
        pass
    
    @abstractmethod
    async def broadcast_message(self, message: AgentMessage, target_group: str) -> bool:
        """广播消息"""
        pass
    
    @abstractmethod
    async def get_message_status(self, message_id: str) -> Dict[str, Any]:
        """获取消息状态"""
        pass
```

### 1.5 可观测性系统接口

```python
@dataclass
class TraceContext:
    """追踪上下文"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    tags: Dict[str, Any]
    baggage: Dict[str, Any]

@dataclass
class Span:
    """跨度"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: Optional[float]
    tags: Dict[str, Any]
    logs: List[Dict[str, Any]]
    status: str

@dataclass
class MetricPoint:
    """指标点"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, Any]
    metric_type: str  # counter, gauge, histogram, timer

@dataclass
class LogEntry:
    """日志条目"""
    timestamp: datetime
    level: str
    message: str
    context: Dict[str, Any]
    trace_id: Optional[str] = None
    span_id: Optional[str] = None

class IDistributedTracer(ABC):
    """分布式追踪器接口"""
    
    @abstractmethod
    async def start_trace(self, operation_name: str) -> TraceContext:
        """开始追踪"""
        pass
    
    @abstractmethod
    async def create_span(self, parent_context: TraceContext, operation_name: str) -> Span:
        """创建跨度"""
        pass
    
    @abstractmethod
    async def finish_span(self, span: Span) -> bool:
        """完成跨度"""
        pass
    
    @abstractmethod
    async def get_trace(self, trace_id: str) -> List[Span]:
        """获取追踪信息"""
        pass

class IMetricsCollector(ABC):
    """指标收集器接口"""
    
    @abstractmethod
    async def record_metric(self, metric: MetricPoint) -> bool:
        """记录指标"""
        pass
    
    @abstractmethod
    async def increment_counter(self, name: str, tags: Dict[str, Any], value: float = 1.0) -> bool:
        """递增计数器"""
        pass
    
    @abstractmethod
    async def set_gauge(self, name: str, tags: Dict[str, Any], value: float) -> bool:
        """设置仪表值"""
        pass
    
    @abstractmethod
    async def record_histogram(self, name: str, tags: Dict[str, Any], value: float) -> bool:
        """记录直方图"""
        pass
    
    @abstractmethod
    async def get_metrics(self, query: str) -> List[MetricPoint]:
        """查询指标"""
        pass

class ILogAggregator(ABC):
    """日志聚合器接口"""
    
    @abstractmethod
    async def collect_log(self, log_entry: LogEntry) -> bool:
        """收集日志"""
        pass
    
    @abstractmethod
    async def search_logs(self, query: str, time_range: Dict[str, datetime]) -> List[LogEntry]:
        """搜索日志"""
        pass
    
    @abstractmethod
    async def get_logs_by_trace(self, trace_id: str) -> List[LogEntry]:
        """按追踪ID获取日志"""
        pass

class IObservabilitySystem(ABC):
    """可观测性系统接口"""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """初始化系统"""
        pass
    
    @abstractmethod
    async def start_trace(self, operation_name: str) -> TraceContext:
        """开始追踪"""
        pass
    
    @abstractmethod
    async def record_metric(self, metric: MetricPoint) -> bool:
        """记录指标"""
        pass
    
    @abstractmethod
    async def collect_log(self, log_entry: LogEntry) -> bool:
        """收集日志"""
        pass
    
    @abstractmethod
    async def get_dashboard_data(self, dashboard_id: str) -> Dict[str, Any]:
        """获取仪表板数据"""
        pass
```

## 2. 专利专用接口

### 2.1 专利撰写流水线接口

```python
@dataclass
class TechnicalDisclosure:
    """技术交底书"""
    disclosure_id: str
    title: str
    abstract: str
    technical_field: str
    background_art: str
    summary: str
    detailed_description: str
    claims: List[str]
    drawings: List[Dict[str, Any]]
    keywords: List[str]
    inventors: List[str]
    assignee: str
    filing_date: Optional[datetime] = None
    priority_claims: List[str] = None

@dataclass
class PatentDocument:
    """专利文档"""
    document_id: str
    title: str
    abstract: str
    technical_field: str
    background_art: str
    summary: str
    detailed_description: str
    claims: List[str]
    drawings: List[Dict[str, Any]]
    references: List[str]
    classification: List[str]
    application_number: Optional[str] = None
    publication_number: Optional[str] = None
    status: str = "draft"
    metadata: Dict[str, Any] = None

class IPatentWritingPipeline(ABC):
    """专利撰写流水线接口"""
    
    @abstractmethod
    async def execute_patent_writing(self, disclosure: TechnicalDisclosure) -> PatentDocument:
        """执行专利撰写"""
        pass
    
    @abstractmethod
    async def get_pipeline_status(self, pipeline_id: str) -> Dict[str, Any]:
        """获取流水线状态"""
        pass
    
    @abstractmethod
    async def cancel_pipeline(self, pipeline_id: str) -> bool:
        """取消流水线"""
        pass
    
    @abstractmethod
    async def get_quality_metrics(self, document_id: str) -> Dict[str, Any]:
        """获取质量指标"""
        pass

class ITechnicalAnalysisAgent(ABC):
    """技术分析智能体接口"""
    
    @abstractmethod
    async def analyze(self, disclosure: TechnicalDisclosure) -> Dict[str, Any]:
        """分析技术交底书"""
        pass
    
    @abstractmethod
    async def extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        pass
    
    @abstractmethod
    async def classify_technology(self, text: str) -> List[str]:
        """技术分类"""
        pass

class IPatentSearchAgent(ABC):
    """专利检索智能体接口"""
    
    @abstractmethod
    async def search_patents(self, keywords: List[str], fields: List[str]) -> List[Dict[str, Any]]:
        """检索专利"""
        pass
    
    @abstractmethod
    async def download_patent(self, patent_number: str) -> Dict[str, Any]:
        """下载专利"""
        pass
    
    @abstractmethod
    async def analyze_relevance(self, patent: Dict[str, Any], query: str) -> float:
        """分析相关性"""
        pass

class IPatentWritingAgent(ABC):
    """专利撰写智能体接口"""
    
    @abstractmethod
    async def write_patent(self, analysis_result: Dict[str, Any]) -> PatentDocument:
        """撰写专利"""
        pass
    
    @abstractmethod
    async def generate_claims(self, technical_features: List[str]) -> List[str]:
        """生成权利要求"""
        pass
    
    @abstractmethod
    async def generate_abstract(self, detailed_description: str) -> str:
        """生成摘要"""
        pass

class IPatentReviewAgent(ABC):
    """专利审查智能体接口"""
    
    @abstractmethod
    async def review_patent(self, patent: PatentDocument) -> Dict[str, Any]:
        """审查专利"""
        pass
    
    @abstractmethod
    async def check_compliance(self, patent: PatentDocument) -> Dict[str, Any]:
        """检查合规性"""
        pass
    
    @abstractmethod
    async def assess_novelty(self, patent: PatentDocument, prior_art: List[Dict[str, Any]]) -> float:
        """评估新颖性"""
        pass
```

## 3. 配置和部署接口

### 3.1 配置管理接口

```python
@dataclass
class Configuration:
    """配置"""
    config_id: str
    name: str
    version: str
    environment: str
    values: Dict[str, Any]
    schema: Dict[str, Any]
    encrypted_fields: List[str] = None
    created_at: datetime = None
    updated_at: datetime = None

class IConfigurationManager(ABC):
    """配置管理器接口"""
    
    @abstractmethod
    async def get_config(self, config_id: str, environment: str) -> Configuration:
        """获取配置"""
        pass
    
    @abstractmethod
    async def set_config(self, config: Configuration) -> bool:
        """设置配置"""
        pass
    
    @abstractmethod
    async def update_config(self, config_id: str, updates: Dict[str, Any]) -> bool:
        """更新配置"""
        pass
    
    @abstractmethod
    async def delete_config(self, config_id: str) -> bool:
        """删除配置"""
        pass
    
    @abstractmethod
    async def validate_config(self, config: Configuration) -> List[str]:
        """验证配置"""
        pass
```

### 3.2 服务发现接口

```python
@dataclass
class ServiceInstance:
    """服务实例"""
    instance_id: str
    service_name: str
    host: str
    port: int
    health_check_url: str
    metadata: Dict[str, Any]
    registration_time: datetime
    last_heartbeat: datetime

class IServiceDiscovery(ABC):
    """服务发现接口"""
    
    @abstractmethod
    async def register_service(self, instance: ServiceInstance) -> bool:
        """注册服务"""
        pass
    
    @abstractmethod
    async def deregister_service(self, instance_id: str) -> bool:
        """注销服务"""
        pass
    
    @abstractmethod
    async def discover_service(self, service_name: str) -> List[ServiceInstance]:
        """发现服务"""
        pass
    
    @abstractmethod
    async def update_service_health(self, instance_id: str, healthy: bool) -> bool:
        """更新服务健康状态"""
        pass
    
    @abstractmethod
    async def get_service_metadata(self, instance_id: str) -> Dict[str, Any]:
        """获取服务元数据"""
        pass
```

## 4. 安全和权限接口

### 4.1 认证授权接口

```python
@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: str
    roles: List[str]
    permissions: List[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    active: bool = True

@dataclass
class Token:
    """令牌"""
    token_id: str
    user_id: str
    token_type: str
    expires_at: datetime
    scopes: List[str]
    metadata: Dict[str, Any]

class IAuthenticationService(ABC):
    """认证服务接口"""
    
    @abstractmethod
    async def authenticate(self, username: str, password: str) -> Optional[Token]:
        """用户认证"""
        pass
    
    @abstractmethod
    async def validate_token(self, token: str) -> Optional[User]:
        """验证令牌"""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Optional[Token]:
        """刷新令牌"""
        pass
    
    @abstractmethod
    async def revoke_token(self, token: str) -> bool:
        """撤销令牌"""
        pass

class IAuthorizationService(ABC):
    """授权服务接口"""
    
    @abstractmethod
    async def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """检查权限"""
        pass
    
    @abstractmethod
    async def get_user_permissions(self, user_id: str) -> List[str]:
        """获取用户权限"""
        pass
    
    @abstractmethod
    async def grant_permission(self, user_id: str, permission: str) -> bool:
        """授予权限"""
        pass
    
    @abstractmethod
    async def revoke_permission(self, user_id: str, permission: str) -> bool:
        """撤销权限"""
        pass
```

## 5. 测试接口

### 5.1 模拟和测试接口

```python
@dataclass
class TestCase:
    """测试用例"""
    test_id: str
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_output: Dict[str, Any]
    test_type: str
    timeout: int = 30

@dataclass
class TestResult:
    """测试结果"""
    test_id: str
    passed: bool
    actual_output: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = None

class ITestFramework(ABC):
    """测试框架接口"""
    
    @abstractmethod
    async def run_test_case(self, test_case: TestCase) -> TestResult:
        """运行测试用例"""
        pass
    
    @abstractmethod
    async def run_test_suite(self, test_suite_id: str) -> List[TestResult]:
        """运行测试套件"""
        pass
    
    @abstractmethod
    async def generate_test_report(self, results: List[TestResult]) -> Dict[str, Any]:
        """生成测试报告"""
        pass
    
    @abstractmethod
    async def mock_agent_response(self, agent_id: str, response: Dict[str, Any]) -> bool:
        """模拟智能体响应"""
        pass
```

## 6. 接口版本管理

### 6.1 版本控制策略

```python
@dataclass
class APIVersion:
    """API版本"""
    version: str
    status: str  # stable, deprecated, experimental
    release_date: datetime
    deprecation_date: Optional[datetime] = None
    sunset_date: Optional[datetime] = None
    migration_guide: Optional[str] = None

class IVersionManager(ABC):
    """版本管理器接口"""
    
    @abstractmethod
    async def get_current_version(self, api_name: str) -> str:
        """获取当前版本"""
        pass
    
    @abstractmethod
    async def get_supported_versions(self, api_name: str) -> List[str]:
        """获取支持的版本"""
        pass
    
    @abstractmethod
    async def is_version_supported(self, api_name: str, version: str) -> bool:
        """检查版本是否支持"""
        pass
    
    @abstractmethod
    async def get_version_info(self, api_name: str, version: str) -> APIVersion:
        """获取版本信息"""
        pass
```

## 7. 接口实现示例

### 7.1 错误处理

```python
class AgentException(Exception):
    """智能体异常"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

class ToolExecutionError(AgentException):
    """工具执行错误"""
    pass

class CommunicationError(AgentException):
    """通信错误"""
    pass

class ValidationError(AgentException):
    """验证错误"""
    pass

class TimeoutError(AgentException):
    """超时错误"""
    pass
```

### 7.2 响应格式标准化

```python
@dataclass
class APIResponse:
    """API响应"""
    success: bool
    data: Any = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
```

这些接口定义为企业级多智能体协作系统提供了完整的规范，确保了系统的模块化、可扩展性和可维护性。所有实现都必须遵循这些接口规范，以便于系统的集成和测试。