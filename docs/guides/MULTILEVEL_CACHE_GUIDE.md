# 多级缓存系统使用指南

> Phase 2.2架构优化 - 三级缓存架构提升上下文访问性能

**版本**: v2.2.0
**作者**: Athena平台团队
**更新日期**: 2026-04-24

---

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [架构说明](#架构说明)
4. [配置选项](#配置选项)
5. [使用示例](#使用示例)
6. [性能调优](#性能调优)
7. [监控与统计](#监控与统计)
8. [故障排查](#故障排查)

---

## 概述

多级缓存系统是Athena平台Phase 2.2架构优化的核心组件，通过三级缓存架构显著提升上下文访问性能：

| 级别 | 类型 | 容量 | TTL | 延迟 | 命中率目标 |
|-----|------|-----|-----|------|----------|
| L1 | 内存 | 1000条 | 5分钟 | <1ms | >70% |
| L2 | Redis | 10000条 | 1小时 | ~5ms | >20% |
| L3 | SQLite | 无限 | 永久 | ~50ms | - |

**性能目标**:
- 总缓存命中率 > 90%
- 平均访问延迟降低 50%
- 吞吐量提升 2x

---

## 快速开始

### 1. 基本使用

```python
import asyncio
from core.context_management.cache import MultiLevelCacheManager, CacheConfig

async def main():
    # 创建缓存管理器（使用默认配置）
    manager = MultiLevelCacheManager()

    # 设置缓存
    await manager.set("user:123", {"name": "Alice", "age": 30})

    # 获取缓存
    user = await manager.get("user:123")
    print(user)  # {'name': 'Alice', 'age': 30}

    # 关闭管理器
    await manager.close()

asyncio.run(main())
```

### 2. 禁用Redis

```python
config = CacheConfig(
    l2_enabled=False,  # 禁用Redis（适合开发环境）
)
manager = MultiLevelCacheManager(config=config)
```

### 3. 自定义配置

```python
config = CacheConfig(
    # L1配置
    l1_capacity=2000,          # L1容量
    l1_ttl_seconds=600,        # L1 TTL（10分钟）
    l1_max_memory_mb=200,      # L1最大内存

    # L2配置
    l2_enabled=True,
    l2_host="localhost",
    l2_port=6379,
    l2_password="your_password",
    l2_ttl_seconds=7200,       # L2 TTL（2小时）

    # L3配置
    l3_db_path="/custom/path/cache.db",
)
manager = MultiLevelCacheManager(config=config)
```

---

## 架构说明

### 缓存层级

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│              MultiLevelCacheManager                      │
│  ┌─────────────┬─────────────┬─────────────┐            │
│  │  L1 Memory  │  L2 Redis   │  L3 SQLite  │            │
│  │  (1000条)   │  (10000条)  │  (无限)     │            │
│  │  TTL: 5min  │  TTL: 1h    │  TTL: 永久  │            │
│  └─────────────┴─────────────┴─────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### 读取策略

```
1. 检查L1内存缓存
   ├─ 命中 → 返回数据
   └─ 未命中 ↓
2. 检查L2 Redis缓存
   ├─ 命中 → 回填L1 → 返回数据
   └─ 未命中 ↓
3. 检查L3 SQLite存储
   ├─ 命中 → 回填L2、L1 → 返回数据
   └─ 未命中 → 返回None
```

### 写入策略

```
写入操作 → 同时写入L1、L2、L3（write-through）
         ↓
    异步写入L2、L3（不阻塞主流程）
```

---

## 配置选项

### CacheConfig 参数

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `l1_capacity` | int | 1000 | L1最大条目数 |
| `l1_ttl_seconds` | int | 300 | L1默认TTL（秒） |
| `l1_max_memory_mb` | int | 100 | L1最大内存（MB） |
| `l2_enabled` | bool | True | 是否启用L2 |
| `l2_host` | str | localhost | Redis主机 |
| `l2_port` | int | 6379 | Redis端口 |
| `l2_password` | str | None | Redis密码 |
| `l2_db` | int | 0 | Redis数据库编号 |
| `l2_ttl_seconds` | int | 3600 | L2默认TTL（秒） |
| `l2_pool_size` | int | 10 | Redis连接池大小 |
| `l3_db_path` | str | ~/.athena/cache/context.db | SQLite数据库路径 |
| `write_through` | bool | True | 是否同时写入所有层级 |
| `populate_lower` | bool | True | 是否回填上级缓存 |
| `enable_null_cache` | bool | False | 是否缓存空值 |

---

## 使用示例

### 基本CRUD操作

```python
# 创建（设置）
await manager.set("key", "value")

# 读取
value = await manager.get("key")

# 更新
await manager.set("key", "new_value")

# 删除
await manager.delete("key")

# 检查存在
exists = await manager.exists("key")
```

### 批量操作

```python
# 批量获取
values = await manager.get_many(["key1", "key2", "key3"])

# 批量设置
data = {"key1": "value1", "key2": "value2"}
count = await manager.set_many(data)
```

### 自定义TTL

```python
# 设置5分钟TTL
await manager.set("session:xyz", session_data, ttl_seconds=300)

# 设置永久有效（L3）
await manager.set("config:theme", "dark", ttl_seconds=None)
```

### 缓存预热

```python
# 预热常用数据
warmup_data = {
    "config:app": {"version": "2.2.0"},
    "user:admin": {"role": "administrator"},
    "permissions:read": ["posts", "comments"],
}
count = await manager.warm_up(warmup_data)
print(f"预热完成: {count}条")
```

### 清理过期条目

```python
# 清理所有层级的过期条目
cleaned = await manager.cleanup_expired()
print(f"清理: L1={cleaned['L1']}条, L3={cleaned['L3']}条")
```

---

## 性能调优

### 1. 调整容量

```python
# 高并发场景：增大L1容量
config = CacheConfig(l1_capacity=5000, l1_max_memory_mb=500)

# 内存受限：减小L1容量
config = CacheConfig(l1_capacity=500, l1_max_memory_mb=50)
```

### 2. 调整TTL

```python
# 热数据：短TTL，保持新鲜
config = CacheConfig(l1_ttl_seconds=60)

# 冷数据：长TTL，减少穿透
config = CacheConfig(l1_ttl_seconds=3600, l2_ttl_seconds=86400)
```

### 3. 禁用写透（提升写入性能）

```python
config = CacheConfig(write_through=False, write_back=True)
```

### 4. 启用空值缓存（防止穿透）

```python
config = CacheConfig(enable_null_cache=True)
```

---

## 监控与统计

### 获取统计信息

```python
# 获取完整统计
stats = await manager.get_full_statistics()

print(f"总请求: {stats['manager']['total_requests']}")
print(f"命中率: {stats['manager']['overall_hit_rate']:.2%}")
print(f"平均延迟: {stats['manager']['average_latency_ms']:.2f}ms")
print(f"L1命中: {stats['manager']['l1_hits']}")
print(f"L2命中: {stats['manager']['l2_hits']}")
print(f"L3命中: {stats['manager']['l3_hits']}")
```

### 健康检查

```python
health = await manager.health_check()
print(f"L1健康: {health['L1']}")
print(f"L2健康: {health['L2']}")
print(f"L3健康: {health['L3']}")
```

### 各层级统计

```python
# L1统计
l1_stats = manager.l1.get_statistics()
print(f"L1命中率: {l1_stats['hit_rate']:.2%}")
print(f"L1利用率: {l1_stats['utilization']:.2%}")

# L3统计
l3_stats = await manager.l3.get_statistics()
print(f"L3条目数: {l3_stats['entries']}")
print(f"L3大小: {l3_stats['total_mb']:.2f}MB")
```

---

## 故障排查

### Redis连接失败

**现象**: L2缓存不生效，日志显示Redis连接错误

**解决方案**:
```python
# 方案1: 检查Redis是否运行
docker-compose ps redis

# 方案2: 禁用L2缓存
config = CacheConfig(l2_enabled=False)

# 方案3: 调整连接参数
config = CacheConfig(
    l2_host="127.0.0.1",  # 尝试localhost或127.0.0.1
    l2_port=6379,
    l2_password=None,    # 如果没有密码
)
```

### 缓存命中率低

**现象**: `overall_hit_rate < 0.7`

**可能原因**:
1. L1容量过小
2. TTL过短
3. 数据访问模式不符合局部性原理

**解决方案**:
```python
# 增大L1容量
config = CacheConfig(l1_capacity=2000)

# 延长TTL
config = CacheConfig(l1_ttl_seconds=600)

# 预热热点数据
await manager.warm_up(hot_data)
```

### 内存占用过高

**现象**: 进程内存持续增长

**解决方案**:
```python
# 减小L1容量
config = CacheConfig(
    l1_capacity=500,
    l1_max_memory_mb=50,
)

# 定期清理
async def periodic_cleanup():
    while True:
        await asyncio.sleep(300)  # 每5分钟
        await manager.cleanup_expired()

asyncio.create_task(periodic_cleanup())
```

### SQLite锁竞争

**现象**: L3写入慢，日志显示database is locked

**解决方案**:
```python
# SQLite已配置WAL模式，如仍有问题：
# 1. 减少并发写入
# 2. 使用批量操作
await manager.l3.set_many(data)

# 3. 定期VACUUM
await manager.l3.vacuum()
```

---

## 最佳实践

### 1. 键命名规范

```python
# 使用冒号分隔的命名空间
"user:123"
"session:abc123"
"config:theme"
"cache:patent:CN123456"
```

### 2. 设置合理的TTL

```python
# 用户会话: 短TTL（5-30分钟）
await manager.set("session:xyz", data, ttl_seconds=1800)

# 配置数据: 长TTL（1-24小时）
await manager.set("config:app", config, ttl_seconds=3600)

# 静态数据: 永久
await manager.set("static:countries", countries, ttl_seconds=None)
```

### 3. 使用批量操作

```python
# ❌ 低效
for key, value in data.items():
    await manager.set(key, value)

# ✅ 高效
await manager.set_many(data)
```

### 4. 处理缓存穿透

```python
# 方案1: 空值缓存
config = CacheConfig(enable_null_cache=True)

# 方案2: 布隆过滤器（业务层实现）
# 方案3: 预热所有有效键
```

---

## 性能基准

基于以下配置的测试结果：

```python
config = CacheConfig(
    l1_capacity=1000,
    l1_ttl_seconds=300,
    l2_enabled=False,
)
```

| 操作 | 吞吐量 | P50延迟 | P95延迟 | P99延迟 |
|-----|--------|--------|--------|--------|
| L1读取 | 500k OPS | 0.05ms | 0.1ms | 0.2ms |
| L3读取 | 10k OPS | 0.5ms | 1ms | 2ms |
| 写入 | 50k OPS | 0.1ms | 0.3ms | 0.5ms |

**缓存命中率**:
- 热数据访问模式: 85-95%
- 随机访问模式: 60-75%
- 冷启动: 0% → 80%（100次操作后）

---

## 附录

### 相关文件

- `core/context_management/cache/__init__.py` - 缓存模块入口
- `core/context_management/cache/l1_memory.py` - L1内存缓存
- `core/context_management/cache/l2_redis.py` - L2 Redis缓存
- `core/context_management/cache/l3_sqlite.py` - L3 SQLite存储
- `core/context_management/cache/multilevel_cache.py` - 多级缓存管理器
- `tests/test_multilevel_cache.py` - 单元测试
- `tests/performance/test_cache_performance.py` - 性能测试

### 运行测试

```bash
# 单元测试
pytest tests/test_multilevel_cache.py -v

# 性能测试
pytest tests/performance/test_cache_performance.py -v -s

# 排除慢速测试
pytest tests/test_multilevel_cache.py -v -m "not slow"
```

---

**文档版本**: v2.2.0
**最后更新**: 2026-04-24
