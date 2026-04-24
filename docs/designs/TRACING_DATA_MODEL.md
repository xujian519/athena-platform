# 分布式追踪数据模型设计

> **文档编号**: BEAD-201-DM
> **创建日期**: 2026-04-24
> **关联文档**: DISTRIBUTED_TRACING_ARCHITECTURE.md

---

## 1. 概述

### 1.1 数据模型目标

- **统一性**: 跨语言（Python/Go）的一致数据格式
- **可扩展性**: 支持自定义属性和事件
- **标准化**: 遵循OpenTelemetry语义约定
- **高效性**: 最小化存储和传输开销

### 1.2 核心概念关系

```
┌─────────────────────────────────────────────────────────────────┐
│                       Trace - Span 关系                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Trace (全局追踪)                                                 │
│  ├─ TraceID: "4bf92f3577b34da6a3ce929d0e0e4736"                  │
│  ├─ Root Span (用户请求)                                        │
│  │   ├─ Child Span 1 (Agent调用)                               │
│  │   │   ├─ Grandchild Span 1.1 (LLM请求)                      │
│  │   │   └─ Grandchild Span 1.2 (数据库查询)                   │
│  │   └─ Child Span 2 (缓存操作)                                │
│  └─ Links (关联其他Trace)                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Span核心数据模型

### 2.1 Span基础结构

```json
{
  "traceId": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spanId": "00f067aa0ba902b7",
  "parentSpanId": "00f067aa0ba90200",
  "traceState": "tenant=athena,user=xujian",
  "name": "xiaona.analyze_patent",
  "kind": "INTERNAL",
  "startTime": "2026-04-24T10:00:00.123456Z",
  "endTime": "2026-04-24T10:00:01.234567Z",
  "duration": 1111111,
  "status": {
    "code": "OK",
    "description": ""
  },
  "attributes": {
    "agent.name": "xiaona",
    "agent.task_type": "patent_analysis",
    "patent.id": "CN123456789A",
    "user.id": "u123456"
  },
  "events": [
    {
      "time": "2026-04-24T10:00:00.500000Z",
      "name": "llm.request.start",
      "attributes": {
        "llm.provider": "claude",
        "llm.model": "claude-3-opus-20240229"
      }
    }
  ],
  "links": [
    {
      "traceId": "a1b2c3d4e5f6g7h8",
      "spanId": "0011223344556677",
      "attributes": {
        "link.type": "related_analysis"
      }
    }
  ],
  "resource": {
    "service.name": "athena-xiaona",
    "service.namespace": "athena",
    "service.version": "2.0.0",
    "deployment.environment": "production",
    "host.name": "athena-agent-01",
    "process.pid": 12345,
    "process.executable.path": "/usr/bin/python3"
  }
}
```

### 2.2 SpanKind枚举

| SpanKind | 描述 | 使用场景 | 示例 |
|----------|------|---------|------|
| INTERNAL | 内部操作 | 方法调用、本地处理 | agent.process_task |
| SERVER | 服务端 | 入站请求处理 | gateway.handle_request |
| CLIENT | 客户端 | 出站请求 | llm.call_claude_api |
| PRODUCER | 生产者 | 消息发送 | kafka.publish_event |
| CONSUMER | 消费者 | 消息处理 | kafka.consume_event |

---

## 3. Trace标识符

### 3.1 TraceID格式

```
TraceID: 16字节 (128位) 十六进制编码
格式: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX (32个字符)

示例: 4bf92f3577b34da6a3ce929d0e0e4736

生成策略:
- Python: uuid.uuid4().hex (使用UUID v4)
- Go: oteltrace.NewTraceID()
- W3C Trace Context: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

### 3.2 SpanID格式

```
SpanID: 8字节 (64位) 十六进制编码
格式: XXXXXXXXXXXXXXXX (16个字符)

示例: 00f067aa0ba902b7

生成策略:
- Python: random.getrandbits(64).to_bytes(8, 'big').hex()
- Go: oteltrace.NewSpanID()
```

### 3.3 TraceContext传播

```http
# HTTP请求头
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
tracestate: tenant=athena,user=xujian,session=abc123

# gRPC Metadata
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
```

**traceparent格式解析**:
```
version-trace_id-parent_id-flags
  ↓        ↓         ↓        ↓
  00    4bf92...  00f06...   01

version: 00 (当前版本)
trace_id: 16字节
parent_id: 8字节
flags: 01=sampled, 00=not sampled
```

---

## 4. 属性标准

### 4.1 通用属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `service.name` | string | 服务名称 | athena-xiaona |
| `service.version` | string | 服务版本 | 2.0.0 |
| `deployment.environment` | string | 部署环境 | production |
| `user.id` | string | 用户ID | u123456 |
| `session.id` | string | 会话ID | sess_abc123 |
| `thread.id` | int | 线程ID | 12345 |
| `thread.name` | string | 线程名称 | ThreadPoolExecutor-0 |

