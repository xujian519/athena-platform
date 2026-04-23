#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利知识图谱模式定义
Patent Knowledge Graph Schema Definition

基于法律法规、审查指南、复审无效决定文书构建的完整知识图谱架构
Based on laws, regulations, examination guidelines, reexamination and invalidation decisions

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ============================================================================
# 实体类型定义 (Entity Types)
# ============================================================================

class EntityType(Enum):
    """知识图谱实体类型"""

    # === 法律法规层 ===
    LAW = 'law'                           # 法律 (如专利法)
    REGULATION = 'regulation'             # 法规 (如实施细则)
    JUDICIAL_INTERPRETATION = 'judicial_interpretation'  # 司法解释
    EXAMINATION_GUIDELINE = 'examination_guideline'     # 审查指南

    # === 条款层 ===
    LEGAL_ARTICLE = 'legal_article'       # 法条
    REGULATION_CLAUSE = 'regulation_clause' # 规章条款
    GUIDELINE_SECTION = 'guideline_section' # 指南章节

    # === 案例层 ===
    INVALIDATION_DECISION = 'invalidation_decision'  # 无效宣告决定
    REEXAMINATION_DECISION = 'reexamination_decision' # 复审决定
    COURT_CASE = 'court_case'             # 法院案例

    # === 技术概念层 ===
    TECHNICAL_CONCEPT = 'technical_concept'  # 技术概念
    PATENT_TYPE = 'patent_type'            # 专利类型
    INVENTION_FIELD = 'invention_field'    # 技术领域
    LEGAL_CONCEPT = 'legal_concept'        # 法律概念

    # === 当事人层 ===
    APPLICANT = 'applicant'               # 申请人
    PATENT_HOLDER = 'patent_holder'        # 专利权人
    PATENT_OFFICE = 'patent_office'        # 专利局
    COURT = 'court'                        # 法院
    EXAMINER = 'examiner'                  # 审查员

    # === 专利层 ===
    PATENT = 'patent'                      # 专利
    PATENT_APPLICATION = 'patent_application' # 专利申请
    CLAIM = 'claim'                        # 权利要求

    # === 程序层 ===
    LEGAL_PROCEDURE = 'legal_procedure'    # 法律程序
    PROCEEDING_STEP = 'proceeding_step'    # 程序步骤
    DEADLINE = 'deadline'                  # 期限
    REQUIREMENT = 'requirement'            # 要求

# ============================================================================
# 关系类型定义 (Relationship Types)
# ============================================================================

class RelationType(Enum):
    """知识图谱关系类型"""

    # === 层次关系 ===
    CONTAINS = 'contains'                  # 包含关系
    PART_OF = 'part_of'                   # 部分关系
    DIVIDED_INTO = 'divided_into'          # 划分关系

    # === 引用关系 ===
    CITES = 'cites'                        # 引用关系
    REFERENCES = 'references'              # 参考关系
    BASED_ON = 'based_on'                  # 基于关系
    ACCORDING_TO = 'according_to'          # 依据关系

    # === 适用关系 ===
    APPLIES_TO = 'applies_to'              # 适用于
    GOVERNS = 'governs'                    # 管辖
    REGULATES = 'regulates'                # 规范

    # === 案例关系 ===
    INTERPRETS = 'interprets'              # 解释
    ILLUSTRATES = 'illustrates'            # 说明
    PRECEDES = 'precedes'                  # 先例
    CONTRADICTS = 'contradicts'           # 矛盾

    # === 技术关系 ===
    RELATES_TO = 'relates_to'              # 关联
    CLASSIFIED_AS = 'classified_as'        # 分类为
    IMPLEMENTS = 'implements'              # 实现
    IMPROVES_UPON = 'improves_upon'        # 改进

    # === 法律关系 ===
    VIOLATES = 'violates'                  # 违反
    COMPLIES_WITH = 'complies_with'        # 符合
    EXEMPTS_FROM = 'exempts_from'          # 豁免

    # === 程序关系 ===
    FOLLOWS = 'follows'                    # 遵循
    REQUIRES = 'requires'                  # 要求
    RESULTS_IN = 'results_in'              # 导致
    TRIGGERS = 'triggers'                  # 触发

    # === 时间关系 ===
    BEFORE = 'before'                      # 之前
    AFTER = 'after'                        # 之后
    SIMULTANEOUS_WITH = 'simultaneous_with' # 同时

    # === 当事人关系 ===
    FILES = 'files'                        # 提交
    OWNS = 'owns'                          # 拥有
    CHALLENGES = 'challenges'              # 挑战
    DEFENDS = 'defends'                    # 辩护

    # === 属性关系 ===
    HAS_PROPERTY = 'has_property'          # 具有...属性
    DEFINES = 'defines'                    # 定义
    SPECIFIES = 'specifies'                # 明确

