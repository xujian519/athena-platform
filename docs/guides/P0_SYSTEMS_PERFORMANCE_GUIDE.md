# P0系统性能优化与最佳实践

**版本**: 1.0.0
**更新日期**: 2026-04-21
**适用对象**: 开发者、运维人员

---

## 📚 目录

1. [性能优化指南](#性能优化指南)
2. [最佳实践](#最佳实践)
3. [常见问题](#常见问题)

---

## 性能优化指南

### Skills系统优化

#### 1. 技能缓存

```python
from core.skills.registry import SkillRegistry

# 使用单例模式避免重复加载
class SkillRegistrySingleton:
    _instance = None
    _registry = None
    
    @classmethod
    def get_instance(cls) -> SkillRegistry:
        if cls._instance is None:
            cls._registry = SkillRegistry()
            cls._instance = cls
        return cls._registry

# 使用
registry = SkillRegistrySingleton.get_instance()
```

#### 2. 延迟加载

```python
# 只在需要时加载技能
class LazySkillLoader:
    def __init__(self):
        self._loaded = False
        self._skills = {}
    
    def get_skill(self, skill_id: str):
        if not self._loaded:
            self._load_skills()
            self._loaded = True
        return self._skills.get(skill_id)
```

#### 3. 批量操作

```python
# 批量注册技能
def register_skills_batch(registry, skills):
    """批量注册技能，减少锁竞争"""
    for skill in skills:
        registry.register(skill)
    # 一次性提交所有更改
```

### Plugins系统优化

#### 1. 插件按需加载

```python
class PluginManager:
    def __init__(self):
        self._loaded_plugins = {}
    
    def get_plugin(self, plugin_id: str):
        if plugin_id not in self._loaded_plugins:
            plugin = self._load_plugin(plugin_id)
            self._loaded_plugins[plugin_id] = plugin
        return self._loaded_plugins[plugin_id]
```

#### 2. 插件预编译

```python
# 预编译Python代码以加快加载
import py_compile

def preload_plugins(plugin_dir):
    for py_file in Path(plugin_dir).rglob("*.py"):
        py_compile.compile(py_file, optimize=2)
```

#### 3. 依赖关系缓存

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def resolve_plugin_dependencies(plugin_id: str):
    """缓存插件依赖解析结果"""
    plugin = registry.get_plugin(plugin_id)
    return plugin.metadata.dependencies
```

### 会话记忆系统优化

#### 1. 批量消息添加

```python
class SessionManager:
    def add_messages_batch(
        self,
        session_id: str,
        messages: List[SessionMessage],
    ):
        """批量添加消息，减少IO操作"""
        session = self.get_session(session_id)
        if session:
            session.messages.extend(messages)
            session.context.message_count += len(messages)
            # 只在最后更新一次
            session.context.update_activity()
```

#### 2. 定期持久化

```python
class AutoSaveSessionManager(SessionManager):
    def __init__(self, *args, auto_save_interval=300, **kwargs):
        super().__init__(*args, **kwargs)
        self.auto_save_interval = auto_save_interval
        self._last_save = time.time()
    
    def add_message(self, *args, **kwargs):
        super().add_message(*args, **kwargs)
        
        # 定期自动保存
        if time.time() - self._last_save > self.auto_save_interval:
            self._auto_save()
            self._last_save = time.time()
```

#### 3. 内存优化

```python
class SessionMemory:
    def __init__(self, max_messages=1000):
        self.max_messages = max_messages
    
    def add_message(self, message: SessionMessage):
        self.messages.append(message)
        
        # 限制内存使用
        if len(self.messages) > self.max_messages:
            # 保留最近的消息
            self.messages = self.messages[-self.max_messages:]
```

---

## 最佳实践

### 1. 错误处理

#### Skills系统

```python
def safe_execute_skill(skill_id: str, params: dict):
    """安全执行技能"""
    try:
        skill = registry.get_skill(skill_id)
        if not skill:
            logger.error(f"技能不存在: {skill_id}")
            return None
        
        if not skill.is_enabled():
            logger.warning(f"技能未启用: {skill_id}")
            return None
        
        return executor.execute(skill_id, params)
    
    except Exception as e:
        logger.error(f"执行技能失败 {skill_id}: {e}")
        return None
```

#### Plugins系统

```python
def safe_load_plugin(plugin_id: str):
    """安全加载插件"""
    try:
        plugin = loader.load_from_file(f"plugins/{plugin_id}.yaml")
        
        # 检查依赖
        for dep in plugin.metadata.dependencies:
            if not registry.get_plugin(dep):
                logger.error(f"缺少依赖: {dep}")
                return None
        
        registry.register(plugin)
        return plugin
    
    except Exception as e:
        logger.error(f"加载插件失败 {plugin_id}: {e}")
        return None
```

#### 会话记忆系统

```python
def safe_add_message(session_id: str, role, content):
    """安全添加消息"""
    try:
        return manager.add_message(
            session_id=session_id,
            role=role,
            content=content,
            token_count=len(content.split()),
        )
    except Exception as e:
        logger.error(f"添加消息失败: {e}")
        # 尝试创建新会话
        manager.create_session(session_id, "default", "default")
        return manager.add_message(session_id, role, content)
```

### 2. 资源管理

#### 连接池管理

```python
from core.database import get_connection_pool

class PooledSessionManager(SessionManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_pool = get_connection_pool()
    
    def save_session_to_db(self, session_id: str):
        """使用连接池保存会话"""
        with self.db_pool.get_connection() as conn:
            # 执行数据库操作
            pass
```

#### 内存限制

```python
import psutil
import resource

def set_memory_limits():
    """设置内存限制"""
    # 限制进程内存使用
    max_memory = 2 * 1024 * 1024 * 1024  # 2GB
    resource.setrlimit(
        resource.RLIMIT_AS,
        (max_memory, max_memory)
    )
```

### 3. 监控和日志

#### 性能监控

```python
import time
from functools import wraps

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            # 记录性能指标
            logger.info(f"{func.__name__} 执行时间: {elapsed:.3f}s")
            
            # 慢查询告警
            if elapsed > 1.0:
                logger.warning(f"⚠️ {func.__name__} 执行缓慢: {elapsed:.3f}s")
            
            return result
        except Exception as e:
            logger.error(f"{func.__name__} 执行失败: {e}")
            raise
    
    return wrapper

# 使用
@monitor_performance
def execute_skill(skill_id: str):
    pass
```

#### 结构化日志

```python
import structlog

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# 使用
logger.info(
    "skill_executed",
    skill_id="patent_analysis",
    execution_time=0.123,
    success=True,
)
```

---

## 常见问题

### Q1: Skills系统 - 技能加载缓慢

**症状**: 加载技能时响应时间过长

**原因**:
- YAML文件过多
- 磁盘IO瓶颈
- 未使用缓存

**解决方案**:
```python
# 1. 使用缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def load_skill_cached(skill_path: str):
    return loader.load_from_file(skill_path)

# 2. 批量加载
skills = loader.load_from_directory("core/skills", register=False)
for skill in skills:
    registry.register(skill)

# 3. 预加载常用技能
preload_skills = ["patent_analysis", "case_retrieval"]
for skill_id in preload_skills:
    registry.get_skill(skill_id)
```

### Q2: Plugins系统 - 插件冲突

**症状**: 多个插件使用同一工具的不同版本

**解决方案**:
```python
# 检测冲突
mapper = SkillToolMapper(registry)
conflicts = mapper.detect_tool_conflicts()

for conflict in conflicts:
    logger.error(f"工具冲突: {conflict['tool']}")
    logger.error(f"  版本: {conflict['versions']}")
    logger.error(f"  技能: {conflict['skills']}")

# 解决方案：统一版本
# 1. 在插件YAML中指定统一版本
# 2. 使用依赖管理
# 3. 虚拟环境隔离
```

### Q3: 会话记忆系统 - 内存泄漏

**症状**: 长时间运行后内存占用持续增长

**原因**:
- 未清理过期会话
- 消息列表无限增长
- 未释放资源

**解决方案**:
```python
# 1. 定期清理
import asyncio

async def cleanup_task():
    while True:
        cleaned = manager.cleanup_expired_sessions()
        logger.info(f"清理了 {cleaned} 个过期会话")
        await asyncio.sleep(300)  # 每5分钟清理一次

# 2. 限制消息数量
class SessionMemory:
    def __init__(self, max_messages=1000):
        self.max_messages = max_messages
    
    def add_message(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_messages:
            # 归档旧消息
            self._archive_old_messages()

# 3. 使用弱引用
import weakref

class SessionManager:
    def __init__(self):
        self._sessions = weakref.WeakValueDictionary()
```

### Q4: 系统集成 - 性能瓶颈

**症状**: 整体响应时间过长

**诊断**:
```python
import cProfile
import pstats

def profile_system():
    """性能分析"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 执行操作
    agent.process(user_input, session_id, user_id)
    
    profiler.disable()
    
    # 分析结果
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 打印前10个最慢的函数
```

**优化建议**:
1. **并行化**: 使用asyncio并行执行独立任务
2. **缓存**: 缓存频繁访问的数据
3. **批量操作**: 减少IO次数
4. **延迟加载**: 按需加载资源

---

## 监控指标

### 关键指标

| 系统 | 指标 | 目标值 | 告警阈值 |
|------|------|--------|----------|
| Skills | 技能加载时间 | <100ms | >500ms |
| Skills | 技能查询时间 | <1ms | >10ms |
| Plugins | 插件加载时间 | <200ms | >1000ms |
| Plugins | 插件激活时间 | <50ms | >200ms |
| Sessions | 消息添加时间 | <1ms | >5ms |
| Sessions | 会话查询时间 | <5ms | >20ms |
| Sessions | 持久化时间 | <50ms | >200ms |

### 监控实现

```python
class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = {}
    
    def record_latency(self, operation: str, latency: float):
        """记录延迟"""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(latency)
    
    def get_stats(self, operation: str) -> dict:
        """获取统计信息"""
        if operation not in self.metrics:
            return {}
        
        latencies = self.metrics[operation]
        return {
            "count": len(latencies),
            "avg": sum(latencies) / len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "p95": sorted(latencies)[int(len(latencies) * 0.95)],
        }

# 使用
metrics = MetricsCollector()

start = time.time()
# 执行操作
skill = registry.get_skill("patent_analysis")
latency = time.time() - start

metrics.record_latency("skill_get", latency)
stats = metrics.get_stats("skill_get")
print(f"平均延迟: {stats['avg']:.3f}s")
```

---

**作者**: Athena平台团队
**最后更新**: 2026-04-21
**版本**: 1.0.0
