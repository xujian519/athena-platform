"""
意图识别服务 - 模型池管理器

实现模型热加载、懒加载和资源管理,提升系统性能和资源利用率。

Author: Xiaonuo
Created: 2025-01-17
Version: 1.0.0
"""

import logging
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from pathlib import Path
from typing import Any

from core.intent.exceptions import ModelLoadError

# ========================================================================
# 模型状态枚举
# ========================================================================


class ModelStatus(str, Enum):
    """模型状态"""

    UNLOADED = "unloaded"  # 未加载
    LOADING = "loading"  # 加载中
    LOADED = "loaded"  # 已加载
    ERROR = "error"  # 加载失败
    UNLOADING = "unloading"  # 卸载中


# ========================================================================
# 模型元数据
# ========================================================================


class ModelMetadata:
    """
    模型元数据

    存储模型的基本信息和状态。
    """

    def __init__(
        self,
        name: str,
        model_type: str,
        model_path: Path,
        device: str = "auto",
        lazy_load: bool = True,
        ttl: int = 3600,
    ):
        """
        初始化模型元数据

        Args:
            name: 模型名称
            model_type: 模型类型(bert, bge-m3等)
            model_path: 模型路径
            device: 设备类型
            lazy_load: 是否懒加载
            ttl: 生存时间(秒),0表示不过期
        """
        self.name = name
        self.model_type = model_type
        self.model_path = Path(model_path)
        self.device = device
        self.lazy_load = lazy_load
        self.ttl = ttl

        # 状态管理
        self.status = ModelStatus.UNLOADED
        self.load_time: float | None = None
        self.last_access: float | None = None
        self.access_count: int = 0

        # 资源
        self.model_instance: Any | None = None
        self.tokenizer_instance: Any | None = None

        # 锁
        self._lock = threading.RLock()

    @property
    def age(self) -> float:
        """模型年龄(秒)"""
        if self.load_time is None:
            return 0
        return time.time() - self.load_time

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        if self.ttl == 0:
            return False
        return self.age > self.ttl

    @property
    def is_loaded(self) -> bool:
        """是否已加载"""
        return self.status == ModelStatus.LOADED


# ========================================================================
# 模型加载器
# ========================================================================


class ModelLoader:
    """
    模型加载器

    负责实际的模型加载和卸载操作。
    """

    @staticmethod
    def load_model(metadata: ModelMetadata) -> tuple[Any, Any]:
        """
        加载模型

        Args:
            metadata: 模型元数据

        Returns:
            (model, tokenizer) 元组

        Raises:
            ModelLoadError: 模型加载失败
        """
        try:
            # 根据模型类型选择加载方式
            if metadata.model_type == "bge-m3":
                return ModelLoader._load_bge_model(metadata)
            elif metadata.model_type == "bert":
                return ModelLoader._load_bert_model(metadata)
            else:
                raise ModelLoadError(
                    model_name=metadata.name, reason=f"不支持的模型类型: {metadata.model_type}"
                )

        except Exception as e:
            raise ModelLoadError(model_name=metadata.name, reason=f"加载失败: {e!s}") from e

    @staticmethod
    def _load_bge_model(metadata: ModelMetadata) -> tuple[Any, Any]:
        """加载BGE模型"""
        from transformers import AutoModel, AutoTokenizer

        # 加载模型
        model = AutoModel.from_pretrained(
            str(metadata.model_path), device_map=metadata.device, trust_remote_code=True
        )
        model.eval()

        # 加载分词器
        tokenizer = AutoTokenizer.from_pretrained(str(metadata.model_path), trust_remote_code=True)

        return model, tokenizer

    @staticmethod
    def _load_bert_model(metadata: ModelMetadata) -> tuple[Any, Any]:
        """加载BERT模型"""
        from transformers import AutoModel, AutoTokenizer

        model = AutoModel.from_pretrained(str(metadata.model_path), device_map=metadata.device)
        model.eval()

        tokenizer = AutoTokenizer.from_pretrained(str(metadata.model_path))

        return model, tokenizer

    @staticmethod
    def unload_model(model: Any, device: str) -> None:
        """
        卸载模型并释放资源

        Args:
            model: 模型实例
            device: 设备类型
        """
        import torch

        # 删除模型引用
        del model

        # 清理GPU内存
        if device in ["cuda", "mps"]:
            torch.cuda.empty_cache()
        elif device == "cpu":
            # 强制垃圾回收
            import gc

            gc.collect()


# ========================================================================
# 模型池
# ========================================================================


