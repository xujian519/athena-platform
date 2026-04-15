# Athena 中间件与技能系统实现指南

## 概述

本次更新为 Athena 工作平台引入了两个重要的系统：
1. **中间件系统** - 基于 DeerFlow 设计的请求处理管道
2. **技能系统** - 模块化的能力扩展系统

---

## 一、中间件系统

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Application                   │
│  ┌───────────────────────────────────────────────────┐  │
│  │            Middleware Pipeline                     │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐         │  │
│  │   │   CORS   │ │  Logging │ │   Auth   │  ...    │  │
│  │   └──────────┘ └──────────┘ └──────────┘         │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                   Route Handler
```

### 核心组件

#### 1. 中间件基类 (`services/api-gateway/src/middleware/base.py`)

```python
class Middleware(ABC):
    @abstractmethod
    async def process(
        self,
        ctx: MiddlewareContext,
        call_next: Callable
    ) -> Response:
        pass
```

#### 2. 内置中间件

| 中间件 | 功能 | 优先级 |
|--------|------|--------|
| `CORSMiddleware` | 跨域请求处理 | 1 |
| `LoggingMiddleware` | 请求日志记录 | 2 |
| `AuthMiddleware` | 身份验证 | 3 |
| `ValidationMiddleware` | 请求验证（SQL注入、XSS防护） | 4 |
| `CacheMiddleware` | 响应缓存 | 5 |
| `MonitoringMiddleware` | 性能监控 | 6 |
| `RateLimitMiddleware` | 速率限制 | 7 |

### 使用方法

#### 基础使用

```python
from fastapi import FastAPI
from services.api_gateway.src.middleware import enable_middleware

app = FastAPI()

# 启用中间件系统
pipeline = enable_middleware(
    app,
    jwt_secret="your-secret-key",
    config={
        "rate_limit_requests": 100,
        "rate_limit_window": 60,
        "cors_origins": ["https://athena.example.com"],
    }
)

@app.get("/api/test")
async def test_endpoint():
    return {"message": "Hello from Athena!"}
```

#### 自定义中间件

```python
from services.api_gateway.src.middleware.base import Middleware, MiddlewareContext

class CustomMiddleware(Middleware):
    async def process(self, ctx: MiddlewareContext, call_next):
        # 前置处理
        ctx.set("custom_data", "value")

        # 调用下一个中间件
        response = await call_next(ctx)

        # 后置处理
        response.headers["X-Custom"] = "Athena"
        return response

# 添加到管道
pipeline.add(CustomMiddleware(), order=5)
```

### 中间件配置

```python
# 详细配置示例
pipeline = setup_middleware(
    app,
    jwt_secret=os.getenv("JWT_SECRET"),

    # 启用开关
    enable_auth=True,
    enable_logging=True,
    enable_rate_limit=True,
    enable_cors=True,

    # CORS 配置
    cors_origins=["https://athena.example.com"],
    cors_credentials=True,

    # 日志配置
    log_level=logging.INFO,
    log_body=False,
    slow_threshold=5.0,

    # 限流配置
    rate_limit_strategy="sliding_window",
    rate_limit_requests=100,
    rate_limit_window=60,
    redis_url="redis://localhost:6379/0",

    # 认证配置
    jwt_algorithm="HS256",
    jwt_expiry=86400,
    api_keys=["key1", "key2"],
)
```

---

## 二、技能系统

### 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                   Skill System                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Skill Manager│  │Skill Registry│  │Skill Executor│ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│         └─────────────────┴─────────────────┘          │
│                           │                            │
│                           ▼                            │
│  ┌───────────────────────────────────────────────────┐ │
│  │                    Skills                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │  public  │ │  custom  │ │ patent-analysis  │  │ │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 技能目录结构

```
skills/
├── SKILL_TEMPLATE.md           # 技能模板
├── public/                     # 公共技能
│   └── hello-world/
│       ├── SKILL.md            # 技能元数据
│       └── hello_world.py      # 技能实现
├── custom/                     # 自定义技能
│   └── your-skill/
│       ├── SKILL.md
│       └── your_skill.py
└── patent-analysis/            # 专利分析技能（示例）
    ├── SKILL.md
    └── analyze.py
```

### 技能元数据格式

```yaml
---
name: "skill_name"           # 唯一标识符
display_name: "技能显示名称"
description: "技能的详细描述"

version: "1.0.0"
author: "作者名"
license: "MIT"

category: "patent_analysis"  # 分类

tags:
  - "tag1"
  - "tag2"

dependencies: []             # 依赖的其他技能

parameters:
  required:
    - "param1"
  optional:
    - "param2"
  types:
    param1: "str"
    param2: "int"
  defaults:
    param2: 10

examples:
  - description: "示例描述"
    input:
      param1: "value1"
    output:
      result: "expected output"

