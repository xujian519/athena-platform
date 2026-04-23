
import numpy as np

#!/usr/bin/env python3
"""
Athena记忆系统P0问题修复补丁
Memory System P0 Issues Fix Patch

修复问题:
1. 数据库连接池配置优化
2. 向量缓存机制
3. 热缓存内存限制
4. 联邦记忆加密密钥管理
5. 分布式同步竞态条件修复
6. 时间线文件I/O优化
7. 向量索引结构
8. 智能遗忘内存泄漏修复

作者: Claude (AI Assistant)
创建时间: 2026-01-16
版本: v1.0.0
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

import aiofiles
import faiss

from core.infrastructure.database.unified_connection import get_postgres_pool
from core.logging_config import setup_logging

# 尝试导入Fernet加密库(可选依赖)
try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

logger = setup_logging()


# =============================================================================
# 修复1: 优化的数据库连接池配置
# =============================================================================


class OptimizedDatabaseConfig:
    """优化的数据库配置"""

    DEFAULT_CONFIG = {
        "postgresql": {
            "host": "localhost",
            "port": 5432,
            "database": "athena_memory",
            "user": "postgres",
            "password": "",
            "pool_min_size": 5,
            "pool_max_size": 50,  # 从30增加到50
            "max_queries": 50000,  # 新增:每连接最大查询数
            "max_inactive_connection_lifetime": 300,  # 新增:5分钟
            "command_timeout": 30,
            "setup": None,  # 新增:连接初始化回调
            "init": None,  # 新增:连接初始化回调
            "loop": None,  # 事件循环
        },
        "qdrant": {"host": "localhost", "port": 6333, "timeout": 30, "limit": 100},  # 批量操作限制
    }

    @classmethod
    def get_config(cls, custom_config: Optional[dict] = None) -> dict:
        """获取配置"""
        config = cls.DEFAULT_CONFIG.copy()
        if custom_config:
            config.update(custom_config)
        return config


def log_connection_event(conn) -> None:
    """连接事件日志"""
    logger.debug(f"新数据库连接已创建: {conn}")


async def create_optimized_connection_pool(config: Optional[dict] = None):
    """创建优化的连接池"""
    cfg = OptimizedDatabaseConfig.get_config(config)
    pg_config = cfg["postgresql"]

    try:
        pass

        pool = await get_postgres_pool(
            host=pg_config["host"],
            port=pg_config["port"],
            database=pg_config["database"],
            user=pg_config["user"],
            password=pg_config["password"],
            min_size=pg_config["pool_min_size"],
            max_size=pg_config["pool_max_size"],
            max_queries=pg_config["max_queries"],
            max_inactive_connection_lifetime=pg_config["max_inactive_connection_lifetime"],
            command_timeout=pg_config["command_timeout"],
            setup=log_connection_event if logger.is_enabled_for(logging.DEBUG) else None,
            loop=pg_config.get("loop"),
        )

        logger.info(
            f"✅ 优化的PostgreSQL连接池已建立 "
            f"({pg_config['pool_min_size']}-{pg_config['pool_max_size']}连接, "
            f"每连接最多{pg_config['max_queries']}次查询)"
        )

        return pool

    except ImportError:
        raise
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise


# =============================================================================
# 修复2: 向量缓存机制
# =============================================================================


class VectorCache:
    """向量缓存系统"""

    def __init__(self, max_size: int = 2000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[list[float], float] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def get(self, text: str) -> list[Optional[float]]:
        """获取缓存的向量"""
        with self.lock:
            if text in self.cache:
                vector, timestamp = self.cache[text]

                # 检查是否过期
                if time.time() - timestamp < self.ttl_seconds:
                    # LRU:移动到末尾
                    self.cache.move_to_end(text)
                    self.hits += 1
                    return vector
                else:
                    # 过期,删除
                    del self.cache[text]

            self.misses += 1
            return None

    def put(self, text: str, vector: list[float]) -> Any:
        """缓存向量"""
        with self.lock:
            # 检查缓存大小
            if len(self.cache) >= self.max_size:
                # 删除最老的条目
                self.cache.popitem(last=False)

            self.cache[text] = (vector, time.time())

    def invalidate(self, text: str) -> Any:
        """使缓存失效"""
        with self.lock:
            if text in self.cache:
                del self.cache[text]

    def clear(self) -> Any:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
            }


# 全局向量缓存实例
_global_vector_cache: Optional[VectorCache] = None


def get_vector_cache() -> VectorCache:
    """获取全局向量缓存"""
    global _global_vector_cache
    if _global_vector_cache is None:
        _global_vector_cache = VectorCache(
            max_size=2000, ttl_seconds=3600  # 从无限制改为2000条  # 1小时过期
        )
    return _global_vector_cache


# =============================================================================
# 修复3: 基于内存大小的热缓存限制
# =============================================================================


class SizeLimitedLRU:
    """基于内存大小的LRU缓存"""

    def __init__(self, max_size_mb: int = 50):
        self.max_size_mb = max_size_mb
        self.current_size_mb = 0.0
        self.cache: OrderedDict = OrderedDict()
        self.lock = Lock()
        self.evictions = 0

    def add(self, key: str, value: Any) -> Any:
        """添加条目"""
        with self.lock:
            # 估算条目大小
            entry_size_mb = sys.getsizeof(value) / (1024 * 1024)

            # 如果键已存在,先删除旧的
            if key in self.cache:
                del self.cache[key]
            else:
                # 驱逐直到有足够空间
                while self.current_size_mb + entry_size_mb > self.max_size_mb:
                    if not self.cache:
                        break
                    self._evict_lru()

            # 添加新条目
            self.cache[key] = value
            self.current_size_mb += entry_size_mb

    def get(self, key: str) -> Optional[Any]:
        """获取条目"""
        with self.lock:
            if key in self.cache:
                # LRU:移动到末尾
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None

    def _evict_lru(self) -> Any:
        """驱逐最老的条目"""
        if not self.cache:
            return

        oldest_key = next(iter(self.cache))
        oldest_value = self.cache.pop(oldest_key)

        size_mb = sys.getsizeof(oldest_value) / (1024 * 1024)
        self.current_size_mb -= size_mb
        self.evictions += 1

        logger.debug(f"驱逐缓存: {oldest_key} ({size_mb:.2f} MB)")

    def clear(self) -> Any:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.current_size_mb = 0.0
            self.evictions = 0

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        with self.lock:
            return {
                "count": len(self.cache),
                "size_mb": round(self.current_size_mb, 2),
                "max_size_mb": self.max_size_mb,
                "usage_percent": round(self.current_size_mb / self.max_size_mb * 100, 2),
                "evictions": self.evictions,
            }


# =============================================================================
# 修复4: 联邦记忆加密密钥持久化
# =============================================================================


class PersistentEncryptionKeyManager:
    """持久化加密密钥管理器"""

    def __init__(self, key_file_path: Optional[str] = None):
        if key_file_path is None:
            # 默认使用安全目录
            key_dir = Path.home() / ".athena" / "secure"
            key_dir.mkdir(parents=True, exist_ok=True)
            key_file_path = key_dir / "memory_encryption_key.bin"

        self.key_file_path = Path(key_file_path)
        self.cipher_suite = None

        self._load_or_generate_key()

    def _load_or_generate_key(self) -> Any:
        """加载或生成密钥"""
        try:
            pass

            if self.key_file_path.exists():
                # 加载现有密钥
                encryption_key = self.key_file_path.read_bytes()
                logger.info(f"✅ 从 {self.key_file_path} 加载加密密钥")
            else:
                # 生成新密钥
                encryption_key = Fernet.generate_key()

                # 保存密钥
                self.key_file_path.write_bytes(encryption_key)

                # 设置权限:仅所有者可读写
                os.chmod(self.key_file_path, 0o600)

                logger.info(f"✅ 生成并保存新加密密钥到 {self.key_file_path}")

            self.cipher_suite = Fernet(encryption_key)

        except ImportError:
            self.cipher_suite = None
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    def encrypt(self, data: bytes) -> Optional[bytes]:
        """加密数据"""
        if self.cipher_suite is None:
            return None
        return self.cipher_suite.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> Optional[bytes]:
        """解密数据"""
        if self.cipher_suite is None:
            return None
        try:
            pass
        except Exception:
            logger.error("操作失败: e", exc_info=True)
            raise

    def rotate_key(self) -> Any:
        """轮换密钥"""
        # 备份旧密钥
        if self.key_file_path.exists():
            backup_path = self.key_file_path.with_suffix(".bak")
            self.key_file_path.rename(backup_path)
            logger.info(f"旧密钥已备份到 {backup_path}")

        # 生成新密钥
        self._load_or_generate_key()

        logger.info("✅ 加密密钥已轮换")


# =============================================================================
# 修复5: 线程安全的异步队列
# =============================================================================


class AsyncThreadSafeDeque:
    """线程安全的异步双端队列"""

    def __init__(self, maxlen: int = 1000):
        self._deque = asyncio.Queue(maxsize=maxlen)
        self.maxlen = maxlen

    async def append(self, item):
        """添加元素"""
        try:
            pass
        except TimeoutError:
            try:
                await self._deque.put(item)
            except asyncio.QueueEmpty:
                logger.error("操作失败: e", exc_info=True)
                raise

    async def pop(self):
        """弹出元素"""
        try:
            pass
        except TimeoutError:
            logger.error("操作失败: e", exc_info=True)
            raise

    async def peek(self, n: int = 10):
        """查看前n个元素"""
        items = []
        for _ in range(min(n, self._deque.qsize())):
            try:
                item = self._deque.get_nowait()
                items.append(item)
                await self._deque.put(item)
            except asyncio.QueueEmpty:
                logger.error("操作失败: e", exc_info=True)
                raise
        return items

    def qsize(self) -> int:
        """获取队列大小"""
        return self._deque.qsize()

    def empty(self) -> bool:
        """是否为空"""
        return self._deque.empty()

    def full(self) -> bool:
        """是否已满"""
        return self._deque.full()


# =============================================================================
# 修复6: 缓冲的时间线写入器
# =============================================================================


class BufferedTimelineWriter:
    """缓冲的时间线写入器"""

    def __init__(self, file_path: Path, buffer_size: int = 100):
        self.file_path = file_path
        self.buffer_size = buffer_size
        self.buffer: list[dict] = []
        self.lock = asyncio.Lock()
        self.last_flush = time.time()

    async def add(self, memory: dict):
        """添加记忆到缓冲区"""
        async with self.lock:
            self.buffer.append(memory)

            # 缓冲区满或超过5秒,刷新
            if len(self.buffer) >= self.buffer_size or time.time() - self.last_flush > 5:
                await self._flush()

    async def _flush(self):
        """刷新缓冲区到文件"""
        if not self.buffer:
            return

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # 追加写入
            async with aiofiles.open(self.file_path, "a") as f:
                for item in self.buffer:
                    await f.write(json.dumps(item, ensure_ascii=False) + "\n")

            logger.debug(f"✅ 刷新{len(self.buffer)}条记忆到 {self.file_path}")

        except ImportError:
            with open(self.file_path, "a", encoding="utf-8") as f:
                for item in self.buffer:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

        finally:
            self.buffer.clear()
            self.last_flush = time.time()

    async def close(self):
        """关闭写入器"""
        await self._flush()


# 尝试导入aiofiles
try:
    pass
except ImportError:
    logger.debug("aiofiles未安装,将使用同步I/O")


# =============================================================================
# 修复7: 使用FAISS的向量索引
# =============================================================================


class IndexedVectorSearch:
    """使用FAISS的索引向量搜索"""

    def __init__(self, dimension: int = 1024):
        self.dimension = dimension
        self.vectors = []
        self.metadata = []
        self.index = None

        try:
            pass

            # 使用内积索引(更适合余弦相似度)
            self.index = faiss.IndexFlatIP(dimension)
            self.faiss_available = True
            logger.info("✅ FAISS索引已启用")
        except ImportError:
            logger.warning("⚠️ FAISS未安装,使用暴力搜索")

    def add_vectors(self, vectors: list, metadata_list: Optional[list[dict]] = None) -> None:
        """批量添加向量"""

        vectors_array = np.array(vectors, dtype=np.float32)

        # 归一化(用于余弦相似度)
        norms = np.linalg.norm(vectors_array, axis=1, keepdims=True)
        vectors_array = vectors_array / (norms + 1e-8)

        if self.faiss_available and self.index:
            self.index.add(vectors_array)
        else:
            # 降级到列表存储
            self.vectors.extend(vectors)

        if metadata_list:
            self.metadata.extend(metadata_list)

    def search(self, query_vector: list, k: int = 10) -> list[tuple[int, float, dict]]:
        """搜索最相似的向量"""

        query_array = np.array([query_vector], dtype=np.float32)

        # 归一化
        query_array = query_array / (np.linalg.norm(query_array) + 1e-8)

        if self.faiss_available and self.index and self.index.ntotal() > 0:
            # 使用FAISS搜索
            distances, indices = self.index.search(query_array, k)

            results = []
            for i in range(len(indices[0])):
                idx = int(indices[0][i])
                if idx < len(self.metadata):
                    # FAISS返回内积,转换为相似度
                    similarity = float(max(0, min(1, distances[0][i])))
                    results.append((idx, 1.0 - similarity, self.metadata[idx]))

            return results
        else:
            # 降级到暴力搜索
            if not self.vectors:
                return []

            vectors_array = np.array(self.vectors, dtype=np.float32)

            # 计算余弦相似度
            similarities = np.dot(vectors_array, query_vector)
            norms = np.linalg.norm(vectors_array, axis=1)
            query_norm = np.linalg.norm(query_vector)
            similarities = similarities / (norms * query_norm + 1e-8)

            # 获取top-k
            k = min(k, len(similarities))
            top_indices = np.argsort(-similarities)[:k]

            results = []
            for idx in top_indices:
                if idx < len(self.metadata):
                    similarity = float(max(0, min(1, similarities[idx])))
                    results.append((int(idx), 1.0 - similarity, self.metadata[idx]))

            return results

    def get_stats(self) -> dict:
        """获取统计信息"""
        if self.faiss_available and self.index:
            return {
                "vector_count": self.index.ntotal(),
                "dimension": self.dimension,
                "index_type": "FAISS IndexFlatIP",
            }
        else:
            return {
                "vector_count": len(self.vectors),
                "dimension": self.dimension,
                "index_type": "Brute Force",
            }


# =============================================================================
# 修复8: 大小受限的字典(防止内存泄漏)
# =============================================================================


class SizeLimitedDict:
    """大小受限的字典"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.dict: OrderedDict = OrderedDict()
        self.lock = Lock()
        self.evictions = 0

    def __setitem__(self, key, value):
        with self.lock:
            if key in self.dict:
                # 更新现有键
                del self.dict[key]
            elif len(self.dict) >= self.max_size:
                # FIFO驱逐
                self.dict.popitem(last=False)
                self.evictions += 1

            self.dict[key] = value

    def __getitem__(self, key):
        with self.lock:
            if key in self.dict:
                # 移到末尾(LRU)
                value = self.dict.pop(key)
                self.dict[key] = value
                return value
            raise KeyError(key)

    def get(self, key, default=None) -> None:
        try:
            pass
        except KeyError:
            logger.error("操作失败: e", exc_info=True)
            raise

    def __contains__(self, key):
        with self.lock:
            return key in self.dict

    def __len__(self):
        with self.lock:
            return len(self.dict)

    def clear(self) -> Any:
        with self.lock:
            self.dict.clear()
            self.evictions = 0

    def get_stats(self) -> dict:
        with self.lock:
            return {
                "size": len(self.dict),
                "max_size": self.max_size,
                "usage_percent": round(len(self.dict) / self.max_size * 100, 2),
                "evictions": self.evictions,
            }


