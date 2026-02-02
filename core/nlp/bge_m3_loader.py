#!/usr/bin/env python3
"""
BGE-M3模型优化加载器
Optimized BGE-M3 Model Loader

支持pytorch_model.bin格式,提供性能优化和错误处理
"""

import os
import threading
import time
from typing import Any, Dict, List, Optional

from core.logging_config import setup_logging

logger = setup_logging()


class BGEM3ModelLoader:
    """BGE-M3模型优化加载器"""

    # 模型配置
    MODEL_CONFIG = {
        "bge-m3": {
            "dimension": 1024,
            "max_seq_length": 8192,
            "model_path": "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3",
            "fallback_paths": [
                "/Users/xujian/Athena工作平台/models/converted/bge-m3",
                "/Users/xujian/Athena工作平台/models/pretrained/bge-m3",
            ],
            "supported_formats": ["pytorch_model.bin", "model.safetensors"],
            "device_priority": ["mps", "cuda", "cpu"],
            "batch_size": 32,
            "normalize_embeddings": True,
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

    def _find_model_path(self) -> str | None:
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
                start_time = time.time()

                # 导入SentenceTransformer
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError:
                    error_msg = (
                        "❌ sentence-transformers未安装,请运行: pip install sentence-transformers"
                    )
                    logger.error(error_msg)
                    self.stats["load_failures"] += 1
                    return False

                # 加载模型(支持pytorch_model.bin和model.safetensors)
                logger.info(f"🔄 正在加载{self.model_name}模型...")
                logger.info(f"📁 模型路径: {model_path}")
                logger.info(f"💻 设备: {device}")

                self.model = SentenceTransformer(
                    model_path,
                    device=device,
                )

                # 验证模型加载
                if self.model is None:
                    raise RuntimeError("模型加载返回None")

                # 获取实际配置
                actual_dimension = self.model.get_sentence_embedding_dimension()
                expected_dimension = self.config["dimension"]

                if actual_dimension != expected_dimension:
                    logger.warning(
                        f"⚠️ 向量维度不匹配: 期望{expected_dimension}, 实际{actual_dimension}"
                    )

                # 记录加载时间
                self.load_time = time.time() - start_time

                self.device = device
                self.is_loaded = True
                self.stats["load_successes"] += 1

                logger.info(f"✅ {self.model_name}模型加载成功!")
                logger.info(f"⏱️  加载时间: {self.load_time:.2f}秒")
                logger.info(f"📊 向量维度: {actual_dimension}")
                logger.info(f"🔗 最大序列长度: {self.config['max_seq_length']} tokens")

                return True

            except Exception as e:
                error_msg = f"❌ 加载{self.model_name}模型失败: {e!s}"
                logger.error(error_msg)
                # 打印完整堆栈跟踪
                import traceback

                logger.error(traceback.format_exc())
                self.stats["load_failures"] += 1
                self.is_loaded = False
                self.model = None
                return False

    def encode(
        self,
        texts: list[str],
        batch_size: int | None = None,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> Any:
        """编码文本为向量

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
            raise

    def encode_batch(
        self,
        texts: list[str],
        batch_size: int | None = None,
        show_progress: bool = False,
        normalize: bool = True,
    ) -> Any:
        """批量编码文本为向量(别名方法,与encode相同)

        Args:
            texts: 文本列表
            batch_size: 批次大小
            show_progress: 是否显示进度
            normalize: 是否归一化

        Returns:
            向量数组
        """
        return self.encode(
            texts, batch_size=batch_size, show_progress=show_progress, normalize=normalize
        )

    def encode_single(self, text: str, normalize: bool = True) -> Any:
        """编码单个文本

        Args:
            text: 单个文本
            normalize: 是否归一化

        Returns:
            向量
        """
        return self.encode([text], normalize=normalize)[0]

    def get_stats(self) -> dict[str, Any]:
        """获取性能统计信息

        Returns:
            统计信息字典
        """
        stats = self.stats.copy()

        # 计算平均处理速度
        if stats["total_texts_processed"] > 0:
            stats["avg_texts_per_second"] = (
                stats["total_texts_processed"] / stats["total_processing_time"]
                if stats["total_processing_time"] > 0
                else 0
            )
        else:
            stats["avg_texts_per_second"] = 0.0

        # 添加模型信息
        stats["model_name"] = self.model_name
        stats["is_loaded"] = self.is_loaded
        stats["device"] = self.device
        stats["load_time"] = self.load_time
        stats["dimension"] = self.config["dimension"]
        stats["max_seq_length"] = self.config["max_seq_length"]

        return stats

    def print_stats(self) -> Any:
        """打印性能统计信息"""
        stats = self.get_stats()

        logger.info("\n" + "=" * 60)
        logger.info(f"📊 {self.model_name} 模型统计信息")
        logger.info("=" * 60)
        logger.info(f"📦 模型名称: {stats['model_name']}")
        logger.info(f"✅ 加载状态: {'已加载' if stats['is_loaded'] else '未加载'}")
        logger.info(f"💻 运行设备: {stats['device']}")
        logger.info(f"📏 向量维度: {stats['dimension']}")
        logger.info(f"🔗 最大序列长度: {stats['max_seq_length']} tokens")
        logger.info(f"⏱️  加载时间: {stats['load_time']:.2f}秒")
        logger.info("\n🔄 加载统计:")
        logger.info(f"  尝试次数: {stats['load_attempts']}")
        logger.info(f"  成功次数: {stats['load_successes']}")
        logger.info(f"  失败次数: {stats['load_failures']}")
        logger.info("\n⚡ 性能统计:")
        logger.info(f"  处理文本数: {stats['total_texts_processed']}")
        logger.info(f"  总处理时间: {stats['total_processing_time']:.2f}秒")
        logger.info(f"  平均速度: {stats['avg_texts_per_second']:.2f} 文本/秒")
        logger.info("=" * 60 + "\n")

    def unload(self) -> Any:
        """卸载模型释放内存"""
        with self.load_lock:
            if self.model is not None:
                del self.model
                self.model = None
                self.is_loaded = False
                logger.info(f"✅ {self.model_name}模型已卸载")


# 全局单例
_model_loaders: dict[str, BGEM3ModelLoader] = {}
_loader_lock = threading.Lock()


def get_bge_m3_loader(model_name: str = "bge-m3") -> BGEM3ModelLoader:
    """获取BGE-M3模型加载器单例

    Args:
        model_name: 模型名称

    Returns:
        模型加载器实例
    """
    with _loader_lock:
        if model_name not in _model_loaders:
            _model_loaders[model_name] = BGEM3ModelLoader(model_name)
        return _model_loaders[model_name]


def load_bge_m3_model(
    model_name: str = "bge-m3", force_reload: bool = False
) -> BGEM3ModelLoader | None:
    """加载BGE-M3模型的便捷函数

    Args:
        model_name: 模型名称
        force_reload: 是否强制重新加载

    Returns:
        模型加载器实例,失败返回None
    """
    loader = get_bge_m3_loader(model_name)
    if loader.load_model(force_reload=force_reload):
        return loader
    return None


if __name__ == "__main__":
    # 测试加载器
    # setup_logging()  # 日志配置已移至模块导入

    logger.info("🚀 测试BGE-M3模型加载器")

    # 加载模型
    loader = load_bge_m3_model()

    if loader and loader.is_loaded:
        # 打印统计信息
        loader.print_stats()

        # 测试编码
        test_texts = [
            "这是一段测试文本。",
            "BGE-M3是一个强大的多语言嵌入模型。",
        ]

        logger.info("🔄 测试文本编码...")
        embeddings = loader.encode(test_texts, show_progress=True)

        logger.info("✅ 编码成功!")
        logger.info(f"📊 输出形状: {embeddings.shape}")
        logger.info(f"📏 向量维度: {len(embeddings[0])}")

        # 打印最终统计
        loader.print_stats()
    else:
        logger.error("❌ 模型加载失败")
