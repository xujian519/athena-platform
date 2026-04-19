#!/usr/bin/env python3
"""
模型加载器
Model Loader

统一管理本地NLP模型的加载和使用

支持的模型:
- BGE-base-zh-v1.5: 向量模型
- chinese_legal_electra: 序列标注模型
- chinese-deberta-v3-base: 语义理解模型

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入配置
try:
    from .config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    model_type: str  # embedding/sequence_tagger/sentence_similarity
    model_path: str
    vector_size: int
    max_sequence_length: int
    device: str = "cpu"
    loaded: bool = False


class ModelLoader:
    """
    模型加载器

    单例模式，统一管理所有本地模型
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 模型基础路径
        self.base_model_path = project_root / "models"

        # 模型注册表
        self.models: dict[str, ModelInfo] = {}

        # 已加载的模型实例
        self.loaded_models: dict[str, Any] = {}

        # 设备配置
        self.device = "cpu"

        self._initialized = True
        logger.info("📦 ModelLoader初始化完成")

    def register_model(
        self,
        name: str,
        model_type: str,
        model_path: str,
        vector_size: int,
        max_sequence_length: int = 512
    ):
        """注册模型"""
        self.models[name] = ModelInfo(
            name=name,
            model_type=model_type,
            model_path=str(self.base_model_path / model_path),
            vector_size=vector_size,
            max_sequence_length=max_sequence_length,
            device=self.device
        )
        logger.info(f"✅ 注册模型: {name} ({model_type})")

    def load_model(self, name: str) -> Any:
        """
        加载模型

        Args:
            name: 模型名称

        Returns:
            模型实例
        """
        # 检查是否已加载
        if name in self.loaded_models:
            return self.loaded_models[name]

        # 获取模型信息
        if name not in self.models:
            raise ValueError(f"模型未注册: {name}")

        model_info = self.models[name]

        logger.info(f"📥 加载模型: {name} from {model_info.model_path}")

        try:
            # 根据模型类型加载
            if model_info.model_type == "embedding":
                model = self._load_embedding_model(model_info)
            elif model_info.model_type == "sequence_tagger":
                model = self._load_sequence_tagger(model_info)
            elif model_info.model_type == "sentence_similarity":
                model = self._load_sentence_similarity_model(model_info)
            else:
                raise ValueError(f"未知模型类型: {model_info.model_type}")

            # 标记为已加载
            model_info.loaded = True
            self.loaded_models[name] = model

            logger.info(f"✅ 模型加载成功: {name}")
            return model

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {name}, 错误: {e}")
            raise

    def _load_embedding_model(self, model_info: ModelInfo):
        """加载向量化模型"""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            model_info.model_path,
            device=self.device
        )

        logger.info(f"  向量维度: {model.get_sentence_embedding_dimension()}")
        return model

    def _load_sequence_tagger(self, model_info: ModelInfo):
        """加载序列标注模型"""
        import torch.nn as nn
        from transformers import AutoModel, AutoTokenizer

        # 加载基础模型
        base_model = AutoModel.from_pretrained(
            model_info.model_path,
            trust_remote_code=True
        )

        # 加载tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_info.model_path,
            trust_remote_code=True
        )

        # 添加分类头（序列标注任务）
        # 标签: B-P, I-P, B-F, I-F, B-E, I-E, O (7类)
        classifier = nn.Linear(base_model.config.hidden_size, 7)

        class SequenceTaggerModel(nn.Module):
            def __init__(self, base_model, classifier):
                super().__init__()
                self.base_model = base_model
                self.classifier = classifier

            def forward(self, **inputs):
                outputs = self.base_model(**inputs)
                logits = self.classifier(outputs.last_hidden_state)
                return logits, outputs.last_hidden_state

        model = SequenceTaggerModel(base_model, classifier)

        logger.info("  分类类别数: 7 (B-P, I-P, B-F, I-F, B-E, I-E, O)")

        return {
            "model": model,
            "tokenizer": tokenizer
        }

    def _load_sentence_similarity_model(self, model_info: ModelInfo):
        """加载句子相似度模型"""
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(
            model_info.model_path,
            device=self.device
        )

        return model

    def get_model(self, name: str) -> Any:
        """
        获取模型（自动加载）

        Args:
            name: 模型名称

        Returns:
            模型实例
        """
        if name not in self.loaded_models:
            return self.load_model(name)
        return self.loaded_models[name]

    def unload_model(self, name: str):
        """卸载模型（释放内存）"""
        if name in self.loaded_models:
            del self.loaded_models[name]
            if name in self.models:
                self.models[name].loaded = False
            logger.info(f"🔌 模型已卸载: {name}")

    def unload_all(self):
        """卸载所有模型"""
        model_names = list(self.loaded_models.keys())
        for name in model_names:
            self.unload_model(name)
        logger.info("🔌 所有模型已卸载")

    def get_loaded_models(self) -> dict[str, ModelInfo]:
        """获取已加载的模型列表"""
        return {
            name: info
            for name, info in self.models.items()
            if info.loaded
        }

    def get_model_info(self, name: str) -> ModelInfo | None:
        """获取模型信息"""
        return self.models.get(name)