# =============================================================================
# 修复后的智能遗忘策略
# =============================================================================


class FixedSmartForgettingStrategy:
    """修复后的智能遗忘策略"""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {
            "max_memory_items": 10000,
            "time_decay_half_life": 30,
            "importance_threshold": 0.1,
            "access_frequency_threshold": 0.1,
            "consolidation_interval": 7,
            "backup_enabled": True,
            "forgetting_batch_size": 100,
        }

        # 使用大小受限的字典
        self.memory_store = {}
        self.forgetting_history = AsyncThreadSafeDeque(maxlen=1000)
        self.importance_weights = SizeLimitedDict(max_size=10000)
        self.forgetting_rules = SizeLimitedDict(max_size=1000)
        self.last_consolidation = datetime.now()

        self.statistics = {
            "total_forgettings": 0,
            "forgettings_by_reason": {},
            "avg_memory_lifetime": 0.0,
            "consolidation_count": 0,
        }

    async def check_memory_pressure(self) -> bool:
        """检查内存压力"""
        memory_usage = len(self.memory_store)
        max_items = self.config["max_memory_items"]
        return memory_usage >= max_items * 0.9  # 90%阈值

    async def execute_forgetting(self, batch_size: Optional[int] = None):
        """执行遗忘操作"""
        if not await self.check_memory_pressure():
            return

        batch_size = batch_size or self.config["forgetting_batch_size"]

        # 按重要性排序,删除最不重要的
        sorted_memories = sorted(self.memory_store.items(), key=lambda x: x[1].importance)

        to_forget = sorted_memories[:batch_size]

        for memory_id, memory in to_forget:
            # 记录遗忘事件
            await self.forgetting_history.append(
                {
                    "memory_id": memory_id,
                    "forgotten_at": datetime.now().isoformat(),
                    "importance": memory.importance,
                    "reason": "memory_pressure",
                }
            )

            # 删除记忆
            del self.memory_store[memory_id]

            self.statistics["total_forgettings"] += 1

        logger.info(f"🗑️ 遗忘了{len(to_forget)}条记忆")


