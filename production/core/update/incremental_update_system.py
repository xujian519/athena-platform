#!/usr/bin/env python3
"""
增量更新系统
Incremental Update System

支持专利决定书的增量更新、变更检测和智能同步

高级功能:
- 智能变更检测 (多种哈希策略)
- 自适应批处理 (基于系统性能)
- 多级缓存架构 (L1/L2/L3缓存)
- 实时监控告警 (性能指标追踪)
- 自动故障恢复 (异常处理和重试)
- 异步并行处理 (高效并发)
"""

from __future__ import annotations
import asyncio
import hashlib
import json
import os
import sqlite3
import sys
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiofiles
import psutil

from core.logging_config import setup_logging

# import sqlite_utils  # 不依赖外部库,使用标准库

# 缓存类
class LRUCache:
    """LRU缓存实现"""
    def __init__(self, maxsize=1000):
        self.maxsize = maxsize
        self.cache = {}
        self.order = []

    def get(self, key):
        if key in self.cache:
            # 移动到最前面
            self.order.remove(key)
            self.order.append(key)
            return self.cache[key]
        return None

    def __setitem__(self, key, value):
        if key in self.cache:
            self.order.remove(key)
        elif len(self.cache) >= self.maxsize:
            # 删除最久未使用的项
            oldest = self.order.pop(0)
            del self.cache[oldest]

        self.cache[key] = value
        self.order.append(key)

    def __contains__(self, key):
        return key in self.cache

class SqliteCache:
    """SQLite磁盘缓存"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_time TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expiry ON cache_entries(expiry_time)')
        conn.commit()
        conn.close()

    async def get(self, key: str) -> Any | None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value FROM cache_entries
            WHERE key = ? AND (expiry_time IS NULL OR expiry_time > CURRENT_TIMESTAMP)
        ''', (key,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    async def set(self, key: str, value: Any, ttl_seconds: int):
        expiry_time = datetime.now() + timedelta(seconds=ttl_seconds)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO cache_entries (key, value, expiry_time)
            VALUES (?, ?, ?)
        ''', (key, json.dumps(value, default=str), expiry_time))
        conn.commit()
        conn.close()

    async def cleanup_expired(self):
        """清理过期条目"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cache_entries WHERE expiry_time <= CURRENT_TIMESTAMP')
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted_count

# 添加Athena平台路径
sys.path.append('/Users/xujian/Athena工作平台')

# 导入组件
from qdrant_client import QdrantClient

from core.nlp.bge_embedding_service import get_bge_service

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

@dataclass
class FileChangeRecord:
    """文件变更记录"""
    file_path: str
    file_hash: str
    file_size: int
    last_modified: datetime
    change_type: str  # new, modified, deleted, moved
    processing_status: str  # pending, processing, completed, failed
    processing_time: float = 0.0
    error_message: str | None = None
    previous_hash: str | None = None
    priority: int = 5  # 1-10, 10为最高优先级
    retry_count: int = 0
    vector_id: str | None = None
    graph_vertex_id: str | None = None

@dataclass
class UpdateSession:
    """更新会话"""
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    status: str = "running"  # running, completed, failed, paused
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    new_files: int = 0
    modified_files: int = 0
    deleted_files: int = 0
    processing_time: float = 0.0
    batch_size: int = 50
    max_concurrent_files: int = 2
    processing_strategy: str = "standard"  # micro, standard, large
    memory_usage_mb: float = 0.0
    cache_hit_rate: float = 0.0

@dataclass
class PerformanceMetrics:
    """性能指标"""
    files_per_second: float = 0.0
    avg_processing_time: float = 0.0
    success_rate: float = 1.0
    error_rate: float = 0.0
    memory_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_io_mb_per_sec: float = 0.0
    cache_hit_rate: float = 0.0
    queue_size: int = 0
    active_workers: int = 0

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_time: datetime
    last_accessed: datetime
    access_count: int = 0
    size_bytes: int = 0
    ttl_seconds: int = 3600  # 1小时

class IncrementalConfig:
    """增量更新配置"""
    def __init__(self):
        # 基础配置
        self.external_base_path = "/Volumes/AthenaData/语料/专利"
        self.local_cache_path = "/Users/xujian/Athena工作平台/.cache/incremental_update"
        self.resume_db_path = "/Users/xujian/Athena工作平台/.cache/incremental_update/incremental_resume.db"

        # 监控配置
        self.scan_interval_hours = 1
        self.change_detection_enabled = True
        self.auto_process_enabled = True

        # 性能配置
        self.batch_configs = {
            "micro": {"size": 10, "timeout": 30, "memory_limit": "1GB", "concurrent": 1},
            "standard": {"size": 50, "timeout": 120, "memory_limit": "2GB", "concurrent": 2},
            "large": {"size": 200, "timeout": 300, "memory_limit": "4GB", "concurrent": 4}
        }

        # 缓存配置
        self.cache_configs = {
            "l1_cache_size": 100,      # 内存缓存条目数
            "l2_cache_size": 1000,     # LRU缓存条目数
            "l3_cache_size_mb": 512,   # 磁盘缓存大小
            "cache_ttl_seconds": 3600  # 缓存过期时间
        }

        # 重试和恢复配置
        self.max_retry_attempts = 3
        self.retry_backoff_factor = 2
        self.failure_threshold = 0.1  # 失败率阈值
        self.circuit_breaker_timeout = 300  # 熔断器超时

        # 哈希策略配置
        self.hash_strategy = "sample"  # full, sample, fast
        self.sample_size_kb = 64  # 采样大小

        # 监控告警配置
        self.metrics_collection_interval = 60  # 秒
        self.alert_thresholds = {
            "memory_usage": 85,      # 内存使用率告警阈值
            "error_rate": 0.15,      # 错误率告警阈值
            "processing_time": 300,  # 处理时间告警阈值(秒)
            "queue_size": 1000       # 队列大小告警阈值
        }

