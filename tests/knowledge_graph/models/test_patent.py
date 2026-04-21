#!/usr/bin/env python3
"""
测试统一专利知识图谱模型

验证合并后的模型功能完整性
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from core.kg_unified.models.patent import (
    # 枚举类型
    NodeType,
    RelationType,
    QueryType,
    # 数据类
    TechnicalTriple,
    FeatureRelation,
    DocumentAnalysis,
    KnowledgeNode,
    KnowledgeRelation,
    SearchResult,
    HybridSearchConfig,
    # 后端
    MemoryGraphBackend,
    # 核心模型
    UnifiedPatentKnowledgeGraph,
    # 兼容层
    PatentKnowledgeGraph,
    EnhancedPatentKnowledgeGraph,
)


# =============================================================================
# 枚举类型测试
# =============================================================================

class TestNodeType:
    """测试节点类型枚举"""

    def test_node_type_values(self):
        """测试节点类型值"""
        assert NodeType.PATENT.value == "patent"
        assert NodeType.TECHNOLOGY.value == "technology"
        assert NodeType.PROBLEM.value == "problem"
        assert NodeType.FEATURE.value == "feature"
        assert NodeType.EFFECT.value == "effect"
        assert NodeType.COMPANY.value == "company"
        assert NodeType.INVENTOR.value == "inventor"
        assert NodeType.LEGAL_CASE.value == "legal_case"
        assert NodeType.ARTICLE.value == "article"
        assert NodeType.CONCEPT.value == "concept"
        assert NodeType.DOCUMENT.value == "document"

    def test_node_type_iteration(self):
        """测试节点类型迭代"""
        types = list(NodeType)
        assert len(types) >= 10  # 至少10种类型


class TestRelationType:
    """测试关系类型枚举"""

    def test_relation_type_values(self):
        """测试关系类型值"""
        assert RelationType.SOLVES.value == "solves"
        assert RelationType.ACHIEVES.value == "achieves"
        assert RelationType.SIMILAR_TO.value == "similar_to"
        assert RelationType.IMPROVES_UPON.value == "improves_upon"
        assert RelationType.CITES.value == "cites"


# =============================================================================
# 数据类测试
# =============================================================================

class TestTechnicalTriple:
    """测试技术三元组数据类"""

    def test_technical_triple_creation(self):
        """测试三元组创建"""
        triple = TechnicalTriple(
            problem="如何提高效率",
            features=["使用AI", "优化算法"],
            effect="效率提升50%",
            source_claim=1
        )

        assert triple.problem == "如何提高效率"
        assert triple.features == ["使用AI", "优化算法"]
        assert triple.effect == "效率提升50%"
        assert triple.source_claim == 1

    def test_technical_triple_str(self):
        """测试三元组字符串表示"""
        triple = TechnicalTriple(
            problem="问题",
            features=["特征1", "特征2"],
            effect="效果"
        )

        str_repr = str(triple)
        assert "问题" in str_repr
        assert "特征1" in str_repr
        assert "效果" in str_repr


class TestFeatureRelation:
    """测试特征关系数据类"""

    def test_feature_relation_creation(self):
        """测试特征关系创建"""
        relation = FeatureRelation(
            source_feature="特征A",
            target_feature="特征B",
            relation_type=RelationType.DEPENDS_ON,
            strength=0.8,
            description="A依赖B"
        )

        assert relation.source_feature == "特征A"
        assert relation.target_feature == "特征B"
        assert relation.relation_type == RelationType.DEPENDS_ON
        assert relation.strength == 0.8
        assert relation.description == "A依赖B"


class TestDocumentAnalysis:
    """测试文档分析数据类"""

    def test_document_analysis_creation(self):
        """测试文档分析创建"""
        triples = [
            TechnicalTriple(
                problem="问题1",
                features=["特征1"],
                effect="效果1"
            )
        ]

        analysis = DocumentAnalysis(
            document_id="doc_001",
            document_type="patent",
            document_name="测试文档",
            triples=triples,
            ipc_classifications=["G06F"]
        )

        assert analysis.document_id == "doc_001"
        assert analysis.document_name == "测试文档"
        assert len(analysis.triples) == 1

    def test_document_analysis_get_features(self):
        """测试获取所有特征"""
        triples = [
            TechnicalTriple(
                problem="问题1",
                features=["特征1", "特征2"],
                effect="效果1"
            ),
            TechnicalTriple(
                problem="问题2",
                features=["特征2", "特征3"],
                effect="效果2"
            )
        ]

        analysis = DocumentAnalysis(
            document_id="doc_001",
            document_type="patent",
            document_name="测试文档",
            triples=triples
        )

        features = analysis.get_all_features()
        assert features == {"特征1", "特征2", "特征3"}

    def test_document_analysis_get_problems(self):
        """测试获取所有问题"""
        triples = [
            TechnicalTriple(
                problem="问题1",
                features=["特征1"],
                effect="效果1"
            ),
            TechnicalTriple(
                problem="问题2",
                features=["特征2"],
                effect="效果2"
            )
        ]

        analysis = DocumentAnalysis(
            document_id="doc_001",
            document_type="patent",
            document_name="测试文档",
            triples=triples
        )

        problems = analysis.get_all_problems()
        assert problems == {"问题1", "问题2"}

    def test_document_analysis_get_effects(self):
        """测试获取所有效果"""
        triples = [
            TechnicalTriple(
                problem="问题1",
                features=["特征1"],
                effect="效果1"
            ),
            TechnicalTriple(
                problem="问题2",
                features=["特征2"],
                effect="效果2"
            )
        ]

        analysis = DocumentAnalysis(
            document_id="doc_001",
            document_type="patent",
            document_name="测试文档",
            triples=triples
        )

        effects = analysis.get_all_effects()
        assert effects == {"效果1", "效果2"}


class TestKnowledgeNode:
    """测试知识节点数据类"""

    def test_knowledge_node_creation(self):
        """测试节点创建"""
        node = KnowledgeNode(
            node_id="node_001",
            node_type=NodeType.PATENT,
            title="测试专利",
            description="这是一个测试专利",
            properties={"application_date": "2023-01-01"}
        )

        assert node.node_id == "node_001"
        assert node.node_type == NodeType.PATENT
        assert node.title == "测试专利"
        assert node.description == "这是一个测试专利"
        assert node.properties == {"application_date": "2023-01-01"}

    def test_knowledge_node_to_dict(self):
        """测试节点转字典"""
        node = KnowledgeNode(
            node_id="node_001",
            node_type=NodeType.PATENT,
            title="测试专利",
            description="测试",
            properties={}
        )

        node_dict = node.to_dict()
        assert node_dict["node_id"] == "node_001"
        assert node_dict["node_type"] == "patent"
        assert node_dict["title"] == "测试专利"
        assert "created_at" in node_dict
        assert "updated_at" in node_dict


class TestKnowledgeRelation:
    """测试知识关系数据类"""

    def test_knowledge_relation_creation(self):
        """测试关系创建"""
        relation = KnowledgeRelation(
            relation_id="rel_001",
            source_id="node_001",
            target_id="node_002",
            relation_type=RelationType.CITES,
            weight=0.9,
            properties={"date": "2023-01-01"}
        )

        assert relation.relation_id == "rel_001"
        assert relation.source_id == "node_001"
        assert relation.target_id == "node_002"
        assert relation.relation_type == RelationType.CITES
        assert relation.weight == 0.9
        assert relation.properties == {"date": "2023-01-01"}

    def test_knowledge_relation_to_dict(self):
        """测试关系转字典"""
        relation = KnowledgeRelation(
            relation_id="rel_001",
            source_id="node_001",
            target_id="node_002",
            relation_type=RelationType.CITES,
            weight=0.9,
            properties={}
        )

        relation_dict = relation.to_dict()
        assert relation_dict["relation_id"] == "rel_001"
        assert relation_dict["relation_type"] == "cites"
        assert relation_dict["weight"] == 0.9
        assert "created_at" in relation_dict


class TestSearchResult:
    """测试搜索结果数据类"""

    def test_search_result_creation(self):
        """测试搜索结果创建"""
        result = SearchResult(
            node_id="node_001",
            title="测试专利",
            content="测试内容",
            score=0.95,
            node_type="patent"
        )

        assert result.node_id == "node_001"
        assert result.title == "测试专利"
        assert result.content == "测试内容"
        assert result.score == 0.95
        assert result.node_type == "patent"


class TestHybridSearchConfig:
    """测试混合搜索配置数据类"""

    def test_hybrid_search_config_defaults(self):
        """测试混合搜索配置默认值"""
        config = HybridSearchConfig()

        assert config.vector_weight == 0.5
        assert config.graph_weight == 0.3
        assert config.text_weight == 0.2
        assert config.max_hops == 2
        assert config.top_k == 50
        assert config.re_rank_top_k == 10


# =============================================================================
# 内存后端测试
# =============================================================================

class TestMemoryGraphBackend:
    """测试内存图后端"""

    @pytest.mark.asyncio
    async def test_memory_backend_initialize(self):
        """测试内存后端初始化"""
        backend = MemoryGraphBackend()
        await backend.initialize()
        assert backend.graph is not None  # 如果NetworkX可用

    @pytest.mark.asyncio
    async def test_memory_backend_add_node(self):
        """测试添加节点"""
        backend = MemoryGraphBackend()
        await backend.initialize()

        node = KnowledgeNode(
            node_id="test_001",
            node_type=NodeType.PATENT,
            title="测试",
            description="测试",
            properties={}
        )

        result = await backend.add_node(node)
        assert result is True
        assert "test_001" in backend._nodes

    @pytest.mark.asyncio
    async def test_memory_backend_search(self):
        """测试搜索"""
        backend = MemoryGraphBackend()
        await backend.initialize()

        # 添加测试节点
        node = KnowledgeNode(
            node_id="test_001",
            node_type=NodeType.PATENT,
            title="AI专利",
            description="人工智能专利",
            properties={}
        )
        await backend.add_node(node)

        # 搜索
        results = await backend.search_nodes("AI", limit=10)
        assert len(results) > 0
        assert results[0].node_id == "test_001"


# =============================================================================
# 兼容层测试
# =============================================================================

class TestCompatibilityLayers:
    """测试兼容层"""

    def test_patent_knowledge_graph_is_unified(self):
        """测试PatentKnowledgeGraph是统一模型的子类"""
        assert issubclass(PatentKnowledgeGraph, UnifiedPatentKnowledgeGraph)

    def test_enhanced_patent_knowledge_graph_is_unified(self):
        """测试EnhancedPatentKnowledgeGraph是统一模型的子类"""
        assert issubclass(EnhancedPatentKnowledgeGraph, UnifiedPatentKnowledgeGraph)


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