# ========== 全局模型加载器实例 ==========

_model_loader = None


def get_model_loader() -> ModelLoader:
    """获取全局模型加载器实例（单例）"""
    global _model_loader
    if _model_loader is None:
        _model_loader = ModelLoader()
        _initialize_default_models(_model_loader)
    return _model_loader


def _initialize_default_models(loader: ModelLoader):
    """初始化默认模型"""
    # BGE向量化模型
    loader.register_model(
        name="BAAI/bge-m3",
        model_type="embedding",
        model_path="BAAI/bge-m3",
        vector_size=1024,  # BGE-M3向量维度（已更新）
        max_sequence_length=512
    )

    # chinese_legal_electra序列标注模型
    loader.register_model(
        name="chinese_legal_electra",
        model_type="sequence_tagger",
        model_path="chinese_legal_electra",
        vector_size=1024,  # BGE-M3向量维度（已更新）
        max_sequence_length=512
    )

    # chinese-deberta-v3-base语义模型
    loader.register_model(
        name="chinese-deberta-v3-base",
        model_type="sentence_similarity",
        model_path="chinese-deberta-v3-base",
        vector_size=1024,  # BGE-M3向量维度（已更新）
        max_sequence_length=512
    )

    logger.info(f"✅ 已注册 {len(loader.models)} 个默认模型")


# ========== 便捷函数 ==========

def load_embedding_model(
    model_name: str = "BAAI/bge-m3"
):
    """加载向量化模型"""
    loader = get_model_loader()
    return loader.get_model(model_name)


def load_sequence_tagger(
    model_name: str = "chinese_legal_electra"
):
    """加载序列标注模型"""
    loader = get_model_loader()
    return loader.get_model(model_name)


def unload_all_models():
    """卸载所有模型"""
    loader = get_model_loader()
    loader.unload_all()


# ========== 示例使用 ==========

def main():
    """示例使用"""
    print("=" * 70)
    print("模型加载器示例")
    print("=" * 70)

    # 1. 获取模型加载器
    loader = get_model_loader()

    # 2. 查看已注册的模型
    print(f"\n📦 已注册的模型 ({len(loader.models)}个):")
    for name, info in loader.models.items():
        print(f"  - {name}")
        print(f"    类型: {info.model_type}")
        print(f"    路径: {info.model_path}")
        print(f"    向量维度: {info.vector_size}")

    # 3. 加载BGE模型
    print("\n📥 加载BGE向量化模型...")
    bge_model = loader.load_model("BAAI/bge-m3")
    print("✅ BGE模型加载成功")

    # 测试向量化
    test_text = "这是一种基于人工智能的图像识别方法"
    embedding = bge_model.encode(test_text)
    print(f"  测试向量维度: {len(embedding)}")

    # 4. 查看已加载的模型
    print("\n📊 已加载的模型:")
    for name, info in loader.get_loaded_models().items():
        print(f"  - {name}")

    # 5. 卸载模型
    print("\n🔌 卸载模型...")
    loader.unload_all()
    print("✅ 所有模型已卸载")


if __name__ == "__main__":
    main()
