#!/usr/bin/env python3
"""
测试统一Neo4j引擎

验证合并后的引擎功能完整性
"""

from unittest.mock import MagicMock, patch

import pytest
from core.kg_unified.engines.neo4j_engine import (
    GraphClient,
    GraphEdge,
    GraphNode,
    GraphType,
    JudgmentNodeType,
    NebulaGraphClient,
    Neo4jConfig,
    Neo4jEngine,
    Neo4jJudgmentClient,
    _import_neo4j,
    get_graph_client,
    get_neo4j_client,
    # 便捷函数
    get_neo4j_engine,
)

# =============================================================================
# 配置测试
# =============================================================================

class TestNeo4jConfig:
    """测试Neo4j配置"""

    def test_default_config(self):
        """测试默认配置"""
        config = Neo4jConfig()
        assert config.uri == "bolt://localhost:7687"
        assert config.username == "neo4j"
        assert config.database == "neo4j"
        assert config.max_pool_size == 50
        assert config.namespace == "default"

    def test_custom_config(self):
        """测试自定义配置"""
        config = Neo4jConfig(
            uri="bolt://custom:7687",
            username="custom_user",
            password="custom_pass",
            database="custom_db",
            namespace="custom_ns"
        )
        assert config.uri == "bolt://custom:7687"
        assert config.username == "custom_user"
        assert config.password == "custom_pass"
        assert config.database == "custom_db"
        assert config.namespace == "custom_ns"

    def test_invalid_database_name(self):
        """测试无效数据库名称"""
        config = Neo4jConfig(database="invalid-db-name")
        with pytest.raises(ValueError, match="Invalid database name"):
            Neo4jEngine(config)

    def test_invalid_namespace(self):
        """测试无效命名空间"""
        config = Neo4jConfig(namespace="invalid-ns-name")
        with pytest.raises(ValueError, match="Invalid namespace"):
            Neo4jEngine(config)


# =============================================================================
# 引擎初始化测试
# =============================================================================

class TestNeo4jEngineInit:
    """测试Neo4j引擎初始化"""

    @patch("core.kg_unified.engines.neo4j_engine._import_neo4j")
    def test_init_with_config(self, mock_import):
        """测试使用配置初始化"""
        mock_neo4j = MagicMock()
        mock_import.return_value = mock_neo4j

        config = Neo4jConfig(
            uri="bolt://test:7687",
            username="test_user",
            password="test_pass"
        )
        engine = Neo4jEngine(config)

        assert engine.config.uri == "bolt://test:7687"
        assert engine.config.username == "test_user"
        assert engine._connected is False

    @patch("core.kg_unified.engines.neo4j_engine._import_neo4j")
    def test_init_with_kwargs(self, mock_import):
        """测试使用kwargs初始化"""
        mock_neo4j = MagicMock()
        mock_import.return_value = mock_neo4j

        engine = Neo4jEngine(
            uri="bolt://kwargs:7687",
            username="kwargs_user"
        )

        assert engine.config.uri == "bolt://kwargs:7687"
        assert engine.config.username == "kwargs_user"


# =============================================================================
# 枚举类型测试
# =============================================================================

class TestGraphType:
    """测试图类型枚举"""

    def test_graph_type_values(self):
        """测试图类型值"""
        assert GraphType.LEGAL_RULES.value == "legal_rules"
        assert GraphType.PATENT_GUIDELINE.value == "patent_guideline"
        assert GraphType.PATENT_INVALIDATION.value == "patent_invalidation"
        assert GraphType.PATENT_REVIEW.value == "patent_review"
        assert GraphType.PATENT_JUDGMENT.value == "patent_judgment"
        assert GraphType.TRADEMARK.value == "trademark"
        assert GraphType.TECH_TERMS.value == "tech_terms"


class TestJudgmentNodeType:
    """测试判决节点类型枚举"""

    def test_judgment_node_type_values(self):
        """测试判决节点类型值"""
        assert JudgmentNodeType.LEGAL_ARTICLE.value == "LegalArticle"
        assert JudgmentNodeType.JUDGMENT_RULE.value == "JudgmentRule"
        assert JudgmentNodeType.TYPICAL_CASE.value == "TypicalCase"
        assert JudgmentNodeType.LEGAL_CONCEPT.value == "LegalConcept"
        assert JudgmentNodeType.DISPUTE_FOCUS.value == "DisputeFocus"


# =============================================================================
# 数据类测试
# =============================================================================

