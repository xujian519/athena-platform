#!/usr/bin/env python3
from __future__ import annotations
"""
统一Neo4j知识图谱引擎
Unified Neo4j Knowledge Graph Engine

合并自3个源文件:
- core/knowledge_graph/neo4j_graph_engine.py (通用知识图谱引擎)
- core/neo4j/neo4j_graph_client.py (通用Neo4j客户端)
- core/judgment_vector_db/storage/neo4j_client.py (专利判决专用客户端)

功能:
- 统一的连接管理
- 多图类型支持
- 节点/边操作
- 图遍历和查询
- 约束和索引管理
- 专利判决专用节点类型
- NebulaGraph兼容层

作者: Athena平台团队
版本: v1.0.0
创建时间: 2026-04-21
"""

import importlib
import logging
import os
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Dict, List

# 使用 TYPE_CHECKING 避免运行时循环导入
if TYPE_CHECKING:
    from neo4j import Driver, GraphDatabase
    from neo4j.exceptions import AuthError, ServiceUnavailable
else:
    # 延迟导入占位符
    Driver = None
    GraphDatabase = None
    ServiceUnavailable = Exception
    AuthError = Exception

# 配置日志
logger = logging.getLogger(__name__)


def _import_neo4j():
    """
    延迟导入第三方 neo4j 包,避免与项目 core.neo4j 模块循环导入

    Returns:
        neo4j 模块对象
    """
    # 临时移除 sys.modules 中的 core.neo4j,避免干扰
    core_neo4j_key = "core.neo4j"
    core_neo4j_init_key = "core.neo4j.__init__"

    saved_core_neo4j = sys.modules.get(core_neo4j_key)
    saved_core_neo4j_init = sys.modules.get(core_neo4j_init_key)

    # 临时移除
    if core_neo4j_key in sys.modules:
        del sys.modules[core_neo4j_key]
    if core_neo4j_init_key in sys.modules:
        del sys.modules[core_neo4j_init_key]

    try:
        # 导入第三方 neo4j 包
        neo4j_module = importlib.import_module("neo4j")
        return neo4j_module
    finally:
        # 恢复 core.neo4j 模块
        if saved_core_neo4j is not None:
            sys.modules[core_neo4j_key] = saved_core_neo4j
        if saved_core_neo4j_init is not None:
            sys.modules[core_neo4j_init_key] = saved_core_neo4j_init


# =============================================================================
# 数据类定义
# =============================================================================

@dataclass
class Neo4jConfig:
    """Neo4j连接配置"""

    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = os.getenv("NEO4J_PASSWORD", "neo4j_password")
    database: str = "neo4j"
    max_pool_size: int = 50
    namespace: str = "default"  # 命名空间,用于隔离不同业务的数据


class GraphType(Enum):
    """知识图谱类型"""
    LEGAL_RULES = "legal_rules"          # 法律规则
    PATENT_GUIDELINE = "patent_guideline"  # 审查指南
    PATENT_INVALIDATION = "patent_invalidation"  # 专利无效
    PATENT_REVIEW = "patent_review"      # 复审
    PATENT_JUDGMENT = "patent_judgment"  # 专利判决
    TRADEMARK = "trademark"              # 商标
    TECH_TERMS = "tech_terms"            # 技术术语


# 专利判决专用节点类型
class JudgmentNodeType(Enum):
    """专利判决图谱节点类型"""
    LEGAL_ARTICLE = "LegalArticle"      # 法律条文
    JUDGMENT_RULE = "JudgmentRule"      # 裁判规则
    TYPICAL_CASE = "TypicalCase"        # 典型案例
    LEGAL_CONCEPT = "LegalConcept"      # 法律概念
    DISPUTE_FOCUS = "DisputeFocus"      # 争议焦点


@dataclass
class GraphNode:
    """知识图谱节点"""
    id: str
    type: str
    properties: Dict[str, Any]
    content: Optional[str] = None
    embedding: List[float] | None = None
    metadata: Dict[str, Any] | None = None


