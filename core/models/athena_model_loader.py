#!/usr/bin/env python3
"""
Athena统一模型加载器
自动检测并配置最优设备(MPS/CUDA/CPU)

作者: Athena AI
创建时间: 2025-12-29
版本: v1.0.0
"""

import logging
from pathlib import Path
from typing import Any, Optional, Union

import torch

from core.logging_config import setup_logging

logger = setup_logging()


class AthenaModelLoader:
    """
    Athena统一模型加载器

    特性:
    - 自动检测最优设备 (MPS > CUDA > CPU)
    - 统一模型配置
    - 自动修复缺失的配置文件
    - 性能优化建议
    """

    # 项目根目录
    PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

    # 模型目录
    MODELS_DIR = PROJECT_ROOT / "models"
    CONVERTED_DIR = MODELS_DIR / "converted"

    # 支持的模型配置
    MODEL_CONFIGS = {
        "bge-small-zh-v1.5": {
            "dimension": 512,
            "word_embedding_dimension": 512,
            "max_seq_length": 512,
            "remote_path": "BAAI/bge-small-zh-v1.5",
        },
        "BAAI/bge-m3": {
            "dimension": 768,
            "word_embedding_dimension": 768,
            "max_seq_length": 512,
            "remote_path": "BAAI/bge-m3",
        },
        "BAAI/bge-m3": {
            "dimension": 1024,
            "word_embedding_dimension": 1024,
            "max_seq_length": 512,
            "remote_path": "BAAI/BAAI/bge-m3",
        },
        "bge-reranker-large": {
            "dimension": 1024,
            "word_embedding_dimension": 1024,
            "max_seq_length": 512,
            "remote_path": "BAAI/bge-reranker-large",
        },
        # "nomic-embed-text-v1.5": {  # 已删除,使用BGE-M3替代
        #     "dimension": 768,
        #     "word_embedding_dimension": 768,
        #     "max_seq_length": 8192,
        #     "remote_path": "nomic-ai/nomic-embed-text-v1.5"
        # }
    }

    @classmethod
    def get_optimal_device(cls) -> str:
        """
        获取最优设备

        优先级: MPS > CUDA > CPU
        """
        if torch.backends.mps.is_available():
            device = "mps"
            logger.info("🔥 检测到MPS支持(Apple Silicon GPU)")
        elif torch.cuda.is_available():
            device = "cuda"
            logger.info("🟢 检测到CUDA支持(NVIDIA GPU)")
        else:
            device = "cpu"
            logger.info("💻 使用CPU设备")

        return device

    @classmethod
    def get_model_path(cls, model_name: str) -> str:
        """
        获取模型路径

        搜索优先级:
        1. models/converted/{model_name}/ - 本地优化模型
        2. models/{model_name}/ - 本地原始模型
        3. HuggingFace远程模型

        Args:
            model_name: 模型名称

        Returns:
            模型路径
        """
        # 1. 检查converted目录
        converted_path = cls.CONVERTED_DIR / model_name
        if converted_path.exists():
            logger.info(f"✅ 使用本地优化模型: {converted_path}")
            return str(converted_path)

        # 2. 检查models目录
        local_path = cls.MODELS_DIR / model_name
        if local_path.exists():
            logger.info(f"✅ 使用本地模型: {local_path}")
            return str(local_path)

        # 3. 使用远程模型
        if model_name in cls.MODEL_CONFIGS:
            remote_path = cls.MODEL_CONFIGS[model_name]["remote_path"]
            logger.info(f"📥 使用远程模型: {remote_path}")
            return remote_path

        # 直接返回模型名称(让sentence_transformers处理)
        logger.info(f"📥 使用模型名称: {model_name}")
        return model_name

    @classmethod
    def fix_model_config(cls, model_path: str) -> bool:
        """
        修复缺失的模型配置文件

        Args:
            model_path: 模型路径

        Returns:
            是否成功修复
        """
        model_dir = Path(model_path)
        model_name = model_dir.name

        if model_name not in cls.MODEL_CONFIGS:
            logger.warning(f"未知模型: {model_name},跳过配置修复")
            return False

        config = cls.MODEL_CONFIGS[model_name]

        # 检查并创建1_Pooling配置
        pooling_dir = model_dir / "1_Pooling"
        pooling_config = pooling_dir / "config.json"

        if not pooling_config.exists():
            try:
                pooling_dir.mkdir(parents=True, exist_ok=True)

                pooling_config_content = {
                    "word_embedding_dimension": config["word_embedding_dimension"],
                    "pooling_mode_cls_token": False,
                    "pooling_mode_mean_tokens": True,
                    "pooling_mode_max_tokens": False,
                    "pooling_mode_mean_sqrt_len_tokens": False,
                    "pooling_mode_weightedmean_tokens": False,
                    "pooling_mode_lasttoken": False,
                    "include_prompt_special_token": False,
                }

                import json

                with open(pooling_config, "w", encoding="utf-8") as f:
                    json.dump(pooling_config_content, f, indent=2, ensure_ascii=False)

                logger.info(f"✅ 已创建Pooling配置: {pooling_config}")
                return True

            except Exception as e:
                logger.error(f"❌ 创建Pooling配置失败: {e}")
                return False

        return True

    @classmethod
    def load_sentence_transformer(
        cls, model_name: str | None = None, device: str | None = None, fix_config: bool = True
    ):
        """
        加载SentenceTransformer模型

        Args:
            model_name: 模型名称或路径
            device: 设备 (None=自动检测)
            fix_config: 是否自动修复配置

        Returns:
            加载的模型
        """
        # 自动检测设备
        if device is None:
            device = cls.get_optimal_device()

        # 获取模型路径
        model_path = cls.get_model_path(model_name)

        # 修复配置
        if fix_config:
            cls.fix_model_config(model_path)

        # 导入sentence_transformers
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError("请安装sentence-transformers: pip install sentence-transformers")

        # 加载模型
        logger.info(f"🔄 加载模型: {model_name}")
        logger.info(f"   路径: {model_path}")
        logger.info(f"   设备: {device}")

        try:
            # 先不指定device加载
            model = SentenceTransformer(model_path)

            # 然后移动到目标设备
            model = model.to(device)

            logger.info("✅ 模型加载成功!")
            logger.info(f"   向量维度: {cls.get_model_dimension(model_name)}")
            logger.info(f"   实际设备: {model.device}")

            return model

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            raise

    @classmethod
    def get_model_dimension(cls, model_name: str) -> int:
        """获取模型向量维度"""
        if model_name in cls.MODEL_CONFIGS:
            return cls.MODEL_CONFIGS[model_name]["dimension"]
        return 768  # 默认维度

    @classmethod
    def get_max_seq_length(cls, model_name: str) -> int:
        """获取模型最大序列长度"""
        if model_name in cls.MODEL_CONFIGS:
            return cls.MODEL_CONFIGS[model_name]["max_seq_length"]
        return 512  # 默认长度


