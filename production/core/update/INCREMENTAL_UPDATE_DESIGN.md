# 专利决定书增量更新机制设计

## 🎯 设计目标

### 核心需求
- **增量处理**: 仅处理变更文件，避免重复计算
- **高效监控**: 快速识别文件变更（新增、修改、删除）
- **断点续传**: 支持大规模处理中断后恢复
- **数据一致性**: 确保向量库和知识图谱同步
- **自动化**: 支持定时自动更新和手动触发

### 性能指标
- **变更检测速度**: <60秒（36,829个文件）
- **增量处理效率**: 95%+时间节省（vs全量重建）
- **系统资源占用**: 内存<4GB，CPU<50%
- **数据准确性**: 99.9%变更识别准确率

## 🏗️ 架构设计

### 三层架构模式

```
┌─────────────────────────────────────────────────────────┐
│                   监控预警层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   文件监控   │ │   性能监控   │ │    异常预警          │   │
│  │   Watcher   │ │   Monitor   │ │    Alert            │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                   增量处理层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   变更检测   │ │   增量解析   │ │    批量处理          │   │
│  │ ChangeDetector│ BatchProcessor│ VectorProcessor      │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│                   数据持久层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐   │
│  │   文件快照   │ │   处理日志   │ │    状态追踪          │   │
│  │ SnapshotDB  │ │ ProcessingLog│ StateTracker         │   │
│  └─────────────┘ └─────────────┘ └─────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 🔄 增量更新流程

### 1. 变更检测阶段

#### 文件快照对比
```python
# 文件快照结构
{
    "file_path": "专利复审决定原文/xxx.doc",
    "file_size": 1024000,
    "modified_time": "2025-12-22T10:30:00Z",
    "file_hash": "sha256:abc123...",
    "processing_status": "completed",
    "last_processed": "2025-12-20T15:20:00Z",
    "vector_id": "vec_12345",
    "graph_vertex_id": "vertex_67890"
}
```

#### 变更类型识别
- **新增文件**: 新快照中存在，旧快照中不存在
- **修改文件**: 文件路径相同但hash不同
- **删除文件**: 旧快照中存在，新快照中不存在
- **无变化**: 文件路径和hash都相同

### 2. 批量处理阶段

#### 处理优先级
```yaml
优先级排序:
  1. 高优先级: 最新修改文件（7天内）
  2. 中优先级: 重要文档（决定书、法律条文）
  3. 低优先级: 历史档案（1年以上）
```

#### 批处理策略
- **微批次**: 10-20个文件/批（适合内存优化）
- **标准批次**: 50-100个文件/批（常规处理）
- **大批次**: 200-500个文件/批（高性能服务器）

### 3. 数据同步阶段

#### 向量库更新
```python
# 删除操作
qdrant_client.delete(
    collection_name="patent_decisions",
    points_selector=models.Filter(
        must=[models.FieldCondition(
            key="file_path",
            match=models.MatchValue(value=file_path)
        )]
    )
)

# 新增/修改操作
qdrant_client.upsert(
    collection_name="patent_decisions",
    points=vector_points
)
```

#### 知识图谱更新
```python
# 删除旧节点
g.execute('DELETE VERTEX Decision WHERE file_path = "path/to/file"')

# 创建新节点
g.execute('INSERT VERTEX Decision (file_path, title, content_hash) VALUES ("path", "title", "hash")')
```

## 📊 核心组件设计

### 1. 文件监控器 (FileWatcher)

**功能特性**:
- 实时文件系统监控（inotify/FSWatch）
- 定期全盘扫描（每日备份检查）
- 文件变更事件过滤和聚合

**监控规则**:
```python
class FileWatcher:
    def __init__(self):
        self.watch_patterns = [
            "*.doc",     # Word文档
            "*.docx",    # Word新版本文档
            "*.pdf",     # PDF文档（未来扩展）
        ]
        self.ignore_patterns = [
            "*.tmp",     # 临时文件
            "~$*",       # Office临时文件
            ".DS_Store", # macOS系统文件
        ]