@dataclass
class GraphEdge:
    """知识图谱边"""
    from_node: str
    to_node: str
    relation_type: str
    properties: Dict[str, Any]
    weight: float | None = 1.0
    confidence: float | None = 1.0


# =============================================================================
# 统一Neo4j引擎
# =============================================================================

class Neo4jEngine:
    """
    统一Neo4j知识图谱引擎

    整合通用图谱功能和专利判决专用功能
    """

    def __init__(self, config: Neo4jConfig | None = None, **kwargs):
        """
        初始化Neo4j引擎

        Args:
            config: Neo4j配置对象
            **kwargs: 直接配置参数(优先级高于config)
        """
        if config:
            self.config = config
        else:
            # 尝试从统一配置获取
            try:
                from core.config.settings import get_database_config
                db_config = get_database_config()
                self.config = Neo4jConfig(
                    uri=db_config.neo4j_uri,
                    username=db_config.neo4j_username,
                    password=db_config.neo4j_password,
                    database=db_config.neo4j_database,
                )
            except Exception:
                # 使用默认配置
                self.config = Neo4jConfig()

        # 更新配置(如果有kwargs传入)
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self._driver: Driver | None = None
        self._connected = False
        self._neo4j = None  # 延迟导入的 neo4j 模块

        # 验证database和namespace名称
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.config.database):
            raise ValueError(
                f"Invalid database name: {self.config.database}. "
                f"Only letters, numbers and underscores are allowed."
            )

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.config.namespace):
            raise ValueError(
                f"Invalid namespace: {self.config.namespace}. "
                f"Only letters, numbers and underscores are allowed."
            )

        logger.info(f"🔗 Neo4j引擎初始化: {self.config.uri}")

    # -------------------------------------------------------------------------
    # 连接管理
    # -------------------------------------------------------------------------

    def _get_neo4j(self):
        """获取第三方 neo4j 包(延迟导入)"""
        if self._neo4j is None:
            self._neo4j = _import_neo4j()
        return self._neo4j

    def connect(self) -> bool:
        """
        连接到Neo4j

        Returns:
            连接是否成功
        """
        try:
            neo4j = self._get_neo4j()

            # 创建Driver
            self._driver = neo4j.GraphDatabase.driver(
                self.config.uri,
                auth=(self.config.username, self.config.password),
                max_connection_pool_size=self.config.max_pool_size,
            )

            # 测试连接
            with self._driver.session(database=self.config.database) as session:
                session.run("RETURN 1")

            self._connected = True
            logger.info(f"✅ Neo4j连接成功: {self.config.database}")
            return True

        except Exception as e:
            error_msg = str(e)
            error_class = type(e).__name__

            if "authentication" in error_msg.lower() or error_class == "AuthError":
                logger.error(f"❌ Neo4j认证失败: {e}")
            elif "unavailable" in error_msg.lower() or error_class == "ServiceUnavailable":
                logger.error(f"❌ Neo4j服务不可用: {e}")
            else:
                logger.error(f"❌ Neo4j连接异常: {e}")
            return False

    def close(self) -> None:
        """关闭连接"""
        if self._driver:
            self._driver.close()
            self._connected = False
            logger.info("🔌 Neo4j连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    @contextmanager
    def session(self, **kwargs):
        """
        创建会话上下文

        Args:
            **kwargs: 会话参数

        Yields:
            Neo4j会话对象
        """
        if not self._connected:
            self.connect()

        with self._driver.session(database=self.config.database, **kwargs) as session:
            yield session

    # -------------------------------------------------------------------------
    # 通用查询执行
    # -------------------------------------------------------------------------

    def execute(self, query: str, parameters: Dict[str, Any] | None = None) -> Any | None:
        """
        执行Cypher查询

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            查询结果对象,失败返回None
        """
        if not self._connected:
            logger.error("⚠️  未连接到Neo4j,请先调用connect()")
            return None

        try:
            with self._driver.session(database=self.config.database) as session:
                result = session.run(query, parameters or {})
                logger.debug(f"✅ 查询执行成功: {query[:50]}...")
                return result

        except Exception as e:
            logger.error(f"❌ 查询执行异常: {e}")
            logger.error(f"查询语句: {query[:100]}")
            return None

    def execute_and_fetch(
        self, query: str, parameters: Dict[str, Any] | None = None
    ) -> list[Dict[str, Any]]:
        """
        执行Cypher查询并获取所有结果

        Args:
            query: Cypher查询语句
            parameters: 查询参数

        Returns:
            结果列表
        """
        result = self.execute(query, parameters)
        if result:
            try:
                return [record.data() for record in result]
            except Exception as e:
                logger.error(f"❌ 获取结果失败: {e}")
                return []
        return []

    # -------------------------------------------------------------------------
    # 约束和索引管理
    # -------------------------------------------------------------------------

    def create_constraint(self, label: str, property: str) -> bool:
        """
        创建唯一性约束

        Args:
            label: 节点标签
            property: 属性名

        Returns:
            是否成功
        """
        query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.{property} IS UNIQUE"
        result = self.execute(query)
        return result is not None

    def create_index(self, label: str, property: str) -> bool:
        """
        创建索引

        Args:
            label: 节点标签
            property: 属性名

        Returns:
            是否成功
        """
        query = f"CREATE INDEX IF NOT EXISTS FOR (n:{label}) ON (n.{property})"
        result = self.execute(query)
        return result is not None

    def list_constraints(self) -> list[Dict[str, Any]]:
        """
        列出所有约束

        Returns:
            约束列表
        """
        result = self.execute("CALL db.constraints() YIELD description RETURN description;")
        if result:
            return [{"description": record["description"]} for record in result]
        return []

    def list_indexes(self) -> list[Dict[str, Any]]:
        """
        列出所有索引

        Returns:
            索引列表
        """
        result = self.execute("CALL db.indexes() YIELD * RETURN *;")
        if result:
            return [record.data() for record in result]
        return []

    # -------------------------------------------------------------------------
    # 图初始化
    # -------------------------------------------------------------------------

    def init_graph(self, graph_type: GraphType | str) -> bool:
        """
        初始化图(创建约束)

        Args:
            graph_type: 图类型

        Returns:
            是否成功
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        try:
            with self._driver.session(database=self.config.database) as session:
                constraint = f"CREATE CONSTRAINT ON (n:{label}) ASSERT n.id IS UNIQUE"
                session.run(constraint)
                logger.debug(f"创建约束: {constraint}")
            return True
        except Exception as e:
            logger.debug(f"约束可能已存在: {e}")
            return True  # 约束已存在不算失败

    def initialize_judgment_graph(self) -> bool:
        """
        初始化专利判决图谱(创建所有约束)

        Returns:
            是否成功
        """
        if not self._connected:
            logger.error("❌ 未连接到Neo4j")
            return False

        try:
            with self._driver.session(database=self.config.database) as session:
                # 创建唯一性约束(同时创建索引)
                constraints = [
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{JudgmentNodeType.LEGAL_ARTICLE.value}) REQUIRE n.id IS UNIQUE",
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{JudgmentNodeType.JUDGMENT_RULE.value}) REQUIRE n.id IS UNIQUE",
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{JudgmentNodeType.TYPICAL_CASE.value}) REQUIRE n.case_id IS UNIQUE",
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{JudgmentNodeType.LEGAL_CONCEPT.value}) REQUIRE n.name IS UNIQUE",
                    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{JudgmentNodeType.DISPUTE_FOCUS.value}) REQUIRE n.id IS UNIQUE",
                ]

                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.info("✅ 创建约束成功")
                    except Exception as e:
                        # 约束可能已存在
                        logger.debug(f"约束已存在或创建失败: {e}")

                logger.info(f"✅ 专利判决图谱初始化完成: {self.config.namespace}")
                return True

        except Exception as e:
            logger.error(f"❌ 初始化图模式失败: {e!s}")
            return False

    # -------------------------------------------------------------------------
    # 节点操作
    # -------------------------------------------------------------------------

    def add_node(self, graph_type: GraphType | str, node: GraphNode) -> bool:
        """
        添加节点

        Args:
            graph_type: 图类型
            node: 节点数据

        Returns:
            是否成功
        """
        self.init_graph(graph_type)

        # 构建Cypher查询
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        properties = {
            "id": node.id,
            "type": node.type,
            "properties": node.properties,
            "content": node.content,
            "embedding": node.embedding,
            "metadata": node.metadata or {},
            "created_at": datetime.now().isoformat()
        }

        # 构建动态Cypher
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        cypher = f"""
        MERGE (n:{label} {{id: $id}})
        SET n += {{{props_str}}}
        """

        try:
            with self._driver.session(database=self.config.database) as session:
                session.run(cypher, properties)
                logger.debug(f"添加节点: {label}/{node.id}")
                return True
        except Exception as e:
            logger.error(f"添加节点失败: {e}")
            return False

    # -------------------------------------------------------------------------
    # 边操作
    # -------------------------------------------------------------------------

    def add_edge(self, graph_type: GraphType | str, edge: GraphEdge) -> bool:
        """
        添加边

        Args:
            graph_type: 图类型
            edge: 边数据

        Returns:
            是否成功
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        cypher = f"""
        MATCH (a:{label} {{id: $from_id}})
        MATCH (b:{label} {{id: $to_id}})
        MERGE (a)-[r:{edge.relation_type}]->(b)
        SET r += $properties
        SET r.weight = $weight
        SET r.confidence = $confidence
        SET r.created_at = $created_at
        """

        properties = {
            "from_id": edge.from_node,
            "to_id": edge.to_node,
            "relation_type": edge.relation_type,
            "properties": edge.properties,
            "weight": edge.weight,
            "confidence": edge.confidence,
            "created_at": datetime.now().isoformat()
        }

        try:
            with self._driver.session(database=self.config.database) as session:
                session.run(cypher, properties)
                logger.debug(f"添加边: {edge.from_node} -> {edge.to_node}")
                return True
        except Exception as e:
            logger.error(f"添加边失败: {e}")
            return False

    def create_relation(
        self, edge_type: str, src_id: str, dst_id: str, **properties
    ) -> bool:
        """
        创建关系(边) - 通用方法

        Args:
            edge_type: 关系类型(如 applies_to, derived_from)
            src_id: 源节点ID
            dst_id: 目标节点ID
            **properties: 关系属性

        Returns:
            是否成功
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                # 构建属性设置语句
                props_str = " ".join([f"r.{k} = ${k}" for k in properties.keys()])

                cypher = f"""
                    MATCH (src {{id: $src_id}})
                    MATCH (dst {{id: $dst_id}})
                    MERGE (src)-[r:{edge_type}]->(dst)
                    SET {props_str}
                    RETURN type(r) as rel_type
                """

                params = {
                    "src_id": src_id,
                    "dst_id": dst_id,
                    **properties,
                }

                result = session.run(cypher, params)
                record = result.single()
                if record:
                    logger.debug(f"✅ 创建关系: {src_id} -> {dst_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ 创建关系失败: {e!s}")
            return False

    # -------------------------------------------------------------------------
    # 查询操作
    # -------------------------------------------------------------------------

    def query_nodes(
        self, graph_type: GraphType | str, filters: Dict[str, Any], limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        查询节点

        Args:
            graph_type: 图类型
            filters: 过滤条件
            limit: 返回数量限制

        Returns:
            节点列表
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        # 构建WHERE条件
        where_clauses = []
        params = {"limit": limit}

        if filters.get("type"):
            where_clauses.append("n.type = $type")
            params["type"] = filters["type"]

        if filters.get("content"):
            where_clauses.append("toLower(n.content) CONTAINS toLower($content)")
            params["content"] = filters["content"]

        if filters.get("properties"):
            for key, value in filters["properties"].items():
                where_clauses.append(f"n.properties.{key} = $prop_{key}")
                params[f"prop_{key}"] = value

        where_str = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        cypher = f"""
        MATCH (n:{label}){where_str}
        RETURN n
        LIMIT $limit
        """

        with self._driver.session(database=self.config.database) as session:
            result = session.run(cypher, params)
            nodes = [record["n"] for record in result]
            return nodes

    # -------------------------------------------------------------------------
    # 图遍历
    # -------------------------------------------------------------------------

    def traverse_graph(
        self,
        graph_type: GraphType | str,
        start_node: str,
        direction: str = "any",
        max_depth: int = 3,
    ) -> list[Dict[str, Any]]:
        """
        图遍历

        Args:
            graph_type: 图类型
            start_node: 起始节点ID
            direction: 方向 (inbound/outbound/any)
            max_depth: 最大深度

        Returns:
            遍历结果
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        if direction == "inbound":
            pattern = "<-[r]-"
        elif direction == "outbound":
            pattern = "-[r]->"
        else:  # any
            pattern = "-[r]-"

        cypher = f"""
        MATCH path = (start:{label} {{id: $start_id}}){pattern}*1..{max_depth}(end:{label})
        RETURN [node IN nodes(path) | node] as nodes,
               [rel IN relationships(path) | rel] as relationships,
               length(path) as depth
        LIMIT 100
        """

        with self._driver.session(database=self.config.database) as session:
            result = session.run(cypher, {"start_id": start_node})
            return list(result)

    def query_shortest_path(self, src_name: str, dst_name: str) -> list[Dict[str, Any]]:
        """
        查询最短路径

        Args:
            src_name: 源节点名称
            dst_name: 目标节点名称

        Returns:
            路径列表
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                cypher = """
                    MATCH (src {name: $src_name})
                    MATCH (dst {name: $dst_name})
                    MATCH path = shortestPath((src)-[*..6]-(dst))
                    RETURN [node in nodes(path) | node.name] as node_names,
                           [rel in relationships(path) | type(rel)] as rel_types
                """
                result = session.run(cypher, {"src_name": src_name, "dst_name": dst_name})

                data = [record.data() for record in result]
                return data

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    # -------------------------------------------------------------------------
    # 专利判决专用方法
    # -------------------------------------------------------------------------

    def insert_legal_article(
        self, name: str, content: str = "", article_type: str = "statute"
    ) -> bool:
        """
        插入法律条文

        Args:
            name: 条文名称(如:专利法第22条第3款)
            content: 条文内容
            article_type: 类型

        Returns:
            是否成功
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                # 使用MERGE避免重复
                cypher = """
                    MERGE (n:LegalArticle {id: $id})
                    SET n.name = $name,
                        n.content = $content,
                        n.article_type = $article_type,
                        n.namespace = $namespace
                    RETURN n.id as id
                """
                result = session.run(
                    cypher,
                    {
                        "id": f"legal_article_{self.config.namespace}_{name}",
                        "name": name,
                        "content": content,
                        "article_type": article_type,
                        "namespace": self.config.namespace,
                    },
                )
                record = result.single()
                if record:
                    logger.debug(f"✅ 插入法律条文: {name}")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ 插入法律条文失败: {e!s}")
            return False

    def insert_judgment_rule(
        self,
        name: str,
        description: str,
        applicability: float,
        core_elements: list[str],
        logic_pattern: str = "",
    ) -> bool:
        """
        插入裁判规则

        Args:
            name: 规则名称
            description: 描述
            applicability: 适用率
            core_elements: 核心要素列表
            logic_pattern: 逻辑模式

        Returns:
            是否成功
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                cypher = """
                    MERGE (n:JudgmentRule {id: $id})
                    SET n.name = $name,
                        n.description = $description,
                        n.applicability = $applicability,
                        n.core_elements = $core_elements,
                        n.logic_pattern = $logic_pattern,
                        n.namespace = $namespace
                    RETURN n.id as id
                """
                result = session.run(
                    cypher,
                    {
                        "id": f"judgment_rule_{self.config.namespace}_{name}",
                        "name": name,
                        "description": description,
                        "applicability": applicability,
                        "core_elements": core_elements,
                        "logic_pattern": logic_pattern,
                        "namespace": self.config.namespace,
                    },
                )
                record = result.single()
                if record:
                    logger.debug(f"✅ 插入裁判规则: {name}")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ 插入裁判规则失败: {e!s}")
            return False

    def insert_typical_case(
        self,
        case_id: str,
        court: str,
        year: int,
        case_type: str,
        judgment_result: str,
        importance: float = 1.0,
    ) -> bool:
        """
        插入典型案例

        Args:
            case_id: 案号
            court: 法院
            year: 年份
            case_type: 案由
            judgment_result: 判决结果
            importance: 重要性

        Returns:
            是否成功
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                cypher = """
                    MERGE (n:TypicalCase {case_id: $case_id})
                    SET n.court = $court,
                        n.year = $year,
                        n.case_type = $case_type,
                        n.judgment_result = $judgment_result,
                        n.importance = $importance,
                        n.namespace = $namespace
                    RETURN n.case_id as case_id
                """
                result = session.run(
                    cypher,
                    {
                        "case_id": case_id,
                        "court": court,
                        "year": year,
                        "case_type": case_type,
                        "judgment_result": judgment_result,
                        "importance": importance,
                        "namespace": self.config.namespace,
                    },
                )
                record = result.single()
                if record:
                    logger.debug(f"✅ 插入典型案例: {case_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ 插入典型案例失败: {e!s}")
            return False

    def query_by_legal_article(self, article_name: str) -> list[Dict[str, Any]]:
        """
        根据法律条文查询相关裁判规则和案例

        Args:
            article_name: 法律条文名称

        Returns:
            查询结果列表
        """
        try:
            with self._driver.session(database=self.config.database) as session:
                cypher = """
                    MATCH (article:LegalArticle {id: $article_id})
                    OPTIONAL MATCH (article)-[:APPLIES_TO]->(rule:JudgmentRule)
                    OPTIONAL MATCH (article)<-[:DERIVED_FROM]-(case:TypicalCase)
                    RETURN article.name as article_name,
                           rule.name as rule_name,
                           rule.description as rule_description,
                           case.case_id as case_id,
                           case.judgment_result as case_result
                """
                result = session.run(
                    cypher, {"article_id": f"legal_article_{self.config.namespace}_{article_name}"}
                )

                data = [record.data() for record in result]
                return data

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    # -------------------------------------------------------------------------
    # 统计信息
    # -------------------------------------------------------------------------

    def get_statistics(self, graph_type: GraphType | str) -> Dict[str, Any]:
        """
        获取图统计信息

        Args:
            graph_type: 图类型

        Returns:
            统计信息字典
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        with self._driver.session(database=self.config.database) as session:
            # 节点数
            node_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
            node_count = node_result.single()["count"]

            # 边数
            edge_result = session.run(f"MATCH ()-[r]->() WHERE type(startNode(r)) = '{label}' RETURN count(r) as count")
            edge_count = edge_result.single()["count"]

            # 节点类型分布
            type_result = session.run(f"""
            MATCH (n:{label})
            RETURN n.type as type, count(n) as count
            ORDER BY count DESC
            """)
            type_distribution = [{"type": record["type"], "count": record["count"]}
                               for record in type_result]

            # 关系类型分布
            rel_result = session.run(f"""
            MATCH ()-[r]->()
            WHERE type(startNode(r)) = '{label}'
            RETURN type(r) as type, count(r) as count
            ORDER BY count DESC
            """)
            relation_distribution = [{"type": record["type"], "count": record["count"]}
                                   for record in rel_result]

            return {
                "graph_type": label,
                "nodes": node_count,
                "edges": edge_count,
                "node_types": type_distribution,
                "relation_types": relation_distribution
            }

    def get_database_info(self) -> Dict[str, Any]:
        """
        获取当前数据库的信息

        Returns:
            数据库信息字典
        """
        info = {
            "database_name": self.config.database,
            "labels": [],
            "relationship_types": [],
            "nodes": 0,
            "relationships": 0,
        }

        # 获取所有Labels(节点类型)
        result = self.execute_and_fetch("CALL db.labels() YIELD label RETURN label;")
        if result:
            info["labels"] = [record["label"] for record in result]

        # 获取所有Relationship Types(关系类型)
        result = self.execute_and_fetch(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType;"
        )
        if result:
            info["relationship_types"] = [record["relationshipType"] for record in result]

        # 获取节点数量
        result = self.execute_and_fetch("MATCH (n) RETURN count(n) AS count;")
        if result:
            info["nodes"] = result[0]["count"] if result else 0

        # 获取关系数量
        result = self.execute_and_fetch("MATCH ()-[r]->() RETURN count(r) AS count;")
        if result:
            info["relationships"] = result[0]["count"] if result else 0

        return info

    def print_status(self) -> None:
        """打印图谱状态"""
        if not self._connected:
            print("❌ 未连接到Neo4j")
            return

        try:
            print("\n" + "=" * 60)
            print("📊 Neo4j知识图谱状态")
            print("=" * 60)
            print(f"连接: {self.config.uri}")
            print(f"数据库: {self.config.database}")
            print(f"命名空间: {self.config.namespace}")

            with self._driver.session(database=self.config.database) as session:
                # 统计各种类型的节点数量
                labels = [
                    "LegalArticle",
                    "JudgmentRule",
                    "TypicalCase",
                    "LegalConcept",
                    "DisputeFocus",
                ]

                print("\n节点统计:")
                for label in labels:
                    try:
                        result = session.run(
                            f"""
                            MATCH (n:{label})
                            WHERE n.namespace = $namespace
                            RETURN count(n) AS count
                        """,
                            {"namespace": self.config.namespace},
                        )
                        record = result.single()
                        count = record["count"] if record else 0
                        print(f"  {label}: {count}")
                    except Exception as e:
                        logger.warning(f"⚠️ 查询{label}节点失败: {e}")

                # 统计关系类型
                try:
                    result = session.run(
                        """
                        MATCH ()-[r]->()
                        WHERE r.namespace = $namespace
                        RETURN type(r) as rel_type, count(r) as count
                        ORDER BY count DESC
                    """,
                        {"namespace": self.config.namespace},
                    )
                    print("\n关系统计:")
                    for record in result:
                        print(f"  {record['rel_type']}: {record['count']}")
                except Exception as e:
                    logger.warning(f"⚠️ 查询关系失败: {e}")

            print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"❌ 获取状态失败: {e!s}")

    # -------------------------------------------------------------------------
    # 全文索引
    # -------------------------------------------------------------------------

    def create_fulltext_index(self, graph_type: GraphType | str, properties: list[str]) -> bool:
        """
        创建全文索引

        Args:
            graph_type: 图类型
            properties: 要索引的属性

        Returns:
            是否成功
        """
        if isinstance(graph_type, str):
            label = graph_type
        else:
            label = graph_type.value

        try:
            with self._driver.session(database=self.config.database) as session:
                for prop in properties:
                    # Neo4j 5.x 全文索引
                    session.run(f"""
                    CREATE FULLTEXT INDEX {label}_{prop}_index IF NOT EXISTS
                    FOR (n:{label})
                    ON EACH [n.{prop}]
                    """)
                    logger.info(f"创建全文索引: {label}.{prop}")
            return True
        except Exception as e:
            logger.warning(f"索引创建失败: {e}")
            return False

    # -------------------------------------------------------------------------
    # 清空数据库
    # -------------------------------------------------------------------------

    def clear_database(self) -> bool:
        """
        清空数据库(危险操作!)

        Returns:
            是否成功
        """
        # 先删除所有关系
        result1 = self.execute("MATCH ()-[r]->() DELETE r")
        # 再删除所有节点
        result2 = self.execute("MATCH (n) DELETE n")
        return result1 is not None and result2 is not None


# =============================================================================
# 兼容层 - 保持向后兼容
# =============================================================================

class GraphClient(Neo4jEngine):
    """
    图数据库客户端兼容层

    提供与旧版客户端兼容的接口
    """

    def __init__(self, **kwargs):
        """初始化客户端"""
        super().__init__(**kwargs)

    def is_succeeded(self) -> bool:
        """兼容方法:查询是否成功"""
        return True


class NebulaGraphClient(Neo4jEngine):
    """
    NebulaGraph客户端兼容层

    保持向后兼容,内部使用Neo4j实现
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        # 映射配置
        mapped_config = None
        if config:
            mapped_config = Neo4jConfig(
                uri=f"bolt://{config.get('host', '127.0.0.1')}:{config.get('port', 7687)}",
                username=config.get("user", "neo4j"),
                password=config.get("password", "password"),
                database=config.get("space_name", "neo4j"),
                namespace=config.get("space_name", "patent_judgments"),
            )
        super().__init__(mapped_config)

    def initialize_space(self) -> bool:
        """兼容方法: 初始化空间 -> 初始化图模式"""
        return self.initialize_judgment_graph()


class Neo4jJudgmentClient(Neo4jEngine):
    """
    Neo4j专利判决知识图谱客户端(兼容层)

    保持与旧版API的兼容性
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        初始化客户端

        Args:
            config: 配置字典
        """
        mapped_config = None
        if config:
            mapped_config = Neo4jConfig(
                uri=config.get("uri", "bolt://localhost:7687"),
                username=config.get("username", "neo4j"),
                password=config.get("password", "password"),
                database=config.get("database", "neo4j"),
                namespace=config.get("namespace", "patent_judgments"),
            )
        super().__init__(mapped_config)


# =============================================================================
# 便捷函数
# =============================================================================

def get_neo4j_engine(**kwargs) -> Neo4jEngine:
    """
    获取Neo4j引擎实例

    Args:
        **kwargs: 连接配置参数

    Returns:
        Neo4j引擎实例
    """
    return Neo4jEngine(**kwargs)


def get_neo4j_client(**kwargs) -> Neo4jEngine:
    """
    获取Neo4j客户端实例(兼容层)

    Args:
        **kwargs: 连接配置参数

    Returns:
        Neo4j客户端实例
    """
    return Neo4jEngine(**kwargs)


def get_graph_client(**kwargs) -> GraphClient:
    """
    获取图数据库客户端实例(兼容层)

    Args:
        **kwargs: 连接配置参数

    Returns:
        图数据库客户端实例
    """
    return GraphClient(**kwargs)


def get_neo4j_judgment_client(config: Dict[str, Any] | None = None) -> Neo4jJudgmentClient | None:
    """
    获取Neo4j判决图谱客户端

    Args:
        config: 配置字典

    Returns:
        Neo4j客户端实例
    """
    client = Neo4jJudgmentClient(config)
    if client.connect():
        return client
    return None


def get_nebula_client(config: Dict[str, Any] | None = None) -> NebulaGraphClient | None:
    """
    获取NebulaGraph客户端单例(兼容层)

    注意: 实际返回的是使用Neo4j实现的兼容层客户端

    Args:
        config: 配置字典

    Returns:
        NebulaGraph客户端实例(实际使用Neo4j)
    """
    client = NebulaGraphClient(config)
    if client.connect():
        return client
    return None


# 全局实例(保持向后兼容)
graph_engine = Neo4jEngine()


# =============================================================================
# 测试代码
# =============================================================================

if __name__ == "__main__":
    import asyncio

    def test():
        print("🧪 测试统一Neo4j引擎")
        print("=" * 80)

        # 创建引擎
        engine = Neo4jEngine()

        # 连接
        print("\n1️⃣  连接Neo4j...")
        if engine.connect():
            print("✅ 连接成功")

            # 获取数据库信息
            print("\n2️⃣  获取数据库信息...")
            info = engine.get_database_info()
            print(f"数据库名称: {info['database_name']}")
            print(f"节点类型: {info['labels']}")
            print(f"关系类型: {info['relationship_types']}")
            print(f"节点数: {info['nodes']}")
            print(f"关系数: {info['relationships']}")

            # 列出约束
            print("\n3️⃣  列出约束...")
            constraints = engine.list_constraints()
            print(f"约束数量: {len(constraints)}")

            # 列出索引
            print("\n4️⃣  列出索引...")
            indexes = engine.list_indexes()
            print(f"索引数量: {len(indexes)}")

            # 关闭连接
            engine.close()
            print("\n✅ 测试完成")
        else:
            print("❌ 连接失败")

    asyncio.run(test())
