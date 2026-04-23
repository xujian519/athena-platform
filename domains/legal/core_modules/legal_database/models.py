#!/usr/bin/env python3
from __future__ import annotations

"""
法律数据库数据模型
Legal Database Models

遵循 ChatGLM 专家建议的高质量表结构设计
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class LegalStatus(str, Enum):
    """法律状态"""

    VALID = "现行有效"
    REPEALED = "已废止"
    PARTIALLY_INVALID = "部分失效"
    NOT_EFFECTIVE = "未生效"


class LegalHierarchy(str, Enum):
    """法律层级"""

    CONSTITUTION = "法律"
    ADMIN_REGULATION = "行政法规"
    DEPARTMENT_RULE = "部门规章"
    LOCAL_REGULATION = "地方性法规"
    JUDICIAL_INTERPRETATION = "司法解释"


class ChangeType(str, Enum):
    """变更类型"""

    ENACTMENT = "制定"
    AMENDMENT = "修订"
    REPEAL = "废止"
    INTERPRETATION = "解释"
    CLEANUP = "清理"


@dataclass
class LegalNorm:
    """法规维度表(质量基准)"""

    id: str
    name: str  # 法规名称
    document_number: str | None = None  # 文号(如"国法〔2023〕X 号")
    issuing_authority: str | None = None  # 发布机关
    issue_date: str | None = None  # 发布日期
    effective_date: str | None = None  # 施行日期
    status: LegalStatus = LegalStatus.VALID  # 状态
    hierarchy: LegalHierarchy | None = None  # 层级
    latest_version_id: str | None = None  # 最新版本号(指向自身或另一个版本 id)

    # 元数据
    category: str | None = None  # 类别(如"宪法相关法"、"行政法")
    file_path: str | None = None  # 原始文件路径

    # 全文(用于检索)
    full_text: str | None = None


@dataclass
class ArticleClause:
    """条款结构表"""

    id: str
    norm_id: str  # 外键到 Norm

    # 层级结构
    book_name: str | None = None  # 编名
    chapter_name: str | None = None  # 章名
    section_name: str | None = None  # 节名

    # 条款标识
    article_number: str | None = None  # 条号(如"第 12 条")
    clause_number: str | None = None  # 款号(如"1","2")
    item_number: str | None = None  # 项号(如"(一)"、"1.")

    # 内容
    original_text: str = ""  # 原始文本(纯文本内容)

    # 时间信息
    effective_date: str | None = None  # 开始生效日期
    expiry_date: str | None = None  # 失效日期

    # 层级路径(用于重建结构)
    hierarchy_path: str = ""  # 如"第一章/第二节/第十二条/第一款"


@dataclass
class NormChange:
    """版本变更表"""

    id: str
    norm_id: str  # 关联的法规ID

    change_type: ChangeType  # 变更类型
    change_basis: str | None = None  # 变更依据文件(另一个 norm_id)
    change_date: str | None = None  # 变更日期
    effective_date: str | None = None  # 生效日期

    remarks: str | None = None  # 备注(如"自某日起某条款不再适用")

    # 元数据
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LegalCitation:
    """引用关系表"""

    id: str
    source_norm_id: str  # 引用源法规ID
    target_norm_id: str  # 被引用法规ID
    source_article_id: str | None = None  # 引用源条款ID
    target_article_id: str | None = None  # 被引用条款ID
    citation_type: str | None = None  # 引用类型(如"根据"、"参照"、"适用")
    citation_context: str | None = None  # 引用上下文


@dataclass
class LegalEntity:
    """法律实体(用于知识图谱)"""

    id: str
    entity_type: str  # 实体类型(Subject/Object/Action/Right/Obligation/Liability)
    entity_name: str  # 实体名称
    entity_text: str  # 原始文本
    source_article_id: str  # 来源条款ID

    # 元数据
    confidence: float = 0.8  # 置信度
    extraction_method: str = "llm"  # 抽取方法(rule/llm/manual)
    span_start: int | None = None  # 文本起始位置
    span_end: int | None = None  # 文本结束位置


@dataclass
class LegalRelation:
    """法律关系(用于知识图谱)"""

    id: str
    from_entity_id: str  # 起始实体ID
    to_entity_id: str  # 目标实体ID
    relation_type: str  # 关系类型
    source_article_id: str  # 来源条款ID
    properties: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.8  # 置信度
    extraction_method: str = "llm"  # 抽取方法


@dataclass
class VectorizedClause:
    """向量化条款(用于Qdrant)"""

    clause_id: str  # 关联ArticleClause.id
    norm_id: str  # 关联LegalNorm.id

    # 向量文本(增强版)
    embedding_text: str  # 用于向量化的增强文本

    # 向量数据
    embedding: list[float] | None = None  # 1024维向量(BGE-M3)

    # 元数据
    norm_name: str = ""  # 法规名称
    hierarchy_path: str = ""  # 层级路径
    article_number: str = ""  # 条号

    # 过滤字段
    is_valid: bool = True  # 是否现行有效
