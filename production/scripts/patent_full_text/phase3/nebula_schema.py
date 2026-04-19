#!/usr/bin/env python3
"""
NebulaGraph知识图谱Schema定义
Patent Knowledge Graph Schema Definition

定义专利问题-特征-效果三元组知识图谱的结构

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


# ========== 枚举类型定义 ==========

class ProblemType(Enum):
    """技术问题类型"""
    TECHNICAL = "technical"      # 技术问题
    COST = "cost"                # 成本问题
    EFFICIENCY = "efficiency"    # 效率问题
    SAFETY = "safety"            # 安全问题


class FeatureCategory(Enum):
    """技术特征类别"""
    STRUCTURAL = "structural"    # 结构特征
    FUNCTIONAL = "functional"    # 功能特征
    PERFORMANCE = "performance"  # 性能特征


class FeatureType(Enum):
    """技术特征类型"""
    COMPONENT = "component"      # 组件/部件
    PARAMETER = "parameter"      # 参数
    PROCESS = "process"          # 过程/方法
    STRUCTURE = "structure"      # 结构


class EffectType(Enum):
    """技术效果类型"""
    DIRECT = "direct"            # 直接效果
    INDIRECT = "indirect"        # 间接效果


class RelationType(Enum):
    """特征关系类型"""
    COMBINATIONAL = "COMBINATIONAL"  # 组合关系
    DEPENDENT = "DEPENDENT"          # 依赖关系
    ALTERNATIVE = "ALTERNATIVE"      # 替代关系
    SEQUENTIAL = "SEQUENTIAL"        # 顺序关系
    HIERARCHICAL = "HIERARCHICAL"    # 层次关系
    CAUSAL = "CAUSAL"                # 因果关系


# ========== TAG定义 ==========

@dataclass
class TagDefinition:
    """TAG（顶点类型）定义"""
    name: str
    properties: dict[str, str]

    def to_ngql(self) -> str:
        """转换为NebulaGraph CREATE TAG语句"""
        props_str = ", ".join([
            f"{prop_name} {prop_type}"
            for prop_name, prop_type in self.properties.items()
        ])
        return f"CREATE TAG IF NOT EXISTS {self.name}({props_str});"


# ========== EDGE定义 ==========

@dataclass
class EdgeDefinition:
    """EDGE（边类型）定义"""
    name: str
    properties: dict[str, str]

    def to_ngql(self) -> str:
        """转换为NebulaGraph CREATE EDGE语句"""
        props_str = ", ".join([
            f"{prop_name} {prop_type}"
            for prop_name, prop_type in self.properties.items()
        ])
        return f"CREATE EDGE IF NOT EXISTS {self.name}({props_str});"


# ========== Schema定义类 ==========

class NebulaSchemaDefinitions:
    """NebulaGraph Schema定义集合"""

    # ========== TAG定义 ==========
    TAGS = {
        # 基础顶点
        "patent": TagDefinition(
            name="patent",
            properties={
                "id": "string",
                "patent_number": "string",
                "publication_number": "string",
                "application_number": "string",
                "title": "string",
                "patent_type": "string",           # invention/utility_model/design
                "ipc_main_class": "string",
                "ipc_subclass": "string",
                "publication_date": "string",
                "application_date": "string",
                "abstract": "string",
                "created_at": "timestamp"
            }
        ),

        "claim": TagDefinition(
            name="claim",
            properties={
                "id": "string",
                "patent_id": "string",
                "claim_number": "int",
                "claim_type": "string",            # independent/dependent
                "claim_text": "string",
                "depends_on": "int",               # 从属权利要求依赖的权利要求号
                "created_at": "timestamp"
            }
        ),

        "applicant": TagDefinition(
            name="applicant",
            properties={
                "id": "string",
                "name": "string",
                "country": "string",
                "type": "string",                  # individual/company/institution
                "created_at": "timestamp"
            }
        ),

        "ipc_class": TagDefinition(
            name="ipc_class",
            properties={
                "id": "string",
                "code": "string",
                "section": "string",
                "subclass": "string",
                "description": "string",
                "created_at": "timestamp"
            }
        ),

        # 技术分析顶点 (核心新增)
        "technical_problem": TagDefinition(
            name="technical_problem",
            properties={
                "id": "string",
                "description": "string",
                "problem_type": "string",          # technical/cost/efficiency/safety
                "source_section": "string",        # background/invention_content
                "severity": "float",               # 严重程度 0-1
                "created_at": "timestamp"
            }
        ),

        "technical_feature": TagDefinition(
            name="technical_feature",
            properties={
                "id": "string",
                "description": "string",
                "feature_category": "string",      # structural/functional/performance
                "feature_type": "string",          # component/parameter/process/structure
                "source_claim": "int",             # 来源权利要求号
                "importance": "float",             # 重要性 0-1
                "created_at": "timestamp"
            }
        ),

        "technical_effect": TagDefinition(
            name="technical_effect",
            properties={
                "id": "string",
                "description": "string",
                "effect_type": "string",           # direct/indirect
                "quantifiable": "bool",            # 是否可量化
                "metrics": "string",               # 量化指标（如"提高10%"）
                "created_at": "timestamp"
            }
        ),

        "solution": TagDefinition(
            name="solution",
            properties={
                "id": "string",
                "patent_id": "string",
                "description": "string",
                "solution_type": "string",         # complete/partial
                "created_at": "timestamp"
            }
        ),

        # 对比分析顶点
        "contrast_document": TagDefinition(
            name="contrast_document",
            properties={
                "id": "string",
                "patent_number": "string",
                "contrast_type": "string",         # D1/D2/D3
                "similarity_score": "float",
                "created_at": "timestamp"
            }
        ),

        "discriminating_feature": TagDefinition(
            name="discriminating_feature",
            properties={
                "id": "string",
                "description": "string",
                "target_patent_id": "string",
                "d1_patent_id": "string",
                "novelty_score": "float",          # 新颖性评分
                "inventive_score": "float",        # 创造性评分
                "created_at": "timestamp"
            }
        ),
    }

    # ========== EDGE定义 ==========
    EDGES = {
        # 基础关系
        "HAS_CLAIM": EdgeDefinition(
            name="HAS_CLAIM",
            properties={
                "sequence": "int"
            }
        ),

        "HAS_APPLICANT": EdgeDefinition(
            name="HAS_APPLICANT",
            properties={
                "role": "string"                   # inventor/applicant/assignee
            }
        ),

        "BELONGS_TO_IPC": EdgeDefinition(
            name="BELONGS_TO_IPC",
            properties={}
        ),

        "DEPENDS_ON": EdgeDefinition(
            name="DEPENDS_ON",
            properties={
                "sequence": "int"
            }
        ),

        # 技术逻辑关系 (问题-特征-效果三元组)
        "SOLVES": EdgeDefinition(
            name="SOLVES",
            properties={
                "support_score": "float",          # 支持度 0-1
                "created_at": "timestamp"
            }
        ),

        "ACHIEVES": EdgeDefinition(
            name="ACHIEVES",
            properties={
                "contribution_score": "float",     # 贡献度 0-1
                "mechanism": "string",             # 作用机理
                "created_at": "timestamp"
            }
        ),

        "RELATES_TO": EdgeDefinition(
            name="RELATES_TO",
            properties={
                "relation_type": "string",         # COMBINATIONAL/DEPENDENT/ALTERNATIVE/...
                "strength": "float",               # 关系强度 0-1
                "description": "string",
                "created_at": "timestamp"
            }
        ),

        # 方案构成关系
        "CONSISTS_OF": EdgeDefinition(
            name="CONSISTS_OF",
            properties={
                "role": "string"                   # primary/secondary/auxiliary
            }
        ),

        # 专利对比关系
        "CITES": EdgeDefinition(
            name="CITES",
            properties={
                "citation_type": "string",         # forward/backward
                "created_at": "timestamp"
            }
        ),

        "SIMILAR_TO": EdgeDefinition(
            name="SIMILAR_TO",
            properties={
                "similarity_score": "float",
                "similar_aspects": "string",       # problem/solution/effect
                "created_at": "timestamp"
            }
        ),

        # 对比分析关系
        "HAS_D1": EdgeDefinition(
            name="HAS_D1",
            properties={
                "created_at": "timestamp"
            }
        ),

        "HAS_D2": EdgeDefinition(
            name="HAS_D2",
            properties={
                "created_at": "timestamp"
            }
        ),

        "NOT_IN_D1": EdgeDefinition(
            name="NOT_IN_D1",
            properties={
                "created_at": "timestamp"
            }
        ),

        "REVEALED_BY": EdgeDefinition(
            name="REVEALED_BY",
            properties={
                "revelation_type": "string",      # explicit/implicit
                "created_at": "timestamp"
            }
        ),
    }


class NebulaSchemaManager:
    """NebulaGraph Schema管理器"""

    def __init__(
        self,
        space_name: str = "patent_full_text_v2",
        partition_num: int = 10,
        replica_factor: int = 1
    ):
        self.space_name = space_name
        self.partition_num = partition_num
        self.replica_factor = replica_factor

    def get_create_space_sql(self) -> str:
        """获取创建空间的SQL"""
        return (
            f"CREATE SPACE IF NOT EXISTS {self.space_name}("
            f"partition_num={self.partition_num}, "
            f"replica_factor={self.replica_factor}, "
            f"vid_type=FIXED_STRING(32)"
            ");"
        )

    def get_use_space_sql(self) -> str:
        """获取使用空间的SQL"""
        return f"USE {self.space_name};"

    def get_all_tag_sql(self) -> list[str]:
        """获取所有创建TAG的SQL"""
        return [
            tag_def.to_ngql()
            for tag_def in NebulaSchemaDefinitions.TAGS.values()
        ]

    def get_all_edge_sql(self) -> list[str]:
        """获取所有创建EDGE的SQL"""
        return [
            edge_def.to_ngql()
            for edge_def in NebulaSchemaDefinitions.EDGES.values()
        ]

    def get_full_schema_sql(self) -> str:
        """获取完整的Schema创建SQL"""
        sql_lines = [
            f"-- NebulaGraph Schema for {self.space_name}",
            "-- Generated by Athena Platform",
            "-- ",
            self.get_create_space_sql(),
            "",
            "-- 等待空间创建完成（约15秒）",
            "SLEEP 15;",
            "",
            self.get_use_space_sql(),
            "",
            "-- 创建TAG（顶点类型）",
            ""
        ]

        # 添加TAG创建语句
        for tag_sql in self.get_all_tag_sql():
            sql_lines.append(tag_sql)

        sql_lines.extend([
            "",
            "-- 创建EDGE（边类型）",
            ""
        ])

        # 添加EDGE创建语句
        for edge_sql in self.get_all_edge_sql():
            sql_lines.append(edge_sql)

        return "\n".join(sql_lines)

    def save_schema_to_file(self, filepath: str) -> None:
        """保存Schema到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.get_full_schema_sql())
        logger.info(f"✅ Schema已保存到: {filepath}")

    def print_schema_summary(self) -> Any:
        """打印Schema摘要"""
        print("=" * 70)
        print(f"NebulaGraph Schema: {self.space_name}")
        print("=" * 70)

        print("\n📊 空间配置:")
        print(f"  分区数: {self.partition_num}")
        print(f"  副本数: {self.replica_factor}")
        print("  VID类型: FIXED_STRING(32)")

        print(f"\n🏷️  TAG类型 ({len(NebulaSchemaDefinitions.TAGS)}个):")
        for tag_name, tag_def in NebulaSchemaDefinitions.TAGS.items():
            prop_count = len(tag_def.properties)
            print(f"  - {tag_name}: {prop_count}个属性")

        print(f"\n🔗 EDGE类型 ({len(NebulaSchemaDefinitions.EDGES)}个):")
        for edge_name, edge_def in NebulaSchemaDefinitions.EDGES.items():
            prop_count = len(edge_def.properties)
            print(f"  - {edge_name}: {prop_count}个属性")

        print("\n" + "=" * 70)


