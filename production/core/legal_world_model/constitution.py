#!/usr/bin/env python3
from __future__ import annotations
"""
Athena法律世界模型宪法 - 核心定义
Constitution of Athena Legal World Model

本模块定义了法律世界模型的宪法性架构,包括:
- 三层架构(基础法律层、专利专业层、司法案例层)
- 核心实体类型
- 核心关系类型
- 基础数据结构

作者: Athena平台团队
版本: v1.1.0
创建: 2026-01-22
更新: 2026-01-23(明确三层架构详细内容)
宪法: .specify/memory/constitution.md
"""


from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

# =============================================================================
# 核心原则枚举
# =============================================================================


class LayerType(Enum):
    """世界模型三层架构类型

    三层架构反映了从通用法律基础到专利专业体系再到司法实践的完整过程:
    - 第一层:基础法律层(民法典、民诉法等通用法律 + 司法解释)
    - 第二层:专利专业层(专利法、审查指南 + 专利复审无效决定书)
    - 第三层:司法案例层(法院判决文书)
    """

    # 第一层:基础法律层
    # 内容:民法典、民事诉讼法、行政诉讼法等通用法律 + 最高人民法院司法解释
    # 数据库表:law_documents
    FOUNDATION_LAW_LAYER = "foundation_law_layer"

    # 第二层:专利专业层
    # 内容:专利法、实施细则、审查指南(规范)+ 专利复审无效决定书(行政案例)
    # 数据库表:patent_law_documents
    PATENT_PROFESSIONAL_LAYER = "patent_professional_layer"

    # 第三层:司法案例层
    # 内容:专利侵权纠纷、权属纠纷、行政诉讼等判决文书
    # 数据库表:judgment_documents
    JUDICIAL_CASE_LAYER = "judicial_case_layer"

    def __lt__(self, other):
        """定义层级顺序,用于排序"""
        order = {
            LayerType.FOUNDATION_LAW_LAYER: 0,
            LayerType.PATENT_PROFESSIONAL_LAYER: 1,
            LayerType.JUDICIAL_CASE_LAYER: 2,
        }
        return order[self] < order[other]


class Principle(Enum):
    """宪法核心原则"""

    AUTHORITATIVE_FIRST = "authoritative_documents_first"  # 权威文档优先
    THREE_LAYER_ARCH = "three_layer_architecture"  # 三层架构
    KNOWLEDGE_GRAPH = "knowledge_graph_representation"  # 知识图谱化
    EXPLAINABILITY = "explainability"  # 可解释性
    TRUTHFULNESS = "truthfulness"  # 真实性
    MINIMAL_NECESSARY = "minimal_necessary"  # 最小必要
    CONTINUOUS_IMPROVEMENT = "continuous_improvement"  # 持续改进


# =============================================================================
# 实体类型定义
# =============================================================================


class LegalEntityType(Enum):
    """法律实体类型 - 第一层和第三层"""

    # === 法律规则实体(第一层:规则层) ===
    LAW = "law"  # 法律条文
    REGULATION = "regulation"  # 法规
    GUIDELINE = "guideline"  # 指南(如审查指南)
    INTERPRETATION = "interpretation"  # 司法解释

    # === 案例实体(第二层:案例层) ===
    INVALIDATION_DECISION = "invalidation_decision"  # 无效决定

    # === 司法实体(第三层:司法层) ===
    JUDGMENT = "judgment"  # 判决文书
    COURT_VERDICT = "court_verdict"  # 法院判决

    # === 程序实体(跨层) ===
    OFFICE_ACTION = "office_action"  # 审查意见
    RESPONSE = "response"  # 答复
    APPEAL = "appeal"  # 申诉
    DECISION = "decision"  # 决定


class PatentEntityType(Enum):
    """专利实体类型"""

    PATENT = "patent"  # 专利
    CLAIM = "claim"  # 权利要求
    EMBODIMENT = "embodiment"  # 实施例
    TECH_FEATURE = "tech_feature"  # 技术特征
    SPECIFICATION = "specification"  # 说明书

    # 专利文献类型
    PATENT_APPLICATION = "patent_application"  # 专利申请
    GRANTED_PATENT = "granted_patent"  # 授权专利
    PUBLISHED_APPLICATION = "published_application"  # 公开申请


