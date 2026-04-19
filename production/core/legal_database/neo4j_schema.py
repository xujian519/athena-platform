#!/usr/bin/env python3
from __future__ import annotations
"""
Neo4j知识图谱Schema定义
Legal Knowledge Graph Schema for Neo4j

版本: v3.0.0
遵循ChatGLM专家建议的法律知识图谱设计
技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

from enum import Enum
from typing import Any


class Neo4jSchema:
    """Neo4j法律知识图谱Schema"""

    # 数据库配置
    DATABASE_NAME = "legaldb"  # Neo4j数据库名称

    # ========== Label定义(节点类型)==========

    # 1. 法规节点
    LABEL_NORM = "Norm"
    CONSTRAINT_NORM = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Norm) REQUIRE n.id IS UNIQUE
    """

    # 2. 条款节点
    LABEL_ARTICLE = "Article"
    CONSTRAINT_ARTICLE = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Article) REQUIRE n.id IS UNIQUE
    """

    # 3. 法律主体
    LABEL_SUBJECT = "Subject"
    CONSTRAINT_SUBJECT = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Subject) REQUIRE n.id IS UNIQUE
    """

    # 4. 法律行为
    LABEL_ACTION = "Action"
    CONSTRAINT_ACTION = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Action) REQUIRE n.id IS UNIQUE
    """

    # 5. 权利
    LABEL_RIGHT = "Right"
    CONSTRAINT_RIGHT = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Right) REQUIRE n.id IS UNIQUE
    """

    # 6. 义务
    LABEL_OBLIGATION = "Obligation"
    CONSTRAINT_OBLIGATION = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Obligation) REQUIRE n.id IS UNIQUE
    """

    # 7. 责任
    LABEL_LIABILITY = "Liability"
    CONSTRAINT_LIABILITY = """
        CREATE CONSTRAINT IF NOT EXISTS FOR (n:Liability) REQUIRE n.id IS UNIQUE
    """

    # ========== 关系类型定义 ==========

    # 1. 结构关系
    RELATIONSHIP_CONTAINS = "CONTAINS"
    RELATIONSHIP_CITES = "CITES"

    # 2. 法律关系
    RELATIONSHIP_IMPOSES_ON = "IMPOSES_ON"
    RELATIONSHIP_GRANTS_TO = "GRANTS_TO"
    RELATIONSHIP_REGULATES = "REGULATES"
    RELATIONSHIP_HAS_CONSEQUENCE = "HAS_CONSEQUENCE"
    RELATIONSHIP_SUBJECT_TO = "SUBJECT_TO"

    # 3. 版本关系
    RELATIONSHIP_REPEALED_BY = "REPEALED_BY"
    RELATIONSHIP_AMENDED_BY = "AMENDED_BY"
    RELATIONSHIP_CONFLICTS_WITH = "CONFLICTS_WITH"

    @classmethod
    def get_all_constraints(cls) -> str:
        """获取所有约束创建语句(Cypher)"""
        return "\n".join(
            [
                cls.CONSTRAINT_NORM,
                cls.CONSTRAINT_ARTICLE,
                cls.CONSTRAINT_SUBJECT,
                cls.CONSTRAINT_ACTION,
                cls.CONSTRAINT_RIGHT,
                cls.CONSTRAINT_OBLIGATION,
                cls.CONSTRAINT_LIABILITY,
            ]
        )

    @classmethod
    def get_full_schema(cls) -> str:
        """获取完整的Schema创建语句(Cypher)"""
        return f"""
-- ============================================
-- Athena 法律知识图谱 Schema
-- Neo4j Graph Database Definition
-- 版本: v3.0.0 (TD-001: 统一图数据库)
-- ============================================

-- 1. 创建唯一性约束(自动创建索引)
{cls.get_all_constraints()}

-- 2. 创建全文索引(用于文本搜索)
CREATE FULLTEXT INDEX norm_search_index IF NOT EXISTS
FOR (n:Norm) ON EACH [n.name, n.category]
OPTIONS {{indexConfig: {{`fulltext.analyzer`: "chinese"}}}};

CREATE FULLTEXT INDEX article_search_index IF NOT EXISTS
FOR (n:Article) ON EACH [n.original_text]
OPTIONS {{indexConfig: {{`fulltext.analyzer`: "chinese"}}}};

-- 3. 创建示例节点和关系(可选)
-- MATCH (n:Norm {{id: "example_norm"}})
-- CREATE (n)-[:CONTAINS]->(a:Article {{id: "example_article"}})
        """

    @classmethod
    def get_cleanup_schema(cls) -> str:
        """获取清理Schema的语句"""
        return """
-- 删除所有节点和关系
MATCH (n) DETACH DELETE n;

