#!/usr/bin/env python3
from __future__ import annotations
"""
混合专利嵌入服务 - Hybrid Patent Embedding Service
双嵌入系统: BGE-M3 (通用) + PatentSBERTa (专利专用)

基于论文分析实施双嵌入策略，结合通用和专利专用嵌入模型的优势。

Author: Athena Team
Version: 1.0.0
Date: 2026-02-26
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


# ========== 嵌入模式 ==========


class EmbeddingMode(Enum):
    """嵌入模式"""
    GENERAL = "general"  # 仅使用通用嵌入 (BGE-M3)
    PATENT = "patent"  # 仅使用专利嵌入 (PatentSBERTa)
    HYBRID = "hybrid"  # 混合模式 (加权融合)
    ADAPTIVE = "adaptive"  # 自适应模式 (根据任务类型选择)


# ========== 嵌入结果 ==========


@dataclass
class HybridEmbedding:
    """混合嵌入结果"""
    general: np.ndarray | None = None  # BGE-M3嵌入 (1024维)
    patent: np.ndarray | None = None  # PatentSBERTa嵌入 (768维)
    fused: np.ndarray | None = None  # 融合嵌入 (可选)

    # 元数据
    mode: EmbeddingMode = EmbeddingMode.HYBRID
    weights: dict[str, float] = None  # 各模型的权重

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        result = {
            "mode": self.mode.value,
        }

        if self.general is not None:
            result["general_dim"] = self.general.shape[0]

        if self.patent is not None:
            result["patent_dim"] = self.patent.shape[0]

        if self.fused is not None:
            result["fused_dim"] = self.fused.shape[0]

        if self.weights:
            result["weights"] = self.weights

        return result


# ========== 混合嵌入服务 ==========


class HybridPatentEmbeddingService:
    """
    混合专利嵌入服务

    核心功能:
    1. 双嵌入生成 (通用 + 专利专用)
    2. 智能嵌入融合
    3. 自适应模式选择
    4. 缓存优化
    """

    # 默认权重配置
    DEFAULT_WEIGHTS = {
        EmbeddingMode.PATENT: {"patent": 1.0, "general": 0.0},
        EmbeddingMode.GENERAL: {"patent": 0.0, "general": 1.0},
        EmbeddingMode.HYBRID: {"patent": 0.7, "general": 0.3},  # 专利专用权重更高
    }

    def __init__(
        self,
        mode: EmbeddingMode = EmbeddingMode.HYBRID,
        cache_size: int = 10000,
        enable_patent_sberta: bool = True,
        enable_bge_m3: bool = True,
    ):
        """
        初始化混合嵌入服务

        Args:
            mode: 默认嵌入模式
            cache_size: 缓存大小
            enable_patent_sberta: 是否启用PatentSBERTa
            enable_bge_m3: 是否启用BGE-M3
        """
        self.mode = mode
        self.enable_patent_sberta = enable_patent_sberta
        self.enable_bge_m3 = enable_bge_m3

        # 编码器实例
        self._bge_encoder = None
        self._patent_encoder = None

        # 缓存
        self._cache: dict[str, HybridEmbedding] = {}
        self._cache_hits = 0
        self._cache_misses = 0

        # 权重配置
        self._weights = self.DEFAULT_WEIGHTS.copy()

        logger.info("🔄 混合专利嵌入服务初始化")
        logger.info(f"   模式: {mode.value}")
        logger.info(f"   PatentSBERTa: {enable_patent_sberta}")
        logger.info(f"   BGE-M3: {enable_bge_m3}")

    async def initialize(self) -> None:
        """延迟初始化编码器"""
        if self.enable_bge_m3 and self._bge_encoder is None:
            try:
                from core.nlp.bge_m3_loader import get_bge_m3_encoder

                self._bge_encoder = get_bge_m3_encoder()
                logger.info("   ✅ BGE-M3编码器已加载")
            except Exception as e:
                logger.warning(f"   ⚠️ BGE-M3编码器加载失败: {e}")
                self.enable_bge_m3 = False

        if self.enable_patent_sberta and self._patent_encoder is None:
            try:
                from core.embedding.patent_sberta_encoder import (
                    get_patent_encoder,
                )

                self._patent_encoder = get_patent_encoder(
                    use_patent_sberta=True,
                    fallback=False,  # 不使用BGE作为后备，因为我们已经有BGE
                )
                self._patent_encoder.initialize()
                logger.info("   ✅ PatentSBERTa编码器已加载")
            except Exception as e:
                logger.warning(f"   ⚠️ PatentSBERTa编码器加载失败: {e}")
                self.enable_patent_sberta = False

        # 如果两个都失败，抛出异常
        if not self.enable_bge_m3 and not self.enable_patent_sberta:
            raise RuntimeError("没有可用的嵌入编码器")

    async def encode(
        self,
        text: str,
        mode: EmbeddingMode | None = None,
        use_cache: bool = True,
    ) -> HybridEmbedding:
        """
        编码文本为混合嵌入

        Args:
            text: 输入文本
            mode: 嵌入模式 (None表示使用默认模式)
            use_cache: 是否使用缓存

        Returns:
            HybridEmbedding: 混合嵌入结果
        """
        # 检查缓存
        cache_key = f"{mode or self.mode.value}:{text[:100]}"
        if use_cache and cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]

        self._cache_misses += 1

        # 使用指定模式或默认模式
        embed_mode = mode or self.mode

        # 确保已初始化
        if not self._bge_encoder and not self._patent_encoder:
            await self.initialize()

        result = HybridEmbedding(mode=embed_mode)

        # 根据模式生成嵌入
        if embed_mode == EmbeddingMode.GENERAL:
            result.general = await self._encode_general(text)

        elif embed_mode == EmbeddingMode.PATENT:
            result.patent = await self._encode_patent(text)

        elif embed_mode == EmbeddingMode.HYBRID:
            result.general = await self._encode_general(text)
            result.patent = await self._encode_patent(text)
            result.fused = self._fuse_embeddings(result.general, result.patent)

        elif embed_mode == EmbeddingMode.ADAPTIVE:
            # 自适应模式：根据文本特征选择
            is_patent_text = self._is_patent_text(text)
            if is_patent_text:
                result.patent = await self._encode_patent(text)
                result.general = await self._encode_general(text)
                result.fused = self._fuse_embeddings(result.general, result.patent)
            else:
                result.general = await self._encode_general(text)

        # 设置权重
        result.weights = self._weights.get(embed_mode, {})

        # 缓存结果
        if use_cache:
            self._cache[cache_key] = result
            # 限制缓存大小
            if len(self._cache) > 10000:
                # 删除最旧的10%
                keys_to_remove = list(self._cache.keys())[:1000]
                for key in keys_to_remove:
                    del self._cache[key]

        return result

    async def encode_patent(
        self,
        title: str,
        abstract: str | None = None,
        claims: str | None = None,
        mode: EmbeddingMode | None = None,
    ) -> HybridEmbedding:
        """
        编码专利文档

        Args:
            title: 专利标题
            abstract: 专利摘要
            claims: 权利要求
            mode: 嵌入模式

        Returns:
            HybridEmbedding: 混合嵌入结果
        """
        # 构建专利文本
        patent_text = title
        if abstract:
            patent_text += f" {abstract}"
        if claims:
            claims_preview = claims[:500] if len(claims) > 500 else claims
            patent_text += f" {claims_preview}"

        return await self.encode(patent_text, mode=mode)

    async def _encode_general(self, text: str) -> np.ndarray:
        """使用BGE-M3编码"""
        if not self.enable_bge_m3 or not self._bge_encoder:
            raise RuntimeError("BGE-M3编码器不可用")

        return self._bge_encoder.encode(text, normalize=True)

    async def _encode_patent(self, text: str) -> np.ndarray:
        """使用PatentSBERTa编码"""
        if not self.enable_patent_sberta or not self._patent_encoder:
            raise RuntimeError("PatentSBERTa编码器不可用")

        return self._patent_encoder.encode(text, normalize=True)

    def _fuse_embeddings(
        self,
        general_emb: np.ndarray,
        patent_emb: np.ndarray,
    ) -> np.ndarray:
        """
        融合两个嵌入向量

        方法: 加权拼接 + 降维

        Args:
            general_emb: 通用嵌入 (1024维)
            patent_emb: 专利嵌入 (768维)

        Returns:
            np.ndarray: 融合嵌入向量
        """
        # 获取权重
        weights = self._weights.get(EmbeddingMode.HYBRID, {})
        patent_weight = weights.get("patent", 0.7)
        general_weight = weights.get("general", 0.3)

        # 归一化
        general_emb = general_emb / np.linalg.norm(general_emb)
        patent_emb = patent_emb / np.linalg.norm(patent_emb)

        # 使用最大维度 (1024)
        max_dim = max(general_emb.shape[0], patent_emb.shape[0])

        # 对齐维度
        if general_emb.shape[0] < max_dim:
            general_padded = np.pad(general_emb, (0, max_dim - general_emb.shape[0]))
        else:
            general_padded = general_emb

        if patent_emb.shape[0] < max_dim:
            patent_padded = np.pad(patent_emb, (0, max_dim - patent_emb.shape[0]))
        else:
            patent_padded = patent_emb

        # 加权融合
        fused = general_weight * general_padded + patent_weight * patent_padded

        # 归一化
        fused = fused / np.linalg.norm(fused)

        return fused

    def _is_patent_text(self, text: str) -> bool:
        """
        判断文本是否为专利文本

        基于特征:
        - 包含专利术语
        - 特定句式结构
        - 关键词匹配
        """
        patent_keywords = [
            "权利要求", "说明书", "摘要", "所述",
            "claim", "embodiment", "wherein", "comprising",
            "一种", "装置", "方法", "系统",
        ]

        text_lower = text.lower()
        keyword_count = sum(1 for kw in patent_keywords if kw in text_lower)

        # 至少包含3个专利关键词
        return keyword_count >= 3

    def set_weights(self, mode: EmbeddingMode, weights: dict[str, float]) -> None:
        """
        设置融合权重

        Args:
            mode: 嵌入模式
            weights: 权重字典 {"patent": 0.7, "general": 0.3}
        """
        self._weights[mode] = weights
        logger.info(f"权重已更新: {mode.value} -> {weights}")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = self._cache_hits / total_requests if total_requests > 0 else 0

        return {
            "cache_size": len(self._cache),
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
        }

    def clear_cache(self) -> None:
        """清空缓存"""
        self._cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        logger.info("缓存已清空")


# ========== 全局服务实例 ==========


_global_hybrid_service: HybridPatentEmbeddingService | None = None


def get_hybrid_embedding_service(
    mode: EmbeddingMode = EmbeddingMode.HYBRID,
    enable_patent_sberta: bool = True,
    enable_bge_m3: bool = True,
) -> HybridPatentEmbeddingService:
    """
    获取全局混合嵌入服务实例

    Args:
        mode: 默认嵌入模式
        enable_patent_sberta: 是否启用PatentSBERTa
        enable_bge_m3: 是否启用BGE-M3

    Returns:
        HybridPatentEmbeddingService: 服务实例
    """
    global _global_hybrid_service

    if _global_hybrid_service is None:
        _global_hybrid_service = HybridPatentEmbeddingService(
            mode=mode,
            enable_patent_sberta=enable_patent_sberta,
            enable_bge_m3=enable_bge_m3,
        )

    return _global_hybrid_service


# ========== 导出 ==========


__all__ = [
    "EmbeddingMode",
    "HybridEmbedding",
    "HybridPatentEmbeddingService",
    "get_hybrid_embedding_service",
]
