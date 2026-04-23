#!/usr/bin/env python3

"""
Neo4j知识图谱客户端
Neo4j Knowledge Graph Client for Patent Judgments

版本: v3.0.0
功能:
- 管理专利判决知识图谱
- 存储/查询 法律条文→裁判规则→典型案例 关系
- 图谱遍历和推理
技术决策: TD-001 - 统一图数据库选择为Neo4j
"""

import re
from typing import Any, Optional

from core.config.unified_config import get_database_config
from core.logging_config import setup_logging

logger = setup_logging()


class Neo4jJudgmentClient:
    """Neo4j专利判决知识图谱客户端"""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        """
        初始化Neo4j客户端

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.driver = None
        self.is_connected = False

        # 从统一配置获取连接信息 (TD-001)
        db_config = get_database_config()
        neo4j_config = db_config.get("neo4j", {})

        self.uri = self.config.get("uri", neo4j_config.get("uri", "bolt://localhost:7687"))
        self.username = self.config.get("username", neo4j_config.get("username", "neo4j"))
        self.password = self.config.get("password", neo4j_config.get("password", "password"))
        self.database = self.config.get("database", neo4j_config.get("database", "neo4j"))

        # 图谱命名空间(用于隔离不同业务的数据)
        self.namespace = self.config.get("namespace", "patent_judgments")

        # 验证database名称(只允许字母、数字和下划线)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.database):
            raise ValueError(
                f"Invalid database name: {self.database}. Only letters, numbers and underscores are allowed."
            )

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", self.namespace):
            raise ValueError(
                f"Invalid namespace: {self.namespace}. Only letters, numbers and underscores are allowed."
            )

    def connect(self) -> bool:
        """
        连接到Neo4j

        Returns:
            是否连接成功
        """
        try:
            from neo4j import GraphDatabase

            logger.info(f"🔄 连接到Neo4j: {self.uri}")

            # 创建驱动
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password),
            )

            # 测试连接
            with self.driver.session(database=self.database) as session:
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if record and record["message"] == "Connection OK":
                    self.is_connected = True
                    logger.info("✅ Neo4j连接成功")
                    return True

            return False

        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e!s}")
            self.is_connected = False
            return False

    def initialize_graph(self) -> bool:
        """
        初始化图模式(约束和索引)

        Returns:
            是否成功
        """
        if not self.is_connected:
            logger.error("❌ 未连接到Neo4j")
            return False

        try:
            with self.driver.session(database=self.database) as session:
                # 创建唯一性约束(同时创建索引)
                constraints = [
                    # 法律条文
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:LegalArticle) REQUIRE n.id IS UNIQUE",
                    # 裁判规则
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:JudgmentRule) REQUIRE n.id IS UNIQUE",
                    # 典型案例
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:TypicalCase) REQUIRE n.case_id IS UNIQUE",
                    # 法律概念
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:LegalConcept) REQUIRE n.name IS UNIQUE",
                    # 争议焦点
                    "CREATE CONSTRAINT IF NOT EXISTS FOR (n:DisputeFocus) REQUIRE n.id IS UNIQUE",
                ]

                for constraint in constraints:
                    try:
                        session.run(constraint)
                        logger.info("✅ 创建约束成功")
                    except Exception as e:
                        # 约束可能已存在
                        logger.debug(f"约束已存在或创建失败: {e}")

                logger.info(f"✅ 图模式初始化完成: {self.namespace}")
                return True

        except Exception as e:
            logger.error(f"❌ 初始化图模式失败: {e!s}")
            return False

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
            with self.driver.session(database=self.database) as session:
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
                        "id": f"legal_article_{self.namespace}_{name}",
                        "name": name,
                        "content": content,
                        "article_type": article_type,
                        "namespace": self.namespace,
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
            with self.driver.session(database=self.database) as session:
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
                        "id": f"judgment_rule_{self.namespace}_{name}",
                        "name": name,
                        "description": description,
                        "applicability": applicability,
                        "core_elements": core_elements,
                        "logic_pattern": logic_pattern,
                        "namespace": self.namespace,
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
            with self.driver.session(database=self.database) as session:
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
                        "namespace": self.namespace,
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

    def create_relation(
        self, edge_type: str, src_id: str, dst_id: str, **properties
    ) -> bool:
        """
        创建关系(边)

        Args:
            edge_type: 关系类型(如 applies_to, derived_from)
            src_id: 源节点ID
            dst_id: 目标节点ID
            **properties: 关系属性

        Returns:
            是否成功
        """
        try:
            with self.driver.session(database=self.database) as session:
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

    def query_by_legal_article(self, article_name: str) -> list[dict[str, Any]]:
        """
        根据法律条文查询相关裁判规则和案例

        Args:
            article_name: 法律条文名称

        Returns:
            查询结果列表
        """
        try:
            with self.driver.session(database=self.database) as session:
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
                    cypher, {"article_id": f"legal_article_{self.namespace}_{article_name}"}
                )

                data = [record.data() for record in result]
                return data

        except Exception as e:
            logger.error(f"❌ 查询失败: {e!s}")
            return []

    def query_shortest_path(self, src_name: str, dst_name: str) -> list[dict[str, Any]]:
        """
        查询最短路径

        Args:
            src_name: 源节点名称
            dst_name: 目标节点名称

        Returns:
            路径列表
        """
        try:
            with self.driver.session(database=self.database) as session:
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

    def print_status(self) -> None:
        """打印图谱状态"""
        if not self.is_connected:
            print("❌ 未连接到Neo4j")
            return

        try:
            print("\n" + "=" * 60)
            print("📊 Neo4j知识图谱状态")
            print("=" * 60)
            print(f"连接: {self.uri}")
            print(f"数据库: {self.database}")
            print(f"命名空间: {self.namespace}")

            with self.driver.session(database=self.database) as session:
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
                            {"namespace": self.namespace},
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
                        {"namespace": self.namespace},
                    )
                    print("\n关系统计:")
                    for record in result:
                        print(f"  {record['rel_type']}: {record['count']}")
                except Exception as e:
                    logger.warning(f"⚠️ 查询关系失败: {e}")

            print("=" * 60 + "\n")

        except Exception as e:
            logger.error(f"❌ 获取状态失败: {e!s}")

    def close(self) -> None:
        """关闭连接"""
        if self.driver:
            self.driver.close()
            self.is_connected = False
            logger.info("✅ Neo4j连接已关闭")


# 便捷函数
def get_neo4j_judgment_client(config: Optional[dict[str, Any]] = None) -> Optional[Neo4jJudgmentClient]:
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


# 兼容层: 保持与旧API的兼容性
class NebulaGraphClient(Neo4jJudgmentClient):
    """
    NebulaGraph客户端兼容层
    保持向后兼容,内部使用Neo4j实现
    """

    def __init__(self, config: Optional[dict[str, Any]] = None):
        # 映射配置
        mapped_config = None
        if config:
            mapped_config = {
                "uri": f"bolt://{config.get('host', '127.0.0.1')}:{config.get('port', 7687)}",
                "username": config.get("user", "neo4j"),
                "password": config.get("password", "password"),
                "database": config.get("space_name", "neo4j"),
                "namespace": config.get("space_name", "patent_judgments"),
            }
        super().__init__(mapped_config)

    def initialize_space(self) -> bool:
        """兼容方法: 初始化空间 -> 初始化图模式"""
        return self.initialize_graph()


def get_nebula_client(config: Optional[dict[str, Any]] = None) -> Optional[NebulaGraphClient]:
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


if __name__ == "__main__":
    # 测试代码
    import os

    # 设置环境变量
    os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
    os.environ.setdefault("NEO4J_USERNAME", "neo4j")
    os.environ.setdefault("NEO4J_PASSWORD", "athena_neo4j_2024")
    os.environ.setdefault("NEO4J_DATABASE", "neo4j")

    # 创建客户端
    client = get_neo4j_judgment_client()

    if client:
        # 初始化图模式
        client.initialize_graph()

        # 打印状态
        client.print_status()

        # 关闭连接
        client.close()

