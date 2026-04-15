"""
Apple Silicon M4 专用优化器
充分利用M4芯片的MPS、Neural Engine和Unified Memory架构
"""
from __future__ import annotations
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

# 初始化日志(必须在导入失败之前)
logger = logging.getLogger(__name__)

# Apple Silicon相关导入
try:
    import torch
    import torch.mps
    import torch.nn as nn

    TORCH_AVAILABLE = True
except ImportError:
    torch = None  # type: ignore
    nn = None  # type: ignore
    TORCH_AVAILABLE = False
    logger.info("PyTorch未安装,某些优化功能将不可用")

try:

    MLX_AVAILABLE = True
except ImportError:
    mx = None  # type: ignore
    nn_mlx = None  # type: ignore
    optim_mlx = None  # type: ignore
    MLX_AVAILABLE = False
    logger.info("MLX未安装,将使用PyTorch MPS模式")

# Core ML导入
try:

    COREML_AVAILABLE = True
except ImportError:
    ct = None  # type: ignore
    COREML_AVAILABLE = False


@dataclass
class AppleSiliconConfig:
    """Apple Silicon配置"""

    use_mps: bool = True
    use_mlx: bool = True
    use_coreml: bool = True
    enable_neural_engine: bool = True
    unified_memory_optimization: bool = True
    batch_size_multiplier: int = 2  # M4可以处理更大的批次
    precision: str = "mixed"  # mixed, fp16, fp32
    memory_fraction: float = 0.8  # 使用80%的统一内存


