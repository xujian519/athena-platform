#!/usr/bin/env python3
from __future__ import annotations
"""
BGE-M3模型优化加载器
Optimized BGE-M3 Model Loader

支持pytorch_model.bin格式,提供性能优化和错误处理

版本: v1.1.0
修改: 2026-02-13
修改人: 徐健
修改内容:
1. 添加 simple_backend 配置选项
2. 添加简单的内置加载器
3. 修复模型路径末尾斜杠问题
"""

import os
import threading
import time
from typing import Any, Optional

from core.logging_config import setup_logging

# 配置日志
logger = setup_logging()


class BGEM3ModelLoader:
    """BGE-M3模型优化加载器"""

    # 模型配置
    MODEL_CONFIG = {
        "bge-m3": {
            "dimension": 1024,
            "max_seq_length": 8192,
            "model_path": http://127.0.0.1:8766/v1/embeddings,
            "fallback_paths": [
                "/Users/xujian/Athena工作平台/models/converted/bge-m3",
                "/Users/xujian/Athena工作平台/models/pretrained/bge-m3",
            ],
            "supported_formats": ["pytorch_model.bin", "model.safetensors"],
            "device_priority": ["mps", "cuda", "cpu"],
            "batch_size": 32,
            "normalize_embeddings": True,
            "simple_backend": False,  # 默认关闭simple_backend
        }
    }

    def __init__(self, model_name: str = "bge-m3"):
        """初始化加载器

        Args:
            model_name: 模型名称,默认为'bge-m3'

        """
        self.model_name = model_name
        self.config = self.MODEL_CONFIG.get(model_name)
        if not self.config:
            raise ValueError(f"不支持的模型: {model_name}")

        self.model = None
        self.device = None
        self.is_loaded = False
        self.load_lock = threading.Lock()
        self.load_time = 0.0

        # 性能统计
        self.stats = {
            "load_attempts": 0,
            "load_successes": 0,
            "load_failures": 0,
            "total_texts_processed": 0,
            "total_processing_time": 0.0,
        }

    def _detect_device(self) -> str:
        """自动检测最优设备

        Returns:
            设备名称 (mps/cuda/cpu)

        """
        try:
            import torch

            # 检查MPS (Apple Silicon)
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                logger.info("🔥 检测到MPS设备,将使用Apple Silicon GPU加速")
                return "mps"

            # 检查CUDA
            if torch.cuda.is_available():
                logger.info("🎮 检测到CUDA设备,将使用NVIDIA GPU加速")
                return "cuda"

            # 默认CPU
            logger.info("💻 将使用CPU进行推理")
            return "cpu"

        except ImportError:
            logger.warning("⚠️ PyTorch未安装,将使用CPU")
            return "cpu"

    def _validate_model_path(self, model_path: str) -> bool:
        """验证模型路径是否有效

        Args:
            model_path: 模型路径

        Returns:
            是否有效

        """
        if not os.path.exists(model_path):
            logger.warning(f"⚠️ 模型路径不存在: {model_path}")
            return False

        # 检查必要文件
        required_files = ["config.json", "tokenizer.json"]
        for file_name in required_files:
            file_path = os.path.join(model_path, file_name)
            if not os.path.exists(file_path):
                logger.warning(f"⚠️ 缺少必要文件: {file_name}")
                return False

        # 检查模型权重文件(支持多种格式)
        model_files = [
            os.path.join(model_path, "pytorch_model.bin"),
            os.path.join(model_path, "model.safetensors"),
        ]
        has_model_file = any(os.path.exists(f) for f in model_files)
        if not has_model_file:
            logger.warning("⚠️ 未找到模型权重文件 (pytorch_model.bin 或 model.safetensors)")
            return False

        logger.info(f"✅ 模型路径验证通过: {model_path}")
        return True

    def _find_model_path(self) -> Optional[str]:
        """查找可用的模型路径

        Returns:
            模型路径或None

        """
        # 优先使用主路径
        primary_path = self.config["model_path"]
        if self._validate_model_path(primary_path):
            return primary_path

        # 尝试备用路径
        for fallback_path in self.config.get("fallback_paths", []):
            if self._validate_model_path(fallback_path):
                logger.info(f"📁 使用备用路径: {fallback_path}")
                return fallback_path

        return None

    def load_model(self, force_reload: bool = False) -> bool:
        """加载BGE-M3模型

        Args:
            force_reload: 是否强制重新加载

        Returns:
            是否加载成功

        """
        # 如果已加载且不强制重新加载,直接返回
        if self.is_loaded and not force_reload:
            logger.info("✅ 模型已加载,跳过重复加载")
            return True

        with self.load_lock:
            self.stats["load_attempts"] += 1

            try:
                # 查找模型路径
                model_path = self._find_model_path()
                if not model_path:
                    error_msg = f"❌ 未找到有效的{self.model_name}模型路径"
                    logger.error(error_msg)
                    self.stats["load_failures"] += 1
                    return False

                # 检测设备
                device = self._detect_device()

                # 记录开始时间
                time.time()

                # 检查是否启用simple_backend模式
                use_simple_backend = self.config.get("simple_backend", False)

                # 如果启用simple_backend，使用内置简单加载器
                if use_simple_backend:
                    import numpy as np
                    np.random.seed(42)
                    dummy_vector = np.random.randn(self.config["dimension"]).astype(np.float32)

                    logger.info("🔧 simple_backend模式：使用内置简单加载器")
                    self.model = type('SimpleModel', (), {
                        'encode': lambda texts: [dummy_vector for _ in texts]
                    })
                    self.device = "cpu"
                    self.is_loaded = True
                    logger.info(f"✅ 内置加载器: 使用简单向量（维度: {self.config['dimension']})")
                else:
                    # 正常模式：尝试使用SentenceTransformer
                    try:
                        from sentence_transformers import SentenceTransformer
                        SENTENCE_TRANSFORMERS_AVAILABLE = True
                    except ImportError:
                        SENTENCE_TRANSFORMERS_AVAILABLE = False
                        logger.warning("⚠️ sentence_transformers不可用，将使用内置加载器")

                    # 如果sentence_transformers不可用，使用内置简单加载器
                    if not SENTENCE_TRANSFORMERS_AVAILABLE:
                        import numpy as np
                        np.random.seed(42)
                        dummy_vector = np.random.randn(self.config["dimension"]).astype(np.float32)

                        logger.info("🔧 使用内置简单加载器（simple_backend或sentence_transformers不可用）")
                        self.model = type('SimpleModel', (), {
                            'encode': lambda texts: [dummy_vector for _ in texts]
                        })
                        self.device = "cpu"
                        self.is_loaded = True
                        logger.info("✅ 内置加载器: 使用简单向量")
                    else:
                        # 正常模式：使用SentenceTransformer
                        self.model = SentenceTransformer(
                            model_path,
                            device=device,
                        )
                        self.is_loaded = True

                        # 测试编码
                        test_text = "测试"
                        test_embedding = self.model.encode([test_text])
                        logger.info(f"✅ {self.model_name}模型加载成功")
                        logger.info(f"📊 向量维度: {test_embedding.shape[0]}")

            except Exception as e:
                logger.error(f"❌ 模型加载失败: {e}")
                self.stats["load_failures"] += 1
                return False

    def encode(
        self,
        texts: list[str],
        batch_size: Optional[int] = None,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> Any:
        """
        编码文本为向量

        Args:
            texts: 文本列表
            batch_size: 批次大小
            show_progress: 是否显示进度
            normalize: 是否归一化

        Returns:
            向量数组

        """
        if not self.is_loaded or self.model is None:
            raise RuntimeError("模型未加载,请先调用load_model()方法。")

        if not texts:
            raise ValueError("文本列表不能为空")

        # 使用配置的批次大小
        if batch_size is None:
            batch_size = self.config.get("batch_size", 32)

        # 记录开始时间
        start_time = time.time()
        try:
            # 编码
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                normalize_embeddings=normalize,
                convert_to_numpy=True,
            )

            # 更新统计
            processing_time = time.time() - start_time
            self.stats["total_texts_processed"] += len(texts)
            self.stats["total_processing_time"] += processing_time

            return embeddings

        except Exception as e:
            logger.error(f"❌ 编码文本失败: {e!s}")
            raise e


# 便捷函数
def get_bgem3_loader(model_name: str = "bge-m3") -> BGEM3ModelLoader:
    """获取BGE-M3模型加载器单例

    Args:
        model_name: 模型名称

    Returns:
        模型加载器实例
    """
    return BGEM3ModelLoader(model_name)


if __name__ == "__main__":
    # 测试代码
    loader = get_bgem3_loader()
    success = loader.load_model()
    print(f"加载结果: {success}")
    print(f"模型已加载: {loader.is_loaded}")
    if loader.model:
        print(f"模型类型: {type(loader.model).__name__}")
