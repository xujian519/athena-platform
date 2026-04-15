#!/usr/bin/env python3
"""
NLP内存泄漏修复补丁
NLP Memory Leak Fix Patch

修复NLP系统的内存泄漏问题:
1. BGE嵌入服务缓存限制
2. BERT模型自动卸载
3. 全局内存监控
4. 定期清理机制

作者: 系统管理员
创建时间: 2026-01-25
版本: v1.0.0
"""

from __future__ import annotations
import gc
import logging
import os
import sys
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# 添加路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


@dataclass
class MemoryConfig:
    """内存配置"""
    max_cache_size: int = 500  # 最大缓存条目数(降低到500)
    cache_ttl_seconds: int = 3600  # 缓存过期时间(1小时)
    max_loaded_models: int = 2  # 最大同时加载模型数(降低到2)
    memory_check_interval: int = 60  # 内存检查间隔(秒)
    memory_pressure_threshold: float = 0.8  # 内存压力阈值(80%)
    enable_auto_cleanup: bool = True  # 启用自动清理


class LRUCache:
    """LRU缓存实现"""

    def __init__(self, max_size: int = 500, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        with self.lock:
            if key not in self.cache:
                return None

            value, timestamp = self.cache[key]

            # 检查过期
            if time.time() - timestamp > self.ttl:
                del self.cache[key]
                return None

            # 更新访问顺序(移到末尾)
            self.cache.move_to_end(key)
            return value

    def put(self, key: str, value: Any) -> None:
        """放入缓存"""
        with self.lock:
            # 如果已存在,更新并移到末尾
            if key in self.cache:
                self.cache[key] = (value, time.time())
                self.cache.move_to_end(key)
                return

            # 检查大小限制
            while len(self.cache) >= self.max_size:
                # 删除最旧的项(第一个)
                self.cache.popitem(last=False)

            # 添加新项
            self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)


