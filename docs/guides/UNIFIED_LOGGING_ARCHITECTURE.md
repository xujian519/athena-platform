# 统一日志系统架构设计

> **Phase 3 Week 3**
> **主题**: 统一日志系统
> **设计时间**: 2026-04-22

---

## 📋 设计目标

### 核心功能
1. **统一格式**: 所有服务使用相同的日志格式
2. **结构化日志**: 使用JSON格式，便于解析和查询
3. **上下文信息**: 自动包含服务名、模块名、请求ID等
4. **多级日志**: 支持DEBUG/INFO/WARNING/ERROR/CRITICAL
5. **灵活输出**: 支持控制台、文件、远程收集
6. **性能优化**: 异步日志，不阻塞主流程

### 非功能性需求
- **高性能**: 日志写入不影响应用性能
- **可靠性**: 日志不丢失，异步写入
- **可扩展**: 易于添加新的日志处理器
- **易用性**: 简单的API，自动收集上下文

---

## 🏗️ 日志架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                   Application Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ Xiaona   │  │ Xiaonuo  │  │ Gateway  │  │ 其他服务 ││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘│
│       │             │             │             │       │
│       └─────────────┴─────────────┴─────────────┘       │
│                         │                               │
│                         ▼                               │
│  ┌──────────────────────────────────────────────────┐  │
│  │        Unified Logging System                     │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Logger       │  │ Formatters   │              │  │
│  │  └──────────────┘  └──────────────┘              │  │
│  │  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │ Handlers     │  │ Filters      │              │  │
│  │  └──────────────┘  └──────────────┘              │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                               │
└─────────────────────────┼───────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌─────────┐     ┌──────────┐
   │ Console │      │  File   │     │  Remote  │
   │ Output  │      │ Storage │     │ Collector│
   └─────────┘      └─────────┘     └──────────┘