# ============================================================================
# 实体数据结构定义
# ============================================================================

@dataclass
class KnowledgeEntity:
    """知识图谱实体基类"""
    id: str                               # 唯一标识符
    type: EntityType                      # 实体类型
    name: str                             # 实体名称
    description: str | None = None     # 描述
    properties: Dict[str, Any] = None     # 属性字典
    source: str | None = None          # 来源文档
    confidence: float = 1.0              # 置信度
    created_at: datetime = None          # 创建时间
    updated_at: datetime = None          # 更新时间

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass
class LawEntity(KnowledgeEntity):
    """法律实体"""
    law_type: str | None = None        # 法律类型
    promulgation_date: datetime | None = None  # 颁布日期
    effective_date: datetime | None = None      # 生效日期
    issuing_authority: str | None = None       # 发布机关

    def __post_init__(self):
        super().__post_init__()
        if self.type != EntityType.LAW:
            self.type = EntityType.LAW

@dataclass
class LegalArticleEntity(KnowledgeEntity):
    """法条实体"""
    article_number: str | None = None  # 条款编号
    content: str | None = None         # 条款内容
    chapter: str | None = None         # 章节
    section: str | None = None         # 节

    def __post_init__(self):
        super().__post_init__()
        if self.type != EntityType.LEGAL_ARTICLE:
            self.type = EntityType.LEGAL_ARTICLE