### 4.2 HTTP属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `http.method` | string | HTTP方法 | POST |
| `http.url` | string | 请求URL | https://api.athena.com/v1/analyze |
| `http.target` | string | 请求路径 | /v1/analyze |
| `http.status_code` | int | 响应状态码 | 200 |
| `http.scheme` | string | 协议 | https |
| `http.host` | string | 主机 | api.athena.com |
| `http.client_ip` | string | 客户端IP | 192.168.1.100 |
| `http.request.content_length` | int | 请求体长度 | 1024 |
| `http.response.content_length` | int | 响应体长度 | 2048 |

### 4.3 Database属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `db.system` | string | 数据库类型 | postgresql |
| `db.name` | string | 数据库名称 | athena |
| `db.user` | string | 数据库用户 | athena_user |
| `db.statement` | string | SQL语句 | SELECT * FROM patents WHERE id = ? |
| `db.operation` | string | 操作类型 | SELECT |
| `db.table` | string | 表名 | patents |
| `db.rows_affected` | int | 影响行数 | 1 |
| `db.connection_string` | string | 连接字符串 | postgresql://localhost:5432/athena |

### 4.4 LLM属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `llm.provider` | string | LLM提供商 | claude |
| `llm.model` | string | 模型名称 | claude-3-opus-20240229 |
| `llm.request.type` | string | 请求类型 | chat |
| `llm.prompt.length` | int | 提示词长度 | 1500 |
| `llm.response.length` | int | 响应长度 | 800 |
| `llm.tokens.input` | int | 输入token数 | 1000 |
| `llm.tokens.output` | int | 输出token数 | 500 |
| `llm.latency.ms` | int | 延迟毫秒 | 2500 |
| `llm.stream` | boolean | 是否流式 | false |

### 4.5 Agent属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `agent.name` | string | Agent名称 | xiaona |
| `agent.type` | string | Agent类型 | legal_expert |
| `agent.task.type` | string | 任务类型 | patent_analysis |
| `agent.task.id` | string | 任务ID | task_abc123 |
| `agent.session.id` | string | 会话ID | session_xyz |
| `agent.parent.agent` | string | 父Agent | xiaonuo |
| `agent coordination.mode` | string | 协作模式 | sequential |

### 4.6 专利领域属性

| 属性名 | 类型 | 描述 | 示例值 |
|-------|------|------|-------|
| `patent.id` | string | 专利号 | CN123456789A |
| `patent.country` | string | 国家代码 | CN |
| `patent.type` | string | 专利类型 | invention |
| `patent.analysis.type` | string | 分析类型 | novelty |
| `patent.search.query` | string | 检索查询 | 深度学习 图像识别 |
| `patent.search.results` | int | 检索结果数 | 25 |

---

## 5. 事件数据模型

### 5.1 事件结构

```json
{
  "time": "2026-04-24T10:00:00.500000Z",
  "name": "cache.miss",
  "attributes": {
    "cache.key": "patent:CN123456789A",
    "cache.type": "redis",
    "cache.ttl": 3600
  }
}
```

### 5.2 预定义事件

| 事件名 | 描述 | 触发时机 |
|-------|------|---------|
| `cache.hit` | 缓存命中 | Redis缓存命中 |
| `cache.miss` | 缓存未命中 | Redis缓存未命中 |
| `llm.request.start` | LLM请求开始 | 调用LLM API |
| `llm.request.complete` | LLM请求完成 | LLM返回响应 |
| `llm.request.error` | LLM请求错误 | LLM调用失败 |
| `db.query.start` | 数据库查询开始 | 执行SQL |
| `db.query.complete` | 数据库查询完成 | 返回结果 |
| `db.query.error` | 数据库查询错误 | SQL执行失败 |
| `agent.invoke.start` | Agent调用开始 | 启动Agent |
| `agent.invoke.complete` | Agent调用完成 | Agent返回结果 |

---

## 6. 状态数据模型

### 6.1 StatusCode枚举

| 代码 | 描述 | 使用场景 |
|-----|------|---------|
| OK | 成功 | 操作正常完成 |
| ERROR | 错误 | 操作失败，可重试 |
| UNSET | 未设置 | 状态未知 |

### 6.2 错误状态示例

```json
{
  "status": {
    "code": "ERROR",
    "description": "LLM API rate limit exceeded"
  },
  "events": [
    {
      "name": "exception",
      "time": "2026-04-24T10:00:01.000000Z",
      "attributes": {
        "exception.type": "RateLimitError",
        "exception.message": "Rate limit exceeded: 100 requests/min",
        "exception.stacktrace": "...",
        "exception.escaped": "true"
      }
    }
  ]
}
```

