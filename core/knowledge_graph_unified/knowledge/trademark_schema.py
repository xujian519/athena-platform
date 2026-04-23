
"""
Trademark Knowledge Graph Schema
商标知识图谱模式定义
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TrademarkEntityType(str, Enum):
    """商标实体类型"""

    LAW = "law"  # 法律 (e.g., 商标法)
    REGULATION = "regulation"  # 行政法规 (e.g., 实施条例)
    GUIDELINE = "guideline"  # 审查指南
    JUDICIAL_INTERPRETATION = "judicial_interpretation"  # 司法解释
    ARTICLE = "article"  # 条款
    CONCEPT = "concept"  # 法律概念 (e.g., 显著性, 驰名商标)
    CASE = "case"  # 案例


class TrademarkRelationType(str, Enum):
    """商标关系类型"""

    CONTAINS = "contains"  # 包含 (Law -> Article)
    DEFINES = "defines"  # 定义 (Article -> Concept)
    REGULATES = "regulates"  # 规制 (Article -> Concept)
    INTERPRETS = "interprets"  # 解释 (Judicial Interpretation -> Law)
    CITES = "cites"  # 引用 (Article -> Law/Article)
    RELATED_TO = "related_to"  # 相关


@dataclass
class TrademarkNode:
    """商标知识图谱节点基类"""

    id: str
    name: str
    type: TrademarkEntityType
    content: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrademarkRelation:
    """商标知识图谱关系基类"""

    source_id: str
    target_id: str
    type: TrademarkRelationType
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0


class TrademarkSchema:
    """商标知识图谱模式管理器"""

    @staticmethod
    def get_node_schema(entity_type: TrademarkEntityType) -> dict[str, str]:
        """获取节点Schema定义"""
        base_schema = {
            "id": "string (unique)",
            "name": "string",
            "type": "string (enum)",
            "content": "text",
        }

        specific_schemas = {
            TrademarkEntityType.LAW: {
                "promulgation_date": "datetime",
                "effective_date": "datetime",
                "issuing_authority": "string",
                "level": "string",  # 法律位阶
            },
            TrademarkEntityType.ARTICLE: {
                "article_number": "string",  # e.g., "第十条"
                "chapter": "string",
                "section": "string",
            },
            TrademarkEntityType.CONCEPT: {"definition": "text", "aliases": "list[string]"},
        }

        schema = base_schema.copy()
        if entity_type in specific_schemas:
            schema.update(specific_schemas[entity_type])

        return schema

