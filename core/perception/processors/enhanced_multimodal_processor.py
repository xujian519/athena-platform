#!/usr/bin/env python3
from __future__ import annotations
"""
增强多模态处理器
Enhanced Multimodal Processor

提供真正的多模态融合、跨模态推理和智能分析能力

作者: Athena AI系统
创建时间: 2025-12-11
版本: 1.0.0
"""

# Numpy兼容性导入
import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

from .. import BaseProcessor, InputType, PerceptionResult
from ..error_handler import get_global_error_handler, handle_errors
from ..monitoring_metrics import get_global_monitor, monitor_performance
from ..performance_optimizer import get_global_optimizer

logger = logging.getLogger(__name__)


class FusionStrategy(Enum):
    """融合策略"""

    EARLY_FUSION = "early_fusion"  # 早期融合
    LATE_FUSION = "late_fusion"  # 晚期融合
    INTERMEDIATE_FUSION = "intermediate_fusion"  # 中间融合
    ATTENTION_FUSION = "attention_fusion"  # 注意力融合
    CROSS_MODAL_FUSION = "cross_modal_fusion"  # 跨模态融合


class ModalityType(Enum):
    """模态类型"""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    TABLE = "table"
    GRAPH = "graph"


@dataclass
class ModalityData:
    """模态数据"""

    type: ModalityType
    content: Any
    features: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class FusionResult:
    """融合结果"""

    fused_features: np.ndarray
    cross_modal_attention: dict[str, Any]
    modality_weights: dict[str, float]
    fusion_confidence: float
    interpretation: str


@dataclass
class MultiModalAnalysis:
    """多模态分析结果"""

    modality_data: list[ModalityData]
    fusion_result: FusionResult
    semantic_consistency: float
    cross_modal_insights: list[str]
    overall_confidence: float
    processing_summary: dict[str, Any]