class SubjectEntityType(Enum):
    """主体实体类型"""

    APPLICANT = "applicant"  # 申请人
    PATENTEE = "patentee"  # 专利权人
    INVENTOR = "inventor"  # 发明人
    ASSIGNEE = "assignee"  # 受让人

    EXAMINER = "examiner"  # 审查员
    REVIEWER = "reviewer"  # 复审员

    JUDGE = "judge"  # 法官
    COURT = "court"  # 法院

    PARTY = "party"  # 当事人(通用)
    PLAINTIFF = "plaintiff"  # 原告
    DEFENDANT = "defendant"  # 被告


# =============================================================================
# 关系类型定义
# =============================================================================


class LegalRelationType(Enum):
    """法律关系类型"""

    # === 引用关系 ===
    CITES = "cites"  # 引用
    CITED_BY = "cited_by"  # 被引用
    BASED_ON = "based_on"  # 基于
    OVERRULES = "overrules"  # 推翻
    DISTINGUISHES = "distinguishes"  # 区分
    FOLLOWS = "follows"  # 遵循

    # === 法律关系 ===
    CONFLICTS_WITH = "conflicts_with"  # 冲突
    SUPPORTS = "supports"  # 支持
    CONTRADICTS = "contradicts"  # 矛盾
    PRECEDES = "precedes"  # 先于
    INTERPRETS = "interprets"  # 解释
    MODIFIES = "modifies"  # 修改
    REPEALS = "repeals"  # 废除


class PatentRelationType(Enum):
    """专利关系类型"""

    # === 归属关系 ===
    ASSIGNED_TO = "assigned_to"  # 受让人归属
    INVENTED_BY = "invented_by"  # 发明者归属
    FILED_BY = "filed_by"  # 申请人归属
    REVIEWED_BY = "reviewed_by"  # 审查员审查

    # === 专利内部关系 ===
    INCLUDES_CLAIM = "includes_claim"  # 包含权利要求
    DEPENDS_ON = "depends_on"  # 依赖于(从属权利要求)
    EMBODIES = "embodies"  # 具体化(实施例)
    DISCLOSES = "discloses"  # 披露(说明书)

    # === 技术关系 ===
    RELATES_TO_TECH = "relates_to_tech"  # 涉及技术
    BELONGS_TO_FIELD = "belongs_to_field"  # 属于技术领域
    SIMILAR_TO = "similar_to"  # 相似技术

    # === 分类关系 ===
    HAS_IPC_CLASS = "has_ipc_class"  # IPC分类
    HAS_CPC_CLASS = "has_cpc_class"  # CPC分类


class ProceduralRelationType(Enum):
    """程序关系类型"""

    TRIGGERED_BY = "triggered_by"  # 触发
    RESPONDED_TO = "responded_to"  # 答复
    APPEALED_AGAINST = "appealed_against"  # 申诉
    REVIEWED_DECISION = "reviewed_decision"  # 复审决定

    # 时间顺序关系
    PRECEDES_IN_TIME = "precedes_in_time"  # 时间上在先
    SUCCEEDS_IN_TIME = "succeeds_in_time"  # 时间上在后


# =============================================================================
# 权威文档类型定义
# =============================================================================


class DocumentType(Enum):
    """权威文档类型"""

    # === 第一层:规则层文档 ===
    STATUTE = "statute"  # 成文法(如专利法)
    REGULATION_DOC = "regulation_doc"  # 法规
    GUIDELINE_DOC = "guideline_doc"  # 指南
    JUDICIAL_INTERPRETATION = "judicial_interpretation"  # 司法解释

    # === 第二层:案例层文档 ===
    INVALIDATION_DECISION_DOC = "invalidation_decision"  # 无效决定

    # === 第三层:司法层文档 ===
    CIVIL_JUDGMENT = "civil_judgment"  # 民事判决
    ADMINISTRATIVE_JUDGMENT = "administrative_judgment"  # 行政判决


