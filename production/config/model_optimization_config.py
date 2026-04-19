#!/usr/bin/env python3
"""
模型优化配置
Model Optimization Configuration for Apple Silicon

针对Apple M4 Pro的优化配置：
1. 使用国内镜像站下载模型
2. 启用MPS加速
3. 内存优化配置
4. 批处理优化

作者: Athena平台团队
创建时间: 2025-12-26
版本: v1.0.0 "Apple Silicon优化"
"""

from __future__ import annotations
import logging
import os
from typing import Any

# torch条件导入
try:
    import torch
except ImportError:
    torch = None

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AppleSiliconOptimizer:
    """Apple Silicon优化器"""

    def __init__(self):
        self.chip_type = "Apple M4 Pro"
        self.memory_gb = 48

    def configure_mirrors(self) -> Any:
        """配置国内镜像站"""
        # HF镜像站
        os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

        # 模型缓存目录（使用SSD）
        cache_dir = os.path.expanduser('~/Athena工作平台/models/cache')
        os.environ['HF_HOME'] = cache_dir
        os.environ['HUGGINGFACE_HUB_CACHE'] = os.path.join(cache_dir, 'hub')

        # 确保目录存在
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'hub'), exist_ok=True)

        logger.info(f"✅ 镜像站配置完成: {os.environ['HF_ENDPOINT']}")
        logger.info(f"✅ 模型缓存目录: {cache_dir}")

    def configure_torch_optimization(self) -> Any:
        """配置PyTorch优化"""
        import torch

        # 启用MPS（Metal Performance Shaders）
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info(f"✅ MPS设备已启用: {device}")

            # 设置MPS内存配置（M4有48GB，可以分配较大内存）
            # 预留8GB给系统，使用40GB用于模型
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'

            return device
        else:
            logger.warning("⚠️ MPS不可用，使用CPU")
            return torch.device("cpu")

    def get_optimal_batch_size(self, model_name: str) -> int:
        """获取最优批处理大小"""
        # M4 Pro有48GB内存，可以设置较大的batch size
        batch_sizes = {
            "t5-base": 32,
            "t5-small": 64,
            "bert-base-chinese": 64,
            "gpt2": 16,
            "default": 32
        }
        return batch_sizes.get(model_name, batch_sizes["default"])

    def configure_model_loading(self) -> Any:
        """配置模型加载参数"""
        return {
            "low_cpu_mem_usage": True,
            "use_safetensors": True,
            # M4支持bf16
            "torch_dtype": "float32",  # T5在MPS上使用float32更稳定
            "device_map": "auto" if torch.backends.mps.is_available() else None,
        }

    def get_inference_kwargs(self) -> Any | None:
        """获取推理优化参数"""
        return {
            "max_length": 512,
            "num_beams": 4,
            "early_stopping": True,
            "length_penalty": 1.0,
        }


def setup_model_optimization() -> Any:
    """设置模型优化"""
    optimizer = AppleSiliconOptimizer()

    # 配置镜像站
    optimizer.configure_mirrors()

    # 配置PyTorch
    device = optimizer.configure_torch_optimization()

    logger.info("✅ 模型优化配置完成")
    return optimizer, device


# 便捷函数
_optimizer = None
_device = None


def get_optimizer() -> Any | None:
    """获取优化器单例"""
    global _optimizer, _device
    if _optimizer is None:
        _optimizer, _device = setup_model_optimization()
    return _optimizer, _device


if __name__ == "__main__":
    optimizer, device = setup_model_optimization()

    print("\n🚀 Apple Silicon优化配置")
    print(f"芯片: {optimizer.chip_type}")
    print(f"内存: {optimizer.memory_gb}GB")
    print(f"设备: {device}")
    print(f"镜像站: {os.environ.get('HF_ENDPOINT', '未设置')}")
    print(f"缓存目录: {os.environ.get('HF_HOME', '未设置')}")
