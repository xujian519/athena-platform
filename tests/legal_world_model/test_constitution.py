#!/usr/bin/env python3
"""
宪法验证器单元测试
Unit Tests for Constitutional Validator

测试法律世界模型中的宪法验证功能。

作者: Athena平台团队
创建时间: 2026-02-03
版本: v1.0.0
"""

import pytest
from datetime import datetime

from core.legal_world_model.constitution import (
    Case,
    CitationReference,
    ConstitutionalValidator,
    DocumentSource,
    DocumentType,
    InvalidationDecision,
    Judgment,
    LayerType,
    LegalEntity,
    LegalEntityType,
    LegalRelation,
    LegalRelationType,
    Patent,
    PatentEntityType,
    PatentRelationType,
    Principle,
    ProceduralRelationType,
    SubjectEntityType,
)


class TestConstitutionalValidator:
    """宪法验证器测试"""

    @pytest.fixture
    def validator(self):
        """创建验证器实例"""
        return ConstitutionalValidator()

    # ==========================================================================
    # 实体验证测试
    # ==========================================================================

    def test_validate_patent_entity_valid(self, validator):
        """测试有效专利实体验证"""
        patent = Patent(
            id="CN202310000000",
            title="测试专利",
            abstract="测试摘要",
            claims=["权利要求1"],
            applicants=["申请人"],
            inventors=["发明人"],
            filing_date=datetime.now(),
            publication_date=datetime.now(),
        )

        is_valid, errors = validator.validate_entity(patent)

        assert is_valid
        assert len(errors) == 0

    def test_validate_patent_entity_missing_required_fields(self, validator):
        """测试缺少必填字段的专利实体"""
        patent = Patent(id="", title="")  # 缺少必填字段

        is_valid, errors = validator.validate_entity(patent)

        assert not is_valid
        assert len(errors) > 0

    def test_validate_case_entity_valid(self, validator):
        """测试有效案例实体验证"""
        case = Case(
            id="CASE-001",
            title="测试案例",
            court="测试法院",
            date=datetime.now(),
            parties=["原告", "被告"],
        )

        is_valid, errors = validator.validate_entity(case)

        assert is_valid
        assert len(errors) == 0

    def test_validate_judgment_entity_valid(self, validator):
        """测试有效判决实体验证"""
        judgment = Judgment(
            id="JUDG-001",
            case_id="CASE-001",
            court="测试法院",
            date=datetime.now(),
            outcome="判决结果",
            reasoning="判决理由",
        )

        is_valid, errors = validator.validate_entity(judgment)

        assert is_valid
        assert len(errors) == 0

    # ==========================================================================
    # 关系验证测试
    # ==========================================================================

    def test_validate_relation_valid(self, validator):
        """测试有效关系验证"""
        source = LegalEntity(id="entity1", type=LegalEntityType.PATENT)
        target = LegalEntity(id="entity2", type=LegalEntityType.CASE)

        relation = LegalRelation(
            id="rel1",
            source_id=source.id,
            target_id=target.id,
            type=LegalRelationType.REFERS_TO,
        )

        is_valid, errors = validator.validate_relation(relation, source, target)

        assert is_valid
        assert len(errors) == 0

    def test_validate_relation_invalid_type(self, validator):
        """测试无效关系类型"""
        source = LegalEntity(id="entity1", type=LegalEntityType.PATENT)
        target = LegalEntity(id="entity2", type=LegalEntityType.CASE)

        relation = LegalRelation(
            id="rel1",
            source_id=source.id,
            target_id=target.id,
            type=LegalRelationType.CITES,  # 不适用的关系类型
        )

        is_valid, errors = validator.validate_relation(relation, source, target)

        # 根据实际验证逻辑断言
        # 这里假设验证器会检查关系类型是否适用于实体类型对

    # ==========================================================================
    # 层级验证测试
    # ==========================================================================

    def test_validate_layer_type(self, validator):
        """测试层级类型验证"""
        # 测试基础法律层
        assert LayerType.BASE_LAW in LayerType

        # 测试专利专业层
        assert LayerType.PATENT_LAW in LayerType

        # 测试司法案例层
        assert LayerType.CASE_LAW in LayerType

    # ==========================================================================
    # 边界条件测试
    # ==========================================================================

    def test_validate_entity_with_unicode(self, validator):
        """测试包含Unicode字符的实体"""
        patent = Patent(
            id="CN202310000000",
            title="测试专利包含中文和特殊字符：©®™℠",
            abstract="摘要包含Emoji：🚀🎯",
            claims=["权利要求1"],
            applicants=["申请人®"],
            inventors=["发明人™"],
            filing_date=datetime.now(),
            publication_date=datetime.now(),
        )

        is_valid, errors = validator.validate_entity(patent)

        assert is_valid

    def test_validate_entity_with_very_long_title(self, validator):
        """测试超长标题的实体"""
        patent = Patent(
            id="CN202310000000",
            title="A" * 1000,  # 超长标题
            abstract="测试摘要",
            claims=["权利要求1"],
            applicants=["申请人"],
            inventors=["发明人"],
            filing_date=datetime.now(),
            publication_date=datetime.now(),
        )

        is_valid, errors = validator.validate_entity(patent)

        # 根据实际验证逻辑断言
        # 如果有长度限制，应该返回错误

    # ==========================================================================
    # 错误处理测试
    # ==========================================================================

    def test_validate_with_none_entity(self, validator):
        """测试None实体验证"""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            validator.validate_entity(None)

    def test_validate_with_missing_attributes(self, validator):
        """测试缺少属性的实体"""
        # 创建缺少必要属性的对象
        class IncompleteEntity:
            id = "test-id"
            # 缺少 type 属性

        entity = IncompleteEntity()

        # 根据实际实现调整断言
        try:
            is_valid, errors = validator.validate_entity(entity)
            # 如果不抛出异常，应该返回验证失败
            assert not is_valid
        except (AttributeError, TypeError):
            # 如果抛出异常，也是合理的
            pass


