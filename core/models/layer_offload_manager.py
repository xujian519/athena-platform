#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型层卸载策略管理器
Model Layer Offload Strategy Manager for llama-cpp-python

智能管理模型层在CPU/GPU之间的分配,优化内存使用和性能
"""

import logging
import psutil
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import gc

logger = logging.getLogger(__name__)


class OffloadStrategy(Enum):
    """卸载策略"""
    # 全部GPU层(最大性能,高内存占用)
    ALL_GPU = "all_gpu"
    # 全部CPU层(最低内存占用,低性能)
    ALL_CPU = "all_cpu"
    # 自动平衡(基于内存和性能自动调整)
    AUTO_BALANCE = "auto_balance"
    # 自定义(手动指定层数)
    CUSTOM = "custom"
    # 性能优先(尽可能多GPU层)
    PERFORMANCE = "performance"
    # 内存优先(尽可能少GPU层)
    MEMORY = "memory"


@dataclass
class OffloadConfig:
    """卸载配置"""
    n_gpu_layers: int  # GPU层数(-1表示全部)
    n_ctx: int = 32768  # 上下文长度
    n_batch: int = 512  # 批处理大小
    n_threads: int = 8  # CPU线程数
    use_mmap: bool = True  # 使用内存映射
    use_mlock: bool = False  # 使用内存锁定
    numa: bool = False  # NUMA优化

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "n_gpu_layers": self.n_gpu_layers,
            "n_ctx": self.n_ctx,
            "n_batch": self.n_batch,
            "n_threads": self.n_threads,
            "use_mmap": self.use_mmap,
            "use_mlock": self.use_mlock,
            "numa": self.numa
        }


@dataclass
class SystemInfo:
    """系统信息"""
    total_memory_gb: float
    available_memory_gb: float
    cpu_count: int
    gpu_memory_gb: float | None = None

    @property
    def memory_usage_percent(self) -> float:
        """内存使用率"""
        return (1 - self.available_memory_gb / self.total_memory_gb) * 100

    @property
    def available_memory_mb(self) -> float:
        """可用内存(MB)"""
        return self.available_memory_gb * 1024


class LayerOffloadManager:
    """
    模型层卸载策略管理器

    核心功能:
    1. 系统资源监控:实时监控CPU/GPU内存使用
    2. 智能策略推荐:基于模型大小和系统资源推荐最佳策略
    3. 自动配置生成:自动生成最优的模型加载参数
    4. 性能预测:预测不同策略的性能表现
    """

    # 模型参数量与GPU内存需求估算(GB)
    MODEL_MEMORY_REQUIREMENTS = {
        # Qwen系列
        "qwen2.5-14b": {"q4_k_m": 8.9, "q5_k_m": 10.8, "q6_k": 12.7, "q8_0": 15.1},
        "qwen2.5-7b": {"q4_k_m": 4.6, "q5_k_m": 5.6, "q6_k": 6.6, "q8_0": 7.9},
        "qwen2.5-3b": {"q4_k_m": 2.0, "q5_k_m": 2.4, "q6_k": 2.8, "q8_0": 3.4},

        # Llama系列
        "llama-3.1-8b": {"q4_k_m": 5.0, "q5_k_m": 6.0, "q6_k": 7.1, "q8_0": 8.5},
        "llama-3-70b": {"q4_k_m": 42.0, "q5_k_m": 51.0, "q6_k": 60.0, "q8_0": 75.0},

        # 通用规则(每10亿参数)
        "generic_per_1b": {
            "q4_k_m": 0.64,  # 4-bit量化
            "q5_k_m": 0.78,  # 5-bit量化
            "q6_k": 0.91,    # 6-bit量化
            "q8_0": 1.08     # 8-bit量化
        }
    }

    # 性能预测参数
    PERFORMANCE_FACTORS = {
        "gpu_speedup": 3.5,      # GPU相对CPU加速比
        "memory_penalty": 0.1,   # 内存不足时的性能惩罚
        "context_penalty": 0.05  # 长上下文性能衰减
    }

    def __init__(self, model_name: str, quantization: str = "q4_k_m"):
        """
        初始化管理器

        Args:
            model_name: 模型名称(如 "qwen2.5-14b")
            quantization: 量化方式(如 "q4_k_m")
        """
        self.model_name = model_name.lower()
        self.quantization = quantization.lower()
        self.system_info = self._get_system_info()
        self.model_memory_gb = self._estimate_model_memory()

        logger.info(f"LayerOffloadManager初始化: model={model_name}, "
                   f"quant={quantization}, memory={self.model_memory_gb:.2f}GB")

    def _get_system_info(self) -> SystemInfo:
        """获取系统信息"""
        memory = psutil.virtual_memory()
        cpu_count = psutil.cpu_count()

        # 对于Apple Silicon,估算GPU内存(通常是统一内存)
        # M4 Pro大约共享系统内存
        gpu_memory_gb = None  # Apple Silicon使用统一内存

        return SystemInfo(
            total_memory_gb=memory.total / (1024**3),
            available_memory_gb=memory.available / (1024**3),
            cpu_count=cpu_count,
            gpu_memory_gb=gpu_memory_gb
        )

    def _estimate_model_memory(self) -> float:
        """估算模型内存需求"""
        # 尝试直接匹配
        if self.model_name in self.MODEL_MEMORY_REQUIREMENTS:
            model_reqs = self.MODEL_MEMORY_REQUIREMENTS[self.model_name]
            if self.quantization in model_reqs:
                return model_reqs[self.quantization]

        # 使用通用规则估算
        # 从模型名称提取参数量
        try:
            if "14b" in self.model_name or "14-b" in self.model_name:
                params = 14
            elif "7b" in self.model_name or "7-b" in self.model_name:
                params = 7
            elif "3b" in self.model_name or "3-b" in self.model_name:
                params = 3
            elif "8b" in self.model_name or "8-b" in self.model_name:
                params = 8
            elif "70b" in self.model_name or "70-b" in self.model_name:
                params = 70
            else:
                params = 7  # 默认7B
        except Exception as e:
            logger.debug(f"空except块已触发: {e}")
            params = 7

        generic_per_1b = self.MODEL_MEMORY_REQUIREMENTS["generic_per_1b"]
        per_1b_memory = generic_per_1b.get(
            self.quantization,
            generic_per_1b["q4_k_m"]  # 默认Q4_K_M
        )

        return params * per_1b_memory

    def recommend_strategy(
        self,
        context_length: int = 32768,
        allow_cpu_fallback: bool = True
    ) -> tuple[OffloadStrategy, OffloadConfig]:
        """
        推荐最佳卸载策略

        Args:
            context_length: 上下文长度
            allow_cpu_fallback: 是否允许CPU回退

        Returns:
            tuple[OffloadStrategy, OffloadConfig]: 策略和配置
        """
        available_gb = self.system_info.available_memory_gb
        model_gb = self.model_memory_gb
        context_overhead_gb = context_length / 32768 * 2.0  # 估算上下文内存开销
        total_required_gb = model_gb + context_overhead_gb

        logger.info(f"内存分析: 可用={available_gb:.2f}GB, "
                   f"模型={model_gb:.2f}GB, "
                   f"上下文开销={context_overhead_gb:.2f}GB, "
                   f"总计={total_required_gb:.2f}GB")

        # 策略决策
        if available_gb >= total_required_gb * 1.5:
            # 充足内存:全部GPU
            strategy = OffloadStrategy.ALL_GPU
            config = OffloadConfig(
                n_gpu_layers=-1,  # 全部GPU
                n_ctx=context_length,
                n_threads=self.system_info.cpu_count
            )
            logger.info("推荐策略: ALL_GPU (内存充足)")

        elif available_gb >= total_required_gb * 1.2:
            # 中等内存:性能优先
            strategy = OffloadStrategy.PERFORMANCE
            # 估算可以加载到GPU的层数
            gpu_ratio = 0.8  # 80%层到GPU
            estimated_layers = self._estimate_total_layers() * gpu_ratio

            config = OffloadConfig(
                n_gpu_layers=int(estimated_layers),
                n_ctx=context_length,
                n_threads=self.system_info.cpu_count
            )
            logger.info(f"推荐策略: PERFORMANCE (约{estimated_layers:.0f}层GPU)")

        elif available_gb >= total_required_gb:
            # 勉强够用:自动平衡
            strategy = OffloadStrategy.AUTO_BALANCE
            gpu_ratio = 0.5  # 50%层到GPU
            estimated_layers = self._estimate_total_layers() * gpu_ratio

            config = OffloadConfig(
                n_gpu_layers=int(estimated_layers),
                n_ctx=min(context_length, 16384),  # 减少上下文
                n_threads=self.system_info.cpu_count
            )
            logger.info(f"推荐策略: AUTO_BALANCE (约{estimated_layers:.0f}层GPU, 上下文限制)")

        elif allow_cpu_fallback:
            # 内存不足:内存优先(部分GPU)
            strategy = OffloadStrategy.MEMORY
            # 只将少量层放到GPU
            estimated_layers = self._estimate_total_layers() * 0.3

            config = OffloadConfig(
                n_gpu_layers=int(estimated_layers),
                n_ctx=min(context_length, 8192),  # 进一步减少上下文
                n_threads=self.system_info.cpu_count,
                use_mmap=True  # 使用内存映射减少内存占用
            )
            logger.info(f"推荐策略: MEMORY (约{estimated_layers:.0f}层GPU, 内存优化)")

        else:
            # 严格模式:全部CPU
            strategy = OffloadStrategy.ALL_CPU
            config = OffloadConfig(
                n_gpu_layers=0,  # 全部CPU
                n_ctx=min(context_length, 4096),
                n_threads=self.system_info.cpu_count,
                use_mmap=True
            )
            logger.warning("推荐策略: ALL_CPU (内存不足,纯CPU模式)")

        return strategy, config

    def _estimate_total_layers(self) -> int:
        """估算模型总层数"""
        # 基于模型架构的估算
        # Transformer模型通常每10亿参数约12层
        try:
            if "14b" in self.model_name:
                return 48  # Qwen2.5-14B约48层
            elif "7b" in self.model_name:
                return 32  # Qwen2.5-7B约32层
            elif "3b" in self.model_name:
                return 24  # Qwen2.5-3B约24层
            else:
                return 32  # 默认
        except Exception as e:
            logger.debug(f"层数估算失败: {e}")
            return 32

    def predict_performance(
        self,
        config: OffloadConfig,
        context_length: int = 4096
    ) -> dict[str, float]:
        """
        预测性能指标

        Args:
            config: 卸载配置
            context_length: 上下文长度

        Returns:
            dict[str, float]: 性能预测
        """
        total_layers = self._estimate_total_layers()
        gpu_layers = config.n_gpu_layers if config.n_gpu_layers > 0 else 0
        if config.n_gpu_layers == -1:
            gpu_layers = total_layers

        gpu_ratio = gpu_layers / total_layers if total_layers > 0 else 0

        # 基础速度(tokens/秒)
        base_cpu_speed = 15.0  # CPU基准速度
        base_gpu_speed = base_cpu_speed * self.PERFORMANCE_FACTORS["gpu_speedup"]

        # 混合推理速度
        estimated_speed = (base_cpu_speed * (1 - gpu_ratio) +
                          base_gpu_speed * gpu_ratio)

        # 内存惩罚
        memory_pressure = (self.model_memory_gb /
                          self.system_info.available_memory_gb)
        if memory_pressure > 0.9:
            estimated_speed *= (1 - self.PERFORMANCE_FACTORS["memory_penalty"])

        # 上下文惩罚
        if context_length > 8192:
            context_penalty = ((context_length - 8192) / 8192 *
                             self.PERFORMANCE_FACTORS["context_penalty"])
            estimated_speed *= (1 - min(context_penalty, 0.3))

        # 加载时间估算
        base_load_time = 15.0  # CPU加载时间(秒)
        gpu_load_time = base_load_time / 5  # GPU加载更快
        estimated_load_time = (base_load_time * (1 - gpu_ratio) +
                              gpu_load_time * gpu_ratio)

        return {
            "estimated_tokens_per_second": max(estimated_speed, 5.0),
            "estimated_load_time_seconds": max(estimated_load_time, 0.5),
            "gpu_layer_ratio": gpu_ratio,
            "memory_usage_gb": self.model_memory_gb,
            "memory_pressure_percent": memory_pressure * 100,
            "context_length": context_length
        }

    def create_custom_config(
        self,
        gpu_layer_ratio: float = 0.5,
        context_length: int = 32768,
        optimize_for: str = "balanced"  # "performance", "memory", "balanced"
    ) -> OffloadConfig:
        """
        创建自定义配置

        Args:
            gpu_layer_ratio: GPU层比例(0-1)
            context_length: 上下文长度
            optimize_for: 优化目标

        Returns:
            OffloadConfig: 自定义配置
        """
        total_layers = self._estimate_total_layers()
        gpu_layers = int(total_layers * max(0, min(1, gpu_layer_ratio)))

        n_threads = self.system_info.cpu_count
        use_mmap = optimize_for != "performance"

        config = OffloadConfig(
            n_gpu_layers=gpu_layers,
            n_ctx=context_length,
            n_threads=n_threads,
            use_mmap=use_mmap
        )

        logger.info(f"自定义配置: {gpu_layers}/{total_layers}层GPU, "
                   f"优化={optimize_for}")

        return config

    def optimize_for_inference(
        self,
        max_memory_gb: float | None = None,
        target_tokens_per_second: float | None = None
    ) -> OffloadConfig:
        """
        针对推理优化配置

        Args:
            max_memory_gb: 最大内存限制(GB)
            target_tokens_per_second: 目标生成速度(tokens/秒)

        Returns:
            OffloadConfig: 优化后的配置
        """
        # 如果有内存限制
        if max_memory_gb is not None:
            max_ratio = max_memory_gb / self.model_memory_gb
            if max_ratio < 1.0:
                # 内存不足,使用内存优先策略
                _, config = self.recommend_strategy(
                    allow_cpu_fallback=True
                )
                # 进一步限制上下文
                config.n_ctx = int(config.n_ctx * max_ratio * 0.8)
                return config

        # 如果有速度目标
        if target_tokens_per_second is not None:
            # 反推需要的GPU层数
            base_cpu_speed = 15.0
            base_gpu_speed = base_cpu_speed * self.PERFORMANCE_FACTORS["gpu_speedup"]

            required_gpu_ratio = ((target_tokens_per_second - base_cpu_speed) /
                                 (base_gpu_speed - base_cpu_speed))
            required_gpu_ratio = max(0, min(1, required_gpu_ratio))

            total_layers = self._estimate_total_layers()
            gpu_layers = int(total_layers * required_gpu_ratio)

            config = OffloadConfig(
                n_gpu_layers=gpu_layers,
                n_ctx=32768,
                n_threads=self.system_info.cpu_count
            )

            logger.info(f"速度优化: 目标{target_tokens_per_second} t/s, "
                       f"需要{gpu_layers}/{total_layers}层GPU")
            return config

        # 默认推荐
        _, config = self.recommend_strategy()
        return config

    def print_analysis(self):
        """打印系统分析报告"""
        print("\n" + "=" * 80)
        print("📊 模型层卸载策略分析")
        print("=" * 80)
        print()
        print("🖥️  系统信息:")
        print(f"   总内存: {self.system_info.total_memory_gb:.2f} GB")
        print(f"   可用内存: {self.system_info.available_memory_gb:.2f} GB")
        print(f"   内存使用率: {self.system_info.memory_usage_percent:.1f}%")
        print(f"   CPU核心数: {self.system_info.cpu_count}")
        print()
        print("🤖 模型信息:")
        print(f"   模型: {self.model_name}")
        print(f"   量化: {self.quantization}")
        print(f"   估算内存: {self.model_memory_gb:.2f} GB")
        print(f"   估算层数: {self._estimate_total_layers()} 层")
        print()

        # 推荐策略
        strategy, config = self.recommend_strategy()
        print("💡 推荐策略:")
        print(f"   策略: {strategy.value.upper()}")
        print(f"   GPU层数: {config.n_gpu_layers if config.n_gpu_layers != -1 else '全部'}")
        print(f"   上下文: {config.n_ctx} tokens")
        print(f"   CPU线程: {config.n_threads}")
        print()

        # 性能预测
        performance = self.predict_performance(config)
        print("📈 性能预测:")
        print(f"   生成速度: {performance['estimated_tokens_per_second']:.2f} tokens/秒")
        print(f"   加载时间: {performance['estimated_load_time_seconds']:.2f} 秒")
        print(f"   GPU层比例: {performance['gpu_layer_ratio']:.1%}")
        print(f"   内存压力: {performance['memory_pressure_percent']:.1f}%")
        print()

        # 不同策略对比
        print("🔄 策略对比:")
        print(f"   {'策略':<15} {'GPU层数':<10} {'速度(t/s)':<12} {'内存(GB)':<10}")
        print("-" * 80)

        strategies_to_compare = [
            (OffloadStrategy.ALL_GPU, OffloadConfig(n_gpu_layers=-1, n_ctx=32768)),
            (OffloadStrategy.PERFORMANCE, OffloadConfig(n_gpu_layers=int(self._estimate_total_layers() * 0.8), n_ctx=32768)),
            (OffloadStrategy.AUTO_BALANCE, OffloadConfig(n_gpu_layers=int(self._estimate_total_layers() * 0.5), n_ctx=32768)),
            (OffloadStrategy.MEMORY, OffloadConfig(n_gpu_layers=int(self._estimate_total_layers() * 0.3), n_ctx=16384)),
            (OffloadStrategy.ALL_CPU, OffloadConfig(n_gpu_layers=0, n_ctx=8192)),
        ]

        for strategy_name, cfg in strategies_to_compare:
            perf = self.predict_performance(cfg)
            gpu_layers_str = (str(cfg.n_gpu_layers) if cfg.n_gpu_layers > 0 else
                             "全部" if cfg.n_gpu_layers == -1 else "0")
            print(f"   {strategy_name.value.upper():<15} {gpu_layers_str:<10} "
                  f"{perf['estimated_tokens_per_second']:<12.2f} "
                  f"{self.model_memory_gb * (0.3 if cfg.n_gpu_layers == 0 else (0.5 + 0.5 * perf['gpu_layer_ratio'])):<10.2f}")

        print()
        print("=" * 80)


# 便捷函数
def analyze_model_offloading(
    model_name: str,
    quantization: str = "q4_k_m"
) -> LayerOffloadManager:
    """
    分析模型卸载策略

    Args:
        model_name: 模型名称
        quantization: 量化方式

    Returns:
        LayerOffloadManager: 管理器实例
    """
    manager = LayerOffloadManager(model_name, quantization)
    manager.print_analysis()
    return manager


def get_optimal_config(
    model_name: str,
    quantization: str = "q4_k_m",
    strategy: str | None = None
) -> OffloadConfig:
    """
    获取最优配置

    Args:
        model_name: 模型名称
        quantization: 量化方式
        strategy: 策略名称(可选,默认自动推荐)

    Returns:
        OffloadConfig: 最优配置
    """
    manager = LayerOffloadManager(model_name, quantization)

    if strategy is None:
        _, config = manager.recommend_strategy()
    else:
        strategy_enum = OffloadStrategy(strategy)
        if strategy_enum == OffloadStrategy.CUSTOM:
            config = manager.create_custom_config(gpu_layer_ratio=0.5)
        else:
            _, config = manager.recommend_strategy()

    return config