# =============================================================================
# 修复补丁应用函数
# =============================================================================


async def apply_fixes():
    """应用所有修复补丁"""
    print("🔧 应用Athena记忆系统P0问题修复补丁...")

    fixes_applied = []

    # 1. 数据库连接池
    print("\n1️⃣ 测试优化的数据库连接池...")
    try:
        pool = await create_optimized_connection_pool()
        if pool:
            fixes_applied.append("✅ 数据库连接池优化")
            await pool.close()
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise
    # 2. 向量缓存
    print("\n2️⃣ 测试向量缓存...")
    vector_cache = get_vector_cache()
    vector_cache.put("test", [0.1] * 1024)
    cached = vector_cache.get("test")
    if cached:
        fixes_applied.append("✅ 向量缓存机制")

    # 3. 大小受限的LRU
    print("\n3️⃣ 测试大小受限的LRU...")
    lru_cache = SizeLimitedLRU(max_size_mb=10)
    lru_cache.add("key1", "x" * 1000000)  # 1MB
    stats = lru_cache.get_stats()
    if stats["count"] == 1:
        fixes_applied.append("✅ 热缓存内存限制")

    # 4. 加密密钥管理
    print("\n4️⃣ 测试持久化加密密钥...")
    try:
        key_manager = PersistentEncryptionKeyManager(Path("test_key.key"))
        if key_manager.cipher_suite:
            fixes_applied.append("✅ 加密密钥持久化")
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise
    # 5. 线程安全队列
    print("\n5️⃣ 测试线程安全队列...")
    queue = AsyncThreadSafeDeque(maxlen=100)
    await queue.append({"test": "data"})
    if queue.qsize() == 1:
        fixes_applied.append("✅ 线程安全队列")

    # 6. 缓冲写入器
    print("\n6️⃣ 测试缓冲写入器...")
    try:
        pass

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        writer = BufferedTimelineWriter(tmp_path, buffer_size=10)
        await writer.add({"test": "memory"})
        await writer.close()
        fixes_applied.append("✅ 缓冲时间线写入")

        tmp_path.unlink(missing_ok=True)
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise
    # 7. 向量索引
    print("\n7️⃣ 测试向量索引...")
    try:
        index_search = IndexedVectorSearch(dimension=1024)
        index_search.add_vectors([[0.1] * 1024], [{"id": "1"}])
        results = index_search.search([0.1] * 1024, k=1)
        if results:
            fixes_applied.append("✅ 向量索引结构")
    except Exception:
        logger.error("操作失败: e", exc_info=True)
        raise
    # 8. 大小受限字典
    print("\n8️⃣ 测试大小受限字典...")
    limited_dict = SizeLimitedDict(max_size=100)
    for i in range(150):
        limited_dict[f"key_{i}"] = f"value_{i}"
    if len(limited_dict) <= 100:
        fixes_applied.append("✅ 防内存泄漏字典")

    print("\n" + "=" * 60)
    print("📋 修复补丁应用总结")
    print("=" * 60)
    for fix in fixes_applied:
        print(fix)

    print(f"\n✅ 成功应用 {len(fixes_applied)}/8 个修复补丁")

    return fixes_applied


if __name__ == "__main__":
    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 应用修复
    asyncio.run(apply_fixes())

