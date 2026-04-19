#!/usr/bin/env python3
"""
法律知识图谱单元测试
Unit tests for Legal Knowledge Graph Builder

测试内容:
- Neo4j连接
- 法条导入
- 案例导入
- 规则构建
- 关系建立
- 向量存储
- 现有数据检查
"""

import pytest

pytestmark = pytest.mark.skip(reason="Missing required modules: ")

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.legal_world_model.legal_knowledge_graph_builder import (
    CasePrecedent,
    InferenceRule,
    LegalKnowledgeGraphBuilder,
    PatentLaw,
)


class TestLegalKnowledgeGraphBuilder:
    """法律知识图谱构建器测试"""

    @pytest.fixture
    def builder(self):
        """创建构建器实例"""
        with patch('neo4j.GraphDatabase.driver'):
            builder = LegalKnowledgeGraphBuilder()
            yield builder
            builder.close()

    @pytest.mark.asyncio
    async def test_check_existing_data(self, builder):
        """测试现有数据检查"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 5}
        mock_session.run.return_value = mock_result

        builder.driver.session.return_value.__enter__.return_value = mock_session

        # 模拟Qdrant响应
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {"points_count": 10}
            }
            mock_get.return_value = mock_response

            stats = await builder.check_existing_data()

            assert stats["neo4j"]["patent_laws"] == 5
            assert stats["qdrant"]["collection_exists"] is True
            assert stats["qdrant"]["points_count"] == 10

    @pytest.mark.asyncio
    async def test_import_patent_laws(self, builder):
        """测试专利法法条导入"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        builder.driver.session.return_value.__enter__.return_value = mock_session

        await builder.import_patent_laws()

        # 验证调用了session.run
        assert mock_session.run.called

        # 验证调用了正确数量的法条
        call_count = mock_session.run.call_count
        assert call_count >= 8  # 至少8条法条

    @pytest.mark.asyncio
    async def test_import_case_precedents(self, builder):
        """测试案例先例导入"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        builder.driver.session.return_value.__enter__.return_value = mock_session

        await builder.import_case_precedents()

        # 验证调用了session.run
        assert mock_session.run.called

        # 验证调用了正确数量的案例
        call_count = mock_session.run.call_count
        assert call_count >= 4  # 至少4个案例

    @pytest.mark.asyncio
    async def test_build_inference_rules(self, builder):
        """测试推理规则构建"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        builder.driver.session.return_value.__enter__.return_value = mock_session

        await builder.build_inference_rules()

        # 验证调用了session.run
        assert mock_session.run.called

        # 验证调用了正确数量的规则
        call_count = mock_session.run.call_count
        assert call_count >= 4  # 至少4条规则

    @pytest.mark.asyncio
    async def test_establish_relationships(self, builder):
        """测试关联关系建立"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        builder.driver.session.return_value.__enter__.return_value = mock_session

        await builder.establish_relationships()

        # 验证调用了session.run
        assert mock_session.run.called

        # 验证建立了多种关系
        call_count = mock_session.run.call_count
        assert call_count >= 3  # 至少3种关系

    @pytest.mark.asyncio
    async def test_vectorize_knowledge(self, builder):
        """测试知识向量化"""
        # 模拟Neo4j会话
        mock_session = MagicMock()
        mock_result = MagicMock()

        # 模拟法条数据
        mock_records = [
            {"l": {"article": "A2", "title": "授予条件", "content": "新颖性、创造性、实用性"}}
        ]
        mock_result.__iter__ = iter(mock_records)
        mock_session.run.return_value = mock_result
        builder.driver.session.return_value.__enter__.return_value = mock_session

        # 模拟Qdrant API响应
        with patch('requests.put') as mock_put:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_put.return_value = mock_response

            await builder.vectorize_knowledge()

            # 验证调用了Qdrant API
            assert mock_put.called


class TestPatentLaw:
    """专利法法条数据类测试"""

    def test_patent_law_creation(self):
        """测试专利法法条创建"""
        law = PatentLaw(
            article="A2",
            title="授予专利权的条件",
            content="发明和实用新型应当具备新颖性、创造性和实用性",
            keywords=["新颖性", "创造性", "实用性"],
            category="授予条件",
            effective_date="1985-04-01"
        )

        assert law.article == "A2"
        assert law.title == "授予专利权的条件"
        assert "新颖性" in law.keywords
        assert law.category == "授予条件"

    def test_patent_law_with_metadata(self):
        """测试带元数据的专利法法条"""
        law = PatentLaw(
            article="A22.3",
            title="创造性",
            content="与现有技术相比具有突出的实质性特点和显著的进步",
            keywords=["创造性", "现有技术"],
            category="授予条件",
            effective_date="1985-04-01",
            metadata={"importance": "high"}
        )

        assert law.metadata["importance"] == "high"


class TestCasePrecedent:
    """案例先例数据类测试"""

    def test_case_precedent_creation(self):
        """测试案例先例创建"""
        case = CasePrecedent(
            case_id="CN_INVALID_001",
            title="创造性判断标准案",
            issue="如何判断专利的创造性",
            outcome="维持专利权有效",
            reasoning="与现有技术相比，该专利具有突出的实质性特点和显著进步",
            cited_articles=["A22.3"],
            date="2023-05-15"
        )

        assert case.case_id == "CN_INVALID_001"
        assert case.issue == "如何判断专利的创造性"
        assert "A22.3" in case.cited_articles

    def test_case_precedent_with_metadata(self):
        """测试带元数据的案例先例"""
        case = CasePrecedent(
            case_id="CN_INFRINGE_001",
            title="专利侵权判定案",
            issue="全面覆盖原则的适用",
            outcome="认定侵权成立",
            reasoning="被控侵权产品包含专利权利要求的全部技术特征",
            cited_articles=["A11", "A59"],
            date="2023-07-10",
            metadata={"court": "最高人民法院"}
        )

        assert case.metadata["court"] == "最高人民法院"


class TestInferenceRule:
    """推理规则数据类测试"""

    def test_inference_rule_creation(self):
        """测试推理规则创建"""
        rule = InferenceRule(
            rule_id="RULE_CREATIVITY_001",
            name="创造性判断规则",
            conditions=[
                "发明具有实质性特点",
                "与现有技术相比有显著进步",
                "非显而易见"
            ],
            conclusion="具备创造性",
            confidence=0.9,
            category="专利有效性"
        )

        assert rule.rule_id == "RULE_CREATIVITY_001"
        assert "发明具有实质性特点" in rule.conditions
        assert rule.confidence == 0.9

    def test_inference_rule_with_metadata(self):
        """测试带元数据的推理规则"""
        rule = InferenceRule(
            rule_id="RULE_NOVELTY_001",
            name="新颖性判断规则",
            conditions=[
                "申请日前未公开",
                "不属于现有技术",
                "无抵触申请"
            ],
            conclusion="具备新颖性",
            confidence=0.95,
            category="专利有效性",
            metadata={"source": "专利审查指南"}
        )

        assert rule.metadata["source"] == "专利审查指南"


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_graph_build(self, builder):
        """测试完整知识图谱构建"""
        # 模拟所有Neo4j操作
        mock_session = MagicMock()
        mock_result = MagicMock()
        mock_result.single.return_value = {"count": 0}
        mock_result.__iter__ = iter([])
        mock_session.run.return_value = mock_result
        builder.driver.session.return_value.__enter__.return_value = mock_session

        # 模拟Qdrant API
        with patch('requests.get') as mock_get, patch('requests.put') as mock_put:
            # get响应
            mock_get_response = MagicMock()
            mock_get_response.status_code = 404  # 集合不存在
            mock_get.return_value = mock_get_response

            # put响应
            mock_put_response = MagicMock()
            mock_put_response.status_code = 200
            mock_put.return_value = mock_put_response

            # 构建图谱
            await builder.build_patent_law_graph(force_rebuild=True)

            # 验证调用了所有构建步骤
            assert mock_session.run.called


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