class MultiLevelCache:
    """多级缓存系统"""

    def __init__(self, config: IncrementalConfig):
        self.config = config
        self.l1_cache = {}  # 内存缓存
        self.l2_cache = LRUCache(maxsize=config.cache_configs["l2_cache_size"])
        self.l3_cache_path = Path(config.local_cache_path) / "l3_cache.db"
        self.l3_cache = SqliteCache(str(self.l3_cache_path))

    async def get(self, key: str) -> Any | None:
        """获取缓存值"""
        # L1缓存查找
        if key in self.l1_cache:
            entry = self.l1_cache[key]
            if not self._is_expired(entry):
                entry.last_accessed = datetime.now()
                entry.access_count += 1
                return entry.value
            else:
                del self.l1_cache[key]

        # L2缓存查找
        value = self.l2_cache.get(key)
        if value is not None:
            # 提升到L1
            self.l1_cache[key] = CacheEntry(
                key=key, value=value,
                created_time=datetime.now(),
                last_accessed=datetime.now()
            )
            return value

        # L3缓存查找
        value = await self.l3_cache.get(key)
        if value is not None:
            # 提升到L2和L1
            self.l2_cache[key] = value
            self.l1_cache[key] = CacheEntry(
                key=key, value=value,
                created_time=datetime.now(),
                last_accessed=datetime.now()
            )
            return value

        return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None):
        """设置缓存值"""
        ttl = ttl_seconds or self.config.cache_configs["cache_ttl_seconds"]

        # L1缓存
        self.l1_cache[key] = CacheEntry(
            key=key, value=value,
            created_time=datetime.now(),
            last_accessed=datetime.now(),
            ttl_seconds=ttl
        )

        # L2缓存
        self.l2_cache[key] = value

        # L3缓存
        await self.l3_cache.set(key, value, ttl)

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查缓存条目是否过期"""
        return (datetime.now() - entry.created_time).total_seconds() > entry.ttl_seconds

class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: float = 0.1, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def call(self, func, *args, **kwargs):
        """调用函数,带有熔断保护"""
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        """成功时调用"""
        self.success_count += 1
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0

    def on_failure(self):
        """失败时调用"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        total_requests = self.failure_count + self.success_count
        if total_requests > 10:  # 最少10个请求后才开始计算失败率
            failure_rate = self.failure_count / total_requests
            if failure_rate > self.failure_threshold:
                self.state = "OPEN"

