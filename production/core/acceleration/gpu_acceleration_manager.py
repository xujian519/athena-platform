from __future__ import annotations
"""
GPU加速管理器
支持Apple Silicon M4的GPU加速功能
"""
import asyncio
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

# GPU相关导入
try:
    import torch
    import torch.mps
    import torch.nn as nn
    from torch.cuda.amp import GradScaler, autocast

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import mlx.core as mx
    MLX_AVAILABLE = True
except ImportError:
    MLX_AVAILABLE = False

try:
    import jax
    JAX_AVAILABLE = True
except ImportError:
    JAX_AVAILABLE = False

logger = logging.getLogger(__name__)


class GPUBackend(Enum):
    """GPU后端类型"""

    MPS = "mps"  # Apple Silicon Metal Performance Shaders
    MLX = "mlx"  # Apple Silicon MLX
    JAX = "jax"  # JAX (支持Apple Silicon)
    CUDA = "cuda"  # NVIDIA CUDA
    CPU = "cpu"  # CPU回退


@dataclass
class GPUConfig:
    """GPU配置"""

    backend: GPUBackend = GPUBackend.MPS
    memory_fraction: float = 0.8
    mixed_precision: bool = True
    enable_dynamic_batching: bool = True
    max_batch_size: int = 128
    min_batch_size: int = 1
    compilation: bool = True
    enable_profiling: bool = False
    cache_size: int = 1000


@dataclass
class GPUMetrics:
    """GPU性能指标"""

    utilization: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 0.0
    temperature: float = 0.0
    power_consumption: float = 0.0


class GPUAccelerator:
    """GPU加速器基类"""

    def __init__(self, name: str, config: GPUConfig):
        self.name = name
        self.config = config
        self.device = None
        self.is_available = False
        self.metrics = GPUMetrics()
        self.performance_cache = {}

    async def initialize(self):
        """初始化GPU加速器"""
        raise NotImplementedError

    async def optimize_model(self, model: Any) -> Any:
        """优化模型"""
        raise NotImplementedError

    async def benchmark(
        self, model: Any, test_input: Any, iterations: int = 100
    ) -> dict[str, float]:
        """性能基准测试"""
        raise NotImplementedError

    async def get_metrics(self) -> GPUMetrics:
        """获取GPU指标"""
        return self.metrics


class MPSAccelerator(GPUAccelerator):
    """MPS加速器(Apple Silicon)"""

    def __init__(self, config: GPUConfig):
        super().__init__("MPS", config)
        self.grad_scaler = None

    async def initialize(self):
        """初始化MPS加速器"""
        if not TORCH_AVAILABLE:
            logger.error("PyTorch不可用,无法使用MPS加速")
            return

        if not torch.backends.mps.is_available():
            logger.error("MPS后端不可用")
            return

        try:
            # 配置MPS
            self.device = torch.device("mps")

            # 设置内存分配
            torch.mps.set_per_process_memory_fraction(self.config.memory_fraction)

            # 混合精度配置
            if self.config.mixed_precision:
                self.grad_scaler = GradScaler()
                torch.backends.mps.enable_mixed_precision = True

            # 启用编译
            if self.config.compilation and hasattr(torch, "compile"):
                logger.info("启用PyTorch 2.0编译优化")

            self.is_available = True
            logger.info("✅ MPS加速器初始化成功")

        except Exception as e:
            logger.error(f"MPS初始化失败: {e}")

    async def optimize_model(self, model: nn.Module) -> nn.Module:
        """优化PyTorch模型"""
        if not self.is_available:
            return model

        try:
            # 移动到MPS设备
            model = model.to(self.device)

            # 编译优化
            if self.config.compilation and hasattr(torch, "compile"):
                logger.info(f"编译模型: {model.__class__.__name__}")
                model = torch.compile(model, mode="max-autotune")

            # 启用混合精度
            if self.config.mixed_precision:
                logger.info("启用混合精度训练")
                model = model.half()

            # 动态批处理
            if self.config.enable_dynamic_batching:
                model = self._enable_dynamic_batching(model)

            logger.info("✅ 模型优化完成")
            return model

        except Exception as e:
            logger.error(f"模型优化失败: {e}")
            return model

    def _enable_dynamic_batching(self, model: nn.Module) -> nn.Module:
        """启用动态批处理"""
        original_forward = model.forward

        def dynamic_forward(*args, **kwargs) -> Any:
            # 动态调整批处理大小
            batch_size = args[0].size(0) if args and hasattr(args[0], "size") else 1
            batch_size = min(
                max(batch_size, self.config.min_batch_size), self.config.max_batch_size
            )

            # 如果需要,调整输入批处理大小
            if args and hasattr(args[0], "resize_"):
                args = (args[0][:batch_size], *args[1:])

            return original_forward(*args, **kwargs)

        model.forward = dynamic_forward
        return model

    @asynccontextmanager
    async def autocast_context(self):
        """混合精度上下文"""
        if self.config.mixed_precision and self.grad_scaler:
            with autocast(device_type="mps"):
                yield
        else:
            yield

    async def benchmark(
        self, model: nn.Module, test_input: torch.Tensor, iterations: int = 100
    ) -> dict[str, float]:
        """MPS性能基准测试"""
        if not self.is_available:
            return {"error": "MPS不可用"}

        model = model.to(self.device)
        test_input = test_input.to(self.device)

        # 预热
        for _ in range(10):
            with torch.no_grad():
                _ = model(test_input)

        torch.mps.synchronize()

        # 正式测试
        times = []
        memory_usage = []

        for i in range(iterations):
            start_time = time.time()

            # 记录内存使用
            memory_mb = torch.mps.current_allocated_memory() / (1024**2)
            memory_usage.append(memory_mb)

            with torch.no_grad():
                model(test_input)

            torch.mps.synchronize()
            end_time = time.time()
            times.append(end_time - start_time)

            if i % 20 == 0:
                logger.info(f"进度: {i}/{iterations}")

        # 计算统计
        times_array = np.array(times)
        memory_array = np.array(memory_usage)

        return {
            "avg_time": float(np.mean(times_array)),
            "min_time": float(np.min(times_array)),
            "max_time": float(np.max(times_array)),
            "std_time": float(np.std(times_array)),
            "throughput": iterations / np.sum(times_array),
            "avg_memory_mb": float(np.mean(memory_array)),
            "peak_memory_mb": float(np.max(memory_array)),
        }

    async def get_metrics(self) -> GPUMetrics:
        """获取MPS指标"""
        if not self.is_available:
            return self.metrics

        try:
            # 内存使用
            allocated_mb = torch.mps.current_allocated_memory() / (1024**2)
            torch.mps.driver_allocated_memory() / (1024**2)

            # 系统信息
            import psutil

            memory_info = psutil.virtual_memory()
            total_memory_gb = memory_info.total / (1024**3)

            self.metrics.memory_used = allocated_mb
            self.metrics.memory_total = total_memory_gb * 1024  # 转换为MB
            self.metrics.utilization = (allocated_mb / (total_memory_gb * 1024)) * 100

        except Exception as e:
            logger.error(f"获取MPS指标失败: {e}")

        return self.metrics


