"""
P2-4: 多模态检索增强系统 - 单元测试

测试覆盖:
1. 枚举类型测试
2. 数据结构测试
3. 图像向量化测试
4. 跨模态检索测试
5. 混合融合测试
6. 端到端检索测试
7. 异步操作测试
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# 导入被测模块
from core.patents.ai_services.multimodal_retrieval import (
    CrossModalRetriever,
    FusionStrategy,
    HybridFusion,
    HybridSearchResult,
    ImageType,
    # 数据结构
    ImageVector,
    # 核心类
    ImageVectorizer,
    MultimodalRetrievalSystem,
    RelevanceLevel,
    RetrievalConfig,
    # 枚举类型
    SearchMode,
    SearchResult,
    TextVector,
    format_search_result,
    # 便捷函数
    hybrid_search,
    multimodal_search,
)

# ============================================================================
# 枚举类型测试
# ============================================================================

class TestEnums:
    """枚举类型测试"""

    def test_search_mode_values(self):
        """测试检索模式枚举值"""
        assert SearchMode.TEXT_ONLY.value == "text_only"
        assert SearchMode.VECTOR_ONLY.value == "vector_only"
        assert SearchMode.HYBRID.value == "hybrid"
        assert SearchMode.IMAGE_ONLY.value == "image_only"
        assert SearchMode.MULTIMODAL.value == "multimodal"

    def test_image_type_values(self):
        """测试图像类型枚举值"""
        assert ImageType.STRUCTURE.value == "structure"
        assert ImageType.FLOWCHART.value == "flowchart"
        assert ImageType.CIRCUIT.value == "circuit"
        assert ImageType.CHEMICAL.value == "chemical"
        assert ImageType.PERSPECTIVE.value == "perspective"
        assert ImageType.EXPLODED.value == "exploded"
        assert ImageType.SECTION.value == "section"
        assert ImageType.UNKNOWN.value == "unknown"

    def test_fusion_strategy_values(self):
        """测试融合策略枚举值"""
        assert FusionStrategy.LINEAR.value == "linear"
        assert FusionStrategy.RRF.value == "rrf"
        assert FusionStrategy.RR_FUSION.value == "rr_fusion"
        assert FusionStrategy.SCORE_NORM.value == "score_norm"
        assert FusionStrategy.LEARNED.value == "learned"

    def test_relevance_level_values(self):
        """测试相关度级别枚举值"""
        assert RelevanceLevel.HIGHLY_RELEVANT.value == "highly_relevant"
        assert RelevanceLevel.RELEVANT.value == "relevant"
        assert RelevanceLevel.PARTIALLY_RELEVANT.value == "partially"
        assert RelevanceLevel.MARGINAL.value == "marginal"
        assert RelevanceLevel.IRRELEVANT.value == "irrelevant"


# ============================================================================
# 数据结构测试
# ============================================================================

class TestDataStructures:
    """数据结构测试"""

    def test_image_vector_creation(self):
        """测试图像向量创建"""
        vector = np.random.randn(768).astype(np.float32)
        image_vector = ImageVector(
            image_id="img_001",
            patent_number="CN1234567A",
            figure_number="图1",
            image_type=ImageType.STRUCTURE,
            vector=vector,
            caption="主结构示意图",
            components=["部件A", "部件B"]
        )

        assert image_vector.image_id == "img_001"
        assert image_vector.patent_number == "CN1234567A"
        assert image_vector.figure_number == "图1"
        assert image_vector.image_type == ImageType.STRUCTURE
        assert image_vector.vector.shape == (768,)
        assert len(image_vector.components) == 2

    def test_image_vector_to_dict(self):
        """测试图像向量转字典"""
        vector = np.random.randn(768).astype(np.float32)
        image_vector = ImageVector(
            image_id="img_001",
            patent_number="CN1234567A",
            figure_number="图1",
            image_type=ImageType.STRUCTURE,
            vector=vector,
            caption="主结构示意图",
            components=["部件A"]
        )

        result = image_vector.to_dict()
        assert result["image_id"] == "img_001"
        assert result["patent_number"] == "CN1234567A"
        assert result["image_type"] == "structure"
        assert result["vector_shape"] == (768,)

    def test_text_vector_creation(self):
        """测试文本向量创建"""
        vector = np.random.randn(768).astype(np.float32)
        text_vector = TextVector(
            text_id="txt_001",
            text="这是一段专利描述文本",
            vector=vector,
            source="description",
            patent_number="CN1234567A",
            section="具体实施方式"
        )

        assert text_vector.text_id == "txt_001"
        assert text_vector.source == "description"
        assert text_vector.vector.shape == (768,)

    def test_search_result_creation(self):
        """测试检索结果创建"""
        result = SearchResult(
            result_id="result_001",
            patent_number="CN1234567A",
            relevance_score=0.85,
            relevance_level=RelevanceLevel.HIGHLY_RELEVANT,
            matched_content="匹配的文本内容",
            matched_images=["img_001", "img_002"],
            source_type="hybrid"
        )

        assert result.result_id == "result_001"
        assert result.relevance_score == 0.85
        assert result.relevance_level == RelevanceLevel.HIGHLY_RELEVANT
        assert len(result.matched_images) == 2

    def test_hybrid_search_result_creation(self):
        """测试混合检索结果创建"""
        text_results = [
            SearchResult(
                result_id="text_001",
                patent_number="CN1111111A",
                relevance_score=0.9,
                relevance_level=RelevanceLevel.HIGHLY_RELEVANT,
                matched_content="文本匹配",
                matched_images=[],
                source_type="text"
            )
        ]

        result = HybridSearchResult(
            query_id="query_001",
            query="检索查询",
            mode=SearchMode.HYBRID,
            text_results=text_results,
            image_results=[],
            fused_results=text_results,
            fusion_strategy=FusionStrategy.RRF,
            text_weight=0.6,
            image_weight=0.4,
            total_time=0.5
        )

        assert result.query_id == "query_001"
        assert result.mode == SearchMode.HYBRID
        assert len(result.text_results) == 1
        assert result.fusion_strategy == FusionStrategy.RRF

    def test_retrieval_config_defaults(self):
        """测试检索配置默认值"""
        config = RetrievalConfig()

        assert config.mode == SearchMode.HYBRID
        assert config.fusion_strategy == FusionStrategy.RRF
        assert config.text_weight == 0.6
        assert config.image_weight == 0.4
        assert config.top_k == 20
        assert config.min_score == 0.3
        assert config.enable_rerank is True


# ============================================================================
# 图像向量化器测试
# ============================================================================

class TestImageVectorizer:
    """图像向量化器测试"""

    @pytest.fixture
    def vectorizer(self):
        """创建向量化器实例"""
        return ImageVectorizer()

    def test_vectorizer_initialization(self, vectorizer):
        """测试向量化器初始化"""
        assert vectorizer.llm_manager is None
        assert len(vectorizer._vector_cache) == 0

    @pytest.mark.asyncio
    async def test_vectorize_image_without_llm(self, vectorizer):
        """测试无LLM时的图像向量化"""
        image_data = b"fake_image_data_for_testing"
        vector = await vectorizer.vectorize_image(image_data)

        assert vector is not None
        assert vector.shape == (768,)
        # 检查归一化
        norm = np.linalg.norm(vector)
        assert abs(norm - 1.0) < 0.01

    @pytest.mark.asyncio
    async def test_vectorize_image_caching(self, vectorizer):
        """测试图像向量化缓存"""
        image_data = b"cached_image_data"

        # 第一次向量化
        vector1 = await vectorizer.vectorize_image(image_data)

        # 第二次向量化（应该使用缓存）
        vector2 = await vectorizer.vectorize_image(image_data)

        # 向量应该相同
        np.testing.assert_array_almost_equal(vector1, vector2)

    def test_detect_image_type(self, vectorizer):
        """测试图像类型检测"""
        # 小图像
        small_image = b"x" * 500
        img_type = vectorizer.detect_image_type(small_image)
        assert img_type == ImageType.UNKNOWN

        # 大图像
        large_image = b"x" * 150000
        img_type = vectorizer.detect_image_type(large_image)
        assert img_type == ImageType.PERSPECTIVE

    def test_build_vectorization_prompt(self, vectorizer):
        """测试向量化提示构建"""
        prompt = vectorizer._build_vectorization_prompt(ImageType.FLOWCHART)
        assert "流程图" in prompt
        assert "分析" in prompt


# ============================================================================
# 跨模态检索器测试
# ============================================================================

class TestCrossModalRetriever:
    """跨模态检索器测试"""

    @pytest.fixture
    def retriever(self):
        """创建检索器实例"""
        return CrossModalRetriever()

    @pytest.fixture
    def sample_image_vector(self):
        """创建样本图像向量"""
        return ImageVector(
            image_id="img_001",
            patent_number="CN1234567A",
            figure_number="图1",
            image_type=ImageType.STRUCTURE,
            vector=np.random.randn(768).astype(np.float32),
            caption="测试图像",
            components=[]
        )

    @pytest.fixture
    def sample_text_vector(self):
        """创建样本文本向量"""
        return TextVector(
            text_id="txt_001",
            text="测试文本",
            vector=np.random.randn(768).astype(np.float32),
            source="description"
        )

    def test_index_image(self, retriever, sample_image_vector):
        """测试图像索引"""
        retriever.index_image(sample_image_vector)

        assert "img_001" in retriever._image_index
        assert retriever._image_index["img_001"].patent_number == "CN1234567A"

    def test_index_text(self, retriever, sample_text_vector):
        """测试文本索引"""
        retriever.index_text(sample_text_vector)

        assert "txt_001" in retriever._text_index
        assert retriever._text_index["txt_001"].source == "description"

    @pytest.mark.asyncio
    async def test_search_by_text(self, retriever, sample_image_vector):
        """测试文本搜索图像"""
        # 索引图像
        retriever.index_image(sample_image_vector)

        # 使用随机查询向量
        query_vector = np.random.randn(768).astype(np.float32)
        results = await retriever.search_by_text(query_vector, top_k=5)

        assert isinstance(results, list)
        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_search_by_image(self, retriever, sample_text_vector):
        """测试图像搜索文本"""
        # 索引文本
        retriever.index_text(sample_text_vector)

        # 使用随机查询向量
        query_vector = np.random.randn(768).astype(np.float32)
        results = await retriever.search_by_image(query_vector, top_k=5)

        assert isinstance(results, list)

    def test_cosine_similarity(self, retriever):
        """测试余弦相似度计算"""
        vec1 = np.array([1, 0, 0], dtype=np.float32)
        vec2 = np.array([1, 0, 0], dtype=np.float32)
        vec3 = np.array([0, 1, 0], dtype=np.float32)

        # 相同向量
        sim = retriever._cosine_similarity(vec1, vec2)
        assert abs(sim - 1.0) < 0.01

        # 正交向量
        sim = retriever._cosine_similarity(vec1, vec3)
        assert abs(sim) < 0.01

        # 空向量
        sim = retriever._cosine_similarity(None, vec1)
        assert sim == 0.0

    def test_get_stats(self, retriever, sample_image_vector, sample_text_vector):
        """测试统计信息"""
        retriever.index_image(sample_image_vector)
        retriever.index_text(sample_text_vector)

        stats = retriever.get_stats()
        assert stats["image_count"] == 1
        assert stats["text_count"] == 1


# ============================================================================
# 混合融合测试
# ============================================================================

class TestHybridFusion:
    """混合融合测试"""

    def test_linear_fusion(self):
        """测试线性融合"""
        text_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
        image_results = [("doc2", 0.8), ("doc4", 0.6)]

        fused = HybridFusion.linear_fusion(
            text_results, image_results,
            text_weight=0.6, image_weight=0.4
        )

        assert isinstance(fused, list)
        # doc2 在两个列表中都出现，应该有更高分数
        doc_ids = [doc_id for doc_id, _ in fused]
        assert "doc2" in doc_ids

    def test_reciprocal_rank_fusion(self):
        """测试RRF融合"""
        text_results = [("doc1", 0.9), ("doc2", 0.8)]
        image_results = [("doc2", 0.8), ("doc3", 0.7)]

        fused = HybridFusion.reciprocal_rank_fusion(
            text_results, image_results, k=60
        )

        assert isinstance(fused, list)
        # doc2 在两个列表中都出现，RRF分数应该更高
        dict(fused)
        # doc2 应该有最高分数
        assert fused[0][0] == "doc2"

    def test_score_normalization_fusion(self):
        """测试分数归一化融合"""
        text_results = [("doc1", 0.9), ("doc2", 0.3)]
        image_results = [("doc2", 0.8), ("doc3", 0.2)]

        fused = HybridFusion.score_normalization_fusion(
            text_results, image_results,
            text_weight=0.5, image_weight=0.5
        )

        assert isinstance(fused, list)
        # 所有分数应该在0-1之间
        for _, score in fused:
            assert 0 <= score <= 1

    def test_empty_results_fusion(self):
        """测试空结果融合"""
        # 空文本结果
        fused = HybridFusion.linear_fusion([], [("doc1", 0.8)])
        assert len(fused) == 1

        # 空图像结果
        fused = HybridFusion.linear_fusion([("doc1", 0.8)], [])
        assert len(fused) == 1

        # 都为空
        fused = HybridFusion.linear_fusion([], [])
        assert len(fused) == 0


# ============================================================================
# 多模态检索系统测试
# ============================================================================

class TestMultimodalRetrievalSystem:
    """多模态检索系统测试"""

    @pytest.fixture
    def system(self):
        """创建系统实例"""
        config = RetrievalConfig(
            mode=SearchMode.HYBRID,
            top_k=10
        )
        return MultimodalRetrievalSystem(config=config)

    def test_system_initialization(self, system):
        """测试系统初始化"""
        assert system.config is not None
        assert system.image_vectorizer is not None
        assert system.cross_modal_retriever is not None

    @pytest.mark.asyncio
    async def test_text_only_search(self, system):
        """测试纯文本检索"""
        config = RetrievalConfig(mode=SearchMode.TEXT_ONLY, top_k=5)
        result = await system.search("测试查询", config=config)

        assert result.mode == SearchMode.TEXT_ONLY
        assert result.query == "测试查询"
        assert isinstance(result, HybridSearchResult)

    @pytest.mark.asyncio
    async def test_hybrid_search(self, system):
        """测试混合检索"""
        config = RetrievalConfig(mode=SearchMode.HYBRID, top_k=10)
        result = await system.search("专利检索", config=config)

        assert result.mode == SearchMode.HYBRID
        assert result.fusion_strategy == FusionStrategy.RRF
        assert result.total_time > 0

    @pytest.mark.asyncio
    async def test_image_search(self, system):
        """测试图像检索"""
        query_image = b"fake_image_data"
        config = RetrievalConfig(mode=SearchMode.IMAGE_ONLY, top_k=5)

        result = await system.search(
            "图像查询",
            query_image=query_image,
            config=config
        )

        assert result.mode == SearchMode.IMAGE_ONLY

    @pytest.mark.asyncio
    async def test_index_images(self, system):
        """测试批量图像索引"""
        images = [
            {
                "image_id": "img_001",
                "image_data": b"image_data_1",
                "patent_number": "CN1111111A",
                "figure_number": "图1",
                "caption": "第一张图"
            },
            {
                "image_id": "img_002",
                "image_data": b"image_data_2",
                "patent_number": "CN2222222A",
                "figure_number": "图2",
                "caption": "第二张图"
            }
        ]

        count = await system.index_images(images)
        assert count == 2

        # 检查索引
        stats = system.get_stats()
        assert stats["image_count"] == 2

    @pytest.mark.asyncio
    async def test_find_similar_images(self, system):
        """测试相似图像查找"""
        # 先索引一些图像
        images = [
            {
                "image_id": "img_001",
                "image_data": b"test_image_data",
                "patent_number": "CN1234567A",
                "figure_number": "图1",
                "caption": "测试图像"
            }
        ]
        await system.index_images(images)

        # 查找相似图像
        query_image = b"query_image_data"
        similar = await system.find_similar_images(query_image, top_k=5)

        assert isinstance(similar, list)

    def test_get_stats(self, system):
        """测试统计信息"""
        stats = system.get_stats()

        assert "image_count" in stats
        assert "text_count" in stats
        assert "cache_size" in stats
        assert "config" in stats

    def test_get_relevance_level(self, system):
        """测试相关度级别判定"""
        assert system._get_relevance_level(0.9) == RelevanceLevel.HIGHLY_RELEVANT
        assert system._get_relevance_level(0.7) == RelevanceLevel.RELEVANT
        assert system._get_relevance_level(0.5) == RelevanceLevel.PARTIALLY_RELEVANT
        assert system._get_relevance_level(0.3) == RelevanceLevel.MARGINAL
        assert system._get_relevance_level(0.1) == RelevanceLevel.IRRELEVANT


# ============================================================================
# 便捷函数测试
# ============================================================================

class TestConvenienceFunctions:
    """便捷函数测试"""

    @pytest.mark.asyncio
    async def test_hybrid_search_function(self):
        """测试混合检索便捷函数"""
        result = await hybrid_search(
            query="测试查询",
            mode=SearchMode.TEXT_ONLY,
            top_k=5
        )

        assert isinstance(result, HybridSearchResult)
        assert result.query == "测试查询"
        assert result.mode == SearchMode.TEXT_ONLY

    @pytest.mark.asyncio
    async def test_multimodal_search_function(self):
        """测试多模态检索便捷函数"""
        query_image = b"test_image"
        result = await multimodal_search(
            query="测试查询",
            query_image=query_image,
            top_k=5
        )

        assert isinstance(result, HybridSearchResult)
        assert result.mode == SearchMode.MULTIMODAL

    def test_format_search_result(self):
        """测试格式化检索结果"""
        result = HybridSearchResult(
            query_id="test_001",
            query="测试查询",
            mode=SearchMode.HYBRID,
            text_results=[],
            image_results=[],
            fused_results=[],
            fusion_strategy=FusionStrategy.RRF,
            text_weight=0.6,
            image_weight=0.4,
            total_time=0.123
        )

        formatted = format_search_result(result)

        assert "多模态检索结果" in formatted
        assert "测试查询" in formatted
        assert "hybrid" in formatted
        assert "0.123 秒" in formatted


# ============================================================================
# 边界条件测试
# ============================================================================

class TestEdgeCases:
    """边界条件测试"""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """测试空查询"""
        system = MultimodalRetrievalSystem()
        result = await system.search("")

        assert result is not None
        assert result.query == ""

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """测试超长查询"""
        system = MultimodalRetrievalSystem()
        long_query = "测试" * 1000
        result = await system.search(long_query)

        assert result is not None

    @pytest.mark.asyncio
    async def test_special_characters_query(self):
        """测试特殊字符查询"""
        system = MultimodalRetrievalSystem()
        special_query = "测试@#$%^&*()查询"
        result = await system.search(special_query)

        assert result is not None

    def test_zero_vector(self):
        """测试零向量"""
        retriever = CrossModalRetriever()
        zero_vec = np.zeros(768, dtype=np.float32)
        other_vec = np.random.randn(768).astype(np.float32)

        sim = retriever._cosine_similarity(zero_vec, other_vec)
        assert sim == 0.0

    @pytest.mark.asyncio
    async def test_large_top_k(self):
        """测试大量结果请求"""
        system = MultimodalRetrievalSystem()
        config = RetrievalConfig(top_k=1000)
        result = await system.search("测试", config=config)

        assert result is not None


# ============================================================================
# 集成测试
# ============================================================================

class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流"""
        # 创建系统
        system = MultimodalRetrievalSystem()

        # 索引图像
        images = [
            {
                "image_id": f"img_{i:03d}",
                "image_data": f"image_data_{i}".encode(),
                "patent_number": f"CN{1000000 + i}A",
                "figure_number": f"图{i}",
                "caption": f"测试图像{i}"
            }
            for i in range(10)
        ]

        indexed = await system.index_images(images)
        assert indexed == 10

        # 执行检索
        result = await system.search("测试查询")
        assert result is not None

        # 获取统计
        stats = system.get_stats()
        assert stats["image_count"] == 10

    @pytest.mark.asyncio
    async def test_different_fusion_strategies(self):
        """测试不同融合策略"""
        system = MultimodalRetrievalSystem()

        strategies = [
            FusionStrategy.LINEAR,
            FusionStrategy.RRF,
            FusionStrategy.SCORE_NORM
        ]

        for strategy in strategies:
            config = RetrievalConfig(fusion_strategy=strategy)
            result = await system.search("测试", config=config)

            assert result.fusion_strategy == strategy


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