-- 删除约束(可选)
-- DROP CONSTRAINT constraint_name_if_exists;
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


class Neo4jQueryBuilder:
    """Neo4j查询构建器"""

    @staticmethod
    def create_node_id(entity_type: str, entity_name: str) -> str:
        """创建节点ID"""
        import hashlib

        hash_obj = hashlib.md5(
            f"{entity_type}:{entity_name}".encode("utf-8", usedforsecurity=False)
        )
        return f"{entity_type}_{hash_obj.hexdigest()}"

    @staticmethod
    def create_node(label: str, props: dict[str, Any]) -> str:
        """
        构建创建节点的Cypher语句

        Args:
            label: 节点标签
            props: 节点属性

        Returns:
            Cypher语句
        """
        props_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
        ", ".join([f"{k}: ${k}" for k in props.keys()])
        return f"""
            MERGE (n:{label} {{id: $id}})
            SET {props_str}
            RETURN n.id as id
        """

    @staticmethod
    def create_relationship(
        src_id: str, dst_id: str, rel_type: str, props: dict[str, Any] | None = None
    ) -> str:
        """
        构建创建关系的Cypher语句

        Args:
            src_id: 源节点ID
            dst_id: 目标节点ID
            rel_type: 关系类型
            props: 关系属性

        Returns:
            Cypher语句
        """
        if props:
            props_str = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
        else:
            props_str = ""

        return f"""
            MATCH (src {{id: $src_id}})
            MATCH (dst {{id: $dst_id}})
            MERGE (src)-[r:{rel_type}]->(dst)
            {f"SET {props_str}" if props_str else ""}
            RETURN type(r) as rel_type
        """

    @staticmethod
    def find_nodes_by_label(label: str, limit: int = 100) -> str:
        """根据标签查找节点"""
        return f"""
            MATCH (n:{label})
            RETURN n.id as id, n.name as name
            LIMIT {limit}
        """

    @staticmethod
    def find_subjects_by_name(subject_name: str) -> str:
        """根据名称查找法律主体"""
        return """
            MATCH (s:Subject {name: $subject_name})
            RETURN s.id as id, s.name as name, s.type as type, s.description as description
        """

    @staticmethod
    def find_rights_for_subject(subject_name: str) -> str:
        """查找主体的所有权利"""
        return """
            MATCH (s:Subject {name: $subject_name})-[:GRANTS_TO]->(r:Right)
            RETURN s.name as subject_name,
                   r.name as right_name,
                   r.description as description
        """

    @staticmethod
    def find_obligations_for_subject(subject_name: str) -> str:
        """查找主体的所有义务"""
        return """
            MATCH (s:Subject {name: $subject_name})-[:IMPOSES_ON]->(o:Obligation)
            RETURN s.name as subject_name,
                   o.name as obligation_name,
                   o.description as description
        """

    @staticmethod
    def find_shortest_path(
        src_label: str, src_name: str, dst_label: str, dst_name: str, max_depth: int = 5
    ) -> str:
        """查找两个节点之间的最短路径"""
        return f"""
            MATCH (src:{src_label} {{name: $src_name}})
            MATCH (dst:{dst_label} {{name: $dst_name}})
            MATCH path = shortestPath((src)-[*..{max_depth}]-(dst))
            RETURN [node in nodes(path) | node.name] as node_names,
                   [rel in relationships(path) | type(rel)] as rel_types,
                   length(path) as path_length
        """

    @staticmethod
    def find_norms_by_keyword(keyword: str, limit: int = 10) -> str:
        """根据关键词搜索法规"""
        return """
            CALL db.index.fulltext.queryNodes('norm_search_index', $keyword)
            YIELD node, score
            RETURN node.id as id, node.name as name, node.status as status, score
            LIMIT $limit
        """

    @staticmethod
    def find_articles_by_text(text: str, limit: int = 10) -> str:
        """根据文本搜索条款"""
        return """
            CALL db.index.fulltext.queryNodes('article_search_index', $text)
            YIELD node, score
            RETURN node.id as id, node.article_number as article_number,
                   node.original_text as original_text, score
            LIMIT $limit
        """

    @staticmethod
    def get_graph_statistics() -> str:
        """获取图谱统计信息"""
        return """
            MATCH (n)
            WITH labels(n)[0] as label, count(n) as count
            RETURN label, count
            ORDER BY count DESC
        """

    @staticmethod
    def get_relationship_statistics() -> str:
        """获取关系统计信息"""
        return """
            MATCH ()-[r]->()
            WITH type(r) as rel_type, count(r) as count
            RETURN rel_type, count
            ORDER BY count DESC
        """


# ========== 兼容层: 保持与旧API的兼容性 ==========