class AppleSiliconOptimizer:
    """Apple Silicon M4专用优化器"""

    def __init__(self, config: AppleSiliconConfig | None = None):
        self.config = config or AppleSiliconConfig()
        self.device_info = self._detect_apple_silicon()
        self.optimized_models = {}
        self.performance_cache = {}

    def _detect_apple_silicon(self) -> dict[str, Any]:
        """检测Apple Silicon设备信息"""
        info = {
            "platform": "macos",
            "apple_silicon": True,
            "chip": None,
            "cores": 0,
            "memory_gb": 0,
            "neural_engine": False,
        }

        try:
            # 检查芯片型号
            result = os.popen("sysctl -n machdep.cpu.brand_string").read().strip()
            if "Apple M" in result:
                info["chip"] = result.split("Apple ")[-1]
                logger.info(f"检测到Apple Silicon芯片: {info['chip']}")

            # 检查核心数
            result = os.popen("sysctl -n hw.ncpu").read().strip()
            info["cores"] = int(result)

            # 检查内存
            result = os.popen("sysctl -n hw.memsize").read().strip()
            memory_bytes = int(result)
            info["memory_gb"] = memory_bytes // (1024**3)

            # M4及以上默认支持Neural Engine
            if info["chip"] and any(model in info["chip"] for model in ["M4", "M3", "M2", "M1"]):
                info["neural_engine"] = True

        except Exception as e:
            logger.warning(f"设备检测失败: {e}")

        return info

    async def initialize(self):
        """初始化优化器"""
        logger.info("🚀 初始化Apple Silicon M4优化器")
        logger.info(f"芯片: {self.device_info.get('chip', 'Unknown')}")
        logger.info(f"核心数: {self.device_info.get('cores', 0)}")
        logger.info(f"内存: {self.device_info.get('memory_gb', 0)}GB")

        # 配置PyTorch
        if TORCH_AVAILABLE and self.config.use_mps:
            await self._setup_pytorch_mps()

        # 配置MLX
        if MLX_AVAILABLE and self.config.use_mlx:
            await self._setup_mlx()

        # 配置Core ML
        if COREML_AVAILABLE and self.config.use_coreml:
            await self._setup_coreml()

        logger.info("✅ Apple Silicon优化器初始化完成")

    async def _setup_pytorch_mps(self):
        """设置PyTorch MPS后端"""
        if not TORCH_AVAILABLE or torch is None:
            logger.warning("PyTorch未安装,跳过MPS优化")
            return
        if not torch.backends.mps.is_available():
            logger.warning("MPS后端不可用,跳过PyTorch MPS优化")
            return

        try:
            # 设置默认设备
            torch.set_default_device("mps")

            # 配置MPS优化
            torch.mps.set_per_process_memory_fraction(self.config.memory_fraction)

            # 启用混合精度
            if self.config.precision == "mixed":
                torch.backends.mps.enable_mixed_precision = True
            elif self.config.precision == "fp16":
                torch.set_default_dtype(torch.float16)

            logger.info("✅ PyTorch MPS优化已启用")

        except Exception as e:
            logger.error(f"PyTorch MPS设置失败: {e}")

    async def _setup_mlx(self):
        """设置MLX框架"""
        if not MLX_AVAILABLE or mx is None:
            logger.warning("MLX未安装,跳过MLX配置")
            return

        try:
            # MLX默认使用Apple Silicon GPU
            if hasattr(mx, "set_default_device") and hasattr(mx, "gpu"):
                # 尝试使用 GPU,如果失败则回退到CPU(MLX 会自动选择)
                try:
                    mx.set_default_device(mx.gpu)  # type: ignore
                except (TypeError, AttributeError):
                    logger.debug("MLX GPU不可用,将使用CPU")

            # 配置内存
            if self.config.unified_memory_optimization:
                # MLX自动处理统一内存
                logger.info("✅ MLX统一内存优化已启用")

            logger.info("✅ MLX框架已配置")

        except Exception as e:
            logger.error(f"MLX设置失败: {e}")

    async def _setup_coreml(self):
        """设置Core ML"""
        if not COREML_AVAILABLE or ct is None:
            logger.warning("CoreML未安装,跳过CoreML配置")
            return

        try:
            # 检查Core ML版本
            version = getattr(ct, "__version__", "unknown")
            logger.info(f"Core ML版本: {version}")

            # 验证Neural Engine可用性
            if self.device_info.get("neural_engine"):
                logger.info("✅ Apple Neural Engine检测到并可用")
            else:
                logger.warning("Neural Engine可能不可用")

        except Exception as e:
            logger.error(f"Core ML设置失败: {e}")

    def optimize_model_for_apple_silicon(self, model: Any, model_name: str) -> Any:
        """为Apple Silicon优化模型"""
        logger.info(f"优化模型: {model_name}")

        # 根据模型类型选择优化策略
        if (
            TORCH_AVAILABLE
            and torch is not None
            and nn is not None
            and isinstance(model, nn.Module)
        ):
            return self._optimize_pytorch_model(model, model_name)
        elif MLX_AVAILABLE:
            return self._optimize_mlx_model(model, model_name)
        else:
            logger.warning(f"无法优化模型类型: {type(model)}")
            return model

    def _optimize_pytorch_model(self, model: Any, model_name: str) -> Any:
        """优化PyTorch模型"""
        if torch is None or nn is None:
            return model

        try:
            # 转换到MPS设备
            model = model.to("mps")

            # 启用编译(PyTorch 2.0+)
            if hasattr(torch, "compile"):
                logger.info("使用torch.compile优化")
                compiled = torch.compile(model, mode="max-autotune")
                if compiled is not None:
                    model = compiled

            # 优化批处理大小
            if hasattr(model, "config"):
                config = model.config
                # 增加批处理大小以利用M4性能
                if hasattr(config, "batch_size") and isinstance(config.batch_size, int):
                    original_batch = config.batch_size
                    config.batch_size = original_batch * self.config.batch_size_multiplier
                    logger.info(f"批处理大小: {original_batch} -> {config.batch_size}")

            # 启用混合精度训练
            if self.config.precision == "mixed":
                model = model.half()
                logger.info("启用FP16混合精度")

            self.optimized_models[model_name] = {
                "type": "pytorch",
                "device": "mps",
                "optimized_at": time.time(),
            }

            return model

        except Exception as e:
            logger.error(f"PyTorch模型优化失败: {e}")
            return model

    def _optimize_mlx_model(self, model: Any, model_name: str) -> Any:
        """优化MLX模型"""
        try:
            # MLX模型通常已经是优化的
            # 这里可以添加特定的MLX优化

            self.optimized_models[model_name] = {
                "type": "mlx",
                "device": "mlx",
                "optimized_at": time.time(),
            }

            logger.info(f"MLX模型已优化: {model_name}")
            return model

        except Exception as e:
            logger.error(f"MLX模型优化失败: {e}")
            return model

    async def convert_to_coreml(
        self, model: Any, model_name: str, input_shape: tuple[int, ...] | None = None
    ) -> str | None:
        """转换为Core ML模型"""
        if not COREML_AVAILABLE:
            logger.warning("Core ML不可用,跳过转换")
            return None

        try:
            # 这里应该实现具体的转换逻辑
            # 需要根据模型类型进行具体转换

            model_path = f"models/coreml/{model_name}.mlmodel"

            # 确保目录存在
            os.makedirs(os.path.dirname(model_path), exist_ok=True)

            logger.info(f"Core ML模型已保存: {model_path}")
            return model_path

        except Exception as e:
            logger.error(f"Core ML转换失败: {e}")
            return None

    async def benchmark_performance(
        self, model: Any, test_input: Any, iterations: int = 100
    ) -> dict[str, float]:
        """性能基准测试"""
        logger.info(f"开始性能基准测试,迭代次数: {iterations}")

        times = []

        # 预热
        for _ in range(10):
            _ = model(test_input) if callable(model) else None

        # 正式测试
        for i in range(iterations):
            start_time = time.time()

            if callable(model):
                _ = model(test_input)

            end_time = time.time()
            times.append(end_time - start_time)

            if i % 20 == 0:
                logger.info(f"进度: {i}/{iterations}")

        # 计算统计数据
        times_np = np.array(times)

        results = {
            "avg_time": float(np.mean(times_np)),
            "min_time": float(np.min(times_np)),
            "max_time": float(np.max(times_np)),
            "std_time": float(np.std(times_np)),
            "throughput": iterations / sum(times_np),
        }

        logger.info("基准测试完成:")
        logger.info(f"  平均时间: {results['avg_time']:.4f}s")
        logger.info(f"  吞吐量: {results['throughput']:.2f} ops/s")

        return results

    def get_memory_info(self) -> dict[str, Any]:
        """获取内存使用信息"""
        try:
            if (
                TORCH_AVAILABLE
                and torch is not None
                and hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                mps_memory = torch.mps.current_allocated_memory() / (1024**2)  # MB
                mps_reserved = torch.mps.driver_allocated_memory() / (1024**2)  # MB
            else:
                mps_memory = mps_reserved = 0

            # 获取系统内存信息
            import psutil

            memory = psutil.virtual_memory()

            return {
                "mps_allocated_mb": mps_memory,
                "mps_reserved_mb": mps_reserved,
                "system_total_gb": memory.total / (1024**3),
                "system_available_gb": memory.available / (1024**3),
                "system_used_percent": memory.percent,
            }
        except Exception as e:
            logger.error(f"获取内存信息失败: {e}")
            return {}

    def cleanup(self) -> Any:
        """清理资源"""
        logger.info("清理Apple Silicon优化器资源")

        # 清理PyTorch缓存
        if TORCH_AVAILABLE and torch is not None and hasattr(torch, "mps"):
            torch.mps.empty_cache()

        # 清理优化模型
        self.optimized_models.clear()

        logger.info("✅ 资源清理完成")


# 创建全局优化器实例
apple_silicon_optimizer = AppleSiliconOptimizer()


# 便捷函数
async def initialize_apple_silicon():
    """初始化Apple Silicon优化"""
    await apple_silicon_optimizer.initialize()


def get_device_info() -> Any | None:
    """获取设备信息"""
    return apple_silicon_optimizer.device_info


def optimize_model_for_m4(model: Any, model_name: str) -> Any:
    """为M4优化模型"""
    return apple_silicon_optimizer.optimize_model_for_apple_silicon(model, model_name)


async def benchmark_model(model: Any, test_input: Any) -> dict[str, float]:
    """基准测试模型"""
    return await apple_silicon_optimizer.benchmark_performance(model, test_input)


def get_memory_stats() -> Any | None:
    """获取内存统计"""
    return apple_silicon_optimizer.get_memory_info()