```

### 2. 增量检测器 (ChangeDetector)

**检测算法**:
```python
async def detect_changes(self, current_snapshot: Dict, last_snapshot: Dict) -> Dict:
    changes = {
        "added": [],
        "modified": [],
        "deleted": [],
        "unchanged": []
    }

    # O(n)时间复杂度的高效对比算法
    current_files = {fp: info['hash'] for fp, info in current_snapshot.items()}
    last_files = {fp: info['hash'] for fp, info in last_snapshot.items()}

    # 检测新增和修改
    for file_path, file_hash in current_files.items():
        if file_path not in last_files:
            changes["added"].append(file_path)
        elif file_hash != last_files[file_path]:
            changes["modified"].append(file_path)
        else:
            changes["unchanged"].append(file_path)

    # 检测删除
    for file_path in last_files:
        if file_path not in current_files:
            changes["deleted"].append(file_path)

    return changes
```

### 3. 批量处理器 (BatchProcessor)

**处理策略**:
```python
class BatchProcessor:
    def __init__(self):
        self.batch_configs = {
            "micro": {"size": 10, "timeout": 30, "memory_limit": "1GB"},
            "standard": {"size": 50, "timeout": 120, "memory_limit": "2GB"},
            "large": {"size": 200, "timeout": 300, "memory_limit": "4GB"}
        }

    async def process_changes(self, changes: Dict, strategy: str = "standard"):
        batch_config = self.batch_configs[strategy]

        # 按优先级排序
        sorted_changes = self._prioritize_changes(changes)

        # 分批处理
        batches = self._create_batches(sorted_changes, batch_config["size"])

        for batch in batches:
            await self._process_batch(batch)
            await self._checkpoint_progress(batch)
```

### 4. 状态追踪器 (StateTracker)

**状态管理**:
```python
class StateTracker:
    def __init__(self):
        self.states = [
            "pending",      # 等待处理
            "processing",   # 正在处理
            "completed",    # 处理完成
            "failed",       # 处理失败
            "skipped"       # 跳过处理
        ]

    async def update_file_status(self, file_path: str, status: str, metadata: Dict = None):
        # 更新处理状态
        # 记录处理时间戳
        # 保存错误信息（如有）
        # 更新统计指标
```

## ⚙️ 配置管理

### 增量更新配置

```yaml
# incremental_config.yaml
incremental_update:
  # 监控配置
  file_monitoring:
    enable_realtime: true
    full_scan_interval: "24h"
    ignore_patterns: ["*.tmp", "~$*", ".DS_Store"]

  # 检测配置
  change_detection:
    hash_algorithm: "sha256"
    batch_size: 100
    parallel_workers: 4

  # 处理配置
  batch_processing:
    strategy: "standard"  # micro, standard, large
    timeout_seconds: 120
    retry_attempts: 3
    memory_threshold_gb: 4

  # 数据库配置
  database:
    snapshot_path: ".cache/decisions/snapshots.db"
    log_path: ".cache/decisions/processing.log"
    checkpoint_interval: 10

  # 性能配置
  performance:
    max_concurrent_files: 2
    cache_size_mb: 512
    gc_interval: "1h"
```

### 自动更新调度

```python
# 定时任务配置
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class IncrementalScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def setup_jobs(self):
        # 每日凌晨2点全盘扫描
        self.scheduler.add_job(
            func=self.full_snapshot_scan,
            trigger='cron',
            hour=2,
            minute=0,
            id='daily_scan'
        )

        # 每15分钟增量检查
        self.scheduler.add_job(
            func=self.incremental_check,
            trigger='interval',
            minutes=15,
            id='incremental_check'
        )

        # 每小时清理临时文件
        self.scheduler.add_job(
            func=self.cleanup_temp_files,
            trigger='interval',
            hours=1,
            id='cleanup'
        )
```

## 🚨 异常处理

### 常见异常场景

#### 1. 文件访问冲突
```python
async def handle_file_conflict(self, file_path: str):
    """处理文件被占用或无法访问的情况"""
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            # 尝试获取文件锁
            async with aiofiles.open(file_path, 'rb') as f:
                content = await f.read()
                return content
        except PermissionError:
            retry_count += 1
            await asyncio.sleep(2 ** retry_count)  # 指数退避

    # 记录失败，跳过此文件
    logger.warning(f"文件访问失败，跳过处理: {file_path}")
    return None