class MLXAccelerator(GPUAccelerator):
    """MLX加速器(Apple Silicon专用)"""

    def __init__(self, config: GPUConfig):
        super().__init__("MLX", config)
        self.optimized_models = {}

    async def initialize(self):
        """初始化MLX加速器"""
        if not MLX_AVAILABLE:
            logger.error("MLX不可用,无法使用MLX加速")
            return

        try:
            # 设置默认设备
            mx.set_default_device(mx.gpu)

            # 配置内存
            if hasattr(mx, "set_memory_limit"):
                memory_gb = self.config.memory_fraction * 8  # 假设8GB内存
                mx.set_memory_limit(memory_gb)

            self.is_available = True
            logger.info("✅ MLX加速器初始化成功")

        except Exception as e:
            logger.error(f"MLX初始化失败: {e}")

    async def optimize_model(self, model: Any) -> Any:
        """优化MLX模型"""
        if not self.is_available:
            return model

        try:
            # MLX通常不需要额外的优化
            # 但可以在这里添加特定的优化逻辑
            logger.info("✅ MLX模型优化完成")
            return model

        except Exception as e:
            logger.error(f"MLX模型优化失败: {e}")
            return model

    async def benchmark(
        self, model: Any, test_input: Any, iterations: int = 100
    ) -> dict[str, float]:
        """MLX性能基准测试"""
        if not self.is_available:
            return {"error": "MLX不可用"}

        times = []

        for i in range(iterations):
            start_time = time.time()

            # 执行模型
            if callable(model):
                model(test_input)

            end_time = time.time()
            times.append(end_time - start_time)

            if i % 20 == 0:
                logger.info(f"进度: {i}/{iterations}")

        times_array = np.array(times)
        return {
            "avg_time": float(np.mean(times_array)),
            "min_time": float(np.min(times_array)),
            "max_time": float(np.max(times_array)),
            "std_time": float(np.std(times_array)),
            "throughput": iterations / np.sum(times_array),
        }