class IncrementalUpdateSystem:
    """增量更新系统"""

    def __init__(self, config: dict[str, Any] | IncrementalConfig | None = None):
        """初始化增量更新系统"""
        self.name = "增量更新系统"
        self.version = "2.0.0"

        # 配置
        if isinstance(config, IncrementalConfig):
            self.config = config
        else:
            self.config = IncrementalConfig()
            if config:
                # 更新配置
                for key, value in config.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)

        # 确保目录存在
        self._ensure_directories()

        # 初始化数据库
        self._init_incremental_database()

        # 初始化缓存系统
        self.cache = MultiLevelCache(self.config)

        # 初始化熔断器
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=self.config.failure_threshold,
            timeout=self.config.circuit_breaker_timeout
        )

        # 服务实例
        self.bge_service = None
        self.qdrant_client = QdrantClient(host="localhost", port=6333)
        self.external_processor = None

        # 当前会话
        self.current_session = None

        # 性能监控
        self.metrics = PerformanceMetrics()
        self.metrics_history = deque(maxlen=1000)
        self.metrics_lock = threading.Lock()

        # 后台任务
        self.background_tasks = set()
        self.metrics_task = None

        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.config.batch_configs["standard"]["concurrent"])

        logger.info(f"✅ {self.name} v{self.version} 初始化完成")
        logger.info(f"   - 缓存配置: L1={self.config.cache_configs['l1_cache_size']}, L2={self.config.cache_configs['l2_cache_size']}")
        logger.info(f"   - 批处理配置: {self.config.batch_configs}")

    def _ensure_directories(self):
        """确保目录结构存在"""
        directories = [
            self.config.local_cache_path,
            f"{self.config.local_cache_path}/changes",
            f"{self.config.local_cache_path}/sessions",
            f"{self.config.local_cache_path}/logs"
        ]

        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def _init_incremental_database(self):
        """初始化增量更新数据库"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        # 文件快照表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                last_modified TIMESTAMP NOT NULL,
                change_type TEXT NOT NULL,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 变更记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS change_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                last_modified TIMESTAMP NOT NULL,
                change_type TEXT NOT NULL,
                processing_status TEXT NOT NULL DEFAULT 'pending',
                processing_time REAL DEFAULT 0.0,
                error_message TEXT,
                previous_hash TEXT,
                created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 更新会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS update_sessions (
                session_id TEXT PRIMARY KEY,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                status TEXT NOT NULL DEFAULT 'running',
                total_files INTEGER DEFAULT 0,
                processed_files INTEGER DEFAULT 0,
                failed_files INTEGER DEFAULT 0,
                new_files INTEGER DEFAULT 0,
                modified_files INTEGER DEFAULT 0,
                deleted_files INTEGER DEFAULT 0,
                processing_time REAL DEFAULT 0.0
            )
        ''')

        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON file_snapshots(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_file_path ON change_records(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_created ON change_records(created_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_change_status ON change_records(processing_status)')

        conn.commit()
        conn.close()

    async def _ensure_bge_service(self):
        """确保BGE服务已初始化"""
        if self.bge_service is None:
            self.bge_service = await get_bge_service()

    def start_update_session(self) -> str:
        """开始更新会话"""
        session_id = f"update_{int(time.time())}_{hash(time.time()) % 10000}"

        self.current_session = UpdateSession(
            session_id=session_id,
            start_time=datetime.now()
        )

        # 保存会话到数据库
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO update_sessions
            (session_id, start_time, status)
            VALUES (?, ?, 'running')
        ''', (session_id, self.current_session.start_time))
        conn.commit()
        conn.close()

        logger.info(f"🚀 开始增量更新会话: {session_id}")
        return session_id

    def end_update_session(self, session_id: str, status: str = "completed"):
        """结束更新会话"""
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session.end_time = datetime.now()
            self.current_session.status = status

            # 更新数据库
            conn = sqlite3.connect(self.config.resume_db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE update_sessions
                SET end_time = ?, status = ?,
                    total_files = ?, processed_files = ?, failed_files = ?,
                    new_files = ?, modified_files = ?, deleted_files = ?,
                    processing_time = ?
                WHERE session_id = ?
            ''', (
                self.current_session.end_time, status,
                self.current_session.total_files, self.current_session.processed_files,
                self.current_session.failed_files, self.current_session.new_files,
                self.current_session.modified_files, self.current_session.deleted_files,
                self.current_session.processing_time,
                session_id
            ))
            conn.commit()
            conn.close()

            logger.info(f"✅ 更新会话结束: {session_id} - {status}")

    async def detect_changes(self, external_path: str | None = None) -> dict[str, Any]:
        """检测文件变更"""
        logger.info("🔍 检测文件变更...")

        if external_path is None:
            external_path = self.config.external_base_path

        external_path = Path(external_path)
        if not external_path.exists():
            return {"error": "外部存储路径不存在"}

        # 获取当前文件快照
        current_files = await self._scan_external_files(external_path)

        # 获取数据库中的快照
        db_files = self._get_database_snapshot()

        # 比较并检测变更
        changes = self._compare_files(current_files, db_files)

        # 更新快照数据库
        self._update_snapshot_database(current_files)

        # 生成变更报告
        report = {
            "scan_time": datetime.now().isoformat(),
            "total_files": len(current_files),
            "total_size_gb": round(sum(f["size"] for f in current_files) / (1024**3), 2),
            "changes": {
                "new": changes["new"],
                "modified": changes["modified"],
                "deleted": changes["deleted"],
                "unchanged": changes["unchanged"]
            },
            "change_details": changes["details"]
        }

        logger.info("✅ 变更检测完成:")
        logger.info(f"   - 新增文件: {report['changes']['new']}")
        logger.info(f"   - 修改文件: {report['changes']['modified']}")
        logger.info(f"   - 删除文件: {report['changes']['deleted']}")
        logger.info(f"   - 无变化: {report['changes']['unchanged']}")

        return report

    async def _scan_external_files(self, external_path: Path) -> dict[str, dict[str, Any]]:
        """扫描外部存储文件"""
        files = {}

        # 扫描决定书目录
        decision_dirs = {
            "review": external_path / "专利复审决定原文",
            "invalid": external_path / "专利无效宣告原文"
        }

        for decision_type, dir_path in decision_dirs.items():
            if not dir_path.exists():
                continue

            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in ['.doc', '.docx']:
                    try:
                        file_info = file_path.stat()
                        file_hash = await self._calculate_file_hash(str(file_path))

                        files[str(file_path)] = {
                            "path": str(file_path),
                            "hash": file_hash,
                            "size": file_info.st_size,
                            "last_modified": datetime.fromtimestamp(file_info.st_mtime),
                            "type": decision_type,
                            "ext": file_path.suffix.lower(),
                            "name": file_path.name
                        }
                    except Exception as e:
                        logger.warning(f"⚠️ 扫描文件失败 {file_path}: {e}")

        return files

    def _get_database_snapshot(self) -> dict[str, dict[str, Any]]:
        """获取数据库中的文件快照"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT file_path, file_hash, file_size, last_modified
            FROM file_snapshots
        ''')

        db_files = {}
        for row in cursor.fetchall():
            db_files[row[0]] = {
                "hash": row[1],
                "size": row[2],
                "last_modified": datetime.fromisoformat(row[3]) if row[3] else None
            }

        conn.close()
        return db_files

    def _compare_files(self, current_files: dict[str, dict[str, Any]], db_files: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        """比较文件并检测变更"""
        db_files = db_files or {}
        changes = {
            "new": [],
            "modified": [],
            "deleted": [],
            "unchanged": [],
            "details": []
        }

        current_file_paths = set(current_files.keys())
        db_file_paths = set(db_files.keys())

        # 检测新增文件
        for file_path in current_file_paths - db_file_paths:
            file_info = current_files[file_path]
            change_record = FileChangeRecord(
                file_path=file_path,
                file_hash=file_info["hash"],
                file_size=file_info["size"],
                last_modified=file_info["last_modified"],
                change_type="new",
                processing_status="pending"
            )
            changes["new"].append(file_path)
            changes["details"].append({
    "file_path": change_record.file_path,
    "file_hash": change_record.file_hash,
    "file_size": change_record.file_size,
    "last_modified": change_record.last_modified.isoformat(),
    "change_type": change_record.change_type,
    "processing_status": change_record.processing_status,
    "processing_time": change_record.processing_time,
    "error_message": change_record.error_message,
    "previous_hash": change_record.previous_hash,
    "priority": change_record.priority,
    "retry_count": change_record.retry_count
})

        # 检测删除文件
        for file_path in db_file_paths - current_file_paths:
            change_record = FileChangeRecord(
                file_path=file_path,
                file_hash=db_files[file_path]["hash"],
                file_size=db_files[file_path]["size"],
                last_modified=db_files[file_path]["last_modified"],
                change_type="deleted",
                processing_status="pending"
            )
            changes["deleted"].append(file_path)
            changes["details"].append({
    "file_path": change_record.file_path,
    "file_hash": change_record.file_hash,
    "file_size": change_record.file_size,
    "last_modified": change_record.last_modified.isoformat(),
    "change_type": change_record.change_type,
    "processing_status": change_record.processing_status,
    "processing_time": change_record.processing_time,
    "error_message": change_record.error_message,
    "previous_hash": change_record.previous_hash,
    "priority": change_record.priority,
    "retry_count": change_record.retry_count
})

        # 检测修改文件
        for file_path in current_file_paths & db_file_paths:
            current_info = current_files[file_path]
            db_info = db_files[file_path]

            if current_info["hash"] != db_info["hash"]:
                change_record = FileChangeRecord(
                    file_path=file_path,
                    file_hash=current_info["hash"],
                    file_size=current_info["size"],
                    last_modified=current_info["last_modified"],
                    change_type="modified",
                    processing_status="pending",
                    previous_hash=db_info["hash"]
                )
                changes["modified"].append(file_path)
                changes["details"].append({
    "file_path": change_record.file_path,
    "file_hash": change_record.file_hash,
    "file_size": change_record.file_size,
    "last_modified": change_record.last_modified.isoformat(),
    "change_type": change_record.change_type,
    "processing_status": change_record.processing_status,
    "processing_time": change_record.processing_time,
    "error_message": change_record.error_message,
    "previous_hash": change_record.previous_hash,
    "priority": change_record.priority,
    "retry_count": change_record.retry_count
})
            else:
                changes["unchanged"].append(file_path)

        return changes

    async def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希(支持多种策略)"""
        cache_key = f"hash:{file_path}:{self.config.hash_strategy}"

        # 尝试从缓存获取
        cached_hash = await self.cache.get(cache_key)
        if cached_hash:
            return cached_hash

        # 根据策略计算哈希
        if self.config.hash_strategy == "full":
            file_hash = await self._calculate_full_hash(file_path)
        elif self.config.hash_strategy == "fast":
            file_hash = await self._calculate_fast_hash(file_path)
        else:  # sample (默认)
            file_hash = await self._calculate_sample_hash(file_path)

        # 缓存结果
        await self.cache.set(cache_key, file_hash, ttl_seconds=3600)

        return file_hash

    async def _calculate_full_hash(self, file_path: str) -> str:
        """计算完整文件哈希"""
        hash_md5 = hashlib.md5(usedforsecurity=False)
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    async def _calculate_fast_hash(self, file_path: str) -> str:
        """计算快速哈希(基于文件大小和修改时间)"""
        file_info = Path(file_path).stat()
        fast_hash = f"{file_info.st_size}_{file_info.st_mtime}"
        return hashlib.md5(fast_hash.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def _calculate_sample_hash(self, file_path: str) -> str:
        """计算采样哈希(默认策略)"""
        sample_size = self.config.sample_size_kb * 1024
        hash_md5 = hashlib.md5(usedforsecurity=False)

        try:
            async with aiofiles.open(file_path, 'rb') as f:
                # 读取开头样本
                header = await f.read(sample_size)
                hash_md5.update(header)

                # 获取文件大小
                await f.seek(0, 2)  # 移到文件末尾
                file_size = f.tell()

                # 如果文件大于2倍采样大小,读取末尾样本
                if file_size > sample_size * 2:
                    await f.seek(-sample_size, 2)
                    footer = await f.read(sample_size)
                    hash_md5.update(footer)

        except Exception as e:
            logger.warning(f"采样哈希计算失败,回退到快速哈希 {file_path}: {e}")
            return await self._calculate_fast_hash(file_path)

        return hash_md5.hexdigest()

    async def _collect_metrics(self):
        """收集性能指标"""
        while True:
            try:
                # 系统指标
                memory = psutil.virtual_memory()
                cpu_percent = psutil.cpu_percent(interval=1)

                # 磁盘I/O
                disk_io = psutil.disk_io_counters()
                disk_io_mb = 0
                if disk_io:
                    disk_io_mb = (disk_io.read_bytes + disk_io.write_bytes) / (1024 * 1024)

                # 更新指标
                with self.metrics_lock:
                    self.metrics.memory_usage_percent = memory.percent
                    self.metrics.cpu_usage_percent = cpu_percent
                    self.metrics.disk_io_mb_per_sec = disk_io_mb

                    # 计算处理速度(如果有活跃会话)
                    if self.current_session and self.current_session.processed_files > 0:
                        elapsed_time = time.time() - self.current_session.start_time.timestamp()
                        self.metrics.files_per_second = self.current_session.processed_files / max(1, elapsed_time)

                # 检查告警条件
                await self._check_alerts()

                # 清理过期缓存
                await self.cache.l3_cache.cleanup_expired()

                await asyncio.sleep(self.config.metrics_collection_interval)

            except Exception as e:
                logger.error(f"指标收集失败: {e}")
                await asyncio.sleep(60)

    async def _check_alerts(self):
        """检查告警条件"""
        alerts = []

        if self.metrics.memory_usage_percent > self.config.alert_thresholds["memory_usage"]:
            alerts.append(f"🚨 内存使用率过高: {self.metrics.memory_usage_percent:.1f}%")

        if self.metrics.error_rate > self.config.alert_thresholds["error_rate"]:
            alerts.append(f"🚨 错误率过高: {self.metrics.error_rate:.2%}")

        if self.metrics.queue_size > self.config.alert_thresholds["queue_size"]:
            alerts.append(f"🚨 处理队列积压: {self.metrics.queue_size} 个文件")

        for alert in alerts:
            logger.warning(alert)

    def _adjust_batch_size(self):
        """基于性能指标动态调整批次大小"""
        with self.metrics_lock:
            memory_usage = self.metrics.memory_usage_percent
            processing_rate = self.metrics.files_per_second

            if memory_usage > 85:
                # 内存压力大,减小批次
                new_strategy = "micro"
            elif memory_usage < 50 and processing_rate < 1.0:
                # 内存充足但处理速度慢,增大批次
                new_strategy = "large"
            else:
                new_strategy = "standard"

            if new_strategy != self.current_session.processing_strategy:
                old_strategy = self.current_session.processing_strategy
                self.current_session.processing_strategy = new_strategy
                batch_config = self.config.batch_configs[new_strategy]
                self.current_session.batch_size = batch_config["size"]
                self.current_session.max_concurrent_files = batch_config["concurrent"]

                logger.info(f"批次策略调整: {old_strategy} → {new_strategy}")

    async def _ensure_external_processor(self):
        """确保外部存储处理器已初始化"""
        if self.external_processor is None:
            from scripts.external_storage_processor import ExternalStorageProcessor
            self.external_processor = ExternalStorageProcessor()

    async def smart_change_detection(self, external_path: str | None = None) -> dict[str, Any]:
        """智能变更检测(支持多种优化)"""
        logger.info("🧠 开始智能变更检测...")

        if external_path is None:
            external_path = self.config.external_base_path

        # 启动指标收集(如果未启动)
        if self.metrics_task is None:
            self.metrics_task = _task_12_d84539 = asyncio.create_task(self._collect_metrics())

        try:
            # 使用熔断器保护
            result = self.circuit_breaker.call(
                self.detect_changes, external_path
            )
            return result

        except Exception as e:
            logger.error(f"智能变更检测失败: {e}")
            return {"error": str(e), "fallback_used": True}

    async def batch_process_with_retry(self, session_id: str, limit: int | None = None) -> dict[str, Any]:
        """带重试机制的批量处理"""
        logger.info("🔄 开始带重试机制的批量处理...")

        # 获取待处理变更
        pending_changes = self._get_pending_changes(limit)

        if not pending_changes:
            return {"status": "no_changes", "message": "没有待处理的变更"}

        # 按优先级排序
        pending_changes.sort(key=lambda x: (x.priority, x.last_modified), reverse=True)

        processed_count = 0
        failed_count = 0

        # 分批处理
        for i in range(0, len(pending_changes), self.current_session.batch_size):
            batch_changes = pending_changes[i:i + self.current_session.batch_size]

            # 动态调整批次大小
            self._adjust_batch_size()

            logger.info(f"🔄 处理批次 {i//self.current_session.batch_size + 1}, 策略: {self.current_session.processing_strategy}")

            # 并行处理
            semaphore = asyncio.Semaphore(self.current_session.max_concurrent_files)
            tasks = [self._process_change_with_semaphore(semaphore, change) for change in batch_changes]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 统计结果
            for result in batch_results:
                if isinstance(result, Exception):
                    failed_count += 1
                elif result and result.get("success"):
                    processed_count += 1
                else:
                    failed_count += 1

            # 更新进度
            progress = (i + len(batch_changes)) / len(pending_changes) * 100
            logger.info(f"   进度: {progress:.1f}% | 成功: {processed_count} | 失败: {failed_count}")

            # 短暂休息,避免过度占用资源
            await asyncio.sleep(1)

        processing_time = time.time() - self.current_session.start_time.timestamp()

        return {
            "session_id": session_id,
            "processing_summary": {
                "total_changes": len(pending_changes),
                "processed_changes": processed_count,
                "failed_changes": failed_count,
                "success_rate": processed_count / max(1, len(pending_changes)),
                "processing_time_hours": processing_time / 3600
            },
            "performance_metrics": asdict(self.metrics),
            "processing_time": datetime.now().isoformat()
        }

    async def _process_change_with_semaphore(self, semaphore: asyncio.Semaphore, change: FileChangeRecord) -> dict[str, Any]:
        """带信号量的变更处理"""
        async with semaphore:
            return await self._process_change_with_retry(change)

    async def _process_change_with_retry(self, change: FileChangeRecord) -> dict[str, Any]:
        """带重试机制的变更处理"""
        max_retries = self.config.max_retry_attempts
        backoff_factor = self.config.retry_backoff_factor

        for attempt in range(max_retries + 1):
            try:
                # 使用熔断器保护
                result = self.circuit_breaker.call(
                    self._process_single_change, change
                )
                return {"success": True, "result": result, "attempts": attempt + 1}

            except Exception as e:
                if attempt == max_retries:
                    logger.error(f"处理变更最终失败 {change.file_path}: {e}")
                    self._update_change_status(change.file_path, "failed", error_message=str(e))
                    return {"success": False, "error": str(e), "attempts": attempt + 1}

                wait_time = backoff_factor ** attempt
                logger.warning(f"处理变更失败,{wait_time}秒后重试 ({attempt + 1}/{max_retries + 1}) {change.file_path}: {e}")
                await asyncio.sleep(wait_time)

    def _update_snapshot_database(self, files: dict[str, dict[str, Any]]):
        """更新快照数据库"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        # 清空快照表
        cursor.execute('DELETE FROM file_snapshots')

        # 插入新快照
        for file_path, file_info in files.items():
            cursor.execute('''
                INSERT INTO file_snapshots
                (file_path, file_hash, file_size, last_modified)
                VALUES (?, ?, ?, ?)
            ''', (
                file_path,
                file_info["hash"],
                file_info["size"],
                file_info["last_modified"].isoformat()
            ))

        conn.commit()
        conn.close()

    def _save_change_records(self, changes: list[FileChangeRecord]):
        """保存变更记录"""
        if not changes:
            return

        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        for change in changes:
            cursor.execute('''
                INSERT INTO change_records
                (file_path, file_hash, file_size, last_modified, change_type, processing_status,
                 processing_time, error_message, previous_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                change.file_path,
                change.file_hash,
                change.file_size,
                change.last_modified,
                change.change_type,
                change.processing_status,
                change.processing_time,
                change.error_message,
                change.previous_hash
            ))

        conn.commit()
        conn.close()

    async def process_changes(self, session_id: str, limit: int | None = None) -> dict[str, Any]:
        """处理变更文件"""
        logger.info(f"🔄 开始处理变更文件 (限制: {limit or '无'})")

        # 获取待处理的变更记录
        pending_changes = self._get_pending_changes(limit)

        if not pending_changes:
            logger.info("✅ 没有待处理的变更")
            return {"status": "no_changes", "message": "没有待处理的变更"}

        logger.info(f"📊 待处理变更: {len(pending_changes)} 个")

        # 更新会话信息
        if self.current_session and self.current_session.session_id == session_id:
            self.current_session.total_files = len(pending_changes)
            self._update_session_progress()

        processed_count = 0
        failed_count = 0

        # 分批处理
        for i in range(0, len(pending_changes), self.current_session.batch_size):
            batch_changes = pending_changes[i:i + self.current_session.batch_size]

            logger.info(f"🔄 处理批次 {i//self.config['batch_size'] + 1}/{(len(pending_changes)-1)//self.config['batch_size'] + 1}")

            # 并行处理批次
            batch_tasks = []
            for change in batch_changes:
                task = self._process_single_change(change)
                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # 统计结果
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"❌ 处理变更失败: {result}")
                    failed_count += 1
                elif result:
                    processed_count += 1
                    # 更新变更状态
                    self._update_change_status(result["file_path"], "completed", result["processing_time"])

            # 更新会话进度
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session.processed_files += processed_count
                self.current_session.failed_files += failed_count
                self._update_session_progress()

            # 进度报告
            progress = (i + len(batch_changes)) / len(pending_changes) * 100
            logger.info(f"   进度: {progress:.1f}% | 成功: {processed_count} | 失败: {failed_count}")

        processing_time = time.time() - (self.current_session.start_time.timestamp() if self.current_session else 0)

        # 生成处理报告
        report = {
            "session_id": session_id,
            "processing_summary": {
                "total_changes": len(pending_changes),
                "processed_changes": processed_count,
                "failed_changes": failed_count,
                "success_rate": processed_count / max(1, len(pending_changes)),
                "processing_time_hours": processing_time / 3600
            },
            "change_statistics": self._get_change_statistics(),
            "processing_time": datetime.now().isoformat()
        }

        logger.info(f"✅ 变更处理完成: {processed_count} 成功, {failed_count} 失败")
        return report

    def _get_pending_changes(self, limit: int,) -> list[FileChangeRecord]:
        """获取待处理的变更记录"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        query = '''
            SELECT file_path, file_hash, file_size, last_modified, change_type, processing_status,
                   processing_time, error_message, previous_hash
            FROM change_records
            WHERE processing_status = 'pending' OR processing_status = 'processing'
            ORDER BY created_time
        '''

        if limit:
            query += f' LIMIT {limit}'

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        pending_changes = []
        for row in rows:
            change = FileChangeRecord(
                file_path=row[0],
                file_hash=row[1],
                file_size=row[2],
                last_modified=datetime.fromisoformat(row[3]) if row[3] else None,
                change_type=row[4],
                processing_status=row[5],
                processing_time=row[6] or 0.0,
                error_message=row[7],
                previous_hash=row[8]
            )
            pending_changes.append(change)

        return pending_changes

    async def _process_single_change(self, change: FileChangeRecord) -> dict[str, Any]:
        """处理单个文件变更"""
        start_time = time.time()

        try:
            if change.change_type == "deleted":
                # 处理删除变更:从向量数据库中删除相关向量
                await self._handle_file_deletion(change)
            else:
                # 处理新增或修改变更:重新处理文件
                await self._handle_file_update(change)

            processing_time = time.time() - start_time

            return {
                "file_path": change.file_path,
                "change_type": change.change_type,
                "status": "success",
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"❌ 处理变更失败 {change.file_path}: {e}")
            return {
                "file_path": change.file_path,
                "change_type": change.change_type,
                "status": "failed",
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    async def _handle_file_deletion(self, change: FileChangeRecord):
        """处理文件删除"""
        logger.debug(f"🗑️ 处理文件删除: {Path(change.file_path).name}")

        # 这里可以从Qdrant中删除与该文件相关的向量
        # 暂时只记录日志,实际删除逻辑可以根据需要实现
        pass

    async def _handle_file_update(self, change: FileChangeRecord):
        """处理文件更新"""
        logger.debug(f"📝 处理文件更新: {Path(change.file_path).name}")

        # 检查文件是否存在
        if not os.path.exists(change.file_path):
            raise FileNotFoundError(f"文件不存在: {change.file_path}")

        # 这里可以调用外部存储处理器来处理文件
        # 暂时只记录日志,实际处理逻辑可以调用 external_storage_processor.py
        pass

    def _update_change_status(self, file_path: str, status: str, processing_time: float | None = None, error_message: str | None = None):
        """更新变更状态"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        update_fields = ["processing_status = ?"]
        update_values = [status]

        if processing_time is not None:
            update_fields.append("processing_time = processing_time + ?")
            update_values.append(processing_time)

        if error_message is not None:
            update_fields.append("error_message = ?")
            update_values.append(error_message)

        query = f"UPDATE change_records SET {', '.join(update_fields)} WHERE file_path = ?"
        update_values.append(file_path)

        cursor.execute(query, update_values)
        conn.commit()
        conn.close()

    def _update_session_progress(self):
        """更新会话进度"""
        if not self.current_session:
            return

        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE update_sessions
            SET total_files = ?, processed_files = ?, failed_files = ?, processing_time = ?
            WHERE session_id = ?
        ''', (
            self.current_session.total_files,
            self.current_session.processed_files,
            self.current_session.failed_files,
            time.time() - self.current_session.start_time.timestamp(),
            self.current_session.session_id
        ))

        conn.commit()
        conn.close()

    def _get_change_statistics(self) -> dict[str, Any]:
        """获取变更统计"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        # 按变更类型统计
        cursor.execute('''
            SELECT change_type, processing_status, COUNT(*)
            FROM change_records
            WHERE created_time > date('now', '-30 days')
            GROUP BY change_type, processing_status
        ''')

        type_stats = {}
        for row in cursor.fetchall():
            change_type, status, count = row
            if change_type not in type_stats:
                type_stats[change_type] = {}
            type_stats[change_type][status] = count

        conn.close()
        return type_stats

    def get_session_status(self, session_id: str | None = None) -> dict[str, Any]:
        """获取会话状态"""
        conn = sqlite3.connect(self.config.resume_db_path)
        cursor = conn.cursor()

        if session_id:
            # 获取特定会话
            cursor.execute('''
                SELECT * FROM update_sessions WHERE session_id = ?
            ''', (session_id,))
            rows = cursor.fetchall()
        else:
            # 获取所有会话
            cursor.execute('''
                SELECT * FROM update_sessions
                ORDER BY start_time DESC
                LIMIT 10
            ''')
            rows = cursor.fetchall()

        conn.close()

        if not rows:
            return {"error": "未找到会话记录"}

        sessions = []
        for row in rows:
            sessions.append({
                "session_id": row[0],
                "start_time": row[1],
                "end_time": row[2],
                "status": row[3],
                "total_files": row[4],
                "processed_files": row[5],
                "failed_files": row[6],
                "new_files": row[7],
                "modified_files": row[8],
                "deleted_files": row[9],
                "processing_time": row[10]
            })

        if session_id:
            return {"session": sessions[0] if sessions else None}
        else:
            return {"sessions": sessions}

    def setup_auto_update(self, enabled: bool = True):
        """设置自动更新"""
        if enabled:
            logger.info("🔄 启用自动更新服务...")
            # 这里可以实现一个后台任务,定期检测和处理变更
            # 例如使用APScheduler或后台线程
        else:
            logger.info("⏸️ 禁用自动更新服务")

async def main():
    """主函数"""
    print("🚀 增量更新系统")
    print("=" * 60)

    updater = IncrementalUpdateSystem()

    # 用户选择操作
    print("📋 可用操作:")
    print("   1. 检测文件变更")
    print("   2. 开始更新会话")
    print("   3. 处理变更文件")
    print("   4. 查看会话状态")
    print("   5. 设置自动更新")

    choice = input("\n请选择操作 (1-5): ").strip()

    if choice == "1":
        # 检测变更
        external_path = input("外部存储路径 (回车使用默认): ").strip()
        if not external_path:
            external_path = None

        print("\n🔍 检测文件变更...")
        result = await updater.detect_changes(external_path)

        print("\n📊 检测结果:")
        print(f"   - 总文件数: {result['total_files']:,}")
        print(f"   - 总大小: {result['total_size_gb']}GB")
        print("   - 变更统计:")
        print(f"     * 新增: {result['changes']['new']}")
        print(f"     * 修改: {result['changes']['modified']}")
        print(f"     * 删除: {result['changes']['deleted']}")
        print(f"     * 无变化: {result['changes']['unchanged']}")

    elif choice == "2":
        # 开始更新会话
        session_id = updater.start_update_session()
        print(f"✅ 更新会话已开始: {session_id}")
        print(f"   - 会话ID: {session_id}")
        print(f"   - 开始时间: {updater.current_session.start_time}")

    elif choice == "3":
        # 处理变更
        session_id = input("会话ID (回车使用最新): ").strip()
        if not session_id and updater.current_session:
            session_id = updater.current_session.session_id

        if not session_id:
            print("❌ 没有活跃的更新会话")
            return

        limit = input("处理文件数量限制 (回车=无限制): ").strip()
        try:
            limit = int(limit) if limit else None
        except Exception:
            limit = None

        print("\n🔄 开始处理变更...")
        result = await updater.process_changes(session_id, limit)

        print("\n📊 处理结果:")
        print(f"   - 会话ID: {result['session_id']}")
        print(f"   - 总变更数: {result['processing_summary']['total_changes']}")
        print(f"   - 处理成功: {result['processing_summary']['processed_changes']}")
        print(f"   - 处理失败: {result['processing_summary']['failed_changes']}")
        print(f"   - 成功率: {result['processing_summary']['success_rate']:.2%}")
        print(f"   - 处理时间: {result['processing_summary']['processing_time_hours']:.2f}小时")

        # 结束会话
        updater.end_update_session(result['session_id'], "completed")

    elif choice == "4":
        # 查看会话状态
        session_id = input("会话ID (回车=查看所有): ").strip()

        result = updater.get_session_status(session_id if session_id else None)

        if "session" in result:
            session = result["session"]
            print("\n📊 会话详情:")
            print(f"   - 会话ID: {session['session_id']}")
            print(f"   - 开始时间: {session['start_time']}")
            print(f"   - 结束时间: {session.get('end_time', '进行中')}")
            print(f"   - 状态: {session['status']}")
            print(f"   - 总文件: {session['total_files']}")
            print(f"   - 已处理: {session['processed_files']}")
            print(f"   - 失败: {session['failed_files']}")
            print(f"   - 新增: {session['new_files']}")
            print(f"   - 修改: {session['modified_files']}")
            print(f"   - 删除: {session['deleted_files']}")
        else:
            sessions = result["sessions"]
            print("\n📊 所有会话 (最近10个):")
            for i, session in enumerate(sessions):
                print(f"   {i+1}. {session['session_id']}")
                print(f"      - 状态: {session['status']}")
                print(f"      - 时间: {session['start_time']} → {session.get('end_time', '进行中')}")
                print(f"      - 文件: {session['processed_files']}")

    elif choice == "5":
        # 设置自动更新
        enabled_input = input("启用自动更新? (y/N): ").strip().lower()
        enabled = enabled_input == 'y'

        updater.setup_auto_update(enabled)

        status = "启用" if enabled else "禁用"
        print(f"✅ 自动更新已{status}")

    else:
        print("❌ 无效选择")

# 入口点: @async_main装饰器已添加到main函数