class DocumentSource(Enum):
    """权威文档来源"""

    CNIPA = "cnipa"  # 国家知识产权局
    SPC = "spc"  # 最高人民法院
    PEOPLE_CONGRESS = "people_congress"  # 全国人大
    STATE_COUNCIL = "state_council"  # 国务院


# =============================================================================
# 数据类定义
# =============================================================================


@dataclass
class LegalEntity:
    """法律实体基类"""

    entity_id: str = field(default_factory=lambda: str(uuid4()))
    entity_type: LegalEntityType | PatentEntityType | SubjectEntityType = None
    name: str = ""
    layer_type: LayerType | None = None
    source_type: DocumentType | None = None
    source: DocumentSource | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后处理"""
        if self.entity_type and not self.layer_type:
            # 根据实体类型自动推断层级
            if isinstance(self.entity_type, LegalEntityType):
                if self.entity_type in [
                    LegalEntityType.LAW,
                    LegalEntityType.REGULATION,
                    LegalEntityType.GUIDELINE,
                    LegalEntityType.INTERPRETATION,
                ]:
                    # 法律、法规、指南、司法解释 -> 基础法律层
                    self.layer_type = LayerType.FOUNDATION_LAW_LAYER
                elif self.entity_type == LegalEntityType.INVALIDATION_DECISION:
                    # 无效决定 -> 专利专业层
                    self.layer_type = LayerType.PATENT_PROFESSIONAL_LAYER
                elif self.entity_type in [LegalEntityType.JUDGMENT, LegalEntityType.COURT_VERDICT]:
                    # 判决文书 -> 司法案例层
                    self.layer_type = LayerType.JUDICIAL_CASE_LAYER


@dataclass
class LegalRule(LegalEntity):
    """法律规则"""

    rule_type: str = ""  # 规则类型:定义/标准/程序
    article: str = ""  # 条款号
    content: str = ""  # 规则内容
    keywords: list[str] = field(default_factory=list)
    related_rules: list[str] = field(default_factory=list)  # 相关规则ID

    def __post_init__(self):
        if self.entity_type is None:
            self.entity_type = LegalEntityType.LAW
        # 调用父类的 __post_init__ 来自动设置 layer_type
        super().__post_init__()


@dataclass
class Case(LegalEntity):
    """案例基类"""

    case_number: str = ""  # 案件编号
    decision_date: datetime | None = None  # 决定日期
    key_issues: list[str] = field(default_factory=list)  # 争议焦点
    reasoning_process: str = ""  # 推理过程
    conclusion: str = ""  # 结论
    legal_basis: list[str] = field(default_factory=list)  # 法律依据
    confidence: float = 0.0  # 推理置信度


@dataclass
class InvalidationDecision(Case):
    """无效复审决定"""

    patent_id: str = ""  # 专利号
    patent_owner: str = ""  # 专利权人
    requester: str = ""  # 请求人
    invalidation_grounds: list[str] = field(default_factory=list)  # 无效理由
    evidence: list[dict[str, Any]] = field(default_factory=list)  # 证据
    decision_result: str = ""  # 决定结果(全部无效/部分无效/维持有效)

    def __post_init__(self):
        if self.entity_type is None:
            self.entity_type = LegalEntityType.INVALIDATION_DECISION
        # 调用父类的 __post_init__ 来自动设置 layer_type
        super().__post_init__()


@dataclass
class Judgment(Case):
    """判决文书"""

    court: str = ""  # 审理法院
    case_type: str = ""  # 案件类型(侵权/权属/行政)
    parties: dict[str, str] = field(default_factory=dict)  # 当事人
    claims_interpretation: dict[str, str] = field(default_factory=dict)  # 权利要求解释
    infringement_finding: dict[str, Any] = field(default_factory=dict)  # 侵权认定
    damages: float | None = None  # 赔偿金额

    def __post_init__(self):
        if self.entity_type is None:
            self.entity_type = LegalEntityType.JUDGMENT
        # 调用父类的 __post_init__ 来自动设置 layer_type
        super().__post_init__()


@dataclass
class Patent(LegalEntity):
    """专利"""

    patent_number: str = ""  # 专利号
    application_number: str = ""  # 申请号
    filing_date: datetime | None = None  # 申请日
    publication_date: datetime | None = None  # 公开日
    grant_date: datetime | None = None  # 授权日
    applicants: list[str] = field(default_factory=list)  # 申请人列表
    inventors: list[str] = field(default_factory=list)  # 发明人列表
    assignees: list[str] = field(default_factory=list)  # 受让人列表
    ipc_classifications: list[str] = field(default_factory=list)  # IPC分类
    title: str = ""  # 标题
    abstract: str = ""  # 摘要
    claims: list[str] = field(default_factory=list)  # 权利要求
    description: str = ""  # 说明书

    def __post_init__(self):
        if self.entity_type is None:
            self.entity_type = PatentEntityType.PATENT


@dataclass
class LegalRelation:
    """法律关系"""

    relation_id: str = field(default_factory=lambda: str(uuid4()))
    relation_type: LegalRelationType | PatentRelationType | ProceduralRelationType = None
    from_entity: str = ""  # 来源实体ID
    to_entity: str = ""  # 目标实体ID
    weight: float = 1.0  # 关系权重
    confidence: float = 1.0  # 置信度
    evidence: list[str] = field(default_factory=list)  # 证据/依据
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# 宪法验证器
# =============================================================================


class ConstitutionalValidator:
    """宪法验证器 - 确保所有操作符合宪法原则"""

    @staticmethod
    def validate_entity_source(entity: LegalEntity) -> bool:
        """
        验证实体来源是否符合权威文档原则

        Args:
            entity: 待验证的实体

        Returns:
            bool: 是否符合宪法原则
        """
        # 原则一:权威文档优先原则
        if entity.source_type is None:
            raise ValueError(f"实体 {entity.entity_id} 缺少来源类型")

        if entity.source is None:
            raise ValueError(f"实体 {entity.entity_id} 缺少来源信息")

        # 验证来源必须是权威来源
        authoritative_sources = {
            DocumentSource.CNIPA,
            DocumentSource.SPC,
            DocumentSource.PEOPLE_CONGRESS,
            DocumentSource.STATE_COUNCIL,
        }

        if entity.source not in authoritative_sources:
            raise ValueError(f"实体 {entity.entity_id} 的来源 {entity.source} 不是权威来源")

        return True

    @staticmethod
    def validate_entity(entity: dict) -> bool:
        """
        验证实体是否符合宪法原则

        这是对外的统一验证接口,整合了所有验证逻辑

        Args:
            entity: 待验证的实体字典,应包含:
                - entity_type: LegalEntityType, 实体类型
                - layer: LayerType, 所属层级
                - (可选) source_type: DocumentSource, 来源类型
                - (可选) source: str, 来源信息

        Returns:
            bool: 是否符合宪法原则

        Raises:
            ValueError: 当实体不符合宪法原则时
            KeyError: 当实体缺少必要字段时
        """
        # 获取实体属性
        entity_type = entity.get("entity_type")
        layer = entity.get("layer")
        source_type = entity.get("source_type")
        source = entity.get("source")

        # 基本验证: 必须有实体类型和层级
        if entity_type is None:
            raise ValueError("实体缺少 entity_type 字段")

        if layer is None:
            raise ValueError("实体缺少 layer 字段")

        # 验证实体类型是否合法
        try:
            if isinstance(entity_type, str):
                entity_type = LegalEntityType(entity_type)
            elif not isinstance(entity_type, LegalEntityType):
                raise ValueError("entity_type 必须是 LegalEntityType 枚举值")
        except ValueError:
            raise ValueError(f"无效的实体类型: {entity_type}") from None

        # 验证层级是否合法
        try:
            if isinstance(layer, str):
                layer = LayerType(layer)
            elif not isinstance(layer, LayerType):
                raise ValueError("layer 必须是 LayerType 枚举值")
        except ValueError:
            raise ValueError(f"无效的层级: {layer}") from None

        # 实体类型和层级的匹配验证
        # 第一层(基础法律层)只能包含法律规则实体
        if layer == LayerType.FOUNDATION_LAW_LAYER:
            allowed_types = {
                LegalEntityType.LAW,
                LegalEntityType.REGULATION,
                LegalEntityType.GUIDELINE,
                LegalEntityType.INTERPRETATION,
            }
            if entity_type not in allowed_types:
                raise ValueError(
                    f"基础法律层不能包含 {entity_type.value} 类型实体, "
                    f"只能是法律规则实体"
                )

        # 第二层(专利专业层)可以包含无效决定和规则实体
        elif layer == LayerType.PATENT_PROFESSIONAL_LAYER:
            allowed_types = {
                LegalEntityType.INVALIDATION_DECISION,
                LegalEntityType.LAW,
                LegalEntityType.REGULATION,
                LegalEntityType.GUIDELINE,
            }
            if entity_type not in allowed_types:
                raise ValueError(
                    f"专利专业层不能包含 {entity_type.value} 类型实体"
                )

        # 第三层(司法案例层)主要包含案例实体
        elif layer == LayerType.JUDICIAL_CASE_LAYER:
            # 司法案例层可以包含任何类型(主要是案例)
            pass

        # 来源验证(如果有提供)
        if source_type is not None or source is not None:
            if source_type is None:
                raise ValueError("提供了 source 但缺少 source_type")

            if source is None:
                raise ValueError("提供了 source_type 但缺少 source")

            # 验证来源必须是权威来源
            authoritative_sources = {
                DocumentSource.CNIPA,
                DocumentSource.SPC,
                DocumentSource.PEOPLE_CONGRESS,
                DocumentSource.STATE_COUNCIL,
            }

            try:
                if isinstance(source_type, str):
                    source_type = DocumentSource(source_type)
                elif not isinstance(source_type, DocumentSource):
                    raise ValueError("source_type 必须是 DocumentSource 枚举值")
            except ValueError:
                raise ValueError(f"无效的来源类型: {source_type}") from None

            if source_type not in authoritative_sources:
                raise ValueError(
                    f"实体来源 {source_type.value} 不是权威来源, "
                    f"必须是: CNIPA(国家知识产权局)、SPC(最高人民法院)等"
                )

        return True

    @staticmethod
    def validate_layer_order(from_layer: LayerType, to_layer: LayerType) -> bool:
        """
        验证层级顺序是否符合三层架构原则

        Args:
            from_layer: 源层级
            to_layer: 目标层级

        Returns:
            bool: 是否符合宪法原则
        """
        # 原则二:三层架构原则
        # 构建时必须按顺序:基础法律层 → 专利专业层 → 司法案例层
        allowed_transitions = {
            LayerType.FOUNDATION_LAW_LAYER: [LayerType.PATENT_PROFESSIONAL_LAYER],
            LayerType.PATENT_PROFESSIONAL_LAYER: [LayerType.JUDICIAL_CASE_LAYER],
            LayerType.JUDICIAL_CASE_LAYER: [],  # 司法案例层是最高层
        }

        if to_layer not in allowed_transitions.get(from_layer, []):
            layer_names = {
                LayerType.FOUNDATION_LAW_LAYER: "基础法律层",
                LayerType.PATENT_PROFESSIONAL_LAYER: "专利专业层",
                LayerType.JUDICIAL_CASE_LAYER: "司法案例层",
            }
            raise ValueError(
                f"违反三层架构原则:不能从 {layer_names[from_layer]} 直接构建到 {layer_names[to_layer]}。"
                f"必须遵循:基础法律层 → 专利专业层 → 司法案例层"
            )

        return True

    @staticmethod
    def validate_relation_explainability(relation: LegalRelation, reasoning: str) -> bool:
        """
        验证关系是否具有可解释性

        Args:
            relation: 待验证的关系
            reasoning: 推理过程

        Returns:
            bool: 是否符合可解释性原则
        """
        # 原则四:可解释性原则
        if not reasoning or len(reasoning.strip()) == 0:
            raise ValueError(f"关系 {relation.relation_id} 缺少推理解释")

        if not relation.evidence:
            raise ValueError(f"关系 {relation.relation_id} 缺少法律依据")

        return True

    @staticmethod
    def validate_truthfulness(entity: LegalEntity, source_verification: bool) -> bool:
        """
        验证实体数据的真实性

        Args:
            entity: 待验证的实体
            source_verification: 是否已验证来源

        Returns:
            bool: 是否符合真实性原则
        """
        # 原则五:真实性原则
        if not source_verification:
            raise ValueError(f"实体 {entity.entity_id} 的来源未经验证")

        # 检查必要字段
        if entity.entity_type in [
            LegalEntityType.LAW,
            LegalEntityType.REGULATION,
            LegalEntityType.GUIDELINE,
        ] and not entity.metadata.get("text") and not entity.name:
            raise ValueError(f"法律规则实体 {entity.entity_id} 缺少内容")

        return True


# =============================================================================
# 权威文档引用格式
# =============================================================================


@dataclass
class CitationReference:
    """权威文档引用"""

    document_type: DocumentType
    source: DocumentSource
    document_id: str  # 文档标识(如条号、案号)
    section: str | None = None  # 章节/条款
    paragraph: str | None = None  # 段落
    url: str | None = None  # 在线地址
    accessed_date: datetime | None = None  # 访问日期

    def format_citation(self) -> str:
        """格式化为标准引用格式"""
        parts = []

        # 来源
        source_names = {
            DocumentSource.CNIPA: "国家知识产权局",
            DocumentSource.SPC: "最高人民法院",
            DocumentSource.PEOPLE_CONGRESS: "全国人大",
            DocumentSource.STATE_COUNCIL: "国务院",
        }

        if self.source in source_names:
            parts.append(source_names[self.source])

        # 文档类型和ID
        type_names = {
            DocumentType.STATUTE: "《专利法》",
            DocumentType.REGULATION_DOC: "《专利法实施细则》",
            DocumentType.GUIDELINE_DOC: "《专利审查指南》",
            DocumentType.INVALIDATION_DECISION_DOC: "无效决定",
            DocumentType.CIVIL_JUDGMENT: "民事判决书",
        }

        if self.document_type in type_names:
            parts.append(type_names[self.document_type])

        if self.document_id:
            parts.append(self.document_id)

        if self.section:
            parts.append(f"第{self.section}条")

        citation = ",".join(parts)
        return citation


# =============================================================================
# 宪法版本信息
# =============================================================================

CONSTITUTION_VERSION = "1.1.0"
CONSTITUTION_RATIFICATION_DATE = datetime(2026, 1, 22)
CONSTITUTION_LAST_AMENDED = datetime(2026, 1, 23)


# =============================================================================
# 导出接口
# =============================================================================

__all__ = [
    "CONSTITUTION_LAST_AMENDED",
    "CONSTITUTION_RATIFICATION_DATE",
    # 版本信息
    "CONSTITUTION_VERSION",
    "Case",
    "CitationReference",
    # 验证器
    "ConstitutionalValidator",
    "DocumentSource",
    # 文档类型
    "DocumentType",
    "InvalidationDecision",
    "Judgment",
    # 核心原则
    "LayerType",
    # 数据类
    "LegalEntity",
    # 实体类型
    "LegalEntityType",
    "LegalRelation",
    # 关系类型
    "LegalRelationType",
    "LegalRule",
    "Patent",
    "PatentEntityType",
    "PatentRelationType",
    "Principle",
    "ProceduralRelationType",
    "SubjectEntityType",
]


if __name__ == "__main__":
    # 测试代码
    print("Athena法律世界模型宪法 - 核心定义")
    print(f"宪法版本: {CONSTITUTION_VERSION}")
    print(f"批准日期: {CONSTITUTION_RATIFICATION_DATE.strftime('%Y-%m-%d')}")
    print()

    # 测试实体创建
    patent_law = LegalRule(
        name="《中华人民共和国专利法》",
        entity_type=LegalEntityType.LAW,
        source=DocumentSource.PEOPLE_CONGRESS,
        source_type=DocumentType.STATUTE,
        article="第22条",
        content="授予专利权的发明和实用新型,应当具备新颖性、创造性和实用性。",
    )

    print(f"创建实体: {patent_law.name}")
    print(f"  层级: {patent_law.layer_type.value}")
    print(f"  来源: {patent_law.source.value}")

    # 测试宪法验证
    try:
        ConstitutionalValidator.validate_entity_source(patent_law)
        print("  ✅ 符合权威文档原则")
    except ValueError as e:
        print(f"  ❌ {e}")
