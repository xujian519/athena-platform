#!/usr/bin/env python3
"""
专利撰写结构化数据定义（简化版）

定义专利撰写流程中的核心数据结构。

使用：
from data_structures import (
    InventionUnderstanding,
    TechnicalFeature,
    ProblemFeatureEffect
)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum

# ==================== 枚举类型 ====================


class InventionType(Enum):
    """发明类型"""

    DEVICE = "device"
    METHOD = "method"
    PRODUCT = "product"
    SYSTEM = "system"
    COMPOSITION = "composition"
    USE = "use"


class PatentType(Enum):
    """专利类型"""

    INVENTION = "invention"
    UTILITY_MODEL = "utility_model"


class FeatureType(Enum):
    """技术特征类型"""

    ESSENTIAL = "essential"
    OPTIONAL = "optional"
    EQUIVALENT = "equivalent"


class DisclosureStatus(Enum):
    """公开状态"""

    FULLY_DISCLOSED = "fully_disclosed"
    PARTIALLY_DISCLOSED = "partially_disclosed"
    NOT_DISCLOSED = "not_disclosed"


class ClaimType(Enum):
    """权利要求类型"""

    INDEPENDENT = "independent"
    DEPENDENT = "dependent"


# ==================== 技术特征 ====================


@dataclass
class TechnicalFeature:
    """技术特征"""

    id: str
    description: str
    feature_type: FeatureType
    component: str | None = None
    function: str | None = None
    equivalent_features: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "feature_type": self.feature_type.value,
            "component": self.component,
            "function": self.function,
            "equivalent_features": self.equivalent_features,
        }


# ==================== 三元组 ====================


@dataclass
class ProblemFeatureEffect:
    """问题-特征-效果三元组"""

    id: str
    technical_problem: str
    technical_features: list[TechnicalFeature]
    technical_effects: list[str]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "technical_problem": self.technical_problem,
            "technical_features": [f.to_dict() for f in self.technical_features],
            "technical_effects": self.technical_effects,
        }


# ==================== 发明理解 ====================


@dataclass
class InventionUnderstanding:
    """发明理解结果"""

    invention_title: str
    invention_type: InventionType
    technical_field: str
    core_innovation: str
    technical_problem: str
    technical_solution: str
    technical_effects: list[str]
    essential_features: list[TechnicalFeature]
    optional_features: list[TechnicalFeature]
    confidence_score: float = 0.0

    def to_dict(self) -> dict:
        return {
            "invention_title": self.invention_title,
            "invention_type": self.invention_type.value,
            "technical_field": self.technical_field,
            "core_innovation": self.core_innovation,
            "technical_problem": self.technical_problem,
            "technical_solution": self.technical_solution,
            "technical_effects": self.technical_effects,
            "essential_features": [f.to_dict() for f in self.essential_features],
            "optional_features": [f.to_dict() for f in self.optional_features],
            "confidence_score": self.confidence_score,
        }


# ==================== 对比分析 ====================


@dataclass
class PriorArtReference:
    """对比文件引用"""

    reference_id: str
    document_number: str
    document_type: str
    relevant_sections: list[str]
    disclosure_status: DisclosureStatus
    disclosed_features: list[str]

    def to_dict(self) -> dict:
        return {
            "reference_id": self.reference_id,
            "document_number": self.document_number,
            "document_type": self.document_type,
            "relevant_sections": self.relevant_sections,
            "disclosure_status": self.disclosure_status.value,
            "disclosed_features": self.disclosed_features,
        }


@dataclass
class FeatureComparison:
    """特征对比结果"""

    triplet_id: str
    feature_id: str
    feature_description: str
    disclosure_status: DisclosureStatus
    disclosed_by: list[str]
    disclosure_location: str | None = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "triplet_id": self.triplet_id,
            "feature_id": self.feature_id,
            "feature_description": self.feature_description,
            "disclosure_status": self.disclosure_status.value,
            "disclosed_by": self.disclosed_by,
            "disclosure_location": self.disclosure_location,
            "notes": self.notes,
        }


# ==================== 权利要求 ====================


@dataclass
class Claim:
    """权利要求"""

    claim_number: int
    claim_type: ClaimType
    content: str
    depends_on: int | None = None
    inventive_point_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "claim_number": self.claim_number,
            "claim_type": self.claim_type.value,
            "content": self.content,
            "depends_on": self.depends_on,
            "inventive_point_id": self.inventive_point_id,
        }


@dataclass
class ClaimsSet:
    """权利要求集合"""

    claims: list[Claim]
    total_claims: int
    independent_claims: int
    dependent_claims: int

    def __post_init__(self):
        self.total_claims = len(self.claims)
        self.independent_claims = sum(
            1 for c in self.claims if c.claim_type == ClaimType.INDEPENDENT
        )
        self.dependent_claims = sum(1 for c in self.claims if c.claim_type == ClaimType.DEPENDENT)

    def to_dict(self) -> dict:
        return {
            "claims": [c.to_dict() for c in self.claims],
            "total_claims": self.total_claims,
            "independent_claims": self.independent_claims,
            "dependent_claims": self.dependent_claims,
        }


# ==================== 说明书 ====================


@dataclass
class SpecificationSection:
    """说明书章节"""

    section_name: str
    content: str
    word_count: int
    status: str = "draft"

    def __post_init__(self):
        self.word_count = len(self.content)

    def to_dict(self) -> dict:
        return {
            "section_name": self.section_name,
            "content": self.content,
            "word_count": self.word_count,
            "status": self.status,
        }


@dataclass
class SpecificationDraft:
    """说明书草稿"""

    invention_title: str
    technical_field: SpecificationSection
    background_art: SpecificationSection
    invention_content: SpecificationSection
    drawing_description: SpecificationSection | None = None
    detailed_description: SpecificationSection = None
    total_word_count: int = 0

    def __post_init__(self):
        self.total_word_count = (
            self.technical_field.word_count
            + self.background_art.word_count
            + self.invention_content.word_count
            + (self.drawing_description.word_count if self.drawing_description else 0)
            + (self.detailed_description.word_count if self.detailed_description else 0)
        )

    def to_dict(self) -> dict:
        return {
            "invention_title": self.invention_title,
            "technical_field": self.technical_field.to_dict(),
            "background_art": self.background_art.to_dict(),
            "invention_content": self.invention_content.to_dict(),
            "drawing_description": self.drawing_description.to_dict()
            if self.drawing_description
            else None,
            "detailed_description": self.detailed_description.to_dict()
            if self.detailed_description
            else None,
            "total_word_count": self.total_word_count,
        }


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 创建技术特征
    feature1 = TechnicalFeature(
        id="F1",
        description="压力传感器阵列",
        feature_type=FeatureType.ESSENTIAL,
        component="床垫主体",
        function="检测用户睡姿",
    )

    # 创建三元组
    triplet = ProblemFeatureEffect(
        id="T1",
        technical_problem="无法准确监测用户睡姿",
        technical_features=[feature1],
        technical_effects=["提高睡姿监测准确度", "降低误报率"],
    )

    # 创建发明理解
    understanding = InventionUnderstanding(
        invention_title="一种智能床垫",
        invention_type=InventionType.DEVICE,
        technical_field="智能家居",
        core_innovation="基于压力传感器阵列的睡姿监测",
        technical_problem="现有床垫无法准确监测用户睡姿",
        technical_solution="采用压力传感器阵列实时监测睡姿",
        technical_effects=["提高准确度", "降低误报率"],
        essential_features=[feature1],
        optional_features=[],
        confidence_score=0.85,
    )

    # 输出 JSON
    import json

    print("三元组示例：")
    print(json.dumps(triplet.to_dict(), ensure_ascii=False, indent=2))
    print("\n发明理解示例：")
    print(json.dumps(understanding.to_dict(), ensure_ascii=False, indent=2))
