from __future__ import annotations

"""
Athena法律世界模型 - 核心模块
Athena Legal World Model - Core Module

本模块实现了法律世界模型的宪法性架构,包括:
- 三层架构(基础法律层、专利专业层、司法案例层)
- 核心实体类型
- 核心关系类型
- 宪法验证器
- 数据库管理器

作者: Athena平台团队
版本: v1.2.0
创建: 2026-01-22
更新: 2026-03-06(添加数据库管理器)
"""

from .constitution import (
    CONSTITUTION_LAST_AMENDED,
    CONSTITUTION_RATIFICATION_DATE,
    # 版本信息
    CONSTITUTION_VERSION,
    Case,
    CitationReference,
    # 验证器
    ConstitutionalValidator,
    DocumentSource,
    # 文档类型
    DocumentType,
    InvalidationDecision,
    Judgment,
    # 核心原则
    LayerType,
    # 数据类
    LegalEntity,
    # 实体类型
    LegalEntityType,
    LegalRelation,
    # 关系类型
    LegalRelationType,
    LegalRule,
    Patent,
    PatentEntityType,
    PatentRelationType,
    Principle,
    ProceduralRelationType,
    SubjectEntityType,
)
from .db_manager import (
    LegalWorldDBManager,
    create_db_manager,
)

__version__ = "1.2.0"
__author__ = "Athena Platform Team"
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
    # 数据库管理
    "LegalWorldDBManager",
    "create_db_manager",
]