@dataclass
class CaseEntity(KnowledgeEntity):
    """案例实体"""
    case_number: str | None = None     # 案件编号
    decision_date: datetime | None = None  # 决定日期
    case_type: str | None = None       # 案件类型
    parties: Optional[List[str] = None             # 当事人
    outcome: str | None = None         # 判决结果
    key_points: Optional[List[str] = None          # 关键要点

    def __post_init__(self):
        super().__post_init__()
        if self.parties is None:
            self.parties = []
        if self.key_points is None:
            self.key_points = []
        if self.type not in [EntityType.INVALIDATION_DECISION,
                           EntityType.REEXAMINATION_DECISION,
                           EntityType.COURT_CASE]:
            # 根据文件名自动判断案例类型
            if self.name and '无效' in self.name:
                self.type = EntityType.INVALIDATION_DECISION
            elif self.name and '复审' in self.name:
                self.type = EntityType.REEXAMINATION_DECISION
            else:
                self.type = EntityType.COURT_CASE

@dataclass
class TechnicalConceptEntity(KnowledgeEntity):
    """技术概念实体"""
    concept_category: str | None = None  # 概念类别
    technical_field: str | None = None   # 技术领域
    definition: str | None = None        # 定义
    related_patents: Optional[List[str] = None       # 相关专利

    def __post_init__(self):
        super().__post_init__()
        if self.related_patents is None:
            self.related_patents = []
        if self.type != EntityType.TECHNICAL_CONCEPT:
            self.type = EntityType.TECHNICAL_CONCEPT

# ============================================================================
# 关系数据结构定义
# ============================================================================

@dataclass
class KnowledgeRelation:
    """知识图谱关系基类"""
    id: str                               # 关系唯一标识
    source: str                           # 源实体ID
    target: str                           # 目标实体ID
    type: RelationType                    # 关系类型
    properties: Dict[str, Any] = None     # 关系属性
    confidence: float = 1.0              # 置信度
    evidence: str | None = None        # 支撑证据
    source_document: str | None = None # 来源文档
    created_at: datetime = None          # 创建时间

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class LegalRelation(KnowledgeRelation):
    """法律关系"""
    legal_basis: str | None = None     # 法律依据
    jurisdiction: str | None = None    # 管辖范围
    scope: str | None = None           # 适用范围

    def __post_init__(self):
        super().__post_init__()

@dataclass
class InterpretationRelation(KnowledgeRelation):
    """解释关系"""
    interpretation_method: str | None = None  # 解释方法
    context: str | None = None         # 解释上下文
    alternative_meanings: Optional[List[str] = None      # 其他含义

    def __post_init__(self):
        super().__post_init__()
        if self.alternative_meanings is None:
            self.alternative_meanings = []

# ============================================================================
# 知识图谱模式定义
# ============================================================================

class PatentKnowledgeGraphSchema:
    """专利知识图谱模式定义"""

    def __init__(self):
        self.entity_types = EntityType
        self.relation_types = RelationType
        self.schema_version = '1.0.0'
        self.create_date = datetime.now()

    def get_entity_properties_schema(self, entity_type: EntityType) -> Dict[str, str]:
        """获取实体类型属性模式"""
        schemas = {
            EntityType.LAW: {
                'id': 'string (primary key)',
                'name': 'string (unique)',
                'law_type': 'string',
                'promulgation_date': 'datetime',
                'effective_date': 'datetime',
                'issuing_authority': 'string',
                'description': 'text',
                'source': 'string'
            },
            EntityType.LEGAL_ARTICLE: {
                'id': 'string (primary key)',
                'name': 'string',
                'article_number': 'string',
                'content': 'text',
                'chapter': 'string',
                'section': 'string',
                'description': 'text',
                'source': 'string'
            },
            EntityType.INVALIDATION_DECISION: {
                'id': 'string (primary key)',
                'name': 'string',
                'case_number': 'string',
                'decision_date': 'datetime',
                'case_type': 'string',
                'parties': 'list[string]',
                'outcome': 'text',
                'key_points': 'list[string]',
                'description': 'text',
                'source': 'string'
            },
            EntityType.REEXAMINATION_DECISION: {
                'id': 'string (primary key)',
                'name': 'string',
                'case_number': 'string',
                'decision_date': 'datetime',
                'case_type': 'string',
                'parties': 'list[string]',
                'outcome': 'text',
                'key_points': 'list[string]',
                'description': 'text',
                'source': 'string'
            },
            EntityType.TECHNICAL_CONCEPT: {
                'id': 'string (primary key)',
                'name': 'string',
                'concept_category': 'string',
                'technical_field': 'string',
                'definition': 'text',
                'related_patents': 'list[string]',
                'description': 'text',
                'source': 'string'
            }
        }
        return schemas.get(entity_type, {})

    def get_relation_properties_schema(self, relation_type: RelationType) -> Dict[str, str]:
        """获取关系类型属性模式"""
        schemas = {
            RelationType.CITES: {
                'id': 'string (primary key)',
                'source': 'string (foreign key)',
                'target': 'string (foreign key)',
                'citation_context': 'text',
                'relevance_score': 'float',
                'confidence': 'float',
                'evidence': 'text',
                'source_document': 'string'
            },
            RelationType.APPLIES_TO: {
                'id': 'string (primary key)',
                'source': 'string (foreign key)',
                'target': 'string (foreign key)',
                'scope': 'string',
                'conditions': 'text',
                'confidence': 'float',
                'evidence': 'text',
                'source_document': 'string'
            },
            RelationType.INTERPRETS: {
                'id': 'string (primary key)',
                'source': 'string (foreign key)',
                'target': 'string (foreign key)',
                'interpretation_method': 'string',
                'context': 'text',
                'confidence': 'float',
                'evidence': 'text',
                'source_document': 'string'
            }
        }
        return schemas.get(relation_type, {})

    def get_schema_description(self) -> str:
        """获取知识图谱模式描述"""
        description = f"""
专利知识图谱模式 v{self.schema_version}

=== 实体类型 (Entity Types) ===
法律法规层:
  - {EntityType.LAW.value}: 法律法规 (如专利法、实施细则)
  - {EntityType.JUDICIAL_INTERPRETATION.value}: 司法解释
  - {EntityType.EXAMINATION_GUIDELINE.value}: 审查指南

条款层:
  - {EntityType.LEGAL_ARTICLE.value}: 法条条款
  - {EntityType.REGULATION_CLAUSE.value}: 规章条款
  - {EntityType.GUIDELINE_SECTION.value}: 指南章节

案例层:
  - {EntityType.INVALIDATION_DECISION.value}: 无效宣告决定
  - {EntityType.REEXAMINATION_DECISION.value}: 复审决定
  - {EntityType.COURT_CASE.value}: 法院案例

技术概念层:
  - {EntityType.TECHNICAL_CONCEPT.value}: 技术概念
  - {EntityType.PATENT_TYPE.value}: 专利类型
  - {EntityType.INVENTION_FIELD.value}: 技术领域
  - {EntityType.LEGAL_CONCEPT.value}: 法律概念

当事人层:
  - {EntityType.APPLICANT.value}: 申请人
  - {EntityType.PATENT_HOLDER.value}: 专利权人
  - {EntityType.PATENT_OFFICE.value}: 专利局
  - {EntityType.COURT.value}: 法院
  - {EntityType.EXAMINER.value}: 审查员

专利层:
  - {EntityType.PATENT.value}: 专利
  - {EntityType.PATENT_APPLICATION.value}: 专利申请
  - {EntityType.CLAIM.value}: 权利要求

程序层:
  - {EntityType.LEGAL_PROCEDURE.value}: 法律程序
  - {EntityType.PROCEEDING_STEP.value}: 程序步骤
  - {EntityType.DEADLINE.value}: 期限
  - {EntityType.REQUIREMENT.value}: 要求

=== 关系类型 (Relationship Types) ===
层次关系:
  - {RelationType.CONTAINS.value}: 包含关系 (法律->法条)
  - {RelationType.PART_OF.value}: 部分关系 (法条->法律)
  - {RelationType.DIVIDED_INTO.value}: 划分关系 (指南->章节)

引用关系:
  - {RelationType.CITES.value}: 引用关系 (案例->法条)
  - {RelationType.REFERENCES.value}: 参考关系
  - {RelationType.BASED_ON.value}: 基于关系
  - {RelationType.ACCORDING_TO.value}: 依据关系

适用关系:
  - {RelationType.APPLIES_TO.value}: 适用于 (法条->案例)
  - {RelationType.GOVERNS.value}: 管辖
  - {RelationType.REGULATES.value}: 规范

案例关系:
  - {RelationType.INTERPRETS.value}: 解释 (案例->法条)
  - {RelationType.ILLUSTRATES.value}: 说明
  - {RelationType.PRECEDES.value}: 先例
  - {RelationType.CONTRADICTS.value}: 矛盾

技术关系:
  - {RelationType.RELATES_TO.value}: 关联
  - {RelationType.CLASSIFIED_AS.value}: 分类为
  - {RelationType.IMPLEMENTS.value}: 实现
  - {RelationType.IMPROVES_UPON.value}: 改进

法律关系:
  - {RelationType.VIOLATES.value}: 违反
  - {RelationType.COMPLIES_WITH.value}: 符合
  - {RelationType.EXEMPTS_FROM.value}: 豁免

程序关系:
  - {RelationType.FOLLOWS.value}: 遵循
  - {RelationType.REQUIRES.value}: 要求
  - {RelationType.RESULTS_IN.value}: 导致
  - {RelationType.TRIGGERS.value}: 触发

当事人关系:
  - {RelationType.FILES.value}: 提交
  - {RelationType.OWNS.value}: 拥有
  - {RelationType.CHALLENGES.value}: 挑战
  - {RelationType.DEFENDS.value}: 辩护

时间关系:
  - {RelationType.BEFORE.value}: 之前
  - {RelationType.AFTER.value}: 之后
  - {RelationType.SIMULTANEOUS_WITH.value}: 同时

属性关系:
  - {RelationType.HAS_PROPERTY.value}: 具有...属性
  - {RelationType.DEFINES.value}: 定义
  - {RelationType.SPECIFIES.value}: 明确

=== 设计原则 ===
1. 分层结构: 法律法规->条款->案例的层次关系
2. 多维关联: 技术、法律、程序的多维度关联
3. 时序关系: 支持法律演进和案例先例关系
4. 可扩展性: 支持新实体类型和关系类型的扩展
5. 可追溯性: 每个实体和关系都有明确的来源

创建时间: {self.create_date.strftime('%Y-%m-%d %H:%M:%S')}
"""
        return description.strip()

    def export_schema(self, file_path: str):
        """导出知识图谱模式到文件"""
        schema_data = {
            'schema_version': self.schema_version,
            'create_date': self.create_date.isoformat(),
            'entity_types': [et.value for et in EntityType],
            'relation_types': [rt.value for rt in RelationType],
            'description': self.get_schema_description()
        }

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, ensure_ascii=False, indent=2, default=str)

    def validate_schema(self) -> bool:
        """验证知识图谱模式"""
        try:
            # 检查实体类型
            if len(EntityType) == 0:
                return False

            # 检查关系类型
            if len(RelationType) == 0:
                return False

            # 检查核心配置
            if not self.schema_version:
                return False

            return True
        except Exception:
            return False

    def validate_entity(self, entity: KnowledgeEntity) -> List[str]:
        """验证实体是否符合模式"""
        errors = []

        if not entity.id:
            errors.append('实体ID不能为空')

        if not entity.name:
            errors.append('实体名称不能为空')

        if not isinstance(entity.type, EntityType):
            errors.append('实体类型必须是EntityType枚举值')

        # 检查必需属性
        required_props = self.get_entity_properties_schema(entity.type)
        for prop, prop_type in required_props.items():
            if prop in ['id', 'name']:  # 已经检查过
                continue

            if prop not in entity.properties:
                errors.append(f"缺少必需属性: {prop}")

        return errors

    def validate_relation(self, relation: KnowledgeRelation) -> List[str]:
        """验证关系是否符合模式"""
        errors = []

        if not relation.id:
            errors.append('关系ID不能为空')

        if not relation.source:
            errors.append('源实体ID不能为空')

        if not relation.target:
            errors.append('目标实体ID不能为空')

        if not isinstance(relation.type, RelationType):
            errors.append('关系类型必须是RelationType枚举值')

        # 检查是否允许自环
        if relation.source == relation.target:
            if relation.type not in [RelationType.RELATES_TO, RelationType.HAS_PROPERTY]:
                errors.append(f"关系类型 {relation.type.value} 不允许自环")

        return errors

# ============================================================================
# 工具函数
# ============================================================================

def generate_entity_id(entity_type: EntityType, name: str, source: str = None) -> str:
    """生成实体唯一标识"""
    import hashlib
    import re

    # 清理名称，移除特殊字符
    clean_name = re.sub(r'[^\w\u4e00-\u9fff]', '_', name)

    # 生成哈希值确保唯一性
    content = f"{entity_type.value}_{name}_{source or ''}"
    hash_value = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]

    return f"{entity_type.value}_{clean_name}_{hash_value}"

def generate_relation_id(source_id: str, target_id: str, relation_type: RelationType) -> str:
    """生成关系唯一标识"""
    import hashlib

    content = f"{source_id}_{relation_type.value}_{target_id}"
    hash_value = hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:8]

    return f"{relation_type.value}_{source_id}_{target_id}_{hash_value}"

# ============================================================================
# 使用示例
# ============================================================================

if __name__ == '__main__':
    # 创建知识图谱模式
    schema = PatentKnowledgeGraphSchema()

    # 打印模式描述
    logger.info('专利知识图谱模式定义')
    logger.info(str('=' * 50))
    logger.info(str(schema.get_schema_description()))

    # 导出模式到文件
    schema.export_schema('/tmp/patent_knowledge_graph_schema.json')
    logger.info(f"\n模式已导出到: /tmp/patent_knowledge_graph_schema.json")

    # 示例实体创建
    patent_law = LawEntity(
        id=generate_entity_id(EntityType.LAW, '中华人民共和国专利法', '2020年修订版'),
        type=EntityType.LAW,
        name='中华人民共和国专利法',
        description='规范专利申请、授权、保护的法律',
        law_type='基本法律',
        promulgation_date=datetime(1984, 3, 12),
        effective_date=datetime(1985, 4, 1),
        issuing_authority='全国人民代表大会常务委员会'
    )

    # 验证实体
    errors = schema.validate_entity(patent_law)
    if errors:
        logger.info(f"实体验证错误: {errors}")
    else:
        logger.info(f"实体验证通过: {patent_law.name}")

    # 示例关系创建
    relation = KnowledgeRelation(
        id=generate_relation_id('case_123', patent_law.id, RelationType.CITES),
        source='case_123',
        target=patent_law.id,
        type=RelationType.CITES,
        evidence='该案例引用了专利法第22条',
        confidence=0.95
    )

    # 验证关系
    errors = schema.validate_relation(relation)
    if errors:
        logger.info(f"关系验证错误: {errors}")
    else:
        logger.info(f"关系验证通过: {relation.type.value}")