enabled: true
---
```

### 创建新技能

#### 方法1: 使用模板

```bash
# 复制模板
cp skills/SKILL_TEMPLATE.md skills/custom/my-skill/SKILL.md

# 编辑 SKILL.md 填写元数据
# 创建实现文件 my-skill.py
```

#### 方法2: 使用装饰器

```python
from core.skills import skill_function, SkillCategory

@skill_function(
    name="my_skill",
    display_name="我的技能",
    description="这是一个示例技能",
    category=SkillCategory.CUSTOM,
    parameters={
        "required": ["text"],
        "types": {"text": str}
    }
)
async def my_skill(text: str) -> dict:
    """技能实现"""
    return {"result": f"处理结果: {text}"}
```

### 在智能体中使用技能

```python
from core.agents.base import BaseAgent
from core.agents.skill_mixin import SkillMixin

class MyAgent(SkillMixin, BaseAgent):
    """支持技能的智能体"""

    async def initialize(self):
        await super().initialize()
        await self.setup_skills()

    async def process_request(self, request: str) -> str:
        # 检查是否有可用技能可以处理
        skills = self.list_available_skills()

        # 使用技能
        result = await self.use_skill(
            "hello_world",
            name="User"
        )

        if result.success:
            return result.data["message"]
        else:
            return "技能执行失败"
```

### 技能执行模式

#### 1. 单个技能执行

```python
result = await executor.execute("skill_name", param1="value1")
```

#### 2. 并行执行

```python
from core.skills import SkillComposer

composer = SkillComposer(executor)
results = await composer.parallel(
    skill_names=["skill1", "skill2", "skill3"],
    parameters_list=[
        {"param": "value1"},
        {"param": "value2"},
        {"param": "value3"}
    ]
)
```

#### 3. 链式执行

```python
results = await executor.execute_chain([
    {"skill_name": "skill1", "parameters": {"input": "data"}},
    {"skill_name": "skill2", "parameters": {"input": "previous_result"}},
    {"skill_name": "skill3", "parameters": {"input": "previous_result"}},
])
```

#### 4. 循环执行

```python
composer = SkillComposer(executor)
results = await composer.loop(
    skill_name="process_item",
    items=[1, 2, 3, 4, 5],
    parameter_name="item"
)
```

---

## 三、API 集成示例

### Gateway + Skills 完整示例

```python
from fastapi import FastAPI, HTTPException, Depends
from services.api_gateway.src.middleware import setup_middleware
from core.skills import SkillManager, SkillExecutor
from pydantic import BaseModel

app = FastAPI(title="Athena Gateway")

# 设置中间件
pipeline = setup_middleware(
    app,
    jwt_secret=os.getenv("JWT_SECRET"),
    enable_rate_limit=True,
)

# 设置技能系统
skill_manager = SkillManager()
skill_executor = SkillExecutor(registry=skill_manager.registry)

@app.on_event("startup")
async def startup():
    """启动时加载技能"""
    await skill_manager.load_all()

# 技能 API
class SkillExecuteRequest(BaseModel):
    skill_name: str
    parameters: dict = {}

@app.post("/api/v1/skills/execute")
async def execute_skill(request: SkillExecuteRequest):
    """执行技能"""
    try:
        result = await skill_executor.execute(
            request.skill_name,
            **request.parameters
        )
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/skills")
async def list_skills():
    """列出所有技能"""
    return {
        "skills": [
            skill_executor.registry.get_metadata(name).to_dict()
            for name in skill_executor.registry.list_enabled()
        ]
    }

@app.get("/api/v1/skills/{skill_name}")
async def get_skill_info(skill_name: str):
    """获取技能详情"""
    metadata = skill_executor.registry.get_metadata(skill_name)
    if not metadata:
        raise HTTPException(status_code=404, detail="Skill not found")
    return metadata.to_dict()
```

---

## 四、迁移现有功能为技能

### 示例：将专利检索转为技能

#### 1. 创建技能元数据 (`skills/patent-retrieval/SKILL.md`)

```yaml
---
name: "patent_retrieval"
display_name: "专利检索"
description: "根据关键词检索相关专利信息"

category: "patent_analysis"

tags:
  - "patent"
  - "search"
  - "retrieval"

parameters:
  required:
    - "query"
  optional:
    - "limit"
    - "filters"
  types:
    query: "str"
    limit: "int"
    filters: "dict"
  defaults:
    limit: 10
---
```

#### 2. 创建技能实现 (`skills/patent-retrieval/patent_retrieval.py`)

```python
from core.skills import Skill, SkillResult, SkillMetadata

class Skill(Skill):
    """专利检索技能"""

    async def execute(self, **kwargs) -> SkillResult:
        query = kwargs.get("query")
        limit = kwargs.get("limit", 10)
        filters = kwargs.get("filters", {})

        # 调用现有的专利检索逻辑
        from patent_hybrid_retrieval import PatentHybridRetrieval
        retriever = PatentHybridRetrieval()

        results = await retriever.search(
            query=query,
            limit=limit,
            **filters
        )

        return SkillResult(
            success=True,
            data={
                "query": query,
                "count": len(results),
                "patents": results
            }
        )