---

## 7. Resource数据模型

### 7.1 Resource结构

```json
{
  "service.name": "athena-xiaona",
  "service.namespace": "athena",
  "service.version": "2.0.0",
  "service.instance.id": "athena-xiaona-prod-01",
  "deployment.environment": "production",

  "host.name": "athena-agent-01",
  "host.id": "i-1234567890abcdef0",
  "host.type": "ec2",
  "host.arch": "amd64",
  "host.image.name": "ami-0123456789abcdef0",
  "host.image.version": "20260424",

  "process.pid": 12345,
  "process.executable.path": "/usr/bin/python3",
  "process.executable.name": "python3",
  "process.command_args": ["python3", "-m", "athena.xiaona"],
  "process.owner": "athena",
  "process.runtime.name": "CPython",
  "process.runtime.version": "3.11.5",
  "process.runtime.description": "Python 3.11.5",

  "telemetry.sdk.name": "opentelemetry",
  "telemetry.sdk.language": "python",
  "telemetry.sdk.version": "1.21.0"
}
```

---

## 8. 语义约定

### 8.1 Span命名约定

| 模式 | 示例 | 说明 |
|-----|------|------|
| `<service>.<operation>` | `xiaona.analyze_patent` | 服务.操作 |
| `<component>.<action>` | `database.query_patent` | 组件.动作 |
| `<protocol>.<method>` | `http.post` | 协议.方法 |

### 8.2 属性键命名约定

```
格式: <namespace>.<entity>.<attribute>

示例:
- http.method (协议.属性)
- db.name (组件.属性)
- llm.model (领域.属性)
- agent.name (领域.属性)
```

### 8.3 属性值约定

| 类型 | 格式 | 示例 |
|-----|------|------|
| string | UTF-8编码 | "athena-xiaona" |
| int | 64位有符号整数 | 12345 |
| double | IEEE 754双精度 | 3.14 |
| bool | true/false | true |
| array | 逗号分隔或JSON数组 | ["a", "b", "c"] |

---

## 9. Elasticsearch索引设计

### 9.1 Spans索引

```json
PUT jaeger-span-2026-04-24
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1,
    "index.lifecycle.name": "jaeger-spans-policy",
    "index.lifecycle.rollover_alias": "jaeger-span"
  },
  "mappings": {
    "properties": {
      "traceID": {
        "type": "keyword"
      },
      "spanID": {
        "type": "keyword"
      },
      "parentSpanID": {
        "type": "keyword"
      },
      "operationName": {
        "type": "keyword"
      },
      "startTime": {
        "type": "date"
      },
      "duration": {
        "type": "long"
      },
      "tags": {
        "type": "object",
        "dynamic": true
      },
      "process": {
        "properties": {
          "serviceName": {
            "type": "keyword"
          },
          "serviceID": {
            "type": "keyword"
          }
        }
      },
      "logs": {
        "type": "nested"
      }
    }
  }
}
```

### 9.2 索引生命周期策略

```json
PUT _ilm/policy/jaeger-spans-policy
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_age": "1d",
            "max_size": "50gb"
          }
        }
      },
      "delete": {
        "min_age": "7d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

---

## 10. 数据采样策略

### 10.1 采样决策模型

```python
class SamplingDecision:
    def __init__(self):
        self.rules = {
            # 错误始终采样
            "error": lambda span: span.status.code == "ERROR",

            # 慢请求始终采样
            "slow": lambda span: span.duration > 100_000_000,  # 100ms

            # LLM请求高比例采样
            "llm": lambda span: span.attributes.get("llm.provider") and random.random() < 0.5,

            # 默认低比例采样
            "default": lambda span: random.random() < 0.01,
        }

    def should_sample(self, span) -> bool:
        # 按优先级检查规则
        for rule_name, rule_func in self.rules.items():
            if rule_func(span):
                return True
        return False
```

### 10.2 采样标签

| 标签 | 值 | 描述 |
|-----|---|------|
| `sampling.probability` | 0.01 | 采样概率 |
| `sampling.decision` | sampled/not_sampled | 采样决策 |
| `sampling.reason` | error/slow/llm/default | 采样原因 |

---

## 11. 数据压缩优化

### 11.1 属性压缩

```python
# 属性值去重
COMMON_VALUES = {
    "http.method": ["GET", "POST", "PUT", "DELETE"],
    "db.system": ["postgresql", "redis", "qdrant"],
    "llm.provider": ["claude", "gpt-4", "deepseek"],
}

def compress_attributes(attributes: dict) -> dict:
    """压缩属性值"""
    compressed = {}
    for key, value in attributes.items():
        if key in COMMON_VALUES and value in COMMON_VALUES[key]:
            compressed[key] = COMMON_VALUES[key].index(value)
        else:
            compressed[key] = value
    return compressed
