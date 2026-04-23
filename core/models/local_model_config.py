#!/usr/bin/env python3
"""
本地模型配置管理
Local Model Configuration Manager

确保使用本地模型而不是在线下载
"""

import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class LocalModelConfig:
    """本地模型配置类"""

    def __init__(self):
        """初始化配置"""
        self.base_path = Path("/Users/xujian/Athena工作平台/models")
        self._load_env_variables()

    def _load_env_variables(self) -> Any:
        """加载环境变量"""
        # 设置关键环境变量,避免在线下载
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(self.base_path)
        os.environ["HF_HOME"] = str(self.base_path)
        os.environ["HUGGINGFACE_HUB_CACHE"] = str(self.base_path)
        os.environ["TRANSFORMERS_CACHE"] = str(self.base_path)
        os.environ["FLAG_EMBEDDING_CACHE"] = str(self.base_path)
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_OFFLINE"] = "1"

    def get_local_model_path(self, model_name: str) -> Optional[str]:
        """获取本地模型路径

        Args:
            model_name: 模型名称

        Returns:
            本地模型路径或None
        """
        model_paths = {
            # BGE模型
            "bge-large-zh-v1.5": str(self.base_path / "bge-large-zh-v1.5"),
            "bge-base-zh-v1.5": str(
                self.base_path
                / "bge-base-zh-v1.5/snapshots/f03589ceff5aac7111bd60cfc7d497ca17ecac65"
            ),
            # 法律模型
            "chinese-legal-electra": str(self.base_path / "chinese_legal_electra"),
            # 中文BERT
            "chinese_bert": str(self.base_path / "chinese_bert"),
            # 多语言模型
            "paraphrase-multilingual-MiniLM-L12-v2": str(
                self.base_path / "paraphrase-multilingual-MiniLM-L12-v2"
            ),
            # 重排序模型
            "bge-reranker-large": str(self.base_path / "bge-reranker-large"),
        }

        return model_paths.get(model_name)

    def is_model_available_locally(self, model_name: str) -> bool:
        """检查模型是否本地可用

        Args:
            model_name: 模型名称

        Returns:
            是否本地可用
        """
        local_path = self.get_local_model_path(model_name)
        if local_path is None:
            return False

        # 检查必要的文件
        required_files = ["config.json"]
        for file_name in required_files:
            if not (Path(local_path) / file_name).exists():
                # 检查是否在snapshot目录中
                snapshot_path = Path(local_path).parent
                if (snapshot_path / file_name).exists():
                    continue
                return False

        return True

    def get_sentence_transformer_model(self, model_name: str) -> str:
        """获取Sentence Transformer模型路径

        Args:
            model_name: 模型名称

        Returns:
            模型路径
        """
        local_path = self.get_local_model_path(model_name)
        if local_path and self.is_model_available_locally(model_name):
            return local_path
        else:
            # 如果本地没有,返回模型名称(会触发警告)
            logger.info(f"⚠️ 警告: 模型 {model_name} 本地不可用,将尝试在线下载")
            return model_name

    def setup_offline_mode(self) -> Any:
        """设置离线模式"""
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"

    def list_available_models(self) -> dict[str, dict[str, str]]:
        """列出所有可用的本地模型

        Returns:
            模型信息字典
        """
        models = {
            "bge-large-zh-v1.5": {
                "path": str(self.base_path / "bge-large-zh-v1.5"),
                "description": "中文大型模型,1024维",
                "dimension": "1024",
            },
            "bge-base-zh-v1.5": {
                "path": str(
                    self.base_path
                    / "bge-base-zh-v1.5/snapshots/f03589ceff5aac7111bd60cfc7d497ca17ecac65"
                ),
                "description": "中文基础模型,768维",
                "dimension": "768",
            },
            "chinese-legal-electra": {
                "path": str(self.base_path / "chinese_legal_electra"),
                "description": "中文法律模型,768维",
                "dimension": "768",
            },
            "chinese_bert": {
                "path": str(self.base_path / "chinese_bert"),
                "description": "中文BERT基础模型,768维",
                "dimension": "768",
            },
        }

        # 检查每个模型的可用性
        for model_name in models:
            models[model_name]["available"] = self.is_model_available_locally(model_name)

        return models


# 创建全局实例
model_config = LocalModelConfig()

# 使用示例:
# from local_model_config import model_config
#
# # 获取本地模型路径
# model_path = model_config.get_local_model_path("bge-large-zh-v1.5")
#
# # 检查模型是否可用
# if model_config.is_model_available_locally("bge-large-zh-v1.5"):
#     logger.info("模型本地可用")
#
# # 获取Sentence Transformer模型
# model = SentenceTransformer(model_config.get_sentence_transformer_model("bge-large-zh-v1.5"))
