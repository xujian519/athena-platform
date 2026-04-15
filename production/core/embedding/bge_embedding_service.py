#!/usr/bin/env python3
"""
BGE向量嵌入服务
BGE Vector Embedding Service for Athena Platform

提供统一的BGE模型嵌入功能,支持多种BGE模型和向量维度
"""


from __future__ import annotations
import asyncio
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from core.logging_config import setup_logging

logger = setup_logging()


class BGEModelConfig:
    """BGE模型配置"""

    # 支持的BGE模型
    MODELS = {
        "bge-m3": {
            "dimension": 1024,
            "max_seq_length": 8192,
            "model_path": "BAAI/bge-m3",
            "description": "多语言模型,支持超长文本(8192),1024维,支持100+工作语言",
        }
    }

    # 本地模型路径配置
    LOCAL_MODEL_DIR = Path(os.getenv("MODEL_PATH", "/Users/xujian/Athena工作平台/models"))

    @classmethod
    def get_model_path(cls, model_name: str) -> str:
        """
        获取模型路径(优先使用本地converted目录中的MPS优化模型)

        搜索顺序:
        1. models/converted/{model_name}/ - MPS优化的本地模型
        2. models/{model_name}/ - 普通本地模型
        3. HuggingFace远程模型

        Args:
            model_name: 模型名称

        Returns:
            模型路径字符串
        """
        if model_name not in cls.MODELS:
            raise ValueError(f"不支持的模型: {model_name},可用模型: {list(cls.MODELS.keys())}")

        # 1. 优先查找converted目录下的BAAI子目录(MPS优化模型)
        converted_path = cls.LOCAL_MODEL_DIR / "converted" / "BAAI" / model_name
        if converted_path.exists():
            logger.info(f"✅ 使用本地MPS优化模型: {converted_path}")
            return str(converted_path)

        # 2. 查找普通本地模型目录
        local_path = cls.LOCAL_MODEL_DIR / model_name
        if local_path.exists():
            logger.info(f"✅ 使用本地模型: {local_path}")
            return str(local_path)

        # 3. 使用HuggingFace远程模型
        remote_path = cls.MODELS[model_name]["model_path"]
        logger.info(f"📥 使用HuggingFace远程模型: {remote_path}")
        return remote_path

    @classmethod
    def get_dimension(cls, model_name: str) -> int:
        """获取模型向量维度"""
        return cls.MODELS[model_name]["dimension"]