# ========== 数据模型定义 ==========

@dataclass
class TechnicalProblem:
    """技术问题数据模型"""
    id: str
    description: str
    problem_type: str  # ProblemType枚举值
    source_section: str  # background/invention_content
    severity: float  # 0-1


@dataclass
class TechnicalFeature:
    """技术特征数据模型"""
    id: str
    description: str
    feature_category: str  # FeatureCategory枚举值
    feature_type: str  # FeatureType枚举值
    source_claim: int  # 来源权利要求号
    importance: float  # 0-1


@dataclass
class TechnicalEffect:
    """技术效果数据模型"""
    id: str
    description: str
    effect_type: str  # EffectType枚举值
    quantifiable: bool
    metrics: str  # 如"提高10%"


@dataclass
class FeatureRelation:
    """特征间关系数据模型"""
    from_feature: str
    to_feature: str
    relation_type: str  # RelationType枚举值
    strength: float  # 0-1
    description: str


@dataclass
class Triple:
    """三元组数据模型"""
    subject: str  # 通常是feature
    relation: str  # SOLVES/ACHIEVES
    object: str  # problem/effect
    confidence: float  # 置信度


@dataclass
class TripleExtractionResult:
    """三元组提取结果"""
    patent_number: str
    success: bool

    # 提取的实体
    problems: list[TechnicalProblem] = field(default_factory=list)
    features: list[TechnicalFeature] = field(default_factory=list)
    effects: list[TechnicalEffect] = field(default_factory=list)

    # 三元组关系
    triples: list[Triple] = field(default_factory=list)

    # 特征间关系
    feature_relations: list[FeatureRelation] = field(default_factory=list)

    # 统计信息
    extraction_confidence: float = 0.0
    processing_time: float = 0.0
    error_message: str | None = None

    def get_summary(self) -> dict[str, Any]:
        """获取结果摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "problem_count": len(self.problems),
            "feature_count": len(self.features),
            "effect_count": len(self.effects),
            "triple_count": len(self.triples),
            "relation_count": len(self.feature_relations),
            "confidence": self.extraction_confidence,
            "processing_time": self.processing_time
        }


# ========== 示例使用 ==========

def main() -> None:
    """示例使用"""
    print("=" * 70)
    print("NebulaGraph Schema定义")
    print("=" * 70)

    # 1. 创建Schema管理器
    manager = NebulaSchemaManager()

    # 2. 打印Schema摘要
    manager.print_schema_summary()

    # 3. 生成Schema SQL
    print("\n📝 生成Schema SQL...")
    manager.save_schema_to_file(
        "/Users/xujian/Athena工作平台/production/dev/scripts/patent_full_text/phase3/nebula_schema.ngql"
    )
    print("✅ Schema已保存到 nebula_schema.ngql")

    # 4. 示例数据模型
    print("\n📊 示例数据模型:")
    problem = TechnicalProblem(
        id="p_001",
        description="现有图像识别方法精度低",
        problem_type="efficiency",
        source_section="background",
        severity=0.8
    )
    print(f"  技术问题: {problem.description}")

    feature = TechnicalFeature(
        id="f_001",
        description="基于深度学习的特征提取模块",
        feature_category="structural",
        feature_type="component",
        source_claim=1,
        importance=0.9
    )
    print(f"  技术特征: {feature.description}")

    triple = Triple(
        subject=feature.id,
        relation="SOLVES",
        object=problem.id,
        confidence=0.95
    )
    print(f"  三元组: {triple.subject} --[{triple.relation}]--> {triple.object} (置信度: {triple.confidence})")


if __name__ == "__main__":
    main()