class ModelPool:
    """
    模型池

    管理多个模型实例的生命周期,支持热加载、懒加载和资源管理。
    """

    def __init__(
        self, max_models: int = 5, max_memory_gb: float = 16.0, unload_policy: str = "lru"
    ):
        """
        初始化模型池

        Args:
            max_models: 最大同时加载的模型数
            max_memory_gb: 最大内存使用(GB)
            unload_policy: 卸载策略 (lru, lfu, fifo)
        """
        self.max_models = max_models
        self.max_memory_gb = max_memory_gb
        self.unload_policy = unload_policy

        # 模型注册表
        self._models: dict[str, ModelMetadata] = {}
        self._model_lock = threading.RLock()

        # 线程池用于异步加载
        self._executor = ThreadPoolExecutor(max_workers=2)

        # 回调函数
        self._on_load_callbacks: list[Callable] = []
        self._on_unload_callbacks: list[Callable] = []

        self.logger = logging.getLogger("intent.model_pool")

    def register_model(self, metadata: ModelMetadata) -> None:
        """
        注册模型

        Args:
            metadata: 模型元数据
        """
        with self._model_lock:
            if metadata.name in self._models:
                self.logger.warning(f"模型 {metadata.name} 已存在,覆盖")
            self._models[metadata.name] = metadata
            self.logger.info(f"注册模型: {metadata.name}")

    def get_model(self, name: str) -> tuple[Any, Any]:
        """
        获取模型实例(懒加载)

        Args:
            name: 模型名称

        Returns:
            (model, tokenizer) 元组

        Raises:
            ModelLoadError: 模型加载失败
        """
        with self._model_lock:
            if name not in self._models:
                raise ModelLoadError(model_name=name, reason="模型未注册")

            metadata = self._models[name]

            # 检查是否已加载
            if metadata.is_loaded:
                # 更新访问时间
                metadata.last_access = time.time()
                metadata.access_count += 1

                # 检查是否过期
                if metadata.is_expired:
                    self._unload_model(metadata)

            # 加载模型
            if not metadata.is_loaded:
                self._load_model(metadata)

            return metadata.model_instance, metadata.tokenizer_instance

    def load_model_async(self, name: str) -> concurrent.futures.Future:
        """
        异步加载模型

        Args:
            name: 模型名称

        Returns:
            Future对象
        """
        return self._executor.submit(self.get_model, name)

    def preload_model(self, name: str) -> None:
        """
        预加载模型

        Args:
            name: 模型名称
        """
        try:
            self.get_model(name)
            self.logger.info(f"模型 {name} 预加载完成")
        except Exception as e:
            self.logger.error(f"模型 {name} 预加载失败: {e}")

    def unload_model(self, name: str) -> None:
        """
        卸载模型

        Args:
            name: 模型名称
        """
        with self._model_lock:
            if name not in self._models:
                return

            metadata = self._models[name]
            self._unload_model(metadata)

    def _load_model(self, metadata: ModelMetadata) -> None:
        """
        加载模型(内部方法)

        Args:
            metadata: 模型元数据
        """
        metadata.status = ModelStatus.LOADING

        try:
            # 检查是否需要卸载其他模型
            self._ensure_capacity()

            # 加载模型
            model, tokenizer = ModelLoader.load_model(metadata)

            # 更新元数据
            metadata.model_instance = model
            metadata.tokenizer_instance = tokenizer
            metadata.status = ModelStatus.LOADED
            metadata.load_time = time.time()
            metadata.last_access = time.time()
            metadata.access_count = 1

            # 触发回调
            for callback in self._on_load_callbacks:
                callback(metadata)

            self.logger.info(
                f"模型 {metadata.name} 加载完成 "
                f"(设备: {metadata.device}, "
                f"耗时: {metadata.load_time:.2f}s)"
            )

        except Exception as e:
            metadata.status = ModelStatus.ERROR
            self.logger.error(f"模型 {metadata.name} 加载失败: {e}")
            raise

    def _unload_model(self, metadata: ModelMetadata) -> None:
        """
        卸载模型(内部方法)

        Args:
            metadata: 模型元数据
        """
        if not metadata.is_loaded:
            return

        metadata.status = ModelStatus.UNLOADING

        try:
            # 卸载模型资源
            if metadata.model_instance is not None:
                ModelLoader.unload_model(metadata.model_instance, metadata.device)

            # 清理引用
            metadata.model_instance = None
            metadata.tokenizer_instance = None
            metadata.status = ModelStatus.UNLOADED

            # 触发回调
            for callback in self._on_unload_callbacks:
                callback(metadata)

            self.logger.info(f"模型 {metadata.name} 已卸载")

        except Exception as e:
            metadata.status = ModelStatus.ERROR
            self.logger.error(f"模型 {metadata.name} 卸载失败: {e}")

    def _ensure_capacity(self) -> None:
        """
        确保有足够的容量加载新模型

        根据卸载策略选择要卸载的模型。
        """
        loaded_models = [m for m in self._models.values() if m.is_loaded]

        if len(loaded_models) >= self.max_models:
            # 需要卸载一些模型
            to_unload = self._select_models_to_unload(loaded_models)
            for metadata in to_unload:
                self._unload_model(metadata)

    def _select_models_to_unload(self, loaded_models: list) -> list:
        """
        选择要卸载的模型

        Args:
            loaded_models: 已加载的模型列表

        Returns:
            要卸载的模型列表
        """
        if self.unload_policy == "lru":
            # 最近最少使用
            return [min(loaded_models, key=lambda m: m.last_access or 0)]

        elif self.unload_policy == "lfu":
            # 最少使用频率
            return [min(loaded_models, key=lambda m: m.access_count)]

        elif self.unload_policy == "fifo":
            # 先进先出
            return [min(loaded_models, key=lambda m: m.load_time or 0)]

        else:
            # 默认:卸载最旧的
            return [min(loaded_models, key=lambda m: m.load_time or float("inf"))]

    def add_load_callback(self, callback: Callable[[ModelMetadata], None]) -> None:
        """
        添加加载回调

        Args:
            callback: 回调函数
        """
        self._on_load_callbacks.append(callback)

    def add_unload_callback(self, callback: Callable[[ModelMetadata], None]) -> None:
        """
        添加卸载回调

        Args:
            callback: 回调函数
        """
        self._on_unload_callbacks.append(callback)

    def get_stats(self) -> dict[str, Any]:
        """
        获取模型池统计信息

        Returns:
            统计信息字典
        """
        with self._model_lock:
            loaded_count = sum(1 for m in self._models.values() if m.is_loaded)

            return {
                "total_models": len(self._models),
                "loaded_models": loaded_count,
                "unloaded_models": len(self._models) - loaded_count,
                "max_models": self.max_models,
                "utilization": f"{loaded_count}/{self.max_models}",
                "models": {
                    name: {
                        "status": metadata.status.value,
                        "age_seconds": metadata.age,
                        "access_count": metadata.access_count,
                        "is_expired": metadata.is_expired,
                    }
                    for name, metadata in self._models.items()
                },
            }

    def cleanup(self) -> None:
        """
        清理所有模型

        卸载所有已加载的模型。
        """
        self.logger.info("清理模型池...")

        with self._model_lock:
            for metadata in list(self._models.values()):
                if metadata.is_loaded:
                    self._unload_model(metadata)

        self._executor.shutdown(wait=True)


