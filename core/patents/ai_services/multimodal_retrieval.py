from __future__ import annotations
"""
P2-4: 多模态检索增强系统

基于学术论文的图像-文本混合检索技术，实现：
1. 专利附图向量化
2. 跨模态相似度检索
3. 混合检索融合

使用模型：
- qwen3.5 (本地): 快速文本向量化
- deepseek-reasoner: 复杂查询理解

参考文献：
- "A Survey on Multimodal Patent Retrieval" (2024)
- "Vision-Language Models for Patent Image Understanding"
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np

# 设置日志
logger = logging.getLogger(__name__)


# ============================================================================
# 枚举类型定义
# ============================================================================

class SearchMode(Enum):
    """检索模式枚举"""
    TEXT_ONLY = "text_only"           # 纯文本检索
    VECTOR_ONLY = "vector_only"       # 纯向量检索
    HYBRID = "hybrid"                 # 文本+向量混合
    IMAGE_ONLY = "image_only"         # 纯图像检索
    MULTIMODAL = "multimodal"         # 多模态检索（文本+图像）


class ImageType(Enum):
    """专利附图类型"""
    STRUCTURE = "structure"           # 结构图
    FLOWCHART = "flowchart"           # 流程图
    CIRCUIT = "circuit"               # 电路图
    CHEMICAL = "chemical"             # 化学结构式
    PERSPECTIVE = "perspective"       # 立体图
    EXPLODED = "exploded"             # 爆炸图
    SECTION = "section"               # 剖面图
    UNKNOWN = "unknown"               # 未知类型


class FusionStrategy(Enum):
    """融合策略枚举"""
    LINEAR = "linear"                 # 线性加权融合
    RR_FUSION = "rr_fusion"           # Reciprocal Rank融合
    RRF = "rrf"                       # Reciprocal Rank Fusion (别名)
    SCORE_NORM = "score_norm"         # 分数归一化融合
    LEARNED = "learned"               # 学习式融合（需要训练）


class RelevanceLevel(Enum):
    """相关度级别"""
    HIGHLY_RELEVANT = "highly_relevant"   # 高度相关 (>0.8)
    RELEVANT = "relevant"                  # 相关 (0.6-0.8)
    PARTIALLY_RELEVANT = "partially"       # 部分相关 (0.4-0.6)
    MARGINAL = "marginal"                  # 边缘相关 (0.2-0.4)
    IRRELEVANT = "irrelevant"              # 不相关 (<0.2)


# ============================================================================
# 数据结构定义
# ============================================================================

@dataclass
class ImageVector:
    """图像向量数据结构"""
    image_id: str                     # 图像唯一标识
    patent_number: str                # 专利号
    figure_number: str                # 图号 (如 "图1", "FIG.2")
    image_type: ImageType             # 图像类型
    vector: np.ndarray                # 图像向量 (768维)
    caption: str                      # 图像说明文字
    components: list[str]             # 组件标注列表
    page_number: int = 0              # 页码
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "image_id": self.image_id,
            "patent_number": self.patent_number,
            "figure_number": self.figure_number,
            "image_type": self.image_type.value,
            "vector_shape": self.vector.shape if self.vector is not None else None,
            "caption": self.caption,
            "components": self.components,
            "page_number": self.page_number,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class TextVector:
    """文本向量数据结构"""
    text_id: str                      # 文本唯一标识
    text: str                         # 原始文本
    vector: np.ndarray                # 文本向量 (768维)
    source: str                       # 来源 (claim/description/abstract)
    patent_number: str = ""           # 专利号
    section: str = ""                 # 章节
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "text_id": self.text_id,
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "vector_shape": self.vector.shape if self.vector is not None else None,
            "source": self.source,
            "patent_number": self.patent_number,
            "section": self.section,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class SearchResult:
    """检索结果数据结构"""
    result_id: str                    # 结果ID
    patent_number: str                # 专利号
    relevance_score: float            # 相关度分数 (0-1)
    relevance_level: RelevanceLevel   # 相关度级别
    matched_content: str              # 匹配内容
    matched_images: list[str]         # 匹配的图像ID列表
    highlight_positions: list[tuple[int, int]] = field(default_factory=list)  # 高亮位置
    source_type: str = "hybrid"       # 来源类型
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "result_id": self.result_id,
            "patent_number": self.patent_number,
            "relevance_score": self.relevance_score,
            "relevance_level": self.relevance_level.value,
            "matched_content": self.matched_content[:200] + "..." if len(self.matched_content) > 200 else self.matched_content,
            "matched_images": self.matched_images,
            "highlight_positions": self.highlight_positions,
            "source_type": self.source_type,
            "metadata": self.metadata
        }


@dataclass
class HybridSearchResult:
    """混合检索结果数据结构"""
    query_id: str                     # 查询ID
    query: str                        # 原始查询
    mode: SearchMode                  # 检索模式
    text_results: list[SearchResult]  # 文本检索结果
    image_results: list[SearchResult] # 图像检索结果
    fused_results: list[SearchResult] # 融合后结果
    fusion_strategy: FusionStrategy   # 融合策略
    text_weight: float                # 文本权重
    image_weight: float               # 图像权重
    total_time: float                 # 总耗时(秒)
    retrieval_stats: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "query_id": self.query_id,
            "query": self.query,
            "mode": self.mode.value,
            "text_results_count": len(self.text_results),
            "image_results_count": len(self.image_results),
            "fused_results_count": len(self.fused_results),
            "fusion_strategy": self.fusion_strategy.value,
            "text_weight": self.text_weight,
            "image_weight": self.image_weight,
            "total_time": self.total_time,
            "retrieval_stats": self.retrieval_stats,
            "top_results": [r.to_dict() for r in self.fused_results[:5]]
        }


@dataclass
class ImageSearchQuery:
    """图像检索查询"""
    query_image_id: Optional[str]     # 查询图像ID
    query_image_vector: np.ndarray | None  # 查询图像向量
    query_text: Optional[str]         # 辅助文本描述
    query_text_vector: np.ndarray | None   # 文本向量
    image_type_filter: ImageType | None    # 图像类型过滤
    top_k: int = 10                   # 返回数量
    min_similarity: float = 0.5       # 最低相似度阈值


@dataclass
class RetrievalConfig:
    """检索配置"""
    mode: SearchMode = SearchMode.HYBRID
    fusion_strategy: FusionStrategy = FusionStrategy.RRF
    text_weight: float = 0.6          # 文本权重
    image_weight: float = 0.4         # 图像权重
    top_k: int = 20                   # 返回结果数
    min_score: float = 0.3            # 最低分数阈值
    enable_rerank: bool = True        # 启用重排序
    rerank_top_n: int = 50            # 重排序数量
    cache_results: bool = True        # 缓存结果


# ============================================================================
# 图像向量化器
# ============================================================================

class ImageVectorizer:
    """
    专利图像向量化器

    使用视觉语言模型将专利附图转换为向量表示
    """

    def __init__(self, llm_manager=None):
        """
        初始化图像向量化器

        Args:
            llm_manager: LLM管理器
        """
        self.llm_manager = llm_manager
        self._vector_cache: dict[str, np.ndarray] = {}

    async def vectorize_image(
        self,
        image_data: bytes | str,
        image_type: ImageType = ImageType.UNKNOWN
    ) -> np.ndarray:
        """
        将图像转换为向量

        Args:
            image_data: 图像数据 (bytes或base64字符串)
            image_type: 图像类型

        Returns:
            768维numpy数组向量
        """
        # 生成缓存键
        if isinstance(image_data, bytes):
            cache_key = hashlib.md5(image_data).hexdigest()
        else:
            cache_key = hashlib.md5(image_data.encode()).hexdigest()

        # 检查缓存
        if cache_key in self._vector_cache:
            logger.debug(f"使用缓存的图像向量: {cache_key[:8]}")
            return self._vector_cache[cache_key]

        # 使用VLM进行图像向量化
        if self.llm_manager:
            try:
                # 构造图像描述提示
                prompt = self._build_vectorization_prompt(image_type)

                # 调用多模态模型
                response = await self.llm_manager.generate(
                    prompt=prompt,
                    images=[image_data] if isinstance(image_data, bytes) else None,
                    model="qwen3.5"  # 使用本地多模态模型
                )

                # 从响应中提取向量表示
                # 实际实现中应该使用模型的embedding输出
                vector = self._extract_vector_from_response(response)

            except Exception as e:
                logger.warning(f"VLM向量化失败，使用备用方法: {e}")
                vector = self._fallback_vectorization(image_data)
        else:
            # 无LLM管理器时使用备用方法
            vector = self._fallback_vectorization(image_data)

        # 缓存结果
        self._vector_cache[cache_key] = vector

        return vector

    def _build_vectorization_prompt(self, image_type: ImageType) -> str:
        """构建向量化提示"""
        type_descriptions = {
            ImageType.STRUCTURE: "结构示意图",
            ImageType.FLOWCHART: "流程图",
            ImageType.CIRCUIT: "电路图",
            ImageType.CHEMICAL: "化学结构式",
            ImageType.PERSPECTIVE: "立体图",
            ImageType.EXPLODED: "爆炸图",
            ImageType.SECTION: "剖面图",
            ImageType.UNKNOWN: "技术图"
        }

        return f"""分析这张专利{type_descriptions.get(image_type, '附图')}，提取以下信息：