class GPUAccelerationManager:
    """GPU加速管理器"""

    def __init__(self, config: GPUConfig | None = None):
        self.config = config or GPUConfig()
        self.accelerators = {}
        self.default_accelerator = None
        self.is_initialized = False

    async def initialize(self):
        """初始化GPU加速管理器"""
        logger.info("🚀 初始化GPU加速管理器")

        # 初始化后端优先级列表
        backends = [GPUBackend.MPS, GPUBackend.MLX, GPUBackend.CUDA, GPUBackend.CPU]

        for backend in backends:
            try:
                accelerator = await self._create_accelerator(backend)
                if accelerator and await self._test_accelerator(accelerator):
                    self.accelerators[backend] = accelerator
                    logger.info(f"✅ {backend.value} 后端可用")

                    # 设置默认加速器(优先使用MPS)
                    if not self.default_accelerator and backend in [GPUBackend.MPS, GPUBackend.MLX]:
                        self.default_accelerator = accelerator
                        logger.info(f"设置默认加速器: {backend.value}")
                else:
                    logger.info(f"⚠️ {backend.value} 后端不可用")
            except Exception as e:
                logger.error(f"{backend.value} 初始化失败: {e}")

        if self.accelerators:
            self.is_initialized = True
            logger.info(f"✅ GPU加速管理器初始化完成,可用后端: {list(self.accelerators.keys())}")
        else:
            logger.warning("❌ 没有可用的GPU后端")

    async def _create_accelerator(self, backend: GPUBackend) -> GPUAccelerator:
        """创建加速器"""
        if backend == GPUBackend.MPS:
            return MPSAccelerator(self.config)
        elif backend == GPUBackend.MLX:
            return MLXAccelerator(self.config)
        else:
            raise ValueError(f"不支持的后端: {backend}")

    async def _test_accelerator(self, accelerator: GPUAccelerator) -> bool:
        """测试加速器"""
        try:
            await accelerator.initialize()
            return accelerator.is_available
        except Exception as e:
            logger.error(f"加速器测试失败: {e}")
            return False

    async def optimize_model(self, model: Any, backend: GPUBackend | None = None) -> Any:
        """优化模型"""
        if not self.is_initialized:
            logger.warning("GPU加速管理器未初始化")
            return model

        # 选择加速器
        if backend:
            accelerator = self.accelerators.get(backend)
            if not accelerator:
                logger.error(f"后端 {backend.value} 不可用")
                return model
        else:
            accelerator = self.default_accelerator
            if not accelerator:
                logger.warning("没有默认GPU加速器")
                return model

        # 优化模型
        return await accelerator.optimize_model(model)

    async def benchmark_model(
        self,
        model: Any,
        test_input: Any,
        backend: GPUBackend | None = None,
        iterations: int = 100,
    ) -> dict[str, Any]:
        """模型基准测试"""
        if not self.is_initialized:
            return {"error": "GPU加速管理器未初始化"}

        if backend:
            accelerator = self.accelerators.get(backend)
            if not accelerator:
                return {"error": f"后端 {backend.value} 不可用"}
        else:
            # 对所有可用后端进行基准测试
            results = {}
            for backend_name, accel in self.accelerators.items():
                try:
                    result = await accel.benchmark(model, test_input, iterations)
                    results[backend_name.value] = result
                except Exception as e:
                    results[backend_name.value] = {"error": str(e)}
            return results

        return await accelerator.benchmark(model, test_input, iterations)

    def get_available_backends(self) -> list[GPUBackend]:
        """获取可用的GPU后端"""
        return list(self.accelerators.keys())

    def get_default_backend(self) -> GPUBackend | None:
        """获取默认后端"""
        if self.default_accelerator:
            # 通过检查MPS是否可用来确定后端
            if isinstance(self.default_accelerator, MPSAccelerator):
                return GPUBackend.MPS
            elif isinstance(self.default_accelerator, MLXAccelerator):
                return GPUBackend.MLX
        return None

    async def get_metrics(self) -> dict[str, GPUMetrics]:
        """获取所有GPU指标"""
        metrics = {}
        for backend, accelerator in self.accelerators.items():
            try:
                metrics[backend.value] = await accelerator.get_metrics()
            except Exception:
                metrics[backend.value] = GPUMetrics()
        return metrics

    async def cleanup(self):
        """清理资源"""
        logger.info("清理GPU加速管理器")
        for accelerator in self.accelerators.values():
            if hasattr(accelerator, "cleanup"):
                await accelerator.cleanup()


# 创建全局GPU加速管理器
gpu_acceleration_manager = GPUAccelerationManager()


# 便捷函数
async def initialize_gpu_acceleration(config: GPUConfig | None = None):
    """初始化GPU加速"""
    await gpu_acceleration_manager.initialize(config)


def optimize_model_for_gpu(model: Any | None,
    backend: GPUBackend | None = None) -> Any:
    """为GPU优化模型"""
    return asyncio.run(gpu_acceleration_manager.optimize_model(model, backend))


def get_default_gpu_backend() -> Any | None:
    """获取默认GPU后端"""
    return gpu_acceleration_manager.get_default_backend()


def is_gpu_available() -> bool:
    """检查GPU是否可用"""
    return (
        gpu_acceleration_manager.is_initialized and len(gpu_acceleration_manager.accelerators) > 0
    )
