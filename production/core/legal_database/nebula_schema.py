#!/usr/bin/env python3
from __future__ import annotations
"""
NebulaGraph知识图谱Schema定义
Legal Knowledge Graph Schema for NebulaGraph

遵循ChatGLM专家建议的法律知识图谱设计
"""

from enum import Enum
from typing import Any


class NebulaSchema:
    """NebulaGraph法律知识图谱Schema"""

    # 图空间配置
    SPACE_NAME = "legaldb"  # 使用更简单的名称
    REPLICA_FACTOR = 1  # 单机环境设置为1
    VID_TYPE = "FIXED_STRING(128)"
    PARTITION_NUM = 1  # 单机环境降低分区数

    # ========== Tag定义(顶点类型)==========

    # 1. 法规节点
    TAG_NORM = """
        CREATE TAG IF NOT EXISTS Norm(
            id string,
            name string,
            status string,
            hierarchy string,
            issuing_authority string,
            effective_date string,
            category string
        );
    """

    # 2. 条款节点
    TAG_ARTICLE = """
        CREATE TAG IF NOT EXISTS Article(
            id string,
            article_number string,
            original_text string,
            hierarchy_path string
        );
    """

    # 3. 法律主体
    TAG_SUBJECT = """
        CREATE TAG IF NOT EXISTS Subject(
            id string,
            name string,
            type string,
            description string
        );
    """

    # 4. 法律行为
    TAG_ACTION = """
        CREATE TAG IF NOT EXISTS Action(
            id string,
            name string,
            type string,
            description string
        );
    """

    # 5. 权利
    TAG_RIGHT = """
        CREATE TAG IF NOT EXISTS Right(
            id string,
            name string,
            type string,
            description string
        );
    """

    # 6. 义务
    TAG_OBLIGATION = """
        CREATE TAG IF NOT EXISTS Obligation(
            id string,
            name string,
            type string,
            description string
        );
    """

    # 7. 责任
    TAG_LIABILITY = """
        CREATE TAG IF NOT EXISTS Liability(
            id string,
            name string,
            type string,
            description string
        );
    """

    # ========== Edge类型定义(关系类型)==========

    # 1. 结构关系
    EDGE_CONTAINS = """
        CREATE EDGE IF NOT EXISTS CONTAINS(
            hierarchy_type string
        );
    """

    # 2. 引用关系
    EDGE_CITES = """
        CREATE EDGE IF NOT EXISTS CITES(
            citation_type string,
            context string
        );
    """

    # 3. 法律关系
    EDGE_IMPOSES_ON = """
        CREATE EDGE IF NOT EXISTS IMPOSES_ON(
            obligation_type string
        );
    """

    EDGE_GRANTS_TO = """
        CREATE EDGE IF NOT EXISTS GRANTS_TO(
            right_type string
        );
    """

    EDGE_REGULATES = """
        CREATE EDGE IF NOT EXISTS REGULATES(
            regulation_type string
        );
    """

    EDGE_HAS_CONSEQUENCE = """
        CREATE EDGE IF NOT EXISTS HAS_CONSEQUENCE(
            consequence_type string
        );
    """

    EDGE_SUBJECT_TO = """
        CREATE EDGE IF NOT EXISTS SUBJECT_TO(
            constraint_type string
        );
    """

    # 4. 版本关系
    EDGE_REPEALED_BY = """
        CREATE EDGE IF NOT EXISTS REPEALED_BY(
            repeal_date string,
            basis string
        );
    """

    EDGE_AMENDED_BY = """
        CREATE EDGE IF NOT EXISTS AMENDED_BY(
            amendment_date string,
            basis string
        );
    """

    EDGE_CONFLICTS_WITH = """
        CREATE EDGE IF NOT EXISTS CONFLICTS_WITH(
            conflict_description string
        );
    """

    @classmethod
    def get_all_tags(cls) -> str:
        """获取所有Tag创建语句"""
        return "\n".join(
            [
                cls.TAG_NORM,
                cls.TAG_ARTICLE,
                cls.TAG_SUBJECT,
                cls.TAG_ACTION,
                cls.TAG_RIGHT,
                cls.TAG_OBLIGATION,
                cls.TAG_LIABILITY,
            ]
        )

    @classmethod
    def get_all_edges(cls) -> str:
        """获取所有Edge创建语句"""
        return "\n".join(
            [
                cls.EDGE_CONTAINS,
                cls.EDGE_CITES,
                cls.EDGE_IMPOSES_ON,
                cls.EDGE_GRANTS_TO,
                cls.EDGE_REGULATES,
                cls.EDGE_HAS_CONSEQUENCE,
                cls.EDGE_SUBJECT_TO,
                cls.EDGE_REPEALED_BY,
                cls.EDGE_AMENDED_BY,
                cls.EDGE_CONFLICTS_WITH,
            ]
        )

    @classmethod
    def get_create_space_statement(cls) -> str:
        """获取创建图空间语句"""
        return f"""
            CREATE SPACE IF NOT EXISTS {cls.SPACE_NAME} (
                partition_num = {cls.PARTITION_NUM},
                replica_factor = {cls.REPLICA_FACTOR},
                vid_type = {cls.VID_TYPE}
            );
        """

    @classmethod
    def get_drop_space_statement(cls) -> str:
        """获取删除图空间语句"""
        return f"DROP SPACE IF EXISTS {cls.SPACE_NAME};"

    @classmethod
    def get_full_schema(cls) -> str:
        """获取完整的Schema创建语句"""
        return f"""
-- ============================================
-- Athena 法律知识图谱 Schema
-- NebulaGraph Graph Space Definition
-- ============================================

-- 1. 创建图空间
{cls.get_create_space_statement()}

-- 使用图空间
USE {cls.SPACE_NAME};

-- 2. 创建Tag(顶点类型)
{cls.get_all_tags()}

-- 3. 创建Edge(边类型)
{cls.get_all_edges()}
        """