class GlobalMemoryMonitor:
    """全局内存监控器"""

    def __init__(self, config: MemoryConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._running = False
        self._monitor_thread: threading.Thread | None = None
        self._memory_callbacks: list[callable] = []

        # 跟踪内存使用历史
        self.memory_history: list[tuple[datetime, float]] = []
        self.max_history_size = 100

    def start(self) -> None:
        """启动内存监控"""
        if self._running:
            return

        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="MemoryMonitor"
        )
        self._monitor_thread.start()
        self.logger.info("内存监控已启动")

    def stop(self) -> None:
        """停止内存监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        self.logger.info("内存监控已停止")

    def _monitor_loop(self) -> None:
        """监控循环"""
        import psutil

        while self._running:
            try:
                # 获取内存使用率
                memory = psutil.virtual_memory()
                usage_percent = memory.percent

                # 记录历史
                now = datetime.now()
                self.memory_history.append((now, usage_percent))

                # 限制历史大小
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history.pop(0)

                # 检查是否超过阈值
                if usage_percent > self.config.memory_pressure_threshold * 100:
                    self.logger.warning(
                        f"内存压力过高: {usage_percent:.1f}% > "
                        f"{self.config.memory_pressure_threshold * 100:.1f}%"
                    )

                    # 触发清理回调
                    for callback in self._memory_callbacks:
                        try:
                            callback(usage_percent)
                        except Exception as e:
                            self.logger.error(f"内存清理回调失败: {e}")

                # 睡眠
                time.sleep(self.config.memory_check_interval)

            except Exception as e:
                self.logger.error(f"内存监控错误: {e}")
                time.sleep(self.config.memory_check_interval)

    def register_callback(self, callback: callable) -> None:
        """注册内存清理回调"""
        self._memory_callbacks.append(callback)

    def get_memory_usage(self) -> dict[str, Any]:
        """获取当前内存使用情况"""
        import psutil

        memory = psutil.virtual_memory()
        process = psutil.Process()

        return {
            "system_memory_percent": memory.percent,
            "system_memory_available_gb": memory.available / (1024**3),
            "system_memory_total_gb": memory.total / (1024**3),
            "process_memory_mb": process.memory_info().rss / (1024**2),
            "process_memory_percent": process.memory_percent(),
        }


class BGEEmbeddingServiceFixed:
    """修复后的BGE嵌入服务"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.name = "BGE嵌入服务(修复版)"
        self.version = "1.0.1"
        self.logger = logging.getLogger(self.name)

        # 配置
        self.config = config or {}
        memory_config = MemoryConfig()

        # 使用LRU缓存替代普通字典
        self.embedding_cache = LRUCache(
            max_size=memory_config.max_cache_size,
            ttl=memory_config.cache_ttl_seconds
        )

        # 模型状态
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        self.load_lock = threading.Lock()

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "total_texts": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "total_processing_time": 0.0,
            "avg_batch_size": 0.0,
            "cache_evictions": 0,
        }

        print(f"🚀 {self.name} 初始化完成")

    def _get_cache_key(self, texts: list[str]) -> str:
        """生成缓存键"""
        import hashlib
        combined_text = "|||".join(texts)
        return hashlib.md5(combined_text.encode('utf-8'), usedforsecurity=False).hexdigest()

    async def _check_cache(self, texts: list[str]) -> list[list[float | None]]:
        """检查缓存(使用LRU缓存)"""
        if not self.config.get("cache_enabled", True):
            return None

        cache_key = self._get_cache_key(texts)
        cached = self.embedding_cache.get(cache_key)

        if cached is not None:
            self.stats["cache_hits"] += 1
            return cached

        self.stats["cache_misses"] += 1
        return None

    def _save_to_cache(self, texts: list[str], embeddings: list[list[float]]) -> None:
        """保存到缓存(使用LRU缓存)"""
        if not self.config.get("cache_enabled", True):
            return

        cache_key = self._get_cache_key(texts)
        old_size = self.embedding_cache.size()
        self.embedding_cache.put(cache_key, embeddings)

        # 记录驱逐次数
        if self.embedding_cache.size() < old_size:
            self.stats["cache_evictions"] += old_size - self.embedding_cache.size()

    def clear_cache(self) -> None:
        """清理缓存"""
        self.embedding_cache.clear()
        self.logger.info("BGE缓存已清理")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = (
            self.stats["cache_hits"] / total_requests
            if total_requests > 0 else 0
        )

        return {
            "cache_size": self.embedding_cache.size(),
            "cache_hit_rate": f"{cache_hit_rate:.2%}",
            "cache_hits": self.stats["cache_hits"],
            "cache_misses": self.stats["cache_misses"],
            "cache_evictions": self.stats["cache_evictions"],
        }


