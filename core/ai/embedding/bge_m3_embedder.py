#!/usr/bin/env python3

"""
基于BGE-M3模型的高质量向量化模块(MPS优化版)
High-Quality Embedding Module Based on BGE-M3 Model (MPS Optimized)

使用BGE-M3(BAAI General Embedding Multilingual)模型生成高质量向量
支持中文专利无效复审决定的语义检索
支持MPS(Apple Silicon GPU)、CUDA、CPU设备
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


class BGE_M3_Embedder:
    """
    BGE-M3模型嵌入器(MPS优化版)

    模型信息:
    - 模型名称: BAAI/bge-m3
    - 向量维度: 1024
    - 支持语言: 多语言(中文、英文等100+种语言)
    - 最大序列长度: 8192 tokens
    - 适合场景: 长文档检索、多语言检索
    - 设备支持: MPS(Apple Silicon)、CUDA、CPU
    """

    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        初始化BGE-M3嵌入器

        Args:
            model_path: 模型路径,默认自动检测本地路径
            device: 运行设备 ('auto', 'mps', 'cuda', 'cpu')
                    auto: 自动检测最优设备(优先MPS > CUDA > CPU)
        """
        self.model_path = model_path
        self.device_preference = device
        self.model_loader = None
        self.dimension = 1024  # BGE-M3的标准维度
        self._initialized = False

    async def initialize(self):
        """异步初始化模型(使用MPS优化加载器)"""
        if self._initialized:
            return

        try:
            # 导入MPS优化的模型加载器
            from core.ai.nlp.bge_m3_loader import BGEM3ModelLoader

            logger.info("🔄 使用MPS优化的BGE-M3加载器")

            # 创建加载器
            self.model_loader = BGEM3ModelLoader()

            # 设置设备
            if self.device_preference == "auto":
                # 自动检测设备
                self.device = self.model_loader._detect_device()
            else:
                self.device = self.device_preference

            logger.info(f"🎯 设备选择: {self.device}")

            # 加载模型
            success = self.model_loader.load_model()

            if success:
                self._initialized = True
                logger.info("✅ BGE-M3模型加载成功")
                logger.info(f"   向量维度: {self.dimension}")
                logger.info(f"   设备: {self.device}")
                logger.info(f"   MPS优化: {'是' if self.device == 'mps' else '否'}")
            else:
                raise RuntimeError("模型加载失败")

        except ImportError as e:
            logger.warning(f"⚠️ MPS优化加载器不可用: {e}")
            logger.info("💡 回退到sentence_transformers加载器")
            await self._initialize_fallback()
        except Exception as e:
            logger.error(f"❌ BGE-M3模型加载失败: {e}")
            raise

    async def _initialize_fallback(self):
        """备用方案: 使用sentence_transformers"""
        try:
            from sentence_transformers import SentenceTransformer

            # 确定模型路径
            if not self.model_path:
                self.model_path = "http://127.0.0.1:8766/v1/embeddings"

            # 确定设备
            if self.device_preference == "auto":
                import torch

                if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    self.device = "mps"
                elif torch.cuda.is_available():
                    self.device = "cuda"
                else:
                    self.device = "cpu"
            else:
                self.device = self.device_preference

            logger.info(f"🔄 使用sentence_transformers加载器,设备: {self.device}")

            self.model = SentenceTransformer(self.model_path, device=self.device)

            # 测试编码
            test_text = "测试文本"
            test_embedding = self.model.encode(test_text)

            self._initialized = True
            logger.info("✅ BGE-M3模型加载成功(备用方案)")
            logger.info(f"   向量维度: {test_embedding.shape[0]}")

        except Exception as e:
            logger.error(f"❌ 备用方案也失败: {e}")
            raise

    async def embed_text(self, text: str) -> list[float]:
        """
        对单个文本进行向量化

        Args:
            text: 输入文本

        Returns:
            向量列表
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 优先使用MPS优化的model_loader
            if self.model_loader is not None:
                embedding = self.model_loader.encode(text)
            else:
                # 回退到sentence_transformers
                embedding = self.model.encode(
                    text, normalize_embeddings=True, show_progress_bar=False
                )

            return embedding.tolist()

        except Exception as e:
            logger.error(f"向量化失败: {e}")
            # 返回零向量作为fallback
            return [0.0] * self.dimension

    async def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """
        批量向量化

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            向量列表(list格式,用于JSON序列化)
        """
        if not self._initialized:
            await self.initialize()

        try:
            # 优先使用MPS优化的model_loader
            if self.model_loader is not None:
                embeddings = self.model_loader.encode_batch(texts, batch_size=batch_size)
                # 确保转换为list格式
                if hasattr(embeddings, "tolist"):
                    embeddings = embeddings.tolist()
                elif not isinstance(embeddings, list):
                    embeddings = list(embeddings)
            else:
                # 回退到sentence_transformers
                vectors = self.model.encode(
                    texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False
                )
                # 转换为列表
                embeddings = [vectors.tolist()] if len(vectors.shape) == 1 else vectors.tolist()

            return embeddings

        except Exception as e:
            logger.error(f"批量向量化失败: {e}")
            return [[0.0] * self.dimension] * len(texts)

    async def embed_decision_chunks(
        self, chunks: list[dict[str, Any], instruction: Optional[str] = None
    ) -> list[list[float]]:
        """
        为专利决定文档块生成高质量向量

        Args:
            chunks: 文档块列表
            instruction: 可选的指令前缀

        Returns:
            向量列表
        """
        # BGE-M3不需要指令前缀,但可以添加以增强效果
        texts = []
        for chunk in chunks:
            text = chunk["content"]

            # 根据chunk类型添加上下文
            chunk_type = chunk.get("chunk_type", "")
            if chunk_type == "key_point":
                text = f"决定要点:{text}"
            elif chunk_type == "conclusion":
                text = f"决定结论:{text}"
            elif chunk_type == "claims":
                text = f"权利要求:{text}"
            elif chunk_type == "background":
                text = f"案件背景:{text}"

            texts.append(text)

        # 批量编码
        embeddings = await self.embed_batch(texts)

        # 根据权重调整向量
        weighted_embeddings = []
        for embedding, chunk in zip(embeddings, chunks, strict=False):
            weight = chunk.get("weight", 1.0)
            # 简单的权重调整(实际应用中可能需要更复杂的方法)
            weighted_vector = [v * weight for v in embedding]
            weighted_embeddings.append(weighted_vector)

        return weighted_embeddings


class CachedEmbedder:
    """带缓存的嵌入器"""

    def __init__(self, embedder: BGE_M3_Embedder, cache_size: int = 10000):
        """
        初始化缓存嵌入器

        Args:
            embedder: 底层嵌入器
            cache_size: 缓存大小
        """
        self.embedder = embedder
        self.cache = {}  # {text_hash: embedding}
        self.cache_size = cache_size
        self.hits = 0
        self.misses = 0

    async def embed_text(self, text: str, use_cache: bool = True) -> list[float]:
        """带缓存的向量化"""
        import hashlib

        # 生成文本哈希
        text_hash = hashlib.md5(text.encode("utf-8"), usedforsecurity=False).hexdigest()

        # 检查缓存
        if use_cache and text_hash in self.cache:
            self.hits += 1
            return self.cache[text_hash]

        # 缓存未命中,进行向量化
        self.misses += 1
        embedding = await self.embedder.embed_text(text)

        # 存入缓存
        if len(self.cache) >= self.cache_size:
            # 简单的LRU策略:移除最早的缓存项
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]

        self.cache[text_hash] = embedding

        return embedding

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "cache_size": len(self.cache),
            "max_cache_size": self.cache_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


# 全局单例
_embedder_instance: Optional[BGE_M3_Embedder] = None
_cached_embedder_instance: Optional[CachedEmbedder] = None


async def get_embedder(use_cache: bool = True) -> BGE_M3_Embedder:
    """获取嵌入器实例"""
    global _embedder_instance

    if _embedder_instance is None:
        _embedder_instance = BGE_M3_Embedder()
        await _embedder_instance.initialize()

    return _embedder_instance


async def get_cached_embedder() -> CachedEmbedder:
    """获取缓存嵌入器实例"""
    global _cached_embedder_instance

    if _cached_embedder_instance is None:
        embedder = await get_embedder()
        _cached_embedder_instance = CachedEmbedder(embedder)

    return _cached_embedder_instance


async def embed_decision_document(json_file: Path, use_cache: bool = True) -> list[dict[str, Any]]:
    """
    为JSON格式的专利决定文档生成向量

    Args:
        json_file: JSON文件路径
        use_cache: 是否使用缓存

    Returns:
        包含向量的文档块列表
    """
    import json

    # 读取JSON
    with open(json_file, encoding="utf-8") as f:
        data = json.load(f)

    # 获取嵌入器
    if use_cache:
        embedder = await get_cached_embedder()
    else:
        embedder = await get_embedder()

    # 为每个chunk生成向量
    chunks_with_embeddings = []

    for _idx, chunk in enumerate(data.get("embedding_chunks", [])):
        # 生成向量
        embedding = await embedder.embed_text(chunk["content"])

        # 添加向量到chunk
        chunk_with_embedding = {
            **chunk,
            "embedding": embedding,
            "embedding_dimension": len(embedding),
        }

        chunks_with_embeddings.append(chunk_with_embedding)

    return chunks_with_embeddings


# 测试代码
async def test_bge_m3_embedder():
    """测试BGE-M3嵌入器"""
    print("=" * 60)
    print("🧪 测试BGE-M3嵌入器")
    print("=" * 60)

    try:
        embedder = BGE_M3_Embedder()
        await embedder.initialize()

        # 测试单个文本
        test_text = "对于风扇类产品,均匀排列环绕在轴心边缘的叶片数量上的差异不足以对产品的整体视觉效果产生显著的影响。"

        print(f"\n📝 测试文本: {test_text}")
        print(f"📏 文本长度: {len(test_text)} 字符")

        embedding = await embedder.embed_text(test_text)

        print("\n✅ 向量化成功")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量前10维: {embedding[:10]}")
        print(f"   向量模长: {np.linalg.norm(embedding):.4f}")

        # 测试批量处理
        texts = [
            "本专利涉及航模飞机涵道风扇的外观设计",
            "专利法第23条规定了外观设计的授予条件",
            "叶片数量差异不影响整体视觉效果",
        ]

        print(f"\n📝 批量测试 {len(texts)} 个文本")
        embeddings = await embedder.embed_batch(texts)

        print("✅ 批量向量化成功")
        print(f"   向量数量: {len(embeddings)}")
        print(f"   向量维度: {len(embeddings[0])}")

        # 测试相似度计算
        from sklearn.metrics.pairwise import cosine_similarity

        similarities = cosine_similarity(embeddings)
        print("\n📊 相似度矩阵:")
        for i in range(len(texts)):
            for j in range(len(texts)):
                if i < j:
                    print(f"   文本{i+1} <-> 文本{j+1}: {similarities[i][j]:.4f}")

        print("\n✅ 测试完成!")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_bge_m3_embedder())