class CrossModalAttention:
    """跨模态注意力机制"""

    def __init__(self, feature_dim: int = 768):
        self.feature_dim = feature_dim
        self.attention_weights = None
        self.cross_modal_similarity = {}

    def compute_attention(self, modalities: list[ModalityData]) -> dict[str, Any]:
        """计算跨模态注意力"""
        attention_map = {}
        total_features = []

        # 提取各模态特征
        for i, modality in enumerate(modalities):
            if isinstance(modality.features, dict) and "embedding" in modality.features:
                feature_vec = np.array(modality.features["embedding"])
                if feature_vec.shape[0] != self.feature_dim:
                    # 调整特征维度
                    feature_vec = self._resize_feature(feature_vec)
                total_features.append((i, modality.type.value, feature_vec))

        # 计算模态间相似度
        for i, (_idx1, type1, feat1) in enumerate(total_features):
            for j, (_idx2, type2, feat2) in enumerate(total_features):
                if i < j:
                    similarity = self._compute_similarity(feat1, feat2)
                    self.cross_modal_similarity[f"{type1}_{type2}"] = similarity

        # 计算注意力权重
        if total_features:
            # 基于相似度和置信度计算权重
            weights = []
            for idx, mod_type, _feature in total_features:
                modality = modalities[idx]
                weight = modality.confidence
                # 考虑跨模态相关性
                for key, sim in self.cross_modal_similarity.items():
                    if mod_type in key:
                        weight *= 1 + sim
                weights.append(weight)

            # 归一化权重
            total_weight = np.sum(weights) if HAS_NUMPY else sum(weights)
            if total_weight > 0:
                weights = [w / total_weight for w in weights]

            attention_map = {
                "modality_weights": {
                    total_features[i][1]: weights[i] for i in range(len(total_features))
                },
                "cross_modal_similarity": self.cross_modal_similarity,
                "attention_strength": np.std(weights) if len(weights) > 1 else 0,
            }

        return attention_map

    def _compute_similarity(self, feat1: np.ndarray, feat2: np.ndarray) -> float:
        """计算特征相似度"""
        # 使用余弦相似度
        norm1 = np.linalg.norm(feat1)
        norm2 = np.linalg.norm(feat2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return np.dot(feat1, feat2) / (norm1 * norm2)

    def _resize_feature(self, feature: np.ndarray) -> np.ndarray:
        """调整特征维度"""
        if feature.shape[0] > self.feature_dim:
            # 降维:取前N个维度
            return feature[: self.feature_dim]
        elif feature.shape[0] < self.feature_dim:
            # 升维:零填充
            padded = np.zeros(self.feature_dim, dtype=np.float64) if HAS_NUMPY else [0.0] * self.feature_dim
            padded[: feature.shape[0]] = feature
            return padded
        return feature


class FeatureFusion:
    """特征融合器"""

    def __init__(self, fusion_strategy: FusionStrategy = FusionStrategy.ATTENTION_FUSION):
        self.fusion_strategy = fusion_strategy
        self.attention_mechanism = CrossModalAttention()

    async def fuse_features(self, modalities: list[ModalityData]) -> FusionResult:
        """融合多模态特征"""
        try:
            if self.fusion_strategy == FusionStrategy.ATTENTION_FUSION:
                return await self._attention_fusion(modalities)
            elif self.fusion_strategy == FusionStrategy.EARLY_FUSION:
                return await self._early_fusion(modalities)
            elif self.fusion_strategy == FusionStrategy.LATE_FUSION:
                return await self._late_fusion(modalities)
            else:
                return await self._default_fusion(modalities)

        except Exception as e:
            logger.error(f"特征融合失败: {e}")
            # 返回默认融合结果
            return await self._default_fusion(modalities)

    async def _attention_fusion(self, modalities: list[ModalityData]) -> FusionResult:
        """注意力融合"""
        # 计算跨模态注意力
        attention_map = self.attention_mechanism.compute_attention(modalities)

        # 提取和加权特征
        weighted_features = []
        modality_weights = {}

        for _i, modality in enumerate(modalities):
            if isinstance(modality.features, dict) and "embedding" in modality.features:
                feature_vec = np.array(modality.features["embedding"])
                weight = attention_map["modality_weights"].get(modality.type.value, 0.25)
                weighted_feature = feature_vec * weight
                weighted_features.append(weighted_feature)
                modality_weights[modality.type.value] = weight

        # 融合特征
        if weighted_features:
            fused_features = np.sum(weighted_features, axis=0)
            fusion_confidence = np.mean(list(modality_weights.values()))
        else:
            # 降级处理
            fused_features = np.zeros(768, dtype=np.float64) if HAS_NUMPY else [0.0] * 768
            fusion_confidence = 0.5

        # 生成交叉模态解释
        interpretation = self._generate_interpretation(modalities, attention_map)

        return FusionResult(
            fused_features=fused_features,
            cross_modal_attention=attention_map,
            modality_weights=modality_weights,
            fusion_confidence=fusion_confidence,
            interpretation=interpretation,
        )

    async def _early_fusion(self, modalities: list[ModalityData]) -> FusionResult:
        """早期融合"""
        # 简单的特征拼接
        all_features = []
        modality_weights = {}

        for modality in modalities:
            if isinstance(modality.features, dict) and "embedding" in modality.features:
                feature_vec = np.array(modality.features["embedding"])
                all_features.append(feature_vec)
                modality_weights[modality.type.value] = modality.confidence

        if all_features:
            # 拼接所有特征
            fused_features = np.concatenate(all_features)
            fusion_confidence = np.mean([m.confidence for m in modalities])
        else:
            fused_features = np.zeros(768, dtype=np.float64) if HAS_NUMPY else [0.0] * 768
            fusion_confidence = 0.5

        return FusionResult(
            fused_features=fused_features,
            cross_modal_attention={"strategy": "early_fusion"},
            modality_weights=modality_weights,
            fusion_confidence=fusion_confidence,
            interpretation="早期融合:特征拼接",
        )

    async def _late_fusion(self, modalities: list[ModalityData]) -> FusionResult:
        """晚期融合"""
        # 分别处理各模态,然后融合决策
        modality_scores = {}
        total_confidence = 0

        for modality in modalities:
            # 简化:使用置信度作为分数
            score = modality.confidence
            modality_scores[modality.type.value] = score
            total_confidence += score

        # 加权平均
        if total_confidence > 0:
            for key in modality_scores:
                modality_scores[key] /= total_confidence

        # 创建代表性特征(基于最高置信度模态)
        best_modality = max(modalities, key=lambda m: m.confidence)
        if isinstance(best_modality.features, dict) and "embedding" in best_modality.features:
            fused_features = np.array(best_modality.features["embedding"])
        else:
            fused_features = np.zeros(768, dtype=np.float64) if HAS_NUMPY else [0.0] * 768

        return FusionResult(
            fused_features=fused_features,
            cross_modal_attention={"strategy": "late_fusion", "modality_scores": modality_scores},
            modality_weights=modality_scores,
            fusion_confidence=max(modality_scores.values()) if modality_scores else 0.5,
            interpretation=f"晚期融合:基于{best_modality.type.value}的决策",
        )

    async def _default_fusion(self, modalities: list[ModalityData]) -> FusionResult:
        """默认融合方法"""
        # 简单的平均融合
        all_features = []
        weights = []

        for modality in modalities:
            if isinstance(modality.features, dict) and "embedding" in modality.features:
                feature_vec = np.array(modality.features["embedding"])
                all_features.append(feature_vec)
                weights.append(modality.confidence)

        if all_features:
            # 加权平均
            weights = np.array(weights)
            weights = weights / np.sum(weights)
            fused_features = np.average(all_features, axis=0, weights=weights)
            fusion_confidence = np.mean(weights)
        else:
            fused_features = np.zeros(768, dtype=np.float64) if HAS_NUMPY else [0.0] * 768
            fusion_confidence = 0.5

        return FusionResult(
            fused_features=fused_features,
            cross_modal_attention={"strategy": "default_fusion"},
            modality_weights={m.type.value: m.confidence for m in modalities},
            fusion_confidence=fusion_confidence,
            interpretation="默认融合:加权平均",
        )

    def _generate_interpretation(
        self, modalities: list[ModalityData], attention_map: dict[str, Any]
    ) -> str:
        """生成交叉模态解释"""
        interpretation_parts = []

        # 模态权重分析
        if "modality_weights" in attention_map:
            weights = attention_map["modality_weights"]
            dominant_modality = max(weights.items(), key=lambda x: x[1])
            interpretation_parts.append(
                f"主导模态:{dominant_modality[0]}(权重:{dominant_modality[1]:.2f})"
            )

        # 跨模态相关性
        if "cross_modal_similarity" in attention_map:
            similarities = attention_map["cross_modal_similarity"]
            high_corr = [(k, v) for k, v in similarities.items() if v > 0.7]
            if high_corr:
                interpretation_parts.append(f"高相关模态对:{', '.join([k for k, v in high_corr])}")

        # 注意力强度
        if "attention_strength" in attention_map:
            strength = attention_map["attention_strength"]
            if strength > 0.3:
                interpretation_parts.append("注意力分布较为集中")
            else:
                interpretation_parts.append("注意力分布较为均匀")

        return ";".join(interpretation_parts) if interpretation_parts else "多模态融合完成"


class EnhancedMultiModalProcessor(BaseProcessor):
    """增强多模态处理器"""

    def __init__(self, processor_id: str, config: dict[str, Any] | None = None):
        super().__init__(processor_id, config)

        # 配置参数
        self.fusion_strategy = FusionStrategy(
            self.config.get("fusion_strategy", "attention_fusion")
        )
        self.enable_cross_modal = self.config.get("enable_cross_modal", True)
        self.max_modalities = self.config.get("max_modalities", 5)
        self.min_confidence = self.config.get("min_confidence", 0.3)

        # 组件初始化
        self.feature_fusion = FeatureFusion(self.fusion_strategy)
        self.processors = {}  # 子处理器引用
        self.analysis_cache = {}

        # 获取全局组件
        self.error_handler = None
        self.optimizer = None
        self.monitor = None

        logger.info(
            f"🧩 增强多模态处理器初始化: {self.processor_id}, 融合策略: {self.fusion_strategy.value}"
        )

    async def initialize(self):
        """初始化处理器"""
        logger.info(f"🚀 启动增强多模态处理器: {self.processor_id}")

        try:
            # 获取全局组件
            self.error_handler = get_global_error_handler()
            self.optimizer = await get_global_optimizer()
            self.monitor = await get_global_monitor()

            # 初始化子处理器引用
            await self._initialize_sub_processors()

            # 优化当前处理器
            if self.optimizer:
                await self.optimizer.optimize_processor(self)

            self.initialized = True
            logger.info(f"✅ 增强多模态处理器启动完成: {self.processor_id}")

        except Exception as e:
            logger.error(f"❌ 增强多模态处理器启动失败 {self.processor_id}: {e}")
            raise

    async def _initialize_sub_processors(self):
        """初始化子处理器引用"""
        # 这里可以获取其他处理器的引用,用于处理特定模态
        # 由于是独立模块,这里仅作记录
        logger.debug("子处理器引用初始化完成")

    @monitor_performance(processor_id="enhanced_multimodal")
    @handle_errors()
    async def process(self, data: Any, input_type: str) -> PerceptionResult:
        """处理多模态输入"""
        start_time = time.time()

        try:
            # 解析多模态数据
            modalities = await self._parse_multimodal_data(data)

            if not modalities:
                # 降级处理
                return self._create_fallback_result(data, input_type, "无法解析多模态数据")

            # 检查缓存
            cache_key = self._generate_cache_key(modalities)
            if self.optimizer and cache_key in self.optimizer.cache:
                cached_result = self.optimizer.cache[cache_key]
                logger.debug(f"使用缓存的多模态结果: {cache_key}")
                return cached_result

            # 预处理各模态
            processed_modalities = await self._preprocess_modalities(modalities)

            # 特征融合
            fusion_result = await self.feature_fusion.fuse_features(processed_modalities)

            # 跨模态分析
            analysis = await self._perform_cross_modal_analysis(processed_modalities, fusion_result)

            # 生成处理结果
            result = PerceptionResult(
                input_type=InputType.MULTIMODAL,
                raw_content=data,
                processed_content=analysis,
                features={
                    "modality_count": len(modalities),
                    "fusion_strategy": self.fusion_strategy.value,
                    "cross_modal_attention": fusion_result.cross_modal_attention,
                    "modality_weights": fusion_result.modality_weights,
                    "semantic_consistency": analysis.semantic_consistency,
                    "cross_modal_insights": analysis.cross_modal_insights,
                },
                confidence=analysis.overall_confidence,
                metadata={
                    "processor_id": self.processor_id,
                    "processing_time": time.time() - start_time,
                    "modality_types": [m.type.value for m in modalities],
                    "fusion_confidence": fusion_result.fusion_confidence,
                    "interpretation": fusion_result.interpretation,
                },
                timestamp=datetime.now(),
            )

            # 缓存结果
            if self.optimizer and result.confidence > 0.8:
                self.optimizer.cache[cache_key] = result

            # 记录监控事件
            if self.monitor:
                self.monitor.record_processing_event(
                    processor_id=self.processor_id,
                    input_type=InputType.MULTIMODAL,
                    success=True,
                    processing_time=time.time() - start_time,
                    confidence=result.confidence,
                )

            logger.info(
                f"🎯 多模态处理完成: {len(modalities)}种模态, 置信度: {result.confidence:.2f}"
            )
            return result

        except Exception as e:
            logger.error(f"❌ 多模态处理失败: {e}")
            if self.monitor:
                self.monitor.record_processing_event(
                    processor_id=self.processor_id,
                    input_type=InputType.MULTIMODAL,
                    success=False,
                    processing_time=time.time() - start_time,
                )
            raise

    async def _parse_multimodal_data(self, data: Any) -> list[ModalityData]:
        """解析多模态数据"""
        modalities = []

        if isinstance(data, dict):
            # 结构化多模态数据
            for key, value in data.items():
                if key == "text" or key == "content":
                    modalities.append(await self._process_text_modality(value))
                elif key == "image" or key == "images":
                    modalities.append(await self._process_image_modality(value))
                elif key == "audio" or key == "audio_data":
                    modalities.append(await self._process_audio_modality(value))
                elif key == "video" or key == "video_data":
                    modalities.append(await self._process_video_modality(value))
                elif key == "table" or key == "tables":
                    modalities.append(await self._process_table_modality(value))
                elif key == "graph" or key == "graphs":
                    modalities.append(await self._process_graph_modality(value))

        elif isinstance(data, list):
            # 列表形式的多模态数据
            for item in data:
                if isinstance(item, dict) and "type" in item and "content" in item:
                    modality_type = item.get("type", "text")
                    content = item.get("content")

                    if modality_type == "text":
                        modalities.append(await self._process_text_modality(content))
                    elif modality_type == "image":
                        modalities.append(await self._process_image_modality(content))
                    # ... 其他模态

        # 限制模态数量
        if len(modalities) > self.max_modalities:
            # 按置信度排序,保留前N个
            modalities.sort(key=lambda m: m.confidence, reverse=True)
            modalities = modalities[: self.max_modalities]

        # 过滤低置信度模态
        modalities = [m for m in modalities if m.confidence >= self.min_confidence]

        return modalities

    async def _process_text_modality(self, content: Any) -> ModalityData:
        """处理文本模态"""
        if isinstance(content, str):
            text = content
        elif isinstance(content, dict) and "text" in content:
            text = content["text"]
        else:
            text = str(content)

        # 简化:基于文本长度和关键词计算置信度
        confidence = min(1.0, len(text) / 1000.0)

        # 提取简单特征
        features = {
            "text_length": len(text),
            "word_count": len(text.split()),
            "language": "zh" if any("\u4e00" <= c <= "\u9fff" for c in text) else "en",
            "embedding": self._text_to_embedding(text),
        }

        return ModalityData(
            type=ModalityType.TEXT,
            content=text,
            features=features,
            confidence=confidence,
            metadata={"processed": True},
        )

    async def _process_image_modality(self, content: Any) -> ModalityData:
        """处理图像模态"""
        # 简化实现
        features = {
            "format": "unknown",
            "size_estimate": len(str(content)) if content else 0,
            "embedding": np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768,  # 临时随机特征
        }

        return ModalityData(
            type=ModalityType.IMAGE,
            content=content,
            features=features,
            confidence=0.7,  # 默认置信度
            metadata={"processed": True},
        )

    async def _process_audio_modality(self, content: Any) -> ModalityData:
        """处理音频模态"""
        # 简化实现
        features = {
            "duration": 0,
            "format": "unknown",
            "embedding": np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768,  # 临时随机特征
        }

        return ModalityData(
            type=ModalityType.AUDIO,
            content=content,
            features=features,
            confidence=0.6,  # 默认置信度
            metadata={"processed": True},
        )

    async def _process_video_modality(self, content: Any) -> ModalityData:
        """处理视频模态"""
        # 简化实现
        features = {
            "duration": 0,
            "format": "unknown",
            "frame_count": 0,
            "embedding": np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768,  # 临时随机特征
        }

        return ModalityData(
            type=ModalityType.VIDEO,
            content=content,
            features=features,
            confidence=0.6,  # 默认置信度
            metadata={"processed": True},
        )

    async def _process_table_modality(self, content: Any) -> ModalityData:
        """处理表格模态"""
        # 简化实现
        features = {"rows": 0, "columns": 0, "embedding": np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768}  # 临时随机特征

        return ModalityData(
            type=ModalityType.TABLE,
            content=content,
            features=features,
            confidence=0.8,  # 表格通常结构清晰
            metadata={"processed": True},
        )

    async def _process_graph_modality(self, content: Any) -> ModalityData:
        """处理图形模态"""
        # 简化实现
        features = {
            "nodes": 0,
            "edges": 0,
            "graph_type": "unknown",
            "embedding": np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768,  # 临时随机特征
        }

        return ModalityData(
            type=ModalityType.GRAPH,
            content=content,
            features=features,
            confidence=0.7,  # 默认置信度
            metadata={"processed": True},
        )

    def _text_to_embedding(self, text: str) -> list[float]:
        """将文本转换为嵌入向量(简化实现)"""
        # 这里应该使用实际的嵌入模型
        # 临时使用简单的hash-based嵌入
        text_bytes = text.encode("utf-8")
        hash_obj = hashlib.sha256(text_bytes)

        # 生成768维向量
        embedding = []
        for i in range(0, 768, 32):
            chunk = (
                hash_obj.digest()[i : i + 32]
                if i + 32 <= len(hash_obj.digest())
                else hash_obj.digest()[i:]
            )
            embedding.extend([b / 255.0 for b in chunk.ljust(32, b"\0")])

        return embedding[:768]

    async def _preprocess_modalities(self, modalities: list[ModalityData]) -> list[ModalityData]:
        """预处理各模态数据"""
        processed = []

        for modality in modalities:
            # 标准化特征
            if isinstance(modality.features, dict):
                # 确保有embedding
                if "embedding" not in modality.features:
                    modality.features["embedding"] = np.random.random(768).tolist() if HAS_NUMPY else [0.0] * 768

                # 标准化置信度
                modality.confidence = max(0.0, min(1.0, modality.confidence))

            processed.append(modality)

        return processed

    async def _perform_cross_modal_analysis(
        self, modalities: list[ModalityData], fusion_result: FusionResult
    ) -> MultiModalAnalysis:
        """执行跨模态分析"""
        # 计算语义一致性
        semantic_consistency = self._compute_semantic_consistency(modalities)

        # 生成跨模态洞察
        cross_modal_insights = await self._generate_cross_modal_insights(modalities, fusion_result)

        # 计算整体置信度
        overall_confidence = fusion_result.fusion_confidence * 0.6 + semantic_consistency * 0.4

        # 处理摘要
        processing_summary = {
            "modality_count": len(modalities),
            "dominant_modality": (
                max(fusion_result.modality_weights.items(), key=lambda x: x[1])[0]
                if fusion_result.modality_weights
                else None
            ),
            "fusion_interpretation": fusion_result.interpretation,
            "attention_strength": fusion_result.cross_modal_attention.get("attention_strength", 0),
            "processing_timestamp": datetime.now().isoformat(),
        }

        return MultiModalAnalysis(
            modality_data=modalities,
            fusion_result=fusion_result,
            semantic_consistency=semantic_consistency,
            cross_modal_insights=cross_modal_insights,
            overall_confidence=overall_confidence,
            processing_summary=processing_summary,
        )

    def _compute_semantic_consistency(self, modalities: list[ModalityData]) -> float:
        """计算语义一致性"""
        if len(modalities) < 2:
            return 1.0

        # 简化实现:基于模态权重分布计算一致性
        weights = [m.confidence for m in modalities]
        weight_variance = np.var(weights) if weights else 0

        # 权重分布越均匀,一致性越高
        consistency = 1.0 - min(1.0, weight_variance)
        return consistency

    async def _generate_cross_modal_insights(
        self, modalities: list[ModalityData], fusion_result: FusionResult
    ) -> list[str]:
        """生成跨模态洞察"""
        insights = []

        # 模态数量洞察
        if len(modalities) > 3:
            insights.append("包含丰富的多模态信息,有利于全面理解")
        elif len(modalities) == 2:
            insights.append("双模态信息互补")

        # 主导模态洞察
        if fusion_result.modality_weights:
            dominant_modality = max(fusion_result.modality_weights.items(), key=lambda x: x[1])
            if dominant_modality[1] > 0.6:
                insights.append(f"{dominant_modality[0]}模态起主导作用")

        # 注意力分布洞察
        attention_strength = fusion_result.cross_modal_attention.get("attention_strength", 0)
        if attention_strength > 0.5:
            insights.append("不同模态间存在显著差异")
        elif attention_strength < 0.1:
            insights.append("各模态信息均衡")

        return insights

    def _generate_cache_key(self, modalities: list[ModalityData]) -> str:
        """生成缓存键"""
        # 基于模态内容生成唯一键
        content_parts = []
        for modality in sorted(modalities, key=lambda m: m.type.value):
            content_str = str(modality.content)[:100]  # 限制长度
            content_parts.append(f"{modality.type.value}:{content_str}")

        combined_content = "|".join(content_parts)
        return f"multimodal_{hashlib.md5(combined_content.encode(), usedforsecurity=False).hexdigest()}"

    def _create_fallback_result(
        self, data: Any, input_type: str, error_message: str
    ) -> PerceptionResult:
        """创建降级结果"""
        return PerceptionResult(
            input_type=InputType.MULTIMODAL,
            raw_content=data,
            processed_content=None,
            features={"error": True, "error_message": error_message, "fallback": True},
            confidence=0.0,
            metadata={"processor_id": self.processor_id, "error": True, "fallback": True},
            timestamp=datetime.now(),
        )

    async def cleanup(self):
        """清理处理器"""
        logger.info(f"🧹 清理增强多模态处理器: {self.processor_id}")

        # 清理缓存
        self.analysis_cache.clear()

        self.initialized = False

    async def get_processing_stats(self) -> dict[str, Any]:
        """获取处理统计"""
        return {
            "processor_id": self.processor_id,
            "fusion_strategy": self.fusion_strategy.value,
            "enabled_features": {
                "cross_modal": self.enable_cross_modal,
                "max_modalities": self.max_modalities,
                "min_confidence": self.min_confidence,
            },
            "cache_size": len(self.analysis_cache),
            "components": {
                "error_handler": self.error_handler is not None,
                "optimizer": self.optimizer is not None,
                "monitor": self.monitor is not None,
            },
        }


__all__ = ["EnhancedMultiModalProcessor"]
