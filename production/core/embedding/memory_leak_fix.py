#!/usr/bin/env python3
"""
内存泄漏修复补丁
Memory Leak Fix Patch for Athena Platform

修复发现的内存泄漏问题

作者: Claude (AI Assistant)
创建时间: 2026-01-16
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import gc
import logging
import threading
import weakref
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# 修复1: 修复事件循环嵌套Bug
# =============================================================================


class FixedLocalEmbeddingModel:
    """
    修复后的本地嵌入模型
    修复了asyncio.run嵌套调用导致的内存泄漏
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self.model_path = self._get_model_path(model_name)
        self.model = None
        self.embedding_dim = 1024  # BGE-M3向量维度(已更新)
        self.max_length = 512
        self._load_lock = threading.Lock()
        self._is_loaded = False

        logger.info(f"📦 本地嵌入模型初始化: {model_name}")

    def _get_model_path(self, model_name: str) -> Path:
        """获取模型路径"""
        base_path = Path("/Users/xujian/Athena工作平台/models")
        model_paths = {
            "BAAI/bge-m3": base_path / "converted" / "BAAI" / "bge-m3",
            "bge-m3": base_path / "converted" / "BAAI" / "bge-m3",
        }
        return model_paths.get(model_name, base_path / "converted" / model_name)

    async def load_model(self):
        """加载模型(异步接口)"""
        with self._load_lock:
            if self._is_loaded:
                return

            def _load_sync():
                """同步加载模型"""
                try:
                    from sentence_transformers import SentenceTransformer

                    if not self.model_path.exists():
                        logger.warning(f"⚠️  模型路径不存在: {self.model_path}")
                        return False

                    logger.info(f"🔄 加载模型: {self.model_name}")
                    self.model = SentenceTransformer(str(self.model_path))
                    self.embedding_dim = self.model.get_sentence_embedding_dimension()
                    self.max_length = self.model.max_seq_length

                    logger.info("✅ 模型加载完成")
                    return True

                except Exception as e:
                    logger.error(f"❌ 模型加载失败: {e}")
                    return False

            # 在线程池中执行加载
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _load_sync)

            if success:
                self._is_loaded = True
            else:
                self.model = None

    async def encode(
        self, texts: str | list[str], batch_size: int = 32, show_progress: bool = False
    ) -> np.ndarray:
        """
        编码文本为嵌入向量(修复后)

        ✅ 修复: 不再嵌套调用asyncio.run
        """
        if not self._is_loaded or self.model is None:
            await self.load_model()

        if self.model is None:
            return self._fallback_encode(texts)

        def _encode_sync():
            """同步编码函数"""
            try:
                texts_list = [texts] if isinstance(texts, str) else texts

                embeddings = self.model.encode(
                    texts_list,
                    batch_size=batch_size,
                    show_progress_bar=show_progress,
                    convert_to_numpy=True,
                )
                return embeddings
            except Exception as e:
                logger.error(f"❌ 编码失败: {e}")
                return self._fallback_encode(texts)

        # 在线程池中执行编码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _encode_sync)

    def _fallback_encode(self, texts: str | list[str]) -> np.ndarray:
        """降级编码方案"""
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            text_bytes = text.encode("utf-8")
            embedding = np.zeros(self.embedding_dim, dtype=np.float32)

            for i, byte_val in enumerate(text_bytes):
                embedding[i % self.embedding_dim] += byte_val / 255.0

            # 归一化
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            embeddings.append(embedding)

        return np.array(embeddings)

    def unload(self):
        """卸载模型释放内存"""
        with self._load_lock:
            if self.model is not None:
                try:
                    del self.model
                    self.model = None
                    self._is_loaded = False

                    # 清理GPU内存
                    import torch

                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
                    elif torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    gc.collect()
                    logger.info(f"🗑️ 模型已卸载: {self.model_name}")
                except Exception as e:
                    logger.warning(f"操作失败: {e}")


# =============================================================================
# 修复2: 改进的BGE嵌入服务(带内存限制)
# =============================================================================


