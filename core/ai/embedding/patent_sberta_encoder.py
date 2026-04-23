#!/usr/bin/env python3

"""
PatentSBERTa编码器 - 专利领域专用语义嵌入
PatentSBERTa Encoder - Domain-Specific Patent Semantic Embedding

基于论文: "PatentSBERTa: Patent embeddings and application to technology landscaping"
论文链接: https://arxiv.org/abs/2103.11933

该模型在百万级专利语料上训练，专门针对专利文本进行优化，
相比通用嵌入模型在专利分类、相似度和检索任务上有显著提升。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import logging
from pathlib import Path

import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


# ========== PatentSBERTa编码器 ==========


class PatentSBERTaEncoder:
    """
    PatentSBERTa编码器

    特性:
    1. 领域专用: 在专利语料上训练，理解专利术语
    2. 多语言: 支持英文、德语专利文本
    3. 高维嵌入: 768维语义向量
    4. 对比学习: 优化的语义相似度计算

    使用方式:
        encoder = PatentSBERTaEncoder()
        embedding = encoder.encode("Patent title and abstract")
    """

    def __init__(
        self,
        model_name: str = "AI-Growth-Lab/PatentSBERTa",
        device: str = "cpu",
        cache_dir: Optional[str] = None,
    ):
        """
        初始化PatentSBERTa编码器

        Args:
            model_name: 模型名称
                - "AI-Growth-Lab/PatentSBERTa": 原始版本
                - "AI-Growth-Lab/PatentSBERTa-v2": 改进版本
            device: 运行设备 ("cpu" 或 "cuda")
            cache_dir: 模型缓存目录
        """
        self.model_name = model_name
        self.device = device
        self.cache_dir = cache_dir or "data/models/patent_sberta"

        # 模型组件
        self._model = None
        self._tokenizer = None

        # 嵌入维度
        self.embedding_dim = 768

        # 初始化标记
        self._initialized = False

        logger.info(f"📝 PatentSBERTa编码器初始化: {model_name}")

    def initialize(self) -> None:
        """延迟加载模型"""
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer

            logger.info("正在加载PatentSBERTa模型...")

            # 创建缓存目录
            Path(self.cache_dir).mkdir(parents=True, exist_ok=True)

            # 加载模型
            self._model = SentenceTransformer(
                self.model_name,
                device=self.device,
                cache_folder=self.cache_dir,
            )

            self._tokenizer = self._model.tokenizer

            self._initialized = True

            logger.info(f"✅ PatentSBERTa模型加载成功 (维度: {self.embedding_dim})")

        except Exception as e:
            logger.error(f"❌ PatentSBERTa模型加载失败: {e}")
            raise

    def encode(
        self,
        text: str | list[str],
        normalize: bool = True,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> np.ndarray | list[np.ndarray]:
        """
        编码文本为嵌入向量

        Args:
            text: 输入文本或文本列表
            normalize: 是否归一化向量
            batch_size: 批处理大小
            show_progress: 是否显示进度

        Returns:
            np.ndarray or List[np.ndarray]: 嵌入向量 (768维)
        """
        if not self._initialized:
            self.initialize()

        # 单个文本
        if isinstance(text, str):
            return self._encode_single(text, normalize)

        # 多个文本
        return self._encode_batch(text, normalize, batch_size, show_progress)

    def _encode_single(self, text: str, normalize: bool) -> np.ndarray:
        """编码单个文本"""
        embedding = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            show_progress_bar=False,
        )

        return embedding

    def _encode_batch(
        self,
        texts: list[str],
        normalize: bool,
        batch_size: int,
        show_progress: bool,
    ) -> list[np.ndarray]:
        """批量编码"""
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=normalize,
            batch_size=batch_size,
            show_progress_bar=show_progress,
        )

        # 如果结果是单个数组(只有一个文本)，转换为列表
        if len(embeddings.shape) == 1:
            return [embeddings]

        return list(embeddings)

    def encode_patent(
        self,
        title: str,
        abstract: Optional[str] = None,
        claims: Optional[str] = None,
        normalize: bool = True,
    ) -> np.ndarray:
        """
        编码专利文档

        Args:
            title: 专利标题
            abstract: 专利摘要 (可选)
            claims: 权利要求 (可选)
            normalize: 是否归一化

        Returns:
            np.ndarray: 专利嵌入向量 (768维)
        """
        # 构建专利文本
        patent_text = title

        if abstract:
            patent_text += f" {abstract}"

        if claims:
            # 权利要求通常很长，只取前500字符
            claims_preview = claims[:500] if len(claims) > 500 else claims
            patent_text += f" {claims_preview}"

        return self.encode(patent_text, normalize=normalize)

    def compute_similarity(
        self,
        text1: str | np.ndarray,
        text2: str | np.ndarray,
    ) -> float:
        """
        计算两个文本的语义相似度

        Args:
            text1: 文本1或嵌入向量1
            text2: 文本2或嵌入向量2

        Returns:
            float: 相似度分数 (0-1)
        """
        # 如果是文本，先编码
        if isinstance(text1, str):
            emb1 = self.encode(text1, normalize=True)
        else:
            emb1 = text1

        if isinstance(text2, str):
            emb2 = self.encode(text2, normalize=True)
        else:
            emb2 = text2

        # 计算余弦相似度
        similarity = np.dot(emb1, emb2)

        return float(similarity)

    @property
    def dimension(self) -> int:
        """返回嵌入维度"""
        return self.embedding_dim

    def get_model_info(self) -> dict:
        """获取模型信息"""
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "device": self.device,
            "initialized": self._initialized,
            "max_sequence_length": self._model.max_seq_length if self._model else 512,
        }


# ========== 全局编码器实例 ==========


_global_patent_sberta: Optional[PatentSBERTaEncoder] = None


def get_patent_sberta_encoder(
    model_name: str = "AI-Growth-Lab/PatentSBERTa",
    device: str = "cpu",
) -> PatentSBERTaEncoder:
    """
    获取全局PatentSBERTa编码器实例

    Args:
        model_name: 模型名称
        device: 运行设备

    Returns:
        PatentSBERTaEncoder: 编码器实例
    """
    global _global_patent_sberta

    if _global_patent_sberta is None:
        _global_patent_sberta = PatentSBERTaEncoder(
            model_name=model_name,
            device=device,
        )

    return _global_patent_sberta


# ========== 后备编码器 (当PatentSBERTa不可用时) ==========


class FallbackPatentEncoder:
    """
    后备专利编码器

    当PatentSBERTa不可用时，使用BGE-M3作为后备
    """

    def __init__(self):
        """初始化后备编码器"""
        from core.ai.nlp.bge_m3_loader import get_bge_m3_encoder

        self._bge_encoder = get_bge_m3_encoder()
        self.embedding_dim = 1024  # BGE-M3是1024维

        logger.info("⚠️ 使用BGE-M3作为PatentSBERTa的后备编码器")

    def encode(
        self,
        text: str | list[str],
        normalize: bool = True,
        **kwargs,
    ) -> np.ndarray | list[np.ndarray]:
        """编码文本"""
        return self._bge_encoder.encode(text, normalize=normalize)

    def encode_patent(
        self,
        title: str,
        abstract: Optional[str] = None,
        claims: Optional[str] = None,
        normalize: bool = True,
    ) -> np.ndarray:
        """编码专利文档"""
        patent_text = title
        if abstract:
            patent_text += f" {abstract}"
        if claims:
            claims_preview = claims[:500] if len(claims) > 500 else claims
            patent_text += f" {claims_preview}"

        return self.encode(patent_text, normalize=normalize)

    def compute_similarity(
        self,
        text1: str | np.ndarray,
        text2: str | np.ndarray,
    ) -> float:
        """计算相似度"""
        from sklearn.metrics.pairwise import cosine_similarity

        emb1 = text1 if isinstance(text1, np.ndarray) else self.encode(text1)
        emb2 = text2 if isinstance(text2, np.ndarray) else self.encode(text2)

        return float(cosine_similarity([emb1], [emb2])[0][0])


# ========== 自动选择编码器 ==========


def get_patent_encoder(
    use_patent_sberta: bool = True,
    fallback: bool = True,
) -> PatentSBERTaEncoder | FallbackPatentEncoder:
    """
    自动获取可用的专利编码器

    Args:
        use_patent_sberta: 优先使用PatentSBERTa
        fallback: 是否启用后备方案

    Returns:
        可用的专利编码器
    """
    if use_patent_sberta:
        try:
            encoder = get_patent_sberta_encoder()
            encoder.initialize()  # 预加载模型
            return encoder
        except Exception as e:
            logger.warning(f"PatentSBERTa加载失败: {e}")
            if fallback:
                logger.info("切换到后备编码器")
                return FallbackPatentEncoder()
            raise

    # 不使用PatentSBERTa，直接返回后备
    if fallback:
        return FallbackPatentEncoder()

    raise RuntimeError("没有可用的专利编码器")


# ========== 导出 ==========


__all__ = [
    "PatentSBERTaEncoder",
    "get_patent_sberta_encoder",
    "FallbackPatentEncoder",
    "get_patent_encoder",
]