```

---

## 📝 日志格式设计

### 统一日志格式

使用JSON格式，便于机器解析和查询。

```json
{
  "timestamp": "2026-04-22T10:00:00.123Z",
  "level": "INFO",
  "service": "xiaona",
  "module": "patent_analysis",
  "function": "analyze_patent",
  "message": "专利分析完成",
  "context": {
    "request_id": "req-001",
    "user_id": "user-123",
    "patent_id": "CN123456789A"
  },
  "extra": {
    "duration_ms": 1234,
    "model": "claude-sonnet-4-6",
    "tokens": 2500
  }
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|-----|------|-----|------|
| timestamp | string | ✅ | ISO 8601格式的时间戳 |
| level | string | ✅ | 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL |
| service | string | ✅ | 服务名称 |
| module | string | ✅ | 模块名称 |
| function | string | ✅ | 函数名称 |
| message | string | ✅ | 日志消息 |
| context | object | ❌ | 上下文信息（请求ID、用户ID等） |
| extra | object | ❌ | 额外信息（性能指标、业务数据等） |
| exception | object | ❌ | 异常信息（仅ERROR/CRITICAL） |

---

## 🎚️ 日志级别设计

### 级别定义

```python
class LogLevel(Enum):
    """日志级别"""
    DEBUG = 10      # 调试信息：详细的诊断信息
    INFO = 20       # 一般信息：重要事件
    WARNING = 30    # 警告信息：潜在问题
    ERROR = 40      # 错误信息：错误但可继续
    CRITICAL = 50   # 严重错误：系统无法继续
```

### 使用场景

| 级别 | 使用场景 | 示例 |
|-----|---------|------|
| DEBUG | 开发调试 | 变量值、函数调用 |
| INFO | 重要事件 | 服务启动、任务完成 |
| WARNING | 潜在问题 | 重试、降级服务 |
| ERROR | 错误处理 | API调用失败、超时 |
| CRITICAL | 严重错误 | 服务崩溃、数据丢失 |

### 默认级别

- **开发环境**: DEBUG
- **测试环境**: INFO
- **生产环境**: WARNING

---

## 🔧 核心组件设计

### 1. UnifiedLogger

统一日志记录器。

```python
class UnifiedLogger:
    """统一日志记录器"""
    
    def __init__(
        self,
        service_name: str,
        level: LogLevel = LogLevel.INFO
    ):
        self.service_name = service_name
        self.level = level
        self.context = {}
    
    def debug(self, message: str, **kwargs):
        """记录DEBUG级别日志"""
        
    def info(self, message: str, **kwargs):
        """记录INFO级别日志"""
        
    def warning(self, message: str, **kwargs):
        """记录WARNING级别日志"""
        
    def error(self, message: str, exception: Exception = None, **kwargs):
        """记录ERROR级别日志"""
        
    def critical(self, message: str, exception: Exception = None, **kwargs):
        """记录CRITICAL级别日志"""
```

### 2. JSONFormatter

JSON格式化器。

```python
class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON"""
        
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "module": record.module,
            "function": record.funcName,
            "message": record.getMessage(),
            "context": self._get_context(record),
            "extra": self._get_extra(record)
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self._format_exception(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)
```

### 3. ContextHandler

上下文处理器。

```python
class ContextHandler:
    """上下文处理器"""
    
    _context = {}
    
    @classmethod
    def set_context(cls, key: str, value: Any):
        """设置上下文"""
        cls._context[key] = value
    
    @classmethod
    def get_context(cls) -> Dict[str, Any]:
        """获取所有上下文"""
        return cls._context.copy()
    
    @classmethod
    def clear_context(cls):
        """清除上下文"""
        cls._context.clear()
```

### 4. LogHandler

日志处理器。

```python
class UnifiedLogHandler:
    """统一日志处理器"""
    
    def __init__(self):
        self.handlers = []
    
    def add_console_handler(self, level: LogLevel = LogLevel.INFO):
        """添加控制台处理器"""
        
    def add_file_handler(
        self,
        filename: str,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5
    ):
        """添加文件处理器（支持轮转）"""
        
    def add_remote_handler(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None
    ):
        """添加远程收集处理器"""
```

---

## 🗂️ 日志收集设计

### 1. 控制台输出

**适用场景**: 开发环境、容器环境

**配置**:
```yaml
logging:
  handlers:
    console:
      class: logging.StreamHandler
      level: INFO
      formatter: json
      stream: ext://sys.stdout
```

### 2. 文件存储

**适用场景**: 所有环境

**配置**:
```yaml
logging:
  handlers:
    file:
      class: logging.handlers.RotatingFileHandler
      level: INFO
      formatter: json
      filename: logs/{service_name}.log
      maxBytes: 10485760  # 10MB
      backupCount: 5
      encoding: utf-8
```

### 3. 远程收集

**适用场景**: 生产环境、分布式系统

**配置**:
```yaml
logging:
  handlers:
    remote:
      class: unified_logging.handlers.RemoteHandler
      level: WARNING
      formatter: json
      url: http://log-collector:5050/logs
      headers:
        X-Service-Token: {service_token}
```

---

## 🎯 日志上下文设计

### 自动上下文

系统自动收集的上下文信息：

```python
{
    "request_id": "req-{uuid}",        # 请求ID
    "service_name": "xiaona",          # 服务名
    "host": "localhost",               # 主机名
    "process_id": 12345,               # 进程ID
    "thread_id": "thread-001",         # 线程ID
    "correlation_id": "corr-001"       # 关联ID
}
```

### 手动上下文

用户可以添加的自定义上下文：

```python
logger.set_context(
    user_id="user-123",
    patent_id="CN123456789A",
    task_id="task-001"
)
```

### 上下文传播

上下文在调用链中自动传播：

```python
# Service A
logger.set_context(request_id="req-001")
logger.info("处理请求")

# Service B（通过RPC调用）
# 自动继承 request_id
logger.info("执行子任务")
```

---

## 🚀 性能优化

### 1. 异步日志

使用队列和后台线程异步写入日志：

```python
class AsyncLogHandler:
    """异步日志处理器"""
    
    def __init__(self, handler: logging.Handler):
        self.handler = handler
        self.queue = queue.Queue(maxsize=1000)
        self.thread = threading.Thread(target=self._process)
        self.thread.start()
    
    def emit(self, record: logging.LogRecord):
        """异步发送日志"""
        try:
            self.queue.put_nowait(record)
        except queue.Full:
            # 队列满时丢弃
            pass
    
    def _process(self):
        """后台处理日志"""
        while True:
            record = self.queue.get()
            self.handler.emit(record)
```

### 2. 批量写入

批量写入远程收集器：

```python
class BatchRemoteHandler:
    """批量远程处理器"""
    
    def __init__(self, url: str, batch_size: int = 100):
        self.url = url
        self.batch_size = batch_size
        self.buffer = []
    
    def emit(self, record: logging.LogRecord):
        """添加到缓冲区"""
        self.buffer.append(record)
        
        if len(self.buffer) >= self.batch_size:
            self.flush()
    
    def flush(self):
        """批量发送"""
        if self.buffer:
            requests.post(self.url, json=self.buffer)
            self.buffer.clear()
```

### 3. 日志级别过滤

在日志记录前过滤低级别日志：

```python
def should_log(self, level: LogLevel) -> bool:
    """判断是否应该记录日志"""
    return level.value >= self.level.value
```

---

## 📊 日志查询设计

### 1. 本地查询

通过命令行查询本地日志文件：

```bash
# 查询所有ERROR级别日志
grep '"level": "ERROR"' logs/xiaona.log

# 查询特定请求的日志
grep '"request_id": "req-001"' logs/xiaona.log

# 查询时间范围的日志
awk '/"timestamp": "2026-04-22T10:00:00/,/"timestamp": "2026-04-22T11:00:00/' logs/xiaona.log
```

### 2. 远程查询

通过日志收集系统查询：

```python
from unified_logging.client import LogQueryClient

client = LogQueryClient(endpoint="http://log-collector:5050")

# 查询ERROR级别日志
logs = client.query(
    service="xiaona",
    level="ERROR",
    start_time="2026-04-22T10:00:00Z",
    end_time="2026-04-22T11:00:00Z"
)

# 查询特定请求的日志
logs = client.query_by_context(
    service="xiaona",
    context_key="request_id",
    context_value="req-001"
)
```

---

## 🔒 日志安全设计

### 1. 敏感信息过滤

自动过滤敏感信息：

```python
class SensitiveDataFilter:
    """敏感数据过滤器"""
    
    SENSITIVE_PATTERNS = [
        r'password["\']?\s*[:=]\s*["\']?[^"\']+',
        r'token["\']?\s*[:=]\s*["\']?[^"\']+',
        r'api_key["\']?\s*[:=]\s*["\']?[^"\']+',
        r'secret["\']?\s*[:=]\s*["\']?[^"\']+',
    ]
    
    def filter(self, message: str) -> str:
        """过滤敏感信息"""
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, '***REDACTED***', message)
        return message
```

### 2. 访问控制

日志访问需要权限控制：

```python
class LogAccessControl:
    """日志访问控制"""
    
    def can_access(self, user: str, service: str, level: str) -> bool:
        """检查是否有权限访问日志"""
        # 开发人员可以访问所有日志
        if has_role(user, "developer"):
            return True
        
        # 运维人员可以访问WARNING及以上
        if has_role(user, "ops") and level in ["WARNING", "ERROR", "CRITICAL"]:
            return True
        
        return False
```

---

## 📁 文件结构

```
core/logging/
├── __init__.py                 # 模块入口
├── unified_logger.py           # 统一日志记录器
├── formatters.py               # 格式化器
│   ├── json_formatter.py      # JSON格式化
│   └── text_formatter.py      # 文本格式化
├── handlers.py                 # 处理器
│   ├── console_handler.py     # 控制台处理器
│   ├── file_handler.py        # 文件处理器
│   └── remote_handler.py      # 远程处理器
├── context.py                  # 上下文管理
├── filters.py                  # 过滤器
└── client.py                   # 日志查询客户端

config/base/
└── logging.yml                 # 基础日志配置

config/environments/
├── development/
│   └── logging.yml             # 开发环境配置
├── test/
│   └── logging.yml             # 测试环境配置
└── production/
    └── logging.yml             # 生产环境配置
```

---

## ✅ 实施计划

### Phase 1: 核心实现 (Day 1-2)
- [ ] 实现UnifiedLogger
- [ ] 实现JSONFormatter
- [ ] 实现基础Handlers
- [ ] 实现Context管理

### Phase 2: 高级功能 (Day 3-4)
- [ ] 实现异步日志
- [ ] 实现批量写入
- [ ] 实现敏感信息过滤
- [ ] 实现远程收集

### Phase 3: 集成和测试 (Day 5-6)
- [ ] 集成到现有服务
- [ ] 性能测试
- [ ] 功能测试
- [ ] 文档编写

---

## 📈 成功标准

### 功能完整性
- [ ] 统一日志格式 ✅
- [ ] 结构化日志 ✅
- [ ] 上下文自动收集 ✅
- [ ] 多种输出方式 ✅

### 性能要求
- [ ] 日志写入不阻塞主流程
- [ ] 吞吐量 > 1000 logs/s
- [ ] 内存占用 < 10MB

### 可用性要求
- [ ] 配置简单
- [ ] API易用
- [ ] 文档完整

---

**日志系统架构设计完成！**

**设计时间**: 2026-04-22
**设计人**: Claude Code (OMC模式)
**下一步**: 实施日志系统