```

#### 2. 内存不足处理
```python
async def handle_memory_pressure(self):
    """内存压力处理"""
    memory_info = psutil.virtual_memory()

    if memory_info.percent > 85:
        logger.warning("内存使用率过高，触发优化措施")

        # 1. 清理缓存
        await self.clear_caches()

        # 2. 减小批次大小
        self.batch_size = max(10, self.batch_size // 2)

        # 3. 强制垃圾回收
        import gc
        gc.collect()

        # 4. 暂停处理，等待内存释放
        await asyncio.sleep(30)
```

#### 3. 网络连接异常
```python
async def handle_connection_failure(self, service_name: str):
    """处理向量库/图数据库连接异常"""
    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            # 尝试重新连接
            if service_name == "qdrant":
                await self.qdrant_client.reconnect()
            elif service_name == "nebula":
                await self.nebula_client.reconnect()

            return True

        except Exception as e:
            retry_count += 1
            wait_time = min(60, 2 ** retry_count)  # 最大等待60秒
            logger.warning(f"{service_name}连接失败，{wait_time}秒后重试: {e}")
            await asyncio.sleep(wait_time)

    return False
```

## 📈 性能优化策略

### 1. 算法优化

#### 文件哈希优化
```python
# 只哈希文件部分内容，提高速度
async def fast_file_hash(self, file_path: str, sample_size: int = 64*1024) -> str:
    """快速文件哈希（只哈希首尾64KB）"""
    hasher = hashlib.sha256()

    async with aiofiles.open(file_path, 'rb') as f:
        # 文件开头
        header = await f.read(sample_size)
        hasher.update(header)

        # 文件结尾（如果文件大于sample_size）
        if await f.seek(0, io.SEEK_END) > sample_size * 2:
            await f.seek(-sample_size, io.SEEK_END)
            footer = await f.read(sample_size)
            hasher.update(footer)

    return hasher.hexdigest()
```

#### 批处理优化
```python
# 智能批次大小调整
def adjust_batch_size(self, current_performance: Dict):
    """基于当前性能动态调整批次大小"""
    processing_rate = current_performance["files_per_second"]
    memory_usage = current_performance["memory_percent"]

    if processing_rate < 1.0 and memory_usage < 70:
        # 性能低但内存充足，增大批次
        self.batch_size = min(200, self.batch_size * 1.2)

    elif memory_usage > 85:
        # 内存压力大，减小批次
        self.batch_size = max(10, self.batch_size // 2)

    logger.info(f"批次大小调整为: {self.batch_size}")
```

### 2. 缓存策略

#### 多级缓存设计
```python
class MultiLevelCache:
    def __init__(self):
        self.l1_cache = {}      # 内存缓存（最近访问）
        self.l2_cache = LRUCache(maxsize=1000)  # LRU缓存
        self.l3_cache = SqliteCache()  # 磁盘缓存

    async def get(self, key: str):
        # L1缓存查找
        if key in self.l1_cache:
            return self.l1_cache[key]

        # L2缓存查找
        value = self.l2_cache.get(key)
        if value:
            self.l1_cache[key] = value  # 提升到L1
            return value

        # L3缓存查找
        value = await self.l3_cache.get(key)
        if value:
            self.l2_cache[key] = value
            self.l1_cache[key] = value

        return value
```

## 📊 监控和告警

### 关键指标监控

```python
class MetricsCollector:
    def __init__(self):
        self.metrics = {
            "processing_rate": 0.0,      # 文件/秒
            "success_rate": 1.0,         # 成功率
            "error_rate": 0.0,          # 错误率
            "memory_usage": 0.0,         # 内存使用率
            "cache_hit_rate": 0.0,       # 缓存命中率
            "queue_size": 0,            # 待处理队列大小
        }

    async def collect_metrics(self):
        """收集实时性能指标"""
        self.metrics["processing_rate"] = self._calculate_processing_rate()
        self.metrics["memory_usage"] = psutil.virtual_memory().percent
        self.metrics["cache_hit_rate"] = self._calculate_cache_hit_rate()

        # 发送到监控系统
        await self.send_to_prometheus(self.metrics)
```

### 告警规则配置

```yaml
alerting_rules:
  critical:
    - name: "processing_stopped"
      condition: "processing_rate == 0"
      duration: "5m"
      action: "restart_service"

    - name: "memory_exhausted"
      condition: "memory_usage > 95"
      duration: "2m"
      action: "emergency_cleanup"

  warning:
    - name: "high_error_rate"
      condition: "error_rate > 0.1"
      duration: "10m"
      action: "log_and_notify"

    - name: "queue_backlog"
      condition: "queue_size > 1000"
      duration: "15m"
      action: "scale_up_workers"
```

## 🔧 API接口设计

### RESTful API

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="增量更新API")

class IncrementalUpdateRequest(BaseModel):
    source_path: str
    update_strategy: str = "standard"
    dry_run: bool = False

class UpdateStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: float
    changes_found: int
    processed_files: int
    errors: List[str]

@app.post("/api/v1/incremental-update/start")
async def start_incremental_update(request: IncrementalUpdateRequest):
    """启动增量更新"""
    try:
        session_id = await incremental_updater.start_update(
            source_path=request.source_path,
            strategy=request.update_strategy,
            dry_run=request.dry_run
        )
        return {"session_id": session_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/incremental-update/status/{session_id}")
async def get_update_status(session_id: str):
    """查询更新状态"""
    status = await incremental_updater.get_status(session_id)
    return UpdateStatusResponse(**status)

@app.post("/api/v1/incremental-update/stop/{session_id}")
async def stop_incremental_update(session_id: str):
    """停止增量更新"""
    success = await incremental_updater.stop_update(session_id)
    return {"success": success, "session_id": session_id}
```

## 🧪 测试策略

### 单元测试覆盖

```python
import pytest
from unittest.mock import AsyncMock, patch

class TestIncrementalUpdater:
    @pytest.fixture
    async def updater(self):
        return IncrementalUpdater()

    async def test_file_hash_calculation(self, updater):
        """测试文件哈希计算"""
        with patch('aiofiles.open', create=True) as mock_file:
            mock_file.return_value.__aenter__.return_value.read.return_value = b"test content"

            hash_value = await updater.calculate_file_hash("test.doc")
            assert len(hash_value) == 64  # SHA256 hex length

    async def test_change_detection(self, updater):
        """测试变更检测"""
        current_snapshot = {"file1.doc": {"hash": "abc123"}}
        last_snapshot = {"file1.doc": {"hash": "def456"}, "file2.doc": {"hash": "ghi789"}}

        changes = await updater.detect_changes(current_snapshot, last_snapshot)

        assert "file1.doc" in changes["modified"]
        assert "file2.doc" in changes["deleted"]
```

### 性能基准测试

```python
async def benchmark_change_detection():
    """变更检测性能基准测试"""
    # 生成36,829个文件的测试快照
    test_snapshot = generate_test_snapshot(36829)

    start_time = time.time()
    changes = await change_detector.detect_changes(test_snapshot, {})
    end_time = time.time()

    processing_time = end_time - start_time
    files_per_second = len(test_snapshot) / processing_time

    print(f"变更检测性能: {files_per_second:.1f} files/second")
    assert files_per_second > 1000  # 期望每秒处理1000+文件
```

## 📋 部署和运维

### Docker容器化

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    antiword \
    pandoc \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 设置环境变量
ENV PYTHONPATH=/app
ENV INCREMENTAL_CONFIG_PATH=/app/config/incremental_config.yaml

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-m", "core.update.incremental_update_service"]
```

### Kubernetes部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: incremental-updater
spec:
  replicas: 1
  selector:
    matchLabels:
      app: incremental-updater
  template:
    metadata:
      labels:
        app: incremental-updater
    spec:
      containers:
      - name: updater
        image: athena/incremental-updater:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "1000m"
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: QDRANT_URL
          value: "http://qdrant-service:6333"
```

## 🎉 总结

### 核心优势

1. **高效性**: 增量处理避免重复计算，95%+时间节省
2. **可靠性**: 多重异常处理和自动恢复机制
3. **可扩展性**: 支持水平扩展和负载均衡
4. **易维护性**: 标准化API和完整的监控体系
5. **灵活性**: 支持多种处理策略和配置选项

### 技术亮点

- **智能变更检测**: O(n)时间复杂度的高效文件对比算法
- **自适应批处理**: 基于系统性能动态调整批次大小
- **多级缓存架构**: L1/L2/L3缓存显著提升处理速度
- **断点续传机制**: 支持大规模处理中断后无缝恢复
- **实时监控告警**: 完整的指标监控和智能告警系统

### 预期效果

通过实施这个增量更新机制，您将获得：

- **处理效率提升**: 从全量重建24小时 → 增量更新15分钟
- **系统资源优化**: 内存占用降低60%，CPU使用率优化
- **数据实时性**: 文件变更15分钟内生效
- **运维自动化**: 无人值守的自动化更新和异常处理
- **可扩展架构**: 支持未来数据量和业务增长需求

这个增量更新机制为专利决定书的大规模处理提供了坚实的技术基础，确保系统的高效、稳定和可维护性。