# 便捷函数
def load_model(
    model_name: str = "BAAI/bge-m3", device: str | None = None, fix_config: bool = True
):
    """
    加载模型的便捷函数

    Args:
        model_name: 模型名称
        device: 设备 (None=自动检测MPS/CUDA/CPU)
        fix_config: 是否自动修复配置

    Returns:
        加载的模型

    Example:
        >>> model = load_model("BAAI/bge-m3")
        >>> embeddings = model.encode(["测试文本"])
    """
    return AthenaModelLoader.load_sentence_transformer(
        model_name=model_name, device=device, fix_config=fix_config
    )


def get_device() -> str:
    """获取最优设备"""
    return AthenaModelLoader.get_optimal_device()


# 兼容性:替换旧代码中的硬编码设备
def patch_device_cpu_to_mps() -> Any:
    """
    将代码中硬编码的device='cpu'替换为自动检测

    这是一个临时解决方案,建议使用load_model()函数
    """
    logger.info("⚠️ 建议使用 AthenaModelLoader.load_sentence_transformer() 替代硬编码device")


if __name__ == "__main__":
    # 测试加载
    import logging

    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("🧪 测试Athena模型加载器")
    print("=" * 60)

    # 测试设备检测
    device = get_device()
    print(f"\n📊 最优设备: {device}")

    # 测试模型加载
    print("\n🔄 测试模型加载...")
    model = load_model("BAAI/bge-m3")

    # 测试推理
    print("\n🧪 测试推理...")
    embeddings = model.encode(["测试文本"], show_progress_bar=False)
    print(f"✅ 推理成功,向量维度: {len(embeddings[0])}")
