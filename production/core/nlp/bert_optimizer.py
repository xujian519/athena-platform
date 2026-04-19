#!/usr/bin/env python3
"""
BERT优化器
BERT Optimizer for Athena Platform

优化BERT模型的加载速度和推理性能

作者: 小诺·双鱼座
创建时间: 2025-12-16
"""

from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any

import torch

logger = logging.getLogger(__name__)


class BERTOptimizer:
    """BERT模型优化器"""

    @staticmethod
    def optimize_model_loading(model: Any) -> None:
        """优化模型加载性能"""
        # 1. 启用半精度推理
        if hasattr(model, "half"):
            model = model.half()
            logger.info("✅ 启用半精度推理")

        # 2. 启用推理模式
        if hasattr(model, "eval"):
            model.eval()

        # 3. 优化设备选择
        device = BERTOptimizer.get_optimal_device()
        if device != "cpu":
            model = model.to(device)
            logger.info(f"✅ 使用设备: {device}")

        # 4. 使用TorchScript编译(可选)
        # try:
        #     model = torch.jit.script(model)
        #     logger.info("✅ 启用TorchScript编译")
        # except Exception as e:
        #     logger.warning(f"TorchScript编译失败: {e}")

        return model

    @staticmethod
    def get_optimal_device() -> Any:
        """获取最优设备"""
        # 检查CUDA
        if torch.cuda.is_available():
            device = "cuda"
            # 检查MPS(Apple Silicon)
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

        logger.info(f"检测到设备: {device}")
        return device

    @staticmethod
    def optimize_tokenizer(tokenizer: Any) -> None:
        """优化tokenizer"""
        # 1. 使用fast tokenizer
        if hasattr(tokenizer, "use_fast"):
            tokenizer.use_fast = True
            logger.info("✅ 启用fast tokenizer")

        return tokenizer

    @staticmethod
    def optimize_cache_config(cache_dir: str) -> Any:
        """优化缓存配置"""
        cache_path = Path(cache_dir)

        # 设置环境变量优化缓存
        os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
        os.environ["HF_HOME"] = str(cache_path)
        os.environ["HUGGINGFACE_HUB_CACHE"] = str(cache_path)

        # 创建缓存目录
        cache_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"✅ 缓存目录: {cache_path}")

    @staticmethod
    def optimize_pytorch() -> Any:
        """优化PyTorch性能"""
        # 1. 设置num_threads
        if hasattr(torch, "set_num_threads"):
            torch.set_num_threads(4)

        # 2. 启用MKL(Intel CPU)
        os.environ["OMP_NUM_THREADS"] = "4"
        os.environ["MKL_NUM_THREADS"] = "4"

        # 3. 优化内存分配
        if hasattr(torch, "cuda"):
            torch.cuda.empty_cache()

        logger.info("✅ PyTorch优化配置完成")

    @staticmethod
    def create_lightweight_config() -> Any:
        """创建轻量级配置"""
        return {
            "torch_dtype": "float16",  # 使用半精度
            "low_cpu_mem_usage": True,
            "use_cache": True,
            "use_fast_tokenizer": True,
            "model_kwargs": {"torch_dtype": "float16", "low_cpu_mem_usage": True},
            "tokenizer_kwargs": {"use_fast": True},
        }


# 便捷函数
def setup_bert_optimization() -> Any:
    """设置BERT优化"""
    BERTOptimizer.optimize_pytorch()
    logger.info("🚀 BERT优化配置已启用")


def get_optimal_device() -> Any | None:
    """获取最优设备"""
    return BERTOptimizer.get_optimal_device()