# ========== 辅助类 ==========


class EntityType(str, Enum):
    """实体类型"""

    NORM = "Norm"
    ARTICLE = "Article"
    SUBJECT = "Subject"
    ACTION = "Action"
    RIGHT = "Right"
    OBLIGATION = "Obligation"
    LIABILITY = "Liability"


class RelationType(str, Enum):
    """关系类型"""

    # 结构关系
    CONTAINS = "CONTAINS"
    CITES = "CITES"

    # 法律关系
    IMPOSES_ON = "IMPOSES_ON"
    GRANTS_TO = "GRANTS_TO"
    REGULATES = "REGULATES"
    HAS_CONSEQUENCE = "HAS_CONSEQUENCE"
    SUBJECT_TO = "SUBJECT_TO"

    # 版本关系
    REPEALED_BY = "REPEALED_BY"
    AMENDED_BY = "AMENDED_BY"
    CONFLICTS_WITH = "CONFLICTS_WITH"


class NebulaQueryBuilder:
    """NebulaGraph查询构建器"""

    @staticmethod
    def create_vertex_id(entity_type: str, entity_name: str) -> str:
        """创建顶点ID"""
        import hashlib

        hash_obj = hashlib.md5(
            f"{entity_type}:{entity_name}".encode("utf-8", usedforsecurity=False)
        )
        return hash_obj.hexdigest()

    @staticmethod
    def insert_vertex(vertex_id: str, tag: str, props: dict[str, Any]) -> str:
        """构建插入顶点的语句"""
        ", ".join([f"{k}: {v}" for k, v in props.items()])
        # 使用外部变量避免 f-string 嵌套问题
        keys_str = ', '.join(props.keys())
        values_str = ', '.join([f'"{v}"' for v in props.values()])
        return f'INSERT VERTEX {tag}({keys_str}) VALUES "{vertex_id}": ({values_str});'

    @staticmethod
    def insert_edge(src_id: str, dst_id: str, edge_type: str, props: dict[str, Any]) -> str:
        """构建插入边的语句"""
        # 使用外部变量避免 f-string 嵌套问题
        keys_str = ', '.join(props.keys())
        values_str = ', '.join([f'"{v}"' for v in props.values()])
        return f'INSERT EDGE {edge_type}({keys_str}) VALUES "{src_id}"->"{dst_id}": ({values_str});'

    @staticmethod
    def find_subjects_by_name(subject_name: str) -> str:
        """根据名称查找法律主体"""
        return f'MATCH (s:Subject {{name: "{subject_name}"}}) RETURN s;'

    @staticmethod
    def find_rights_for_subject(subject_name: str) -> str:
        """查找主体的所有权利"""
        return f"""
            MATCH (s:Subject {{name: "{subject_name}"}})-[:GRANTS_TO]->(r:Right)
            RETURN s.name, r.name, r.description;
        """

    @staticmethod
    def find_obligations_for_subject(subject_name: str) -> str:
        """查找主体的所有义务"""
        return f"""
            MATCH (s:Subject {{name: "{subject_name}"}})-[:IMPOSES_ON]->(o:Obligation)
            RETURN s.name, o.name, o.description;
        """
