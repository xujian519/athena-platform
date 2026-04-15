#!/usr/bin/env python3
"""
多模态专利检索器
Multimodal Patent Retriever

功能:
1. 文本编码 - 使用sentence-transformers对专利文本进行编码
2. 图像编码 - 使用CLIP对专利附图进行编码
3. 联合检索 - 同时基于文本和图像进行检索
4. 相似度计算 - 计算查询与专利的相似度

作者: Athena平台团队
创建时间: 2026-01-31
版本: v1.0.0
"""

from __future__ import annotations
import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# 数据模型
# ============================================================================


class QueryType(str, Enum):
    """查询类型"""
    TEXT_ONLY = "text_only"           # 纯文本查询
    IMAGE_ONLY = "image_only"         # 纯图像查询
    MULTIMODAL = "multimodal"         # 多模态查询


@dataclass
class RetrievalResult:
    """检索结果"""
    patent_id: str
    title: str
    abstract: str = ""
    similarity_score: float = 0.0
    text_similarity: float = 0.0
    image_similarity: float = 0.0
    image_captions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "patent_id": self.patent_id,
            "title": self.title,
            "abstract": self.abstract,
            "similarity_score": self.similarity_score,
            "text_similarity": self.text_similarity,
            "image_similarity": self.image_similarity,
            "image_captions": self.image_captions,
            "metadata": self.metadata
        }


@dataclass
class MultimodalQuery:
    """多模态查询"""
    query_id: str
    query_type: QueryType
    text: str | None = None
    image_data: bytes | None = None
    image_path: str | None = None
    fusion_weights: dict[str, float] = field(default_factory=lambda: {"text": 0.6, "image": 0.4})
    top_k: int = 10
    filters: dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 多模态专利检索器
# ============================================================================