class NebulaSchema(Neo4jSchema):
    """
    NebulaSchema兼容层
    保持向后兼容,内部使用Neo4j实现
    """

    # 映射旧属性名到新实现
    SPACE_NAME = Neo4jSchema.DATABASE_NAME  # 映射 space_name 到 database_name
    REPLICA_FACTOR = 1
    VID_TYPE = "FIXED_STRING(128)"
    PARTITION_NUM = 1

    # Tag定义映射到Label定义
    TAG_NORM = "-- Neo4jSchema.LABEL_NORM ( migrated to Neo4j Label )"
    TAG_ARTICLE = "-- Neo4jSchema.LABEL_ARTICLE ( migrated to Neo4j Label )"
    TAG_SUBJECT = "-- Neo4jSchema.LABEL_SUBJECT ( migrated to Neo4j Label )"
    TAG_ACTION = "-- Neo4jSchema.LABEL_ACTION ( migrated to Neo4j Label )"
    TAG_RIGHT = "-- Neo4jSchema.LABEL_RIGHT ( migrated to Neo4j Label )"
    TAG_OBLIGATION = "-- Neo4jSchema.LABEL_OBLIGATION ( migrated to Neo4j Label )"
    TAG_LIABILITY = "-- Neo4jSchema.LABEL_LIABILITY ( migrated to Neo4j Label )"

    # Edge定义映射到Relationship定义
    EDGE_CONTAINS = "-- Neo4jSchema.RELATIONSHIP_CONTAINS ( migrated to Neo4j Relationship )"
    EDGE_CITES = "-- Neo4jSchema.RELATIONSHIP_CITES ( migrated to Neo4j Relationship )"
    EDGE_IMPOSES_ON = "-- Neo4jSchema.RELATIONSHIP_IMPOSES_ON ( migrated to Neo4j Relationship )"
    EDGE_GRANTS_TO = "-- Neo4jSchema.RELATIONSHIP_GRANTS_TO ( migrated to Neo4j Relationship )"
    EDGE_REGULATES = "-- Neo4jSchema.RELATIONSHIP_REGULATES ( migrated to Neo4j Relationship )"
    EDGE_HAS_CONSEQUENCE = "-- Neo4jSchema.RELATIONSHIP_HAS_CONSEQUENCE ( migrated to Neo4j Relationship )"
    EDGE_SUBJECT_TO = "-- Neo4jSchema.RELATIONSHIP_SUBJECT_TO ( migrated to Neo4j Relationship )"
    EDGE_REPEALED_BY = "-- Neo4jSchema.RELATIONSHIP_REPEALED_BY ( migrated to Neo4j Relationship )"
    EDGE_AMENDED_BY = "-- Neo4jSchema.RELATIONSHIP_AMENDED_BY ( migrated to Neo4j Relationship )"
    EDGE_CONFLICTS_WITH = "-- Neo4jSchema.RELATIONSHIP_CONFLICTS_WITH ( migrated to Neo4j Relationship )"


class NebulaQueryBuilder(Neo4jQueryBuilder):
    """
    NebulaQueryBuilder兼容层
    保持向后兼容,内部使用Neo4j实现
    """

    @staticmethod
    def insert_vertex(vertex_id: str, tag: str, props: dict[str, Any]) -> str:
        """
        兼容方法: 插入顶点 -> 创建节点

        注意: 返回的是Cypher语句,需要参数化执行
        """
        # 返回Cypher MERGE语句
        props_str = ", ".join([f"n.{k} = ${k}" for k in props.keys()])
        return f"""
            MERGE (n:{tag} {{id: $id}})
            SET {props_str}
            RETURN n.id as id
        """

    @staticmethod
    def insert_edge(src_id: str, dst_id: str, edge_type: str, props: dict[str, Any]) -> str:
        """
        兼容方法: 插入边 -> 创建关系

        注意: 返回的是Cypher语句,需要参数化执行
        """
        props_str = ", ".join([f"r.{k} = ${k}" for k in props.keys()])
        return f"""
            MATCH (src {{id: $src_id}})
            MATCH (dst {{id: $dst_id}})
            MERGE (src)-[r:{edge_type}]->(dst)
            SET {props_str}
            RETURN type(r) as rel_type
        """


if __name__ == "__main__":
    # 打印完整Schema
    print("=" * 80)
    print("Neo4j法律知识图谱Schema")
    print("=" * 80)
    print(Neo4jSchema.get_full_schema())
    print()

    # 打印统计查询
    print("节点统计查询:")
    print(Neo4jQueryBuilder.get_graph_statistics())
    print()
    print("关系统计查询:")
    print(Neo4jQueryBuilder.get_relationship_statistics())
