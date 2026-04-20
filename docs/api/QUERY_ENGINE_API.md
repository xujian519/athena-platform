# Query Engine API 参考文档

**版本**: 1.0.0
**更新日期**: 2026-04-20
**适用对象**: 开发者

---

## 目录

1. [快速开始](#快速开始)
2. [核心API](#核心api)
3. [数据源适配器](#数据源适配器)
4. [缓存策略](#缓存策略)
5. [跨数据源查询](#跨数据源查询)
6. [性能优化](#性能优化)
7. [故障排查](#故障排查)

---

## 快速开始

### 安装依赖

```bash
# PostgreSQL
pip install asyncpg

# Redis
pip install redis

# Qdrant
pip install qdrant-client

# Neo4j
pip install neo4j
```

### 基本使用

```python
from core.query_engine import create_query_engine
from core.query_engine.types import DataSourceType

# 创建查询引擎
engine = await create_query_engine(
    postgres_config={
        "host": "localhost",
        "port": 5432,
        "database": "athena",
        "user": "athena",
        "password": "password",
    },
    redis_config={
        "host": "localhost",
        "port": 6379,
    },
    enable_cache=True,
)

# 执行查询
result = await engine.execute(
    query="SELECT * FROM users WHERE id = $1",
    data_source=DataSourceType.POSTGRESQL,
    parameters={"id": 123},
)

print(result.data)  # 查询结果
print(result.stats.execution_time)  # 执行时间

# 关闭连接
await engine.disconnect_all()
```

---

## 核心API

### QueryEngine

查询引擎核心类，提供统一的查询接口。

#### 初始化

```python
from core.query_engine import QueryEngine

engine = QueryEngine(
    cache=None,  # 可选的缓存策略
    enable_cache=True,  # 是否启用缓存
)
```

#### 方法

##### register_adapter()

注册数据源适配器。

```python
from core.query_engine.adapters import PostgreSQLAdapter

adapter = PostgreSQLAdapter(config={
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "user": "user",
    "password": "pass",
})

engine.register_adapter(
    data_source=DataSourceType.POSTGRESQL,
    adapter=adapter,
)
```

##### execute()

执行单个查询。

```python
result = await engine.execute(
    query="SELECT * FROM users WHERE active = true",
    data_source=DataSourceType.POSTGRESQL,
    parameters=None,  # 查询参数
    use_cache=True,  # 是否使用缓存
    cache_ttl=3600,  # 缓存过期时间（秒）
)
```

##### execute_cross_source()

执行跨数据源查询。

```python
result = await engine.execute_cross_source(
    queries={
        DataSourceType.POSTGRESQL: "SELECT * FROM users",
        DataSourceType.REDIS: "GET user_cache:all",
    },
    join_strategy="sequential",  # sequential, parallel, merge
    join_key="user_id",  # merge策略必需
)
```

##### explain()

解释查询计划。

```python
plan = engine.explain(
    query="SELECT * FROM users JOIN orders ON users.id = orders.user_id",
    data_source=DataSourceType.POSTGRESQL,
)

print(plan.steps)  # 执行步骤
print(plan.estimated_cost)  # 预估成本
```

##### health_check()

健康检查。

```python
health = await engine.health_check()
# {
#     "postgresql": {"status": "healthy", ...},
#     "redis": {"status": "healthy", ...},
# }
```

### QueryResult

查询结果类。

#### 属性

| 属性 | 类型 | 说明 |
|-----|------|------|
| `data` | `list[dict]` | 结果数据 |
| `status` | `QueryStatus` | 查询状态 |
| `stats` | `QueryStats` | 统计信息 |
| `error` | `str \| None` | 错误信息 |
| `metadata` | `dict` | 元数据 |

#### 方法

##### to_dict()

转换为字典。

```python
result_dict = result.to_dict()
```

##### is_success

是否成功（属性）。

```python
if result.is_success:
    print("查询成功")
```

##### row_count

结果行数（属性）。

```python
print(f"返回 {result.row_count} 行")
```

### QueryStats

查询统计信息。

#### 属性

| 属性 | 类型 | 说明 |
|-----|------|------|
| `execution_time` | `float` | 执行时间（秒） |
| `rows_affected` | `int` | 影响行数 |
| `rows_returned` | `int` | 返回行数 |
| `cache_hit` | `bool` | 缓存命中 |
| `data_source` | `DataSourceType` | 数据源类型 |
| `query_complexity` | `int` | 查询复杂度 |
| `memory_used` | `int` | 内存使用（字节） |
| `timestamp` | `datetime` | 时间戳 |

---

## 数据源适配器

### PostgreSQL适配器

支持标准SQL查询、参数化查询、批量操作。

```python
from core.query_engine.adapters import PostgreSQLAdapter

adapter = PostgreSQLAdapter({
    "host": "localhost",
    "port": 5432,
    "database": "athena",
    "user": "athena",
    "password": "password",
    "pool_size": 20,  # 连接池大小
})

await adapter.connect()

# 执行查询
result = await adapter.execute(
    query="SELECT * FROM patents WHERE id = $1",
    parameters={"id": "CN123456789A"},
)

# 批量执行
results = await adapter.execute_batch(
    queries=[
        "SELECT * FROM patents WHERE id = $1",
        "SELECT * FROM patents WHERE id = $2",
    ],
    parameters=[
        {"id": "CN123456789A"},
        {"id": "CN987654321A"},
    ],
)

# 事务执行
results = await adapter.execute_transaction(
    queries=[
        "INSERT INTO logs (message) VALUES ($1)",
        "UPDATE status SET last_update = NOW()",
    ],
    parameters=[
        {"message": "操作完成"},
        None,
    ],
)
```

### Redis适配器

支持String、Hash、List、Set、ZSet操作。

```python
from core.query_engine.adapters import RedisAdapter

adapter = RedisAdapter({
    "host": "localhost",
    "port": 6379,
    "password": None,
    "db": 0,
})

await adapter.connect()

# String操作
result = await adapter.execute("GET", {"key": "mykey"})
result = await adapter.execute("SET", {"key": "mykey", "value": "myvalue", "ex": 3600})

# Hash操作
result = await adapter.execute("HGET", {"name": "user:123", "key": "name"})
result = await adapter.execute("HSET", {"name": "user:123", "key": "name", "value": "Alice"})
result = await adapter.execute("HGETALL", {"name": "user:123"})

# List操作
result = await adapter.execute("LPUSH", {"name": "queue", "values": ["task1", "task2"]})
result = await adapter.execute("LRANGE", {"name": "queue", "start": 0, "end": -1})

# Set操作
result = await adapter.execute("SADD", {"name": "tags", "members": ["ai", "patent"]})
result = await adapter.execute("SMEMBERS", {"name": "tags"})

# Sorted Set操作
result = await adapter.execute("ZADD", {"name": "rank", "member": "doc1", "score": 100})
result = await adapter.execute("ZRANGE", {"name": "rank", "start": 0, "end": -1})
```

### Qdrant适配器

支持向量搜索、推荐、滚动查询。

```python
from core.query_engine.adapters import QdrantAdapter

adapter = QdrantAdapter({
    "host": "localhost",
    "port": 6333,
    "api_key": None,
})

await adapter.connect()

# 向量搜索
result = await adapter.execute("search", {
    "collection_name": "patents",
    "vector": [0.1, 0.2, ...],  # 768维向量
    "limit": 10,
    "score_threshold": 0.7,
    "with_payload": True,
})

# 推荐查询
result = await adapter.execute("recommend", {
    "collection_name": "patents",
    "positive": ["doc1", "doc2"],
    "negative": ["doc3"],
    "limit": 10,
})

# 滚动查询
result = await adapter.execute("scroll", {
    "collection_name": "patents",
    "filter": {"must": [{"key": "category", "match": {"value": "AI"}}]},
    "limit": 100,
})

# 创建集合
result = await adapter.execute("create_collection", {
    "collection_name": "new_collection",
    "vector_size": 768,
})
```

### Neo4j适配器

支持Cypher查询、节点关系操作。

```python
from core.query_engine.adapters import Neo4jAdapter

adapter = Neo4jAdapter({
    "uri": "bolt://localhost:7687",
    "user": "neo4j",
    "password": "password",
    "database": "neo4j",
})

await adapter.connect()

# 查询节点
result = await adapter.execute(
    "MATCH (p:Patent {id: $id}) RETURN p",
    parameters={"id": "CN123456789A"},
)

# 查询关系
result = await adapter.execute(
    "MATCH (p1:Patent)-[r:CITES]->(p2:Patent) RETURN p1, r, p2",
)

# 创建节点和关系
result = await adapter.execute(
    "CREATE (p:Patent {id: $id, title: $title})",
    parameters={"id": "CN123456789A", "title": "AI专利"},
)

# 事务执行
results = await adapter.execute_transaction(
    queries=[
        "CREATE (p:Patent {id: $id})",
        "MATCH (p:Patent {id: $id}) SET p.title = $title",
    ],
    parameters=[
        {"id": "CN123456789A"},
        {"id": "CN123456789A", "title": "新标题"},
    ],
)
```

---

## 缓存策略

### MemoryCache

内存缓存，适合开发和小规模应用。

```python
from core.query_engine.cache import MemoryCache

cache = MemoryCache(
    max_size=1000,  # 最大缓存条目
    default_ttl=3600,  # 默认过期时间（秒）
)

await cache.set("key", result, ttl=7200)
cached_result = await cache.get("key")
```

### MultiLevelCache

多级缓存（L1内存 + L2 Redis）。

```python
from core.query_engine.cache import MemoryCache, RedisCache, MultiLevelCache

import redis.asyncio as aioredis

redis_client = await aioredis.Redis(host="localhost", port=6379)

cache = MultiLevelCache(
    l1_cache=MemoryCache(),
    l2_cache=RedisCache(redis_client),
)

# 自动从L1读取，未命中时从L2读取并回填L1
result = await cache.get("key")
```

---

## 跨数据源查询

### 顺序执行（Sequential）

按顺序执行各数据源查询。

```python
result = await engine.execute_cross_source(
    queries={
        DataSourceType.POSTGRESQL: "SELECT * FROM users",
        DataSourceType.REDIS: "GET user_cache:all",
    },
    join_strategy="sequential",
)
```

### 并行执行（Parallel）

并行执行各数据源查询。

```python
result = await engine.execute_cross_source(
    queries={
        DataSourceType.POSTGRESQL: "SELECT * FROM patents WHERE id = $1",
        DataSourceType.QDRANT: "search",  # 向量搜索相似专利
    },
    join_strategy="parallel",
)
```

### 合并执行（Merge）

按指定键合并结果。

```python
result = await engine.execute_cross_source(
    queries={
        DataSourceType.POSTGRESQL: "SELECT * FROM patent_info",
        DataSourceType.REDIS: "HGETALL patent_metadata",
    },
    join_strategy="merge",
    join_key="patent_id",
)
```

---

## 性能优化

### 查询优化

```python
from core.query_engine import QueryOptimizer

# SQL优化
optimized = QueryOptimizer.optimize_sql(
    "select  *  from  users  where  id  =  1"
)
# => "SELECT * FROM users WHERE id = 1"

# 复杂度估算
complexity = QueryOptimizer.estimate_complexity(
    query="SELECT * FROM users JOIN orders ON ...",
    data_source=DataSourceType.POSTGRESQL,
)
```

### 连接池配置

```python
# PostgreSQL连接池
adapter = PostgreSQLAdapter({
    "pool_size": 50,  # 根据并发量调整
})
```

### 缓存策略

1. **热点数据**: 使用内存缓存
2. **持久化需求**: 使用多级缓存
3. **TTL设置**: 根据数据更新频率调整

---

## 故障排查

### 常见问题

#### 1. 连接失败

```
错误: 数据源连接失败: postgresql
```

**解决方案**:
- 检查数据库服务是否运行
- 验证连接配置（主机、端口、用户名、密码）
- 检查网络连接

#### 2. 查询超时

```
错误: 查询执行超时
```

**解决方案**:
- 增加timeout参数
- 优化查询语句
- 添加索引

#### 3. 缓存未命中

```
缓存命中率过低
```

**解决方案**:
- 检查缓存TTL设置
- 验证缓存键生成逻辑
- 调整缓存大小

### 调试模式

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("core.query_engine")
logger.setLevel(logging.DEBUG)
```

---

**作者**: Athena平台团队
**最后更新**: 2026-04-20
**版本**: 1.0.0