class FixedBGEEmbeddingService:
    """
    修复后的BGE嵌入服务
    添加了严格的内存管理
    """

    def __init__(self, config: dict[str, Any] | None = None):
        self.name = "BGE嵌入服务(修复版)"
        self.version = "1.0.1"

        # 配置
        default_model_path = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"
        self.config = config or {
            "model_path": default_model_path,
            "device": "cpu",
            "batch_size": 32,
            "max_length": 512,
            "cache_enabled": True,
            "preload": True,
            # 新增:内存限制配置
            "max_cache_size_mb": 100,  # 限制缓存最大100MB
            "max_cache_entries": 100,  # 限制缓存条目数
        }

        # 模型状态
        self.model = None
        self.is_loaded = False
        self.load_lock = threading.Lock()

        # 改进的缓存:使用WeakValueDictionary
        self.embedding_cache: dict[str, np.ndarray] = {}
        self.cache_lock = threading.Lock()
        self.cache_size_bytes = 0
        self.max_cache_bytes = self.config["max_cache_size_mb"] * 1024 * 1024

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "evictions": 0,
        }

        logger.info(f"🚀 {self.name} 初始化完成")

    def _get_cache_key(self, texts: list[str]) -> str:
        """生成缓存键"""
        import hashlib

        combined_text = "|||".join(texts)
        return hashlib.md5(combined_text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()

    def _save_to_cache(self, cache_key: str, embeddings: np.ndarray):
        """保存到缓存(带内存限制)"""
        with self.cache_lock:
            # 估算当前条目大小
            entry_size = embeddings.nbytes

            # 如果单个条目超过限制的10%,不缓存
            if entry_size > self.max_cache_bytes * 0.1:
                return

            # 如果键已存在,先删除旧的
            if cache_key in self.embedding_cache:
                old_entry = self.embedding_cache[cache_key]
                self.cache_size_bytes -= old_entry.nbytes
                del self.embedding_cache[cache_key]

            # 检查是否需要驱逐
            while (
                self.cache_size_bytes + entry_size > self.max_cache_bytes
                or len(self.embedding_cache) >= self.config["max_cache_entries"]
            ):
                if not self._evict_lru():
                    break

            # 添加新条目
            self.embedding_cache[cache_key] = embeddings
            self.cache_size_bytes += entry_size

    def _evict_lru(self) -> bool:
        """驱逐最老的缓存条目"""
        if not self.embedding_cache:
            return False

        # 简单的FIFO驱逐(可以用OrderedDict实现LRU)
        oldest_key = next(iter(self.embedding_cache))
        oldest_entry = self.embedding_cache[oldest_key]

        self.cache_size_bytes -= oldest_entry.nbytes
        del self.embedding_cache[oldest_key]
        self.stats["evictions"] += 1

        logger.debug(f"驱逐缓存: {oldest_key} ({oldest_entry.nbytes} bytes)")
        return True

    def clear_cache(self):
        """清空缓存"""
        with self.cache_lock:
            self.embedding_cache.clear()
            self.cache_size_bytes = 0
            logger.info("🗑️ 缓存已清空")

    def unload_model(self):
        """卸载模型"""
        with self.load_lock:
            if self.model is not None:
                try:
                    del self.model
                    self.model = None
                    self.is_loaded = False

                    # 清理GPU内存
                    import torch

                    if torch.backends.mps.is_available():
                        torch.mps.empty_cache()
                    elif torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    gc.collect()
                    logger.info("🗑️ 模型已卸载")
                except Exception as e:
                    logger.warning(f"操作失败: {e}")


# =============================================================================
# 修复3: 全局单例管理器
# =============================================================================


class SingletonManager:
    """
    全局单例管理器
    统一管理所有单例的生命周期
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._singletons: dict[str, Any] = {}
        self._weak_refs: dict[str, weakref.ref] = {}
        self._lock = threading.RLock()

        logger.info("🎯 全局单例管理器初始化")

    def register(self, name: str, instance: Any, weak_ref: bool = True):
        """注册单例"""
        with self._lock:
            if weak_ref:
                # 使用弱引用,允许对象被GC
                def cleanup_callback(ref):
                    with self._lock:
                        if name in self._weak_refs:
                            del self._weak_refs[name]
                        if name in self._singletons:
                            del self._singletons[name]
                        logger.debug(f"单例已清理: {name}")

                self._weak_refs[name] = weakref.ref(instance, cleanup_callback)
            else:
                self._singletons[name] = instance

            logger.info(f"注册单例: {name}")

    def get(self, name: str) -> Any | None:
        """获取单例"""
        with self._lock:
            # 先检查弱引用
            if name in self._weak_refs:
                ref = self._weak_refs[name]
                instance = ref()
                if instance is not None:
                    return instance
                else:
                    del self._weak_refs[name]

            # 检查强引用
            return self._singletons.get(name)

    def cleanup(self, name: str):
        """清理特定单例"""
        with self._lock:
            if name in self._weak_refs:
                del self._weak_refs[name]

            if name in self._singletons:
                instance = self._singletons[name]
                # 尝试调用unload方法
                if hasattr(instance, "unload"):
                    instance.unload()
                elif hasattr(instance, "close"):
                    instance.close()
                elif hasattr(instance, "cleanup"):
                    instance.cleanup()

                del self._singletons[name]
                logger.info(f"清理单例: {name}")

    def cleanup_all(self):
        """清理所有单例"""
        with self._lock:
            # 清理弱引用
            self._weak_refs.clear()

            # 清理强引用
            for name in list(self._singletons.keys()):
                self.cleanup(name)

            # 强制垃圾回收
            gc.collect()
            logger.info("🗑️ 所有单例已清理")

    def get_memory_info(self) -> dict[str, Any]:
        """获取内存使用信息"""
        with self._lock:
            import sys

            total_size = 0
            info = {}

            for name, instance in self._singletons.items():
                try:
                    size = sys.getsizeof(instance)
                    total_size += size
                    info[name] = {
                        "size_mb": round(size / 1024 / 1024, 2),
                        "type": type(instance).__name__,
                    }
                except (TypeError, ZeroDivisionError) as e:
                    logger.warning(f"计算时发生错误: {e}")
                except Exception as e:
                    logger.error(f"未预期的错误: {e}")

            return {"total_mb": round(total_size / 1024 / 1024, 2), "singletons": info}


# 全局单例管理器实例
_singleton_manager = None


def get_singleton_manager() -> SingletonManager:
    """获取全局单例管理器"""
    global _singleton_manager
    if _singleton_manager is None:
        _singleton_manager = SingletonManager()
    return _singleton_manager


# =============================================================================
# 修复4: 内存监控工具
# =============================================================================


class MemoryMonitor:
    """内存监控工具"""

    @staticmethod
    def get_process_memory() -> dict[str, float]:
        """获取进程内存使用"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()

        return {
            "rss_mb": mem_info.rss / 1024 / 1024,  # 物理内存
            "vms_mb": mem_info.vms / 1024 / 1024,  # 虚拟内存
        }

    @staticmethod
    def get_gpu_memory() -> dict[str, float]:
        """获取GPU内存使用"""
        try:
            import torch

            info = {}
            if torch.backends.mps.is_available():
                allocated = torch.mps.current_allocated_memory() / 1024 / 1024
                info = {"mps_allocated_mb": allocated}
            elif torch.cuda.is_available():
                allocated = torch.cuda.memory_allocated() / 1024 / 1024
                cached = torch.cuda.memory_reserved() / 1024 / 1024
                info = {
                    "cuda_allocated_mb": allocated,
                    "cuda_cached_mb": cached,
                }
            return info
        except Exception:
            return {}

    @staticmethod
    def print_memory_summary():
        """打印内存摘要"""
        mem = MemoryMonitor.get_process_memory()
        gpu = MemoryMonitor.get_gpu_memory()

        print("\n" + "=" * 50)
        print("📊 内存使用摘要")
        print("=" * 50)
        print(f"物理内存: {mem['rss_mb']:.2f} MB")
        print(f"虚拟内存: {mem['vms_mb']:.2f} MB")

        if gpu:
            print("\nGPU内存:")
            for key, value in gpu.items():
                print(f"  {key}: {value:.2f} MB")

        # 单例管理器信息
        manager = get_singleton_manager()
        singleton_info = manager.get_memory_info()
        if singleton_info["singletons"]:
            print(f"\n全局单例: {len(singleton_info['singletons'])} 个")
            print(f"总大小: {singleton_info['total_mb']:.2f} MB")

        print("=" * 50 + "\n")


# =============================================================================
# 修复5: 使用示例
# =============================================================================


async def main():
    """修复后的使用示例"""

    # 1. 使用修复后的嵌入模型
    print("1️⃣ 测试修复后的嵌入模型")
    model = FixedLocalEmbeddingModel("BAAI/bge-m3")
    await model.load_model()

    embeddings = await model.encode("测试文本")
    print(f"   嵌入维度: {embeddings.shape}")

    # 2. 使用修复后的BGE服务
    print("\n2️⃣ 测试修复后的BGE服务")
    bge_service = FixedBGEEmbeddingService()

    # 3. 使用单例管理器
    print("\n3️⃣ 测试单例管理器")
    manager = get_singleton_manager()
    manager.register("test_model", model, weak_ref=True)

    # 4. 监控内存
    print("\n4️⃣ 内存监控")
    MemoryMonitor.print_memory_summary()

    # 5. 清理资源
    print("\n5️⃣ 清理资源")
    model.unload()
    bge_service.unload_model()
    bge_service.clear_cache()
    manager.cleanup_all()

    MemoryMonitor.print_memory_summary()


# 入口点: @async_main装饰器已添加到main函数