class BGEEmbeddingService:
    """BGE向量嵌入服务"""

    def __init__(
        self,
        model_name: str = "bge-m3",
        device: str = "cpu",
        batch_size: int = 32,
        cache_size: int = 1000,
    ):
        """
        初始化BGE嵌入服务

        Args:
            model_name: BGE模型名称
            device: 运行设备 ("cpu" 或 "cuda")
            batch_size: 批处理大小
            cache_size: 缓存大小
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self.cache_size = cache_size

        # 模型配置
        self.dimension = BGEModelConfig.get_dimension(model_name)
        self.model_path = BGEModelConfig.get_model_path(model_name)

        # 嵌入缓存
        self._embedding_cache: dict[str, np.ndarray] = {}

        # 加载模型
        self._model: SentenceTransformer | None = None
        self._initialize_model()

    def _initialize_model(self) -> Any:
        """初始化BGE模型"""
        try:
            logger.info(f"加载BGE模型: {self.model_name} from {self.model_path}")

            # 检测并启用MPS加速
            import torch

            if self.device == "cpu" and torch.backends.mps.is_available():
                logger.info("🔥 检测到MPS支持,自动启用MPS加速")
                self.device = "mps"

            self._model = SentenceTransformer(self.model_path, device=self.device)

            # 确保模型在正确的设备上
            if hasattr(self._model, "to"):
                self._model = self._model.to(self.device)

            logger.info(f"✅ BGE模型加载成功,设备: {self.device},向量维度: {self.dimension}")
        except Exception as e:
            logger.error(f"❌ BGE模型加载失败: {e}")
            raise

    @property
    def model(self) -> SentenceTransformer:
        """获取模型实例(延迟加载)"""
        if self._model is None:
            self._initialize_model()
        assert self._model is not None, "Model should be initialized after _initialize_model()"
        return self._model

    def encode(
        self, texts: str | list[str], normalize: bool = True, show_progress: bool = False
    ) -> np.ndarray:
        """
        编码文本为向量

        Args:
            texts: 文本或文本列表
            normalize: 是否归一化向量
            show_progress: 是否显示进度

        Returns:
            向量数组 (n_texts, dimension)
        """
        if isinstance(texts, str):
            texts = [texts]

        # 检查缓存
        cached_embeddings = []
        uncached_texts = []
        uncached_indices = []

        for i, text in enumerate(texts):
            if text in self._embedding_cache:
                cached_embeddings.append((i, self._embedding_cache[text]))
            else:
                uncached_texts.append(text)
                uncached_indices.append(i)

        # 编码未缓存的文本
        if uncached_texts:
            embeddings = self.model.encode(
                uncached_texts,
                normalize_embeddings=normalize,
                batch_size=self.batch_size,
                show_progress_bar=show_progress,
            )

            # 更新缓存
            for text, embedding in zip(uncached_texts, embeddings, strict=False):
                if len(self._embedding_cache) < self.cache_size:
                    self._embedding_cache[text] = embedding

            # 合并结果
            all_embeddings = [None] * len(texts)

            # 添加缓存的嵌入
            for i, emb in cached_embeddings:
                all_embeddings[i] = emb

            # 添加新计算的嵌入
            for idx, emb in zip(uncached_indices, embeddings, strict=False):
                all_embeddings[idx] = emb

            return np.array(all_embeddings)
        else:
            # 全部来自缓存
            return np.array([emb for _, emb in cached_embeddings])

    async def encode_async(self, texts: str | list[str], normalize: bool = True) -> np.ndarray:
        """异步编码文本"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.encode(texts, normalize=normalize))

    def encode_single(self, text: str, normalize: bool = True) -> list[float]:
        """
        编码单个文本

        Args:
            text: 输入文本
            normalize: 是否归一化

        Returns:
            向量列表
        """
        embedding = self.encode(text, normalize=normalize)
        return embedding[0].tolist()

    def encode_batch(self, texts: list[str], normalize: bool = True) -> list[list[float]]:
        """
        批量编码文本

        Args:
            texts: 文本列表
            normalize: 是否归一化

        Returns:
            向量列表
        """
        embeddings = self.encode(texts, normalize=normalize)
        return [emb.tolist() for emb in embeddings]

    def similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度分数 (0-1)
        """
        emb1 = self.encode(text1, normalize=True)
        emb2 = self.encode(text2, normalize=True)

        # 计算余弦相似度
        return float(np.dot(emb1[0], emb2[0]))

    def search(self, query: str, documents: list[str], top_k: int = 10) -> list[dict[str, Any]]:
        """
        向量搜索

        Args:
            query: 查询文本
            documents: 文档列表
            top_k: 返回top-k结果

        Returns:
            搜索结果列表 [{"index": int, "score": float, "document": str}, ...]
        """
        query_emb = self.encode(query, normalize=True)
        doc_embs = self.encode(documents, normalize=True)

        # 计算相似度
        scores = np.dot(doc_embs, query_emb.T).flatten()

        # 获取top-k
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append(
                {"index": int(idx), "score": float(scores[idx]), "document": documents[idx]}
            )

        return results

    def clear_cache(self) -> None:
        """清空嵌入缓存"""
        self._embedding_cache.clear()
        logger.info("嵌入缓存已清空")

    def get_cache_stats(self) -> dict[str, int | float]:
        """获取缓存统计信息"""
        return {
            "cached_embeddings": len(self._embedding_cache),
            "cache_size": self.cache_size,
            "cache_usage": (
                len(self._embedding_cache) / self.cache_size if self.cache_size > 0 else 0
            ),
        }


# =============================================================================
# 全局服务实例
# =============================================================================

# 服务实例缓存
_services: dict[str, BGEEmbeddingService] = {}


@lru_cache(maxsize=4)
def get_bge_service(model_name: str = "bge-m3", device: str = "cpu") -> BGEEmbeddingService:
    """
    获取BGE服务实例(单例模式)

    Args:
        model_name: 模型名称
        device: 设备类型

    Returns:
        BGEEmbeddingService实例
    """
    cache_key = f"{model_name}_{device}"

    if cache_key not in _services:
        logger.info(f"创建新的BGE服务实例: {model_name} on {device}")
        _services[cache_key] = BGEEmbeddingService(model_name=model_name, device=device)

    return _services[cache_key]


# =============================================================================
# 便捷函数
# =============================================================================


def embed_text(text: str, model_name: str = "bge-m3") -> list[float]:
    """编码单个文本(便捷函数)"""
    service = get_bge_service(model_name)
    return service.encode_single(text)


def embed_texts(texts: list[str], model_name: str = "bge-m3") -> list[list[float]]:
    """批量编码文本(便捷函数)"""
    service = get_bge_service(model_name)
    return service.encode_batch(texts)


def search_similar(
    query: str, documents: list[str], top_k: int = 10, model_name: str = "bge-m3"
) -> list[dict[str, Any]]:
    """搜索相似文档(便捷函数)"""
    service = get_bge_service(model_name)
    return service.search(query, documents, top_k=top_k)


# =============================================================================
# 主程序
# =============================================================================

if __name__ == "__main__":
    import sys

    # 配置日志
    # setup_logging()  # 日志配置已移至模块导入

    # 测试BGE服务
    print("=" * 60)
    print("BGE向量嵌入服务测试")
    print("=" * 60)

    try:
        # 获取服务
        service = get_bge_service("bge-m3")

        # 测试文本
        query = "专利检索系统"
        documents = [
            "专利是保护发明创造的重要法律制度",
            "商标用于区分商品或服务的来源",
            "版权保护原创作品的著作权",
            "专利检索可以帮助查找相关技术",
        ]

        # 编码
        print("\n1. 编码查询文本...")
        query_vector = service.encode_single(query)
        print(f"   向量维度: {len(query_vector)}")
        print(f"   前5个值: {query_vector[:5]}")

        # 搜索
        print("\n2. 向量搜索...")
        results = service.search(query, documents, top_k=3)
        for i, result in enumerate(results, 1):
            print(f"   {i}. [{result['score']:.4f}] {result['document']}")

        # 相似度
        print("\n3. 计算相似度...")
        similarity = service.similarity(query, documents[0])
        print(f"   相似度: {similarity:.4f}")

        # 缓存统计
        print("\n4. 缓存统计...")
        stats = service.get_cache_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