class MultimodalPatentRetriever:
    """
    多模态专利检索器

    功能:
    1. 文本编码 - sentence-transformers
    2. 图像编码 - CLIP
    3. 联合检索 - 加权融合
    4. 向量数据库集成
    """

    def __init__(
        self,
        text_encoder_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        clip_model: str = "openai/clip-vit-base-patch32",
        device: str | None = None,
        cache_dir: str | None = None,
        vector_db_config: dict | None = None
    ):
        """
        初始化多模态专利检索器

        Args:
            text_encoder_model: 文本编码器模型名称
            clip_model: CLIP模型名称
            device: 运行设备 (None=自动检测)
            cache_dir: 模型缓存目录
            vector_db_config: 向量数据库配置
        """
        self.text_encoder_model = text_encoder_model
        self.clip_model_name = clip_model

        # 自动检测设备
        if device is None:
            self.device = self._detect_device()
        else:
            self.device = device

        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/huggingface")

        # 模型实例（延迟加载）
        self.text_encoder = None
        self.clip_model = None
        self.clip_processor = None

        # 向量数据库（需要时初始化）
        self.vector_db = None
        self.vector_db_config = vector_db_config

        logger.info(f"MultimodalPatentRetriever初始化完成 (device={self.device})")

    def _detect_device(self) -> str:
        """自动检测最佳设备"""
        try:
            import torch

            if torch.backends.mps.is_available():
                logger.info("检测到MPS设备，将使用GPU加速")
                return "mps"
            elif torch.cuda.is_available():
                logger.info("检测到CUDA设备，将使用GPU加速")
                return "cuda"
            else:
                return "cpu"

        except ImportError:
            return "cpu"

    def load_models(self):
        """加载模型（延迟加载）"""
        if self.text_encoder is None:
            self._load_text_encoder()

        if self.clip_model is None:
            self._load_clip_model()

    def _load_text_encoder(self):
        """加载文本编码器"""
        try:
            from sentence_transformers import SentenceTransformer

            self.text_encoder = SentenceTransformer(
                self.text_encoder_model,
                device=self.device,
                cache_folder=self.cache_dir
            )

            embedding_dim = self.text_encoder.get_sentence_embedding_dimension()
            logger.info(f"文本编码器加载成功: {self.text_encoder_model}, 维度: {embedding_dim}")

        except Exception as e:
            logger.error(f"文本编码器加载失败: {e}")
            raise

    def _load_clip_model(self):
        """加载CLIP模型"""
        try:
            from transformers import CLIPModel, CLIPProcessor

            self.clip_processor = CLIPProcessor.from_pretrained(
                self.clip_model_name,
                cache_dir=self.cache_dir
            )
            self.clip_model = CLIPModel.from_pretrained(
                self.clip_model_name,
                cache_dir=self.cache_dir
            ).to(self.device)

            logger.info(f"CLIP模型加载成功: {self.clip_model_name}")

        except Exception as e:
            logger.error(f"CLIP模型加载失败: {e}")
            raise

    # ========================================================================
    # 编码功能
    # ========================================================================

    def encode_text(
        self,
        text: str,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        编码文本为向量

        Args:
            text: 输入文本
            batch_size: 批处理大小

        Returns:
            文本向量 (numpy array)
        """
        self.load_models()

        try:
            embedding = self.text_encoder.encode(
                text,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            return embedding

        except Exception as e:
            logger.error(f"文本编码失败: {e}")
            # 返回零向量
            return np.zeros(self.text_encoder.get_sentence_embedding_dimension())

    def encode_texts(
        self,
        texts: list[str],
        batch_size: int = 32
    ) -> np.ndarray:
        """
        批量编码文本

        Args:
            texts: 文本列表
            batch_size: 批处理大小

        Returns:
            文本向量矩阵 (numpy array)
        """
        self.load_models()

        try:
            embeddings = self.text_encoder.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            return embeddings

        except Exception as e:
            logger.error(f"批量文本编码失败: {e}")
            return np.zeros((len(texts), self.text_encoder.get_sentence_embedding_dimension()))

    def encode_image(
        self,
        image_input: str | bytes | Path
    ) -> np.ndarray:
        """
        编码图像为向量

        Args:
            image_input: 图像输入（文件路径或字节数据）

        Returns:
            图像向量 (numpy array)
        """
        self.load_models()

        try:
            # 加载图像
            from PIL import Image

            if isinstance(image_input, (str, Path)):
                image = Image.open(image_input).convert("RGB")
            elif isinstance(image_input, bytes):
                import io
                image = Image.open(io.BytesIO(image_input)).convert("RGB")
            else:
                raise ValueError(f"不支持的图像输入类型: {type(image_input)}")

            # 调整大小

            inputs = self.clip_processor(
                images=image,
                return_tensors="pt"
            ).to(self.device)

            # 获取图像特征
            with import_torch().no_grad():
                image_features = self.clip_model.get_image_features(**inputs)

            # 归一化
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            return image_features.cpu().numpy()[0]

        except Exception as e:
            logger.error(f"图像编码失败: {e}")
            # 返回零向量（CLIP默认512维）
            return np.zeros(512)

    def encode_multimodal(
        self,
        text: str | None = None,
        image_input: str | bytes | Path | None = None,
        fusion_weights: dict[str, float] | None = None
    ) -> np.ndarray:
        """
        多模态联合编码

        Args:
            text: 文本输入
            image_input: 图像输入
            fusion_weights: 融合权重 {"text": 0.6, "image": 0.4}

        Returns:
            联合向量 (numpy array)
        """
        self.load_models()

        # 默认权重
        if fusion_weights is None:
            fusion_weights = {"text": 0.6, "image": 0.4}

        vectors = []
        weights = []

        # 文本编码
        if text:
            text_emb = self.encode_text(text)
            vectors.append(text_emb)
            weights.append(fusion_weights.get("text", 0.6))

        # 图像编码
        if image_input:
            image_emb = self.encode_image(image_input)
            vectors.append(image_emb)
            weights.append(fusion_weights.get("image", 0.4))

        if not vectors:
            raise ValueError("至少需要提供文本或图像输入")

        # 归一化权重
        weights = np.array(weights)
        weights = weights / weights.sum()

        # 加权融合
        # 需要将向量对齐到相同维度
        max_dim = max(v.shape[0] for v in vectors)
        aligned_vectors = []

        for v in vectors:
            if v.shape[0] < max_dim:
                # 零填充
                padded = np.zeros(max_dim)
                padded[:v.shape[0]] = v
                aligned_vectors.append(padded)
            else:
                # 截断
                aligned_vectors.append(v[:max_dim])

        # 加权求和
        fused = np.average(aligned_vectors, axis=0, weights=weights)

        # L2归一化
        fused = fused / np.linalg.norm(fused)

        return fused

    # ========================================================================
    # 检索功能
    # ========================================================================

    async def search(
        self,
        query: MultimodalQuery,
        patent_collection: list[dict] | None = None
    ) -> list[RetrievalResult]:
        """
        执行多模态检索

        Args:
            query: 多模态查询对象
            patent_collection: 专利集合（如果未使用向量数据库）

        Returns:
            检索结果列表
        """
        try:
            # 1. 编码查询
            query_emb = self.encode_multimodal(
                text=query.text,
                image_input=query.image_path or query.image_data,
                fusion_weights=query.fusion_weights
            )

            # 2. 执行检索
            if self.vector_db is not None:
                # 使用向量数据库
                results = await self._search_from_vector_db(query_emb, query)
            elif patent_collection is not None:
                # 使用内存中的专利集合
                results = await self._search_from_memory(query_emb, query, patent_collection)
            else:
                raise ValueError("必须提供向量数据库或专利集合")

            # 3. 排序和过滤
            results = self._sort_and_filter(results, query)

            return results[:query.top_k]

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    async def _search_from_vector_db(
        self,
        query_emb: np.ndarray,
        query: MultimodalQuery
    ) -> list[RetrievalResult]:
        """从向量数据库检索"""
        # TODO: 集成Qdrant或Milvus
        raise NotImplementedError("向量数据库集成待实现")

    async def _search_from_memory(
        self,
        query_emb: np.ndarray,
        query: MultimodalQuery,
        patent_collection: list[dict]
    ) -> list[RetrievalResult]:
        """从内存专利集合检索"""
        results = []

        for patent in patent_collection:
            # 计算相似度
            similarity = self._compute_similarity(query_emb, patent)

            # 创建结果对象
            result = RetrievalResult(
                patent_id=patent.get("patent_id", ""),
                title=patent.get("title", ""),
                abstract=patent.get("abstract", ""),
                similarity_score=similarity,
                metadata=patent
            )

            results.append(result)

        return results

    def _compute_similarity(
        self,
        query_emb: np.ndarray,
        patent: dict
    ) -> float:
        """计算查询与专利的相似度"""
        # 这里简化处理，实际应该分别计算文本和图像相似度
        patent_emb = patent.get("embedding")
        if patent_emb is None:
            return 0.0

        # 余弦相似度
        similarity = np.dot(query_emb, patent_emb) / (
            np.linalg.norm(query_emb) * np.linalg.norm(patent_emb)
        )

        return float(similarity)

    def _sort_and_filter(
        self,
        results: list[RetrievalResult],
        query: MultimodalQuery
    ) -> list[RetrievalResult]:
        """排序和过滤结果"""
        # 按相似度降序排序
        results.sort(key=lambda x: x.similarity_score, reverse=True)

        # 应用过滤器
        if query.filters:
            filtered_results = []
            for result in results:
                match = True
                for key, value in query.filters.items():
                    if key in result.metadata:
                        if isinstance(value, list):
                            if result.metadata[key] not in value:
                                match = False
                                break
                        else:
                            if result.metadata[key] != value:
                                match = False
                                break
                if match:
                    filtered_results.append(result)
            results = filtered_results

        return results

    # ========================================================================
    # 辅助方法
    # ========================================================================

    async def index_patent(
        self,
        patent_id: str,
        title: str,
        abstract: str,
        claims: str,
        image_paths: list[str] | None = None
    ) -> dict[str, Any]:
        """
        索引单个专利

        Args:
            patent_id: 专利ID
            title: 标题
            abstract: 摘要
            claims: 权利要求
            image_paths: 附图路径列表

        Returns:
            索引结果（包含向量）
        """
        self.load_models()

        # 组合文本
        combined_text = f"{title} {abstract} {claims}"

        # 编码文本
        text_emb = self.encode_text(combined_text)

        # 编码图像
        image_embeddings = []
        image_captions = []

        if image_paths:
            for img_path in image_paths:
                try:
                    img_emb = self.encode_image(img_path)
                    image_embeddings.append(img_emb)

                    # 生成图像描述（可选）
                    # caption = self._generate_caption(img_path)
                    # image_captions.append(caption)

                except Exception as e:
                    logger.warning(f"图像编码失败 {img_path}: {e}")

        # 构建索引数据
        index_data = {
            "patent_id": patent_id,
            "title": title,
            "abstract": abstract,
            "text_embedding": text_emb.tolist(),
            "image_embeddings": [emb.tolist() for emb in image_embeddings],
            "image_captions": image_captions,
            "timestamp": datetime.now().isoformat()
        }

        # 存储到向量数据库（如果配置）
        if self.vector_db is not None:
            await self._store_to_vector_db(index_data)

        return index_data

    async def _store_to_vector_db(self, index_data: dict[str, Any]):
        """存储到向量数据库"""
        # TODO: 集成Qdrant或Milvus
        pass


# ============================================================================
# 工具函数
# ============================================================================


def import_torch():
    """延迟导入torch"""
    import torch
    return torch


if __name__ == "__main__":
    async def main():
        # 创建检索器
        retriever = MultimodalPatentRetriever()

        # 测试文本编码
        text = "一种无线通信基站设备，包括天线单元和信号处理单元"
        text_emb = retriever.encode_text(text)
        print(f"文本向量维度: {text_emb.shape}")

        # 测试多模态编码
        fused_emb = retriever.encode_multimodal(
            text="无线通信基站",
            fusion_weights={"text": 1.0, "image": 0.0}
        )
        print(f"多模态向量维度: {fused_emb.shape}")

        print("\n检索器测试完成！")

    # 运行测试
    asyncio.run(main())