1. 图像类型确认
2. 主要组件和部件
3. 连接关系和结构特征
4. 技术要点

请用简洁的语言描述图像的核心技术内容。"""

    def _extract_vector_from_response(self, response: str) -> np.ndarray:
        """从响应中提取向量"""
        # 简化实现：基于响应文本生成伪向量
        # 实际应使用模型的embedding输出
        text_hash = hashlib.sha256(response.encode()).hexdigest()
        seed = int(text_hash[:8], 16)
        np.random.seed(seed)
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)  # 归一化
        return vector

    def _fallback_vectorization(self, image_data: bytes | str) -> np.ndarray:
        """备用向量化方法"""
        if isinstance(image_data, bytes):
            data_hash = hashlib.sha256(image_data).hexdigest()
        else:
            data_hash = hashlib.sha256(image_data.encode()).hexdigest()

        seed = int(data_hash[:8], 16)
        np.random.seed(seed)
        vector = np.random.randn(768).astype(np.float32)
        vector = vector / np.linalg.norm(vector)
        return vector

    def detect_image_type(self, image_data: bytes) -> ImageType:
        """
        检测图像类型

        Args:
            image_data: 图像数据

        Returns:
            检测到的图像类型
        """
        # 简化实现：基于图像特征判断
        # 实际应使用CNN分类器
        if len(image_data) < 1000:
            return ImageType.UNKNOWN

        # 基于图像大小粗略估计
        if len(image_data) > 100000:
            return ImageType.PERSPECTIVE
        elif len(image_data) > 50000:
            return ImageType.STRUCTURE
        else:
            return ImageType.FLOWCHART


# ============================================================================
# 跨模态检索器
# ============================================================================

class CrossModalRetriever:
    """
    跨模态检索器

    实现文本-图像的跨模态相似度计算和检索
    """

    def __init__(
        self,
        embedding_service=None,
        vector_store=None
    ):
        """
        初始化跨模态检索器

        Args:
            embedding_service: 嵌入服务
            vector_store: 向量存储
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self._image_index: dict[str, ImageVector] = {}
        self._text_index: dict[str, TextVector] = {}

    def index_image(self, image_vector: ImageVector) -> None:
        """索引图像向量"""
        self._image_index[image_vector.image_id] = image_vector
        logger.debug(f"索引图像: {image_vector.image_id}")

    def index_text(self, text_vector: TextVector) -> None:
        """索引文本向量"""
        self._text_index[text_vector.text_id] = text_vector
        logger.debug(f"索引文本: {text_vector.text_id}")

    async def search_by_text(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None
    ) -> list[tuple[str, float]]:
        """
        使用文本向量搜索图像

        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            (image_id, similarity) 元组列表
        """
        results = []

        for image_id, img_vec in self._image_index.items():
            # 应用过滤条件
            if filters:
                if not self._match_filters(img_vec, filters):
                    continue

            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, img_vec.vector)

            if similarity > 0:  # 只保留正相似度
                results.append((image_id, similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    async def search_by_image(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
        filters: Optional[dict[str, Any]] = None
    ) -> list[tuple[str, float]]:
        """
        使用图像向量搜索文本

        Args:
            query_vector: 查询向量
            top_k: 返回数量
            filters: 过滤条件

        Returns:
            (text_id, similarity) 元组列表
        """
        results = []

        for text_id, txt_vec in self._text_index.items():
            # 应用过滤条件
            if filters:
                if not self._match_filters(txt_vec, filters):
                    continue

            # 计算余弦相似度
            similarity = self._cosine_similarity(query_vector, txt_vec.vector)

            if similarity > 0:
                results.append((text_id, similarity))

        # 按相似度排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        if vec1 is None or vec2 is None:
            return 0.0

        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    def _match_filters(self, item: ImageVector | TextVector, filters: dict[str, Any]) -> bool:
        """检查是否匹配过滤条件"""
        for key, value in filters.items():
            if hasattr(item, key):
                item_value = getattr(item, key)
                if isinstance(item_value, Enum):
                    if item_value.value != value:
                        return False
                elif item_value != value:
                    return False
        return True

    def get_stats(self) -> dict[str, int]:
        """获取索引统计"""
        return {
            "image_count": len(self._image_index),
            "text_count": len(self._text_index)
        }


# ============================================================================
# 混合检索融合器
# ============================================================================

class HybridFusion:
    """
    混合检索融合器

    实现多种融合策略
    """

    @staticmethod
    def linear_fusion(
        text_results: list[tuple[str, float]],
        image_results: list[tuple[str, float]],
        text_weight: float = 0.6,
        image_weight: float = 0.4
    ) -> list[tuple[str, float]]:
        """
        线性加权融合

        Args:
            text_results: 文本检索结果
            image_results: 图像检索结果
            text_weight: 文本权重
            image_weight: 图像权重

        Returns:
            融合后的结果
        """
        fused_scores: dict[str, float] = {}

        # 归一化并加权文本结果
        if text_results:
            max_text = max(s for _, s in text_results) if text_results else 1.0
            for doc_id, score in text_results:
                normalized = score / max_text if max_text > 0 else 0
                fused_scores[doc_id] = normalized * text_weight

        # 归一化并加权图像结果
        if image_results:
            max_image = max(s for _, s in image_results) if image_results else 1.0
            for doc_id, score in image_results:
                normalized = score / max_image if max_image > 0 else 0
                if doc_id in fused_scores:
                    fused_scores[doc_id] += normalized * image_weight
                else:
                    fused_scores[doc_id] = normalized * image_weight

        # 排序
        results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return results

    @staticmethod
    def reciprocal_rank_fusion(
        text_results: list[tuple[str, float]],
        image_results: list[tuple[str, float]],
        k: int = 60
    ) -> list[tuple[str, float]]:
        """
        Reciprocal Rank Fusion (RRF)

        RRF(d) = Σ 1/(k + rank(d))

        Args:
            text_results: 文本检索结果
            image_results: 图像检索结果
            k: RRF常数 (默认60)

        Returns:
            融合后的结果
        """
        rrf_scores: dict[str, float] = {}

        # 处理文本结果
        for rank, (doc_id, _) in enumerate(text_results, 1):
            rrf_scores[doc_id] = 1.0 / (k + rank)

        # 处理图像结果
        for rank, (doc_id, _) in enumerate(image_results, 1):
            if doc_id in rrf_scores:
                rrf_scores[doc_id] += 1.0 / (k + rank)
            else:
                rrf_scores[doc_id] = 1.0 / (k + rank)

        # 排序
        results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return results

    @staticmethod
    def score_normalization_fusion(
        text_results: list[tuple[str, float]],
        image_results: list[tuple[str, float]],
        text_weight: float = 0.6,
        image_weight: float = 0.4
    ) -> list[tuple[str, float]]:
        """
        分数归一化融合 (Min-Max归一化)

        Args:
            text_results: 文本检索结果
            image_results: 图像检索结果
            text_weight: 文本权重
            image_weight: 图像权重

        Returns:
            融合后的结果
        """
        fused_scores: dict[str, float] = {}

        # 文本结果归一化
        if text_results:
            scores = [s for _, s in text_results]
            min_s, max_s = min(scores), max(scores)
            range_s = max_s - min_s if max_s != min_s else 1.0

            for doc_id, score in text_results:
                normalized = (score - min_s) / range_s
                fused_scores[doc_id] = normalized * text_weight

        # 图像结果归一化
        if image_results:
            scores = [s for _, s in image_results]
            min_s, max_s = min(scores), max(scores)
            range_s = max_s - min_s if max_s != min_s else 1.0

            for doc_id, score in image_results:
                normalized = (score - min_s) / range_s
                if doc_id in fused_scores:
                    fused_scores[doc_id] += normalized * image_weight
                else:
                    fused_scores[doc_id] = normalized * image_weight

        # 排序
        results = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return results


# ============================================================================
# 多模态检索系统主类
# ============================================================================

class MultimodalRetrievalSystem:
    """
    多模态检索系统

    整合图像向量化、跨模态检索和混合融合功能
    """

    def __init__(
        self,
        llm_manager=None,
        embedding_service=None,
        vector_store=None,
        config: RetrievalConfig | None = None
    ):
        """
        初始化多模态检索系统

        Args:
            llm_manager: LLM管理器
            embedding_service: 嵌入服务
            vector_store: 向量存储
            config: 检索配置
        """
        self.llm_manager = llm_manager
        self.config = config or RetrievalConfig()

        # 初始化子组件
        self.image_vectorizer = ImageVectorizer(llm_manager)
        self.cross_modal_retriever = CrossModalRetriever(
            embedding_service,
            vector_store
        )

        # 结果缓存
        self._result_cache: dict[str, HybridSearchResult] = {}

        logger.info("多模态检索系统初始化完成")

    async def search(
        self,
        query: str,
        query_image: bytes | None = None,
        config: RetrievalConfig | None = None,
        filters: Optional[dict[str, Any]] = None
    ) -> HybridSearchResult:
        """
        执行多模态检索

        Args:
            query: 文本查询
            query_image: 查询图像 (可选)
            config: 检索配置 (可选)
            filters: 过滤条件 (可选)

        Returns:
            混合检索结果
        """
        start_time = time.time()
        used_config = config or self.config

        # 生成查询ID
        query_id = f"query_{int(time.time() * 1000)}"

        logger.info(f"开始检索: query_id={query_id}, mode={used_config.mode.value}")

        # 根据检索模式执行不同策略
        text_results: list[SearchResult] = []
        image_results: list[SearchResult] = []

        # 文本检索
        if used_config.mode in [SearchMode.TEXT_ONLY, SearchMode.HYBRID, SearchMode.MULTIMODAL]:
            text_results = await self._text_search(query, used_config, filters)

        # 图像检索
        if used_config.mode in [SearchMode.IMAGE_ONLY, SearchMode.MULTIMODAL] and query_image:
            image_results = await self._image_search(query_image, used_config, filters)

        # 混合检索（文本触发图像）
        if used_config.mode == SearchMode.HYBRID:
            # 使用文本向量搜索相关图像
            image_results = await self._cross_modal_search(query, used_config, filters)

        # 融合结果
        fused_results = self._fuse_results(
            text_results,
            image_results,
            used_config
        )

        # 计算总耗时
        total_time = time.time() - start_time

        # 构建结果
        result = HybridSearchResult(
            query_id=query_id,
            query=query,
            mode=used_config.mode,
            text_results=text_results,
            image_results=image_results,
            fused_results=fused_results,
            fusion_strategy=used_config.fusion_strategy,
            text_weight=used_config.text_weight,
            image_weight=used_config.image_weight,
            total_time=total_time,
            retrieval_stats={
                "text_count": len(text_results),
                "image_count": len(image_results),
                "fused_count": len(fused_results)
            }
        )

        # 缓存结果
        if used_config.cache_results:
            self._result_cache[query_id] = result

        logger.info(f"检索完成: query_id={query_id}, 耗时={total_time:.3f}s, 结果数={len(fused_results)}")

        return result

    async def _text_search(
        self,
        query: str,
        config: RetrievalConfig,
        filters: Optional[dict[str, Any]]
    ) -> list[SearchResult]:
        """执行文本检索"""
        results = []

        # 模拟检索过程
        # 实际应调用向量数据库
        stats = self.cross_modal_retriever.get_stats()
        text_count = stats.get("text_count", 0)

        if text_count > 0:
            # 模拟生成结果
            for i in range(min(config.top_k, 5)):
                result = SearchResult(
                    result_id=f"text_result_{i}",
                    patent_number=f"CN{1000000 + i}A",
                    relevance_score=0.9 - i * 0.1,
                    relevance_level=self._get_relevance_level(0.9 - i * 0.1),
                    matched_content=f"匹配的文本内容片段 {i+1}",
                    matched_images=[],
                    source_type="text"
                )
                results.append(result)

        return results

    async def _image_search(
        self,
        query_image: bytes,
        config: RetrievalConfig,
        filters: Optional[dict[str, Any]]
    ) -> list[SearchResult]:
        """执行图像检索"""
        results = []

        # 向量化查询图像
        query_vector = await self.image_vectorizer.vectorize_image(query_image)

        # 使用向量搜索
        search_results = await self.cross_modal_retriever.search_by_image(
            query_vector,
            top_k=config.top_k,
            filters=filters
        )

        # 转换为SearchResult
        for i, (result_id, score) in enumerate(search_results):
            result = SearchResult(
                result_id=result_id,
                patent_number=f"CN{2000000 + i}A",
                relevance_score=score,
                relevance_level=self._get_relevance_level(score),
                matched_content=f"图像匹配 {result_id}",
                matched_images=[result_id],
                source_type="image"
            )
            results.append(result)

        return results

    async def _cross_modal_search(
        self,
        query: str,
        config: RetrievalConfig,
        filters: Optional[dict[str, Any]]
    ) -> list[SearchResult]:
        """执行跨模态检索"""
        results = []

        # 获取文本向量
        # 实际应使用embedding服务
        query_vector = np.random.randn(768).astype(np.float32)
        query_vector = query_vector / np.linalg.norm(query_vector)

        # 使用文本向量搜索图像
        search_results = await self.cross_modal_retriever.search_by_text(
            query_vector,
            top_k=config.top_k,
            filters=filters
        )

        # 转换为SearchResult
        for i, (result_id, score) in enumerate(search_results):
            result = SearchResult(
                result_id=result_id,
                patent_number=f"CN{3000000 + i}A",
                relevance_score=score,
                relevance_level=self._get_relevance_level(score),
                matched_content=f"跨模态匹配 {result_id}",
                matched_images=[result_id],
                source_type="cross_modal"
            )
            results.append(result)

        return results

    def _fuse_results(
        self,
        text_results: list[SearchResult],
        image_results: list[SearchResult],
        config: RetrievalConfig
    ) -> list[SearchResult]:
        """融合检索结果"""
        # 转换为(id, score)格式
        text_tuples = [(r.result_id, r.relevance_score) for r in text_results]
        image_tuples = [(r.result_id, r.relevance_score) for r in image_results]

        # 根据融合策略选择方法
        if config.fusion_strategy == FusionStrategy.LINEAR:
            fused_tuples = HybridFusion.linear_fusion(
                text_tuples, image_tuples,
                config.text_weight, config.image_weight
            )
        elif config.fusion_strategy in [FusionStrategy.RRF, FusionStrategy.RR_FUSION]:
            fused_tuples = HybridFusion.reciprocal_rank_fusion(
                text_tuples, image_tuples
            )
        elif config.fusion_strategy == FusionStrategy.SCORE_NORM:
            fused_tuples = HybridFusion.score_normalization_fusion(
                text_tuples, image_tuples,
                config.text_weight, config.image_weight
            )
        else:
            # 默认使用线性融合
            fused_tuples = HybridFusion.linear_fusion(
                text_tuples, image_tuples,
                config.text_weight, config.image_weight
            )

        # 构建结果映射
        result_map = {r.result_id: r for r in text_results + image_results}

        # 创建融合结果
        fused_results = []
        for result_id, score in fused_tuples:
            if result_id in result_map:
                # 更新分数
                original = result_map[result_id]
                fused = SearchResult(
                    result_id=result_id,
                    patent_number=original.patent_number,
                    relevance_score=score,
                    relevance_level=self._get_relevance_level(score),
                    matched_content=original.matched_content,
                    matched_images=original.matched_images,
                    highlight_positions=original.highlight_positions,
                    source_type="fused",
                    metadata=original.metadata
                )
                fused_results.append(fused)
            else:
                # 新结果
                fused = SearchResult(
                    result_id=result_id,
                    patent_number=f"CN{4000000}A",
                    relevance_score=score,
                    relevance_level=self._get_relevance_level(score),
                    matched_content=f"融合结果 {result_id}",
                    matched_images=[],
                    source_type="fused"
                )
                fused_results.append(fused)

        # 应用分数阈值
        fused_results = [r for r in fused_results if r.relevance_score >= config.min_score]

        # 限制数量
        return fused_results[:config.top_k]

    def _get_relevance_level(self, score: float) -> RelevanceLevel:
        """根据分数获取相关度级别"""
        if score >= 0.8:
            return RelevanceLevel.HIGHLY_RELEVANT
        elif score >= 0.6:
            return RelevanceLevel.RELEVANT
        elif score >= 0.4:
            return RelevanceLevel.PARTIALLY_RELEVANT
        elif score >= 0.2:
            return RelevanceLevel.MARGINAL
        else:
            return RelevanceLevel.IRRELEVANT

    async def index_images(
        self,
        images: list[dict[str, Any]]
    ) -> int:
        """
        批量索引图像

        Args:
            images: 图像列表，每个元素包含:
                - image_data: 图像数据
                - patent_number: 专利号
                - figure_number: 图号
                - caption: 图像说明

        Returns:
            成功索引的数量
        """
        indexed_count = 0

        for img_info in images:
            try:
                # 检测图像类型
                image_type = self.image_vectorizer.detect_image_type(
                    img_info.get("image_data", b"")
                )

                # 向量化
                vector = await self.image_vectorizer.vectorize_image(
                    img_info.get("image_data"),
                    image_type
                )

                # 创建ImageVector
                image_vector = ImageVector(
                    image_id=img_info.get("image_id", f"img_{int(time.time() * 1000)}"),
                    patent_number=img_info.get("patent_number", ""),
                    figure_number=img_info.get("figure_number", ""),
                    image_type=image_type,
                    vector=vector,
                    caption=img_info.get("caption", ""),
                    components=img_info.get("components", [])
                )

                # 索引
                self.cross_modal_retriever.index_image(image_vector)
                indexed_count += 1

            except Exception as e:
                logger.error(f"索引图像失败: {e}")

        logger.info(f"批量索引完成: {indexed_count}/{len(images)}")
        return indexed_count

    async def find_similar_images(
        self,
        query_image: bytes,
        top_k: int = 10,
        min_similarity: float = 0.5
    ) -> list[tuple[ImageVector, float]]:
        """
        查找相似图像

        Args:
            query_image: 查询图像
            top_k: 返回数量
            min_similarity: 最低相似度

        Returns:
            (ImageVector, similarity) 元组列表
        """
        # 向量化查询图像
        query_vector = await self.image_vectorizer.vectorize_image(query_image)

        # 搜索
        results = await self.cross_modal_retriever.search_by_text(
            query_vector,
            top_k=top_k
        )

        # 转换结果
        similar_images = []
        for image_id, similarity in results:
            if similarity >= min_similarity:
                if image_id in self.cross_modal_retriever._image_index:
                    image_vec = self.cross_modal_retriever._image_index[image_id]
                    similar_images.append((image_vec, similarity))

        return similar_images

    def get_stats(self) -> dict[str, Any]:
        """获取系统统计信息"""
        retriever_stats = self.cross_modal_retriever.get_stats()

        return {
            "image_count": retriever_stats.get("image_count", 0),
            "text_count": retriever_stats.get("text_count", 0),
            "cache_size": len(self._result_cache),
            "config": {
                "mode": self.config.mode.value,
                "fusion_strategy": self.config.fusion_strategy.value,
                "text_weight": self.config.text_weight,
                "image_weight": self.config.image_weight
            }
        }


# ============================================================================
# 便捷函数
# ============================================================================

async def hybrid_search(
    query: str,
    query_image: bytes | None = None,
    mode: SearchMode = SearchMode.HYBRID,
    top_k: int = 20,
    llm_manager=None
) -> HybridSearchResult:
    """
    混合检索便捷函数

    Args:
        query: 文本查询
        query_image: 查询图像 (可选)
        mode: 检索模式
        top_k: 返回数量
        llm_manager: LLM管理器

    Returns:
        混合检索结果
    """
    config = RetrievalConfig(
        mode=mode,
        top_k=top_k
    )

    system = MultimodalRetrievalSystem(llm_manager=llm_manager, config=config)
    return await system.search(query, query_image)


async def multimodal_search(
    query: str,
    query_image: bytes,
    top_k: int = 20,
    llm_manager=None
) -> HybridSearchResult:
    """
    多模态检索便捷函数

    Args:
        query: 文本查询
        query_image: 查询图像
        top_k: 返回数量
        llm_manager: LLM管理器

    Returns:
        混合检索结果
    """
    return await hybrid_search(
        query=query,
        query_image=query_image,
        mode=SearchMode.MULTIMODAL,
        top_k=top_k,
        llm_manager=llm_manager
    )


def format_search_result(result: HybridSearchResult) -> str:
    """
    格式化检索结果为可读字符串

    Args:
        result: 混合检索结果

    Returns:
        格式化字符串
    """
    lines = [
        "=" * 60,
        "多模态检索结果",
        "=" * 60,
        "",
        f"【查询ID】 {result.query_id}",
        f"【查询内容】 {result.query}",
        f"【检索模式】 {result.mode.value}",
        f"【融合策略】 {result.fusion_strategy.value}",
        "",
        f"【文本结果】 {len(result.text_results)} 条",
        f"【图像结果】 {len(result.image_results)} 条",
        f"【融合结果】 {len(result.fused_results)} 条",
        "",
        "【Top 5 结果】",
        "-" * 60
    ]

    for i, r in enumerate(result.fused_results[:5], 1):
        lines.extend([
            "",
            f"{i}. {r.patent_number}",
            f"   相关度: {r.relevance_score:.2%} ({r.relevance_level.value})",
            f"   匹配内容: {r.matched_content[:50]}...",
            f"   匹配图像: {len(r.matched_images)} 张"
        ])

    lines.extend([
        "",
        "-" * 60,
        f"【总耗时】 {result.total_time:.3f} 秒",
        "=" * 60
    ])

    return "\n".join(lines)


# ============================================================================
# 模块导出
# ============================================================================

__all__ = [
    # 枚举类型
    "SearchMode",
    "ImageType",
    "FusionStrategy",
    "RelevanceLevel",
    # 数据结构
    "ImageVector",
    "TextVector",
    "SearchResult",
    "HybridSearchResult",
    "ImageSearchQuery",
    "RetrievalConfig",
    # 核心类
    "ImageVectorizer",
    "CrossModalRetriever",
    "HybridFusion",
    "MultimodalRetrievalSystem",
    # 便捷函数
    "hybrid_search",
    "multimodal_search",
    "format_search_result"
]