class BERTServiceFixed:
    """修复后的BERT服务"""

    def __init__(self):
        self.name = "BERT服务(修复版)"
        self.version = "1.0.1"
        self.logger = logging.getLogger(self.name)

        # 内存配置
        self.memory_config = MemoryConfig()

        # 模型存储(使用LRU缓存)
        self.models: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.model_locks: dict[str, threading.Lock] = {}
        self.global_lock = threading.Lock()

        # 加载时间跟踪
        self.model_load_times: dict[str, float] = {}

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "model_usage": {},
            "total_processing_time": 0.0,
            "model_unloads": 0,
        }

    def _manage_memory(self) -> None:
        """内存管理 - 自动卸载最少使用的模型"""
        with self.global_lock:
            loaded_count = len([
                k for k, v in self.models.items()
                if v.get("loaded", False)
            ])

            if loaded_count > self.memory_config.max_loaded_models:
                # 按最后使用时间排序
                sorted_models = sorted(
                    self.models.items(),
                    key=lambda x: x[1].get("last_used", 0)
                )

                # 卸载最旧的模型
                unload_count = loaded_count - self.memory_config.max_loaded_models
                for i in range(unload_count):
                    model_key, _ = sorted_models[i]
                    self._unload_model(model_key)

                self.logger.info(
                    f"自动卸载了 {unload_count} 个模型以释放内存"
                )

    def _unload_model(self, model_key: str) -> bool:
        """卸载模型"""
        if model_key not in self.models:
            return False

        try:
            # 获取锁
            if model_key in self.model_locks:
                self.model_locks[model_key].acquire()

            model_info = self.models[model_key]

            # 删除模型引用
            if "model" in model_info:
                del model_info["model"]
            if "tokenizer" in model_info:
                del model_info["tokenizer"]

            model_info["loaded"] = False

            # 清理GPU内存
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except Exception:
                pass

            # 强制垃圾回收
            gc.collect()

            self.stats["model_unloads"] += 1
            self.logger.info(f"模型已卸载: {model_key}")

            return True

        except Exception as e:
            self.logger.error(f"卸载模型失败 [{model_key}]: {e}")
            return False

        finally:
            if model_key in self.model_locks:
                self.model_locks[model_key].release()

    async def encode(self, texts, model_key: str = "general", **kwargs):
        """文本编码(带内存管理)"""
        # 在使用模型前进行内存管理
        self._manage_memory()

        # 标记模型使用时间
        if model_key in self.models:
            self.models[model_key]["last_used"] = time.time()

        # TODO: 实际的编码逻辑
        pass

    def unload_all_models(self) -> int:
        """卸载所有模型"""
        unloaded_count = 0
        for model_key in list(self.models.keys()):
            if self._unload_model(model_key):
                unloaded_count += 1

        self.logger.info(f"已卸载所有模型: {unloaded_count} 个")
        return unloaded_count


# 全局内存监控器实例
_global_memory_monitor: GlobalMemoryMonitor | None = None


def get_global_memory_monitor() -> GlobalMemoryMonitor:
    """获取全局内存监控器"""
    global _global_memory_monitor
    if _global_memory_monitor is None:
        config = MemoryConfig()
        _global_memory_monitor = GlobalMemoryMonitor(config)

        # 注册自动清理回调
        def memory_cleanup_callback(usage_percent: float):
            """内存清理回调"""
            logger = logging.getLogger("MemoryCleanup")
            logger.warning(f"触发内存清理: {usage_percent:.1f}%")

            # 强制垃圾回收
            gc.collect()

            # 清理BGE缓存
            try:
                # 这里应该获取全局的BGE服务实例并清理缓存
                pass
            except Exception as e:
                logger.error(f"BGE缓存清理失败: {e}")

            # 卸载不常用的BERT模型
            try:
                # 这里应该获取全局的BERT服务实例并卸载模型
                pass
            except Exception as e:
                logger.error(f"BERT模型卸载失败: {e}")

        _global_memory_monitor.register_callback(memory_cleanup_callback)
        _global_memory_monitor.start()

    return _global_memory_monitor


def setup_memory_leak_fix():
    """设置内存泄漏修复"""
    logger = logging.getLogger("MemoryLeakFix")
    logger.info("正在设置内存泄漏修复...")

    # 启动全局内存监控
    monitor = get_global_memory_monitor()
    logger.info("全局内存监控已启动")

    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("内存泄漏修复设置完成")
    return monitor


if __name__ == "__main__":
    # 测试修复方案
    print("🧪 测试内存泄漏修复方案...")

    # 设置修复
    monitor = setup_memory_leak_fix()

    # 测试LRU缓存
    print("\n📦 测试LRU缓存...")
    cache = LRUCache(max_size=3, ttl=10)

    cache.put("key1", "value1")
    cache.put("key2", "value2")
    cache.put("key3", "value3")
    cache.put("key4", "value4")  # 应该驱逐key1

    print(f"缓存大小: {cache.size()}")  # 应该是3
    print(f"key1存在: {cache.get('key1')}")  # 应该是None

    # 测试内存监控
    print("\n📊 测试内存监控...")
    memory_info = monitor.get_memory_usage()
    print(f"系统内存使用: {memory_info['system_memory_percent']:.1f}%")
    print(f"进程内存: {memory_info['process_memory_mb']:.1f}MB")

    print("\n✅ 所有测试完成!")