```

---

## 五、文件清单

### 中间件系统

| 文件 | 描述 |
|------|------|
| `services/api-gateway/src/middleware/__init__.py` | 中间件模块导出 |
| `services/api-gateway/src/middleware/base.py` | 中间件基类和管道 |
| `services/api-gateway/src/middleware/auth.py` | 认证中间件 |
| `services/api-gateway/src/middleware/logging.py` | 日志中间件 |
| `services/api-gateway/src/middleware/rate_limit.py` | 限流中间件 |
| `services/api-gateway/src/middleware/cors.py` | CORS 中间件 |
| `services/api-gateway/src/middleware/cache.py` | **缓存中间件**（新增） |
| `services/api-gateway/src/middleware/validation.py` | **验证中间件**（新增） |
| `services/api-gateway/src/middleware/monitoring.py` | **监控中间件**（新增） |
| `services/api-gateway/src/middleware/fastapi.py` | FastAPI 集成 |

### 技能系统

| 文件 | 描述 |
|------|------|
| `core/skills/__init__.py` | 技能模块导出 |
| `core/skills/base.py` | 技能基类和数据模型 |
| `core/skills/registry.py` | 技能注册中心 |
| `core/skills/manager.py` | 技能管理器 |
| `core/skills/executor.py` | 技能执行器 |
| `core/agents/skill_mixin.py` | 智能体技能集成 |
| `skills/SKILL_TEMPLATE.md` | 技能模板 |
| `skills/public/hello-world/SKILL.md` | 示例技能元数据 |
| `skills/public/hello-world/hello_world.py` | 示例技能实现 |

---

## 六、扩展中间件详解

### 缓存中间件 (CacheMiddleware)

**功能**：
- 基于 Redis 的 HTTP 响应缓存
- 智能缓存键生成（基于路径、参数、头部）
- 支持 TTL 配置和缓存规则
- 缓存命中率统计

**使用示例**：
```python
from services.api_gateway.src.middleware import CacheMiddleware

cache = CacheMiddleware(
    redis_url="redis://localhost:6379/1",
    default_ttl=60,
    cache_rules=[
        {
            "path_pattern": "^/api/v1/patents",
            "ttl": 300,
            "methods": ["GET"],
        }
    ]
)
pipeline.add(cache, order=5)
```

### 验证中间件 (ValidationMiddleware)

**功能**：
- SQL 注入检测（4种特征模式）
- XSS 攻击检测（9种特征模式）
- 路径遍历检测（6种特征模式）
- Pydantic 模型验证
- 请求体大小限制

**使用示例**：
```python
from services.api_gateway.src.middleware import ValidationMiddleware

validation = ValidationMiddleware(
    max_body_size=10 * 1024 * 1024,
    enable_sql_injection_check=True,
    enable_xss_check=True,
)

# 添加验证模型
from middleware.validation import PatentSearchRequest
validation.add_validation_model(
    "/api/v1/patents/search",
    "POST",
    PatentSearchRequest
)
pipeline.add(validation, order=4)
```

### 监控中间件 (MonitoringMiddleware)

**功能**：
- 请求响应时间统计（P50, P95, P99）
- 错误率监控
- 慢请求检测
- 并发请求数统计
- Prometheus/InfluxDB/StatsD 格式导出

**使用示例**：
```python
from services.api_gateway.src.middleware import MonitoringMiddleware

monitoring = MonitoringMiddleware(
    slow_threshold=3.0,
    metrics_window_size=1000,
)
pipeline.add(monitoring, order=6)

# 获取指标
metrics = monitoring.get_metrics()

# 导出 Prometheus 格式
prometheus_metrics = monitoring.get_prometheus_metrics()

# 使用指标导出器
from services.api_gateway.src.middleware import MetricsExporter
exporter = MetricsExporter(monitoring)
influx_metrics = exporter.export_influx()
```

## 七、下一步建议

### 短期（1-2周）

1. **✅ 完善中间件** - 已完成
   - ✅ 添加缓存中间件
   - ✅ 添加请求验证中间件
   - ✅ 添加性能监控中间件

2. **扩展技能库**
   - 将现有专利分析功能迁移为技能
   - 创建文档生成技能
   - 创建数据可视化技能

### 中期（1个月）

3. **沙盒系统**
   - 实现安全的代码执行环境
   - 支持用户自定义脚本

4. **技能市场**
   - 支持技能分享
   - 版本管理

---

## 八、参考

- [DeerFlow 项目](https://github.com/yamadajoe/deer-flow) - 中间件和技能系统设计参考
- [FastAPI 中间件文档](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Athena 项目文档](../README.md)