class TestGraphNode:
    """测试图节点数据类"""

    def test_graph_node_creation(self):
        """测试节点创建"""
        node = GraphNode(
            id="test_id",
            type="test_type",
            properties={"key": "value"},
            content="test content",
            embedding=[0.1, 0.2, 0.3],
            metadata={"meta": "data"}
        )

        assert node.id == "test_id"
        assert node.type == "test_type"
        assert node.properties == {"key": "value"}
        assert node.content == "test content"
        assert node.embedding == [0.1, 0.2, 0.3]
        assert node.metadata == {"meta": "data"}

    def test_graph_node_optional_fields(self):
        """测试节点可选字段"""
        node = GraphNode(
            id="test_id",
            type="test_type",
            properties={}
        )

        assert node.id == "test_id"
        assert node.content is None
        assert node.embedding is None
        assert node.metadata is None


class TestGraphEdge:
    """测试图边数据类"""

    def test_graph_edge_creation(self):
        """测试边创建"""
        edge = GraphEdge(
            from_node="node1",
            to_node="node2",
            relation_type="CONNECTS",
            properties={"weight": 1.0},
            weight=0.8,
            confidence=0.9
        )

        assert edge.from_node == "node1"
        assert edge.to_node == "node2"
        assert edge.relation_type == "CONNECTS"
        assert edge.properties == {"weight": 1.0}
        assert edge.weight == 0.8
        assert edge.confidence == 0.9

    def test_graph_edge_optional_fields(self):
        """测试边可选字段"""
        edge = GraphEdge(
            from_node="node1",
            to_node="node2",
            relation_type="CONNECTS",
            properties={}
        )

        assert edge.weight == 1.0  # 默认值
        assert edge.confidence == 1.0  # 默认值


# =============================================================================
# 兼容层测试
# =============================================================================

class TestCompatibilityLayers:
    """测试兼容层"""

    def test_graph_client_is_neo4j_engine(self):
        """测试GraphClient是Neo4jEngine的子类"""
        client = GraphClient()
        assert isinstance(client, Neo4jEngine)

    def test_graph_client_is_succeeded(self):
        """测试GraphClient兼容方法"""
        client = GraphClient()
        assert client.is_succeeded() is True

    def test_nebula_graph_client_is_neo4j_engine(self):
        """测试NebulaGraphClient是Neo4jEngine的子类"""
        client = NebulaGraphClient({})
        assert isinstance(client, Neo4jEngine)

    def test_nebula_graph_client_config_mapping(self):
        """测试NebulaGraphClient配置映射"""
        config = {
            "host": "192.168.1.1",
            "port": 9669,
            "user": "nebula_user",
            "password": "nebula_pass",
            "space_name": "test_space"
        }
        client = NebulaGraphClient(config)

        assert client.config.uri == "bolt://192.168.1.1:9669"
        assert client.config.username == "nebula_user"
        assert client.config.password == "nebula_pass"
        assert client.config.database == "test_space"
        assert client.config.namespace == "test_space"

    def test_neo4j_judgment_client_is_neo4j_engine(self):
        """测试Neo4jJudgmentClient是Neo4jEngine的子类"""
        client = Neo4jJudgmentClient({})
        assert isinstance(client, Neo4jEngine)


# =============================================================================
# 便捷函数测试
# =============================================================================

class TestConvenienceFunctions:
    """测试便捷函数"""

    @patch("core.kg_unified.engines.neo4j_engine._import_neo4j")
    def test_get_neo4j_engine(self, mock_import):
        """测试get_neo4j_engine函数"""
        mock_neo4j = MagicMock()
        mock_import.return_value = mock_neo4j

        engine = get_neo4j_engine(uri="bolt://test:7687")
        assert isinstance(engine, Neo4jEngine)
        assert engine.config.uri == "bolt://test:7687"

    @patch("core.kg_unified.engines.neo4j_engine._import_neo4j")
    def test_get_neo4j_client(self, mock_import):
        """测试get_neo4j_client函数"""
        mock_neo4j = MagicMock()
        mock_import.return_value = mock_neo4j

        client = get_neo4j_client(uri="bolt://test:7687")
        assert isinstance(client, Neo4jEngine)

    @patch("core.kg_unified.engines.neo4j_engine._import_neo4j")
    def test_get_graph_client(self, mock_import):
        """测试get_graph_client函数"""
        mock_neo4j = MagicMock()
        mock_import.return_value = mock_neo4j

        client = get_graph_client(uri="bolt://test:7687")
        assert isinstance(client, GraphClient)


# =============================================================================
# 延迟导入测试
# =============================================================================

class TestDelayedImport:
    """测试延迟导入机制"""

    @patch("core.kg_unified.engines.neo4j_engine.sys")
    def test_import_neo4j_avoids_circular_import(self, mock_sys):
        """测试延迟导入避免循环导入"""
        # 模拟sys.modules
        mock_sys.modules = {}

        # 导入neo4j模块
        neo4j_module = _import_neo4j()

        # 验证返回的是neo4j模块
        assert neo4j_module is not None


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
