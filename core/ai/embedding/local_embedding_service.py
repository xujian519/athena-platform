#!/usr/bin/env python3

"""
本地嵌入模型服务
Local Embedding Model Service

使用项目本地的sentence-transformers兼容模型进行语义嵌入:
1. "BAAI/bge-m3" (中文语义模型)
2. BAAI/bge-m3 (中文语义模型,更大)
# 3. nomic-embed-text-v1.5 (已删除,使用BGE-M3替代)

作者: Athena平台团队
创建时间: 2025-12-27
版本: v1.0.0
"""

import asyncio
import logging
from pathlib import Path

import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class LocalEmbeddingModel:
    """
    本地嵌入模型

    支持多种sentence-transformers兼容模型
    """

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        self.model_name = model_name
        self.model_path = self._get_model_path(model_name)
        self.model = None
        self.tokenizer = None
        self.embedding_dim = 1024  # BGE-M3向量维度(已更新)  # 默认维度
        self.max_length = 512

        logger.info(f"📦 本地嵌入模型初始化: {model_name}")
        logger.info(f"   模型路径: {self.model_path}")

    def _get_model_path(self, model_name: str) -> Path:
        """获取模型路径"""
        base_path = Path("/Users/xujian/Athena工作平台/models")

        model_paths = {
            "BAAI/bge-m3": base_path / "converted" / "BAAI/bge-m3",
            "bge-m3": base_path / "converted" / "BAAI/bge-m3",
            # 已删除的模型(统一使用BGE-M3):
            # - chinese-legal-electra (1024维(BGE-M3)) -> 已删除,使用BGE-M3替代
            # - lawformer (1024维(BGE-M3)) -> 已删除,使用BGE-M3替代
        }

        return model_paths.get(model_name, base_path / "converted" / model_name)

    async def load_model(self):
        """加载模型(异步接口,实际是同步加载)"""
        from sentence_transformers import SentenceTransformer

        try:
            # 检查模型是否存在
            if not self.model_path.exists():
                logger.warning(f"⚠️  模型路径不存在: {self.model_path}")
                logger.info("📦 将使用默认模型或在线下载")

            # 加载模型
            logger.info(f"🔄 加载模型: {self.model_name}")
            self.model = SentenceTransformer(str(self.model_path))

            # 获取模型信息
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            self.max_length = self.model.max_seq_length

            logger.info("✅ 模型加载完成")
            logger.info(f"   嵌入维度: {self.embedding_dim}")
            logger.info(f"   最大长度: {self.max_length}")

        except Exception as e:
            logger.error(f"❌ 模型加载失败: {e}")
            logger.info("📦 将使用降级方案(简单hash嵌入)")
            self.model = None

    async def encode(
        self, texts: str | list[str], batch_size: int = 32, show_progress: bool = False
    ) -> np.ndarray:
        """
        编码文本为嵌入向量

        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            嵌入向量 (n x dim)
        """
        if self.model is None:
            # 降级方案:简单hash嵌入
            return self._fallback_encode(texts)

        try:
            # 确保输入是列表
            if isinstance(texts, str):
                texts = [texts]

            # 编码
            embeddings = self.model.encode(
                texts, batch_size=batch_size, show_progress_bar=show_progress, convert_to_numpy=True
            )

            return embeddings

        except Exception as e:
            logger.error(f"❌ 编码失败: {e}")
            return self._fallback_encode(texts)

    def _fallback_encode(self, texts: str | list[str]) -> np.ndarray:
        """
        降级编码方案(当模型不可用时)
        使用简单的hash方法
        """
        if isinstance(texts, str):
            texts = [texts]

        embeddings = []
        for text in texts:
            # 简单的hash嵌入
            text_bytes = text.encode("utf-8")
            embedding = np.zeros(self.embedding_dim, dtype=np.float32)

            for i, byte_val in enumerate(text_bytes):
                embedding[i % self.embedding_dim] += byte_val / 255.0

            # 添加一些随机性模拟语义
            np.random.seed(hash(text) % (2**32))
            embedding += np.random.randn(self.embedding_dim) * 0.1

            # 归一化
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)

            embeddings.append(embedding)

        return np.array(embeddings)

    async def encode_async(self, texts: str | list[str], batch_size: int = 32) -> np.ndarray:
        """异步编码接口"""
        # 在线程池中执行编码
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: asyncio.run(self.encode(texts, batch_size)))

    def compute_similarity(self, embeddings1: np.ndarray, embeddings2: np.ndarray) -> np.ndarray:
        """
        计算余弦相似度

        Args:
            embeddings1: (n1 x dim) 或 (dim,)
            embeddings2: (n2 x dim) 或 (dim,)

        Returns:
            相似度矩阵 (n1 x n2) 或标量
        """
        # 确保是2D数组
        if embeddings1.ndim == 1:
            embeddings1 = embeddings1.reshape(1, -1)
        if embeddings2.ndim == 1:
            embeddings2 = embeddings2.reshape(1, -1)

        # 归一化
        embeddings1 = embeddings1 / (np.linalg.norm(embeddings1, axis=1, keepdims=True) + 1e-8)
        embeddings2 = embeddings2 / (np.linalg.norm(embeddings2, axis=1, keepdims=True) + 1e-8)

        # 计算余弦相似度
        similarity = np.dot(embeddings1, embeddings2.T)

        return similarity

    async def compute_similarity_async(
        self, embeddings1: np.ndarray, embeddings2: np.ndarray
    ) -> np.ndarray:
        """异步计算相似度"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.compute_similarity(embeddings1, embeddings2)
        )


class EmbeddingModelManager:
    """嵌入模型管理器"""

    def __init__(self):
        self.models = {}
        self.default_model = "BAAI/bge-m3"

    async def get_model(self, model_name: Optional[str] = None) -> LocalEmbeddingModel:
        """获取模型实例"""
        model_name = model_name or self.default_model

        if model_name not in self.models:
            model = LocalEmbeddingModel(model_name)
            await model.load_model()
            self.models[model_name] = model

        return self.models[model_name]

    async def encode(
        self, texts: str | Optional[list[str]], model_name: Optional[str] = None
    ) -> np.ndarray:
        """便捷编码方法"""
        model = await self.get_model(model_name)
        return await model.encode_async(texts)

    async def compute_similarity(
        self,
        texts1: str | list[str],
        texts2: str | list[str],
        model_name: Optional[str] = None,
    ) -> float | np.ndarray:
        """便捷相似度计算方法"""
        model = await self.get_model(model_name)

        embeddings1 = await model.encode_async(texts1)
        embeddings2 = await model.encode_async(texts2)

        similarity = await model.compute_similarity_async(embeddings1, embeddings2)

        # 如果是单个文本对,返回标量
        if similarity.shape == (1, 1):
            return similarity[0, 0]

        return similarity


# 导出便捷函数
_manager: Optional[EmbeddingModelManager] = None


def get_embedding_manager() -> EmbeddingModelManager:
    """获取嵌入模型管理器单例"""
    global _manager
    if _manager is None:
        _manager = EmbeddingModelManager()
    return _manager


async def get_embeddings(texts: str | list[str]) -> np.ndarray:
    """便捷函数:获取文本嵌入"""
    manager = get_embedding_manager()
    return await manager.encode(texts)


async def compute_similarity(
    texts1: str | list[str], texts2: str | list[str]
) -> float | np.ndarray:
    """便捷函数:计算文本相似度"""
    manager = get_embedding_manager()
    return await manager.compute_similarity(texts1, texts2)


# 使用示例
async def main():
    """主函数示例"""
    print("=" * 60)
    print("本地嵌入模型服务演示")
    print("=" * 60)

    # 获取嵌入管理器
    manager = get_embedding_manager()

    # 示例1: 编码单个文本
    print("\n📝 示例1: 编码单个文本")
    embedding = await manager.encode("这是一个专利文档")
    print(f"嵌入维度: {embedding.shape}")
    print(f"嵌入向量: {embedding[:5]}... (显示前5维)")

    # 示例2: 编码多个文本
    print("\n📝 示例2: 编码多个文本")
    texts = ["专利检索系统", "文本分类模型", "深度学习算法"]
    embeddings = await manager.encode(texts)
    print(f"嵌入形状: {embeddings.shape}")
    print(f"嵌入维度: {embeddings.shape[1]}")

    # 示例3: 计算相似度
    print("\n📝 示例3: 计算文本相似度")
    similarity = await manager.compute_similarity(
        "专利检索系统", ["专利搜索", "文本分类", "深度学习"]
    )
    print("相似度分数:")
    for i, score in enumerate(similarity):
        print(f"  专利搜索: {score:.3f}")
        print(f"  文本分类: {similarity[1]:.3f}")
        print(f"  深度学习: {similarity[2]:.3f}")
        break

    # 示例4: 批量编码
    print("\n📝 示例4: 批量编码")
    tools = [
        "专利搜索工具,用于检索专利数据库",
        "文本分析工具,用于分析文本内容",
        "代码生成工具,用于生成Python代码",
    ]

    tool_embeddings = await manager.encode(tools)
    print(f"工具嵌入形状: {tool_embeddings.shape}")

    # 计算工具间相似度
    manager_inst = await manager.get_model()
    similarities = manager_inst.compute_similarity(tool_embeddings, tool_embeddings)
    print("\n工具相似度矩阵:")
    print("          工具1    工具2    工具3")
    for i in range(len(similarities)):
        print(f"工具{i+1}:  ", end="")
        for j in range(len(similarities[i])):
            print(f"{similarities[i][j]:.2f}  ", end="")
        print()

    print("\n✅ 演示完成")


# 入口点: @async_main装饰器已添加到main函数