# ========================================================================
# 全局模型池实例
# ========================================================================

_global_model_pool: ModelPool | None = None


def get_model_pool() -> ModelPool:
    """
    获取全局模型池实例

    Returns:
        全局模型池实例
    """
    global _global_model_pool
    if _global_model_pool is None:
        # 配置模型池
        from core.intent.config_loader import get_intent_config

        config = get_intent_config()
        max_models = config.get("performance.concurrency.max_models", 5)

        _global_model_pool = ModelPool(max_models=max_models)

        # 注册常用模型
        _register_default_models(_global_model_pool)

    return _global_model_pool


def _register_default_models(pool: ModelPool) -> None:
    """
    注册默认模型

    Args:
        pool: 模型池实例
    """
    from core.intent.config_loader import get_intent_config

    config = get_intent_config()

    # BGE-M3模型
    bge_path = config.get_model_path("bge_m3")
    bge_metadata = ModelMetadata(
        name="bge-m3",
        model_type="bge-m3",
        model_path=bge_path,
        device=config.get_device("bge_m3"),
        lazy_load=True,
        ttl=7200,  # 2小时
    )
    pool.register_model(bge_metadata)

    # BERT模型
    try:
        bert_path = config.get_model_path("bert")
        bert_metadata = ModelMetadata(
            name="bert",
            model_type="bert",
            model_path=bert_path,
            device=config.get_device("bert"),
            lazy_load=True,
            ttl=3600,  # 1小时
        )
        pool.register_model(bert_metadata)
    except Exception:
        # BERT可能不存在,忽略
        pass


def reset_model_pool() -> None:
    """重置全局模型池"""
    global _global_model_pool
    if _global_model_pool is not None:
        _global_model_pool.cleanup()
    _global_model_pool = None


# ========================================================================
# 导出
# ========================================================================

__all__ = [
    "ModelLoader",
    "ModelMetadata",
    "ModelPool",
    "ModelStatus",
    "get_model_pool",
    "reset_model_pool",
]