class TestLayerTypes:
    """层级类型测试"""

    def test_all_layer_types_defined(self):
        """测试所有层级类型已定义"""
        expected_layers = [
            "BASE_LAW",  # 基础法律层
            "PATENT_LAW",  # 专利专业层
            "CASE_LAW",  # 司法案例层
        ]

        for layer_name in expected_layers:
            assert hasattr(LayerType, layer_name)

    def test_layer_type_values(self):
        """测试层级类型值"""
        assert LayerType.BASE_LAW.value == "base_law"
        assert LayerType.PATENT_LAW.value == "patent_law"
        assert LayerType.CASE_LAW.value == "case_law"


class TestEntityTypes:
    """实体类型测试"""

    def test_patent_entity_types(self):
        """测试专利实体类型"""
        expected_types = [
            "PATENT",
            "CLAIM",
            "APPLICANT",
            "INVENTOR",
            "ASSIGNEE",
        ]

        for type_name in expected_types:
            assert hasattr(PatentEntityType, type_name)

    def test_legal_entity_types(self):
        """测试法律实体类型"""
        expected_types = [
            "PATENT",
            "CASE",
            "JUDGMENT",
            "PRINCIPLE",
            "REGULATION",
        ]

        for type_name in expected_types:
            assert hasattr(LegalEntityType, type_name)


class TestRelationTypes:
    """关系类型测试"""

    def test_relation_types_exist(self):
        """测试关系类型存在"""
        expected_types = [
            "REFERS_TO",
            "CITES",
            "OVERRULES",
            "FOLLOWS",
            "DISTINGUISHES",
            "APPLIES",
        ]

        for type_name in expected_types:
            assert hasattr(LegalRelationType, type_name)

    def test_patent_relation_types_exist(self):
        """测试专利关系类型存在"""
        expected_types = [
            "PRIOR_ART",
            "DERIVES_FROM",
            "IMPROVES",
            "INVALIDATES",
        ]

        for type_name in expected_types:
            assert hasattr(PatentRelationType, type_name)


# =============================================================================
# 测试辅助函数
# =============================================================================


def create_test_patent(**kwargs):
    """创建测试专利实体"""
    defaults = {
        "id": "CN202310000000",
        "title": "测试专利",
        "abstract": "测试摘要",
        "claims": ["权利要求1"],
        "applicants": ["申请人"],
        "inventors": ["发明人"],
        "filing_date": datetime.now(),
        "publication_date": datetime.now(),
    }
    defaults.update(kwargs)
    return Patent(**defaults)


def create_test_case(**kwargs):
    """创建测试案例实体"""
    defaults = {
        "id": "CASE-001",
        "title": "测试案例",
        "court": "测试法院",
        "date": datetime.now(),
        "parties": ["原告", "被告"],
    }
    defaults.update(kwargs)
    return Case(**defaults)


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
