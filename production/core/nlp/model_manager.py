#!/usr/bin/env python3
"""
智能模型管理器
Intelligent Model Manager

优化NLP模型的加载、缓存和内存管理

作者: 系统管理员
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import gc
import threading
import time
from contextlib import contextmanager
from typing import Any

import torch


class LazyModelLoader:
    """懒加载模型类"""

    def __init__(self, model_path: str, model_class, device: str = "cpu"):
        self.model_path = model_path
        self.model_class = model_class
        self.device = device
        self._model = None
        self._lock = threading.Lock()
        self._load_time = None

    @property
    def model(self) -> Any:
        """懒加载属性"""
        if self._model is None:
            with self._lock:
                if self._model is None:
                    self._model = self._load_model()
        return self._model

    def _load_model(self) -> Any:
        """实际加载模型"""
        start_time = time.time()
        try:
            # 安全修复: 禁用trust_remote_code防止任意代码执行
            model = self.model_class.from_pretrained(
                self.model_path,
                trust_remote_code=False,  # 安全: 不执行模型中的自定义代码
                local_files_only=True,
            )
            model.to(self.device)

            # MPS设备启用FP16量化
            if self.device.type == "mps":
                model = model.half()

            model.eval()

            self._load_time = time.time() - start_time
            print(f"✅ 模型加载完成: {self.model_path} (耗时: {self._load_time:.2f}s)")

            return model
        except Exception as e:
            print(f"❌ 模型加载失败 {self.model_path}: {e}")
            raise

    def is_loaded(self) -> bool:
        """检查模型是否已加载"""
        return self._model is not None

    def unload(self) -> Any:
        """卸载模型释放内存"""
        with self._lock:
            if self._model is not None:
                del self._model
                self._model = None
                self._clear_memory()
                print(f"🗑️ 模型已卸载: {self.model_path}")

    def _clear_memory(self) -> Any:
        """清理内存"""
        if torch.backends.mps.is_available():
            # MPS设备内存清理
            torch.mps.empty_cache()
        elif torch.cuda.is_available():
            # CUDA设备内存清理
            torch.cuda.empty_cache()

        # 强制垃圾回收
        gc.collect()


class ModelManager:
    """智能模型管理器"""

    def __init__(self, max_memory_models: int = 3):
        self.models: dict[str, LazyModelLoader] = {}
        self.model_configs: dict[str, dict] = {}
        self.loading_locks: dict[str, threading.Lock] = {}
        self.max_memory_models = max_memory_models
        self.usage_stats: dict[str, dict] = {}

        # 设备检测
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        print(f"🎯 模型管理器初始化完成,使用设备: {self.device}")

    def register_model(self, name: str, model_path: str, model_class, **kwargs) -> None:
        """注册模型"""
        if name not in self.loading_locks:
            self.loading_locks[name] = threading.Lock()

        self.models[name] = LazyModelLoader(
            model_path=model_path, model_class=model_class, device=self.device, **kwargs
        )

        self.model_configs[name] = {
            "path": model_path,
            "class": model_class.__name__,
            "registered_time": time.time(),
            **kwargs,
        }

        self.usage_stats[name] = {"load_count": 0, "total_usage_time": 0.0, "last_used": None}

        print(f"📝 模型已注册: {name} -> {model_path}")

    def get_model(self, name: str) -> Any | None:
        """获取模型(自动加载)"""
        if name not in self.models:
            raise ValueError(f"模型未注册: {name}")

        # 内存管理 - 如果已加载模型过多,卸载最少使用的
        self._manage_memory()

        loader = self.models[name]

        # 更新使用统计
        self.usage_stats[name]["load_count"] += 1
        self.usage_stats[name]["last_used"] = time.time()

        return loader.model

    def _manage_memory(self) -> Any:
        """内存管理 - 智能卸载模型"""
        loaded_models = [
            (name, loader) for name, loader in self.models.items() if loader.is_loaded()
        ]

        if len(loaded_models) >= self.max_memory_models:
            # 按最后使用时间排序,卸载最少使用的模型
            loaded_models.sort(key=lambda x: self.usage_stats[x[0]].get("last_used", 0))

            # 卸载最旧的模型
            for i in range(len(loaded_models) - self.max_memory_models + 1):
                _name, loader = loaded_models[i]
                loader.unload()

    @contextmanager
    def temporary_model(self, name: str) -> Any:
        """临时使用模型上下文管理器"""
        model = self.get_model(name)
        start_time = time.time()

        try:
            yield model
        finally:
            # 更新使用时间
            usage_time = time.time() - start_time
            self.usage_stats[name]["total_usage_time"] += usage_time

    def unload_model(self, name: str) -> Any:
        """手动卸载模型"""
        if name in self.models:
            self.models[name].unload()

    def unload_all(self) -> Any:
        """卸载所有模型"""
        for _name, loader in self.models.items():
            if loader.is_loaded():
                loader.unload()

    def get_memory_info(self) -> dict[str, Any]:
        """获取内存使用信息"""
        loaded_models = []
        total_memory = 0

        for name, loader in self.models.items():
            if loader.is_loaded():
                model_info = {
                    "name": name,
                    "load_time": loader._load_time,
                    "usage_stats": self.usage_stats[name],
                }
                loaded_models.append(model_info)

                # 估算模型内存使用(粗略)
                if hasattr(loader.model, "parameters"):
                    param_count = sum(p.numel() for p in loader.model.parameters())
                    # 假设FP16每个参数2字节
                    estimated_memory = param_count * 2 / (1024**3)  # GB
                    total_memory += estimated_memory
                    model_info["estimated_memory_gb"] = estimated_memory

        return {
            "device": str(self.device),
            "loaded_models": len(loaded_models),
            "total_models": len(self.models),
            "estimated_memory_gb": round(total_memory, 2),
            "models": loaded_models,
        }

    def get_performance_stats(self) -> dict[str, Any]:
        """获取性能统计"""
        stats = {
            "registered_models": len(self.models),
            "model_configs": self.model_configs,
            "usage_stats": self.usage_stats,
            "memory_info": self.get_memory_info(),
        }

        # 计算平均使用时间
        for _name, usage in self.usage_stats.items():
            if usage["load_count"] > 0:
                avg_time = usage["total_usage_time"] / usage["load_count"]
                usage["avg_usage_time"] = avg_time

        return stats

    def optimize_for_device(self) -> Any:
        """根据设备优化设置"""
        if self.device.type == "mps":
            print("🍎 检测到Apple Silicon,启用MPS优化")
            # MPS特定优化设置
            torch.mps.set_per_process_memory_fraction(0.8)

        elif self.device.type == "cuda":
            print("🎮 检测到CUDA,启用GPU优化")
            # CUDA特定优化设置
            torch.backends.cudnn.benchmark = True

        else:
            print("💻 使用CPU优化模式")


# 全局模型管理器实例
global_model_manager = None


def get_model_manager() -> ModelManager:
    """获取全局模型管理器实例"""
    global global_model_manager
    if global_model_manager is None:
        global_model_manager = ModelManager()
    return global_model_manager


def reset_model_manager() -> Any:
    """重置全局模型管理器"""
    global global_model_manager
    if global_model_manager is not None:
        global_model_manager.unload_all()
    global_model_manager = None


if __name__ == "__main__":
    # 测试模型管理器
    manager = ModelManager()
    manager.optimize_for_device()

    # 显示内存信息
    memory_info = manager.get_memory_info()
    print("\n📊 内存信息:")
    print(f"   设备: {memory_info['device']}")
    print(f"   已加载模型: {memory_info['loaded_models']}")
    print(f"   总模型数: {memory_info['total_models']}")
    print(f"   估计内存使用: {memory_info['estimated_memory_gb']}GB")