```

### 11.2 Span批量编码

```python
import msgpack

def encode_spans_batch(spans: list) -> bytes:
    """批量编码Spans"""
    return msgpack.packb({
        "spans": spans,
        "count": len(spans),
        "version": "1.0",
    })

def decode_spans_batch(data: bytes) -> list:
    """解码Spans批次"""
    return msgpack.unpackb(data)["spans"]
```

---

## 12. 数据完整性校验

### 12.1 Trace完整性检查

```python
def validate_trace_integrity(trace_id: str, spans: list) -> dict:
    """验证Trace完整性"""
    issues = []

    # 检查根Span
    root_spans = [s for s in spans if not s.get("parentSpanId")]
    if len(root_spans) != 1:
        issues.append(f"Expected 1 root span, found {len(root_spans)}")

    # 检查父子关系
    span_ids = {s["spanId"] for s in spans}
    for span in spans:
        if span.get("parentSpanId") and span["parentSpanId"] not in span_ids:
            issues.append(f"Orphan span: {span['spanId']} has missing parent {span['parentSpanId']}")

    # 检查时间顺序
    for span in spans:
        if span["startTime"] > span["endTime"]:
            issues.append(f"Invalid time: span {span['spanId']} ends before it starts")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }
```

---

## 附录A: 完整Schema示例

### A.1 典型Agent调用Trace

```json
{
  "traceID": "4bf92f3577b34da6a3ce929d0e0e4736",
  "spans": [
    {
      "traceID": "4bf92f3577b34da6a3ce929d0e0e4736",
      "spanID": "00f067aa0ba902b7",
      "operationName": "POST /api/v1/analyze",
      "kind": "SERVER",
      "startTime": 1713945600000000,
      "duration": 2500000000,
      "tags": {
        "http.method": "POST",
        "http.url": "/api/v1/analyze",
        "http.status_code": 200,
        "user.id": "u123456"
      },
      "process": {
        "serviceName": "athena-gateway",
        "serviceID": "gateway-01"
      }
    },
    {
      "traceID": "4bf92f3577b34da6a3ce929d0e0e4736",
      "spanID": "00f067aa0ba902b8",
      "parentSpanID": "00f067aa0ba902b7",
      "operationName": "xiaonuo.coordinate",
      "kind": "INTERNAL",
      "startTime": 1713945600100000,
      "duration": 2300000000,
      "tags": {
        "agent.name": "xiaonuo",
        "agent.task_type": "patent_analysis",
        "session.id": "sess_abc123"
      },
      "process": {
        "serviceName": "athena-xiaonuo",
        "serviceID": "xiaonuo-01"
      }
    },
    {
      "traceID": "4bf92f3577b34da6a3ce929d0e0e4736",
      "spanID": "00f067aa0ba902b9",
      "parentSpanID": "00f067aa0ba902b8",
      "operationName": "xiaona.analyze_novelty",
      "kind": "INTERNAL",
      "startTime": 1713945600200000,
      "duration": 1800000000,
      "tags": {
        "agent.name": "xiaona",
        "agent.sub_agent": "novelty_analyzer",
        "patent.id": "CN123456789A"
      },
      "process": {
        "serviceName": "athena-xiaona",
        "serviceID": "xiaona-01"
      },
      "logs": [
        {
          "timestamp": 1713945600300000,
          "fields": [
            {"key": "event", "value": "llm.request.start"},
            {"key": "llm.provider", "value": "claude"}
          ]
        },
        {
          "timestamp": 1713945601900000,
          "fields": [
            {"key": "event", "value": "llm.request.complete"},
            {"key": "llm.tokens.input", "value": "1500"},
            {"key": "llm.tokens.output", "value": "800"}
          ]
        }
      ]
    }
  ]
}
```

---

## 附录B: 术语表

| 术语 | 定义 |
|-----|------|
| Trace | 代表一个请求或事务在分布式系统中的完整执行路径 |
| Span | Trace中的基本工作单元，代表系统中的单个操作 |
| SpanID | 唯一标识Trace中的一个Span |
| TraceID | 唯一标识一个完整的Trace |
| ParentSpanID | 标识Span的父Span，用于构建调用树 |
| Context | 跨进程传播的追踪上下文信息 |
| Attribute | Span的键值对属性 |
| Event | Span内时间点发生的带时间戳注解 |
| Link | 关联其他Trace的引用 |
| Resource | 生成Span的实体描述 |
| Instrumentation | 将追踪代码添加到应用程序的过程 |
| Propagator | 跨进程传播上下文的组件 |
| Processor | 处理和导出Span的组件 |
| Sampler | 决定是否记录Trace的组件 |
