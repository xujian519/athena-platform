#!/usr/bin/env python3
"""
Neo4j知识图谱构建器
Legal Knowledge Graph Builder for Neo4j

版本: v3.0.0
技术决策: TD-001 - 统一图数据库选择为Neo4j

从PostgreSQL读取法规数据,抽取实体和关系,构建Neo4j知识图谱

核心变更:
- ConnectionPool → GraphDatabase.driver
- nGQL INSERT VERTEX/EDGE → Cypher MERGE语句
- USE space → session database参数
- 配置: addresses+user+password+space → uri+username+password+database

作者: Athena AI Team
创建时间: 2026-01-19
更新时间: 2026-01-25 (TD-001: 迁移到Neo4j)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# 安全查询工具导入
from core.legal_database.citation_extractor import CitationExtractor, ExtractedCitation
from core.legal_database.extractor import ExtractedEntity, ExtractedRelation, HybridLegalExtractor
from core.legal_database.neo4j_schema import (
    EntityType,
    Neo4jQueryBuilder,
    Neo4jSchema,
    RelationType,
)
from core.legal_database.relation_extractor import (
    ExtractedRelation as ExtractedEntityRelation,
)
from core.legal_database.relation_extractor import (
    LegalRelationExtractor,
)

logger = logging.getLogger(__name__)


@dataclass
class GraphBuildStats:
    """图谱构建统计"""

    nodes_created: int = 0
    relationships_created: int = 0
    norms_imported: int = 0
    articles_imported: int = 0
    entities_extracted: int = 0
    relations_imported: int = 0


class Neo4jLegalKnowledgeGraphBuilder:
    """Neo4j法律知识图谱构建器 (TD-001: 替换NebulaGraph)"""

    def __init__(self, neo4j_config: dict[str, Any] | None = None):
        """
        初始化图谱构建器

        Args:
            neo4j_config: Neo4j配置
                {
                    'uri': 'bolt://localhost:7687',
                    'username': 'neo4j',
                    'password': 'password',
                    'database': 'legaldb'
                }
        """
        self.config = neo4j_config or {
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password",
            "database": "legaldb",
        }

        # Neo4j驱动
        self.driver = None

        # 实体抽取器(可选,用于高级实体抽取)
        self.entity_extractor = None
        self.relation_extractor = None

        # 统计信息
        self.stats = GraphBuildStats()

        logger.info("✅ Neo4j图谱构建器初始化完成")
        logger.info(f"   URI: {self.config['uri']}")
        logger.info(f"   Database: {self.config['database']}")

    def connect(self) -> bool:
        """
        连接Neo4j (TD-001: 完整实现)

        Returns:
            是否连接成功
        """
        try:
            # TD-001: 使用Neo4j驱动
            try:
                from neo4j import GraphDatabase
            except ImportError:
                logger.error("❌ neo4j-python未安装")
                logger.info("   安装方法: pip install neo4j")
                return False

            logger.info(f"🔗 连接Neo4j: {self.config['uri']}")

            # 创建驱动
            self.driver = GraphDatabase.driver(
                self.config["uri"],
                auth=(self.config["username"], self.config["password"]),
            )

            # 测试连接
            with self.driver.session(database=self.config["database"]) as session:
                result = session.run("RETURN 'Connection OK' as message")
                record = result.single()
                if not record or record["message"] != "Connection OK":
                    logger.warning("⚠️ Neo4j连接测试失败")
                    return False

            logger.info("✅ Neo4j连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ Neo4j连接失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("📊 Neo4j连接已关闭")

    def initialize_graph(self) -> bool:
        """
        初始化图数据库和Schema (TD-001: 替换initialize_space)

        创建约束和索引

        Returns:
            是否成功
        """
        try:
            logger.info("📋 初始化Neo4j Schema...")

            with self.driver.session(database=self.config["database"]) as session:
                # 创建约束
                constraints = Neo4jSchema.get_all_constraints().split("\n")

                for constraint in constraints:
                    constraint = constraint.strip()
                    if constraint and "CREATE CONSTRAINT" in constraint:
                        try:
                            session.run(constraint)
                            logger.debug(f"✅ 创建约束: {constraint[:50]}...")
                        except Exception as e:
                            if "already exists" not in str(e).lower():
                                logger.warning(f"⚠️  约束创建警告: {e}")

                # 创建全文索引
                try:
                    session.run(
                        """
                        CREATE FULLTEXT INDEX norm_search_index IF NOT EXISTS
                        FOR (n:Norm) ON EACH [n.name, n.category]
                        OPTIONS {indexConfig: {`fulltext.analyzer`: "chinese"}}
                    """
                    )
                    session.run(
                        """
                        CREATE FULLTEXT INDEX article_search_index IF NOT EXISTS
                        FOR (n:Article) ON EACH [n.original_text]
                        OPTIONS {indexConfig: {`fulltext.analyzer`: "chinese"}}
                    """
                    )
                    logger.info("✅ 全文索引创建成功")
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        logger.warning(f"⚠️  索引创建警告: {e}")

            logger.info("✅ Neo4j Schema初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ Schema初始化失败: {e}")
            return False

    def build_from_postgresql(self, pg_conn, limit: int | None = None) -> bool:
        """
        从PostgreSQL构建基础图谱结构

        Args:
            pg_conn: PostgreSQL连接
            limit: 限制导入数量(用于测试)

        Returns:
            是否成功
        """
        try:
            cursor = pg_conn.cursor()

            # 1. 导入法规节点
            logger.info("📥 开始导入法规节点...")

            # 使用参数化查询防止SQL注入
            base_query = """
                SELECT id, name, status, hierarchy, issuing_authority,
                       effective_date, category
                FROM legal_norms
            """
            if limit:
                base_query += " LIMIT %s"
                cursor.execute(base_query, (limit,))
            else:
                cursor.execute(base_query)

            norms = cursor.fetchall()
            for norm in norms:
                self._insert_norm_node(norm)
                self.stats.norms_imported += 1

            logger.info(f"✅ 导入{len(norms)}个法规节点")

            # 2. 导入条款节点
            logger.info("📥 开始导入条款节点...")

            # 使用参数化查询防止SQL注入
            base_query = """
                SELECT c.id, c.norm_id, c.article_number, c.original_text, c.hierarchy_path
                FROM legal_clauses c
            """
            if limit:
                base_query += " LIMIT %s"
                cursor.execute(base_query, (limit,))
            else:
                cursor.execute(base_query)

            clauses = cursor.fetchall()
            for clause in clauses:
                self._insert_article_node(clause)
                self.stats.articles_imported += 1

            logger.info(f"✅ 导入{len(clauses)}个条款节点")

            # 3. 创建CONTAINS关系(法规包含条款)
            logger.info("🔗 创建结构关系...")

            # 使用参数化查询防止SQL注入
            base_query = """
                SELECT c.norm_id, c.id
                FROM legal_clauses c
            """
            if limit:
                base_query += " LIMIT %s"
                cursor.execute(base_query, (limit,))
            else:
                cursor.execute(base_query)

            for norm_id, clause_id in cursor:
                self._insert_contains_relationship(norm_id, clause_id)
                self.stats.relationships_created += 1

            logger.info(f"✅ 创建{self.stats.relationships_created}条结构关系")

            return True

        except Exception as e:
            logger.error(f"❌ 从PostgreSQL构建失败: {e}")
            return False

    def extract_and_import_entities(
        self,
        pg_conn,
        use_rule_extraction: bool = True,
        use_cloud_llm: bool = False,
        limit: int | None = None,
    ) -> bool:
        """
        抽取实体并导入到知识图谱

        Args:
            pg_conn: PostgreSQL连接
            use_rule_extraction: 是否使用规则抽取
            use_cloud_llm: 是否使用云端LLM
            limit: 限制处理数量

        Returns:
            是否成功
        """
        try:
            # 初始化实体抽取器和关系抽取器
            if use_rule_extraction or use_cloud_llm:
                self.entity_extractor = HybridLegalExtractor(
                    {
                        "use_rule_extraction": use_rule_extraction,
                        "use_cloud_llm": use_cloud_llm,
                        "cloud_llm_ratio": 0.05,  # 仅5%使用云端
                    }
                )

                if use_cloud_llm:
                    self.entity_extractor.init_cloud_llm()

            # 初始化关系抽取器
            self.relation_extractor = LegalRelationExtractor()

            cursor = pg_conn.cursor()

            # 获取条款列表
            # 使用参数化查询防止SQL注入
            base_query = """
                SELECT c.id, c.original_text, n.name
                FROM legal_clauses c
                JOIN legal_norms n ON c.norm_id = n.id
            """
            if limit:
                base_query += " LIMIT %s"
                cursor.execute(base_query, (limit,))
            else:
                cursor.execute(base_query)

            clauses = cursor.fetchall()

            logger.info(f"🔄 开始抽取实体和关系({len(clauses)}个条款)...")

            for clause_id, clause_text, _norm_name in clauses:
                try:
                    # 抽取实体
                    entities, _ = self.entity_extractor.extract_from_clause(
                        clause_text, clause_id, importance_score=0.5
                    )

                    # 导入实体
                    for entity in entities:
                        self._insert_entity_node(entity, clause_id)
                        self.stats.entities_extracted += 1

                    # 抽取关系
                    relations = self.relation_extractor.extract_relations(
                        entities, clause_text, clause_id
                    )

                    # 导入关系
                    for relation in relations:
                        self._insert_entity_relationship(relation)
                        self.stats.relations_imported += 1

                    # 每处理1000个条款输出一次进度
                    if self.relation_extractor.stats["total_clauses"] % 1000 == 0:
                        logger.info(
                            f"  已处理 {self.relation_extractor.stats['total_clauses']} 个条款..."
                        )

                except Exception as e:
                    logger.warning(f"⚠️  实体/关系抽取失败 {clause_id}: {e}")

            logger.info(f"✅ 抽取并导入{self.stats.entities_extracted}个实体")
            logger.info(f"✅ 抽取并导入{self.stats.relations_imported}条关系")

            # 打印统计
            if self.entity_extractor:
                self.entity_extractor.print_stats()
            if self.relation_extractor:
                self.relation_extractor.print_stats()

            return True

        except Exception as e:
            logger.error(f"❌ 实体抽取失败: {e}")
            return False

    def _execute_cypher(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """
        执行Cypher语句 (TD-001: 替换_execute_statement)

        Args:
            query: Cypher查询语句
            params: 查询参数

        Returns:
            查询结果
        """
        if not self.driver:
            raise RuntimeError("未连接到Neo4j")

        with self.driver.session(database=self.config["database"]) as session:
            result = session.run(query, params or {})
            return result

    def _insert_norm_node(self, norm_data: tuple):
        """
        插入法规节点 (TD-001: 替_insert_norm_vertex)

        Args:
            norm_data: 法规数据元组
        """
        norm_id, name, status, hierarchy, issuing_authority, effective_date, category = norm_data

        # 生成节点ID (使用原始norm_id作为唯一标识)
        node_id = str(norm_id)

        # 构建属性
        props = {
            "id": node_id,
            "name": name or "",
            "status": status or "现行有效",
            "hierarchy": hierarchy or "",
            "issuing_authority": issuing_authority or "",
            "effective_date": str(effective_date) if effective_date else "",
            "category": category or "",
        }

        # Cypher MERGE语句
        cypher = """
            MERGE (n:Norm {id: $id})
            SET n.name = $name,
                n.status = $status,
                n.hierarchy = $hierarchy,
                n.issuing_authority = $issuing_authority,
                n.effective_date = $effective_date,
                n.category = $category
            RETURN n.id as id
        """

        try:
            self._execute_cypher(cypher, props)
            self.stats.nodes_created += 1
        except Exception as e:
            logger.error(f"❌ 法规节点插入失败 {norm_id}: {e}")

    def _insert_article_node(self, clause_data: tuple):
        """
        插入条款节点 (TD-001: 替换_insert_article_vertex)

        Args:
            clause_data: 条款数据元组
        """
        clause_id, _norm_id, article_number, original_text, hierarchy_path = clause_data

        # 生成节点ID
        node_id = str(clause_id)

        # 截断过长的文本
        text = (original_text or "")[:500]

        # Cypher MERGE语句
        cypher = """
            MERGE (n:Article {id: $id})
            SET n.article_number = $article_number,
                n.original_text = $original_text,
                n.hierarchy_path = $hierarchy_path
            RETURN n.id as id
        """

        props = {
            "id": node_id,
            "article_number": article_number or "",
            "original_text": text,
            "hierarchy_path": hierarchy_path or "",
        }

        try:
            self._execute_cypher(cypher, props)
            self.stats.nodes_created += 1
        except Exception as e:
            logger.error(f"❌ 条款节点插入失败 {clause_id}: {e}")

    def _insert_entity_node(self, entity: ExtractedEntity, clause_id: str):
        """
        插入实体节点 (TD-001: 替换_insert_entity_vertex)

        Args:
            entity: 抽取的实体
            clause_id: 条款ID
        """
        # 根据实体类型选择Label
        label_map = {
            "Subject": "Subject",
            "Action": "Action",
            "Right": "Right",
            "Obligation": "Obligation",
            "Liability": "Liability",
        }

        label = label_map.get(entity.entity_type, "Subject")

        # 生成节点ID
        node_id = Neo4jQueryBuilder.create_node_id(label, entity.entity_name)

        # Cypher MERGE语句
        cypher = f"""
            MERGE (n:{label} {{id: $id}})
            SET n.name = $name,
                n.type = $type,
                n.description = $description
            RETURN n.id as id
        """

        props = {
            "id": node_id,
            "name": entity.entity_name,
            "type": entity.entity_type,
            "description": (entity.entity_text or "")[:100],
        }

        try:
            self._execute_cypher(cypher, props)
            self.stats.nodes_created += 1
        except Exception as e:
            # 可能是重复插入,忽略
            logger.debug(f"实体节点插入已存在: {node_id}")

    def _insert_contains_relationship(self, norm_id: str, clause_id: str):
        """
        插入CONTAINS关系 (TD-001: 替换_insert_contains_edge)

        Args:
            norm_id: 法规ID
            clause_id: 条款ID
        """
        # Cypher MERGE语句
        cypher = """
            MATCH (norm:Norm {id: $norm_id})
            MATCH (article:Article {id: $article_id})
            MERGE (norm)-[r:CONTAINS]->(article)
            SET r.hierarchy_type = 'article'
            RETURN type(r) as rel_type
        """

        props = {
            "norm_id": str(norm_id),
            "article_id": str(clause_id),
        }

        try:
            self._execute_cypher(cypher, props)
        except Exception as e:
            logger.warning(f"⚠️  关系插入失败 {norm_id}->{clause_id}: {e}")

    def print_stats(self):
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 知识图谱构建统计")
        logger.info("=" * 60)
        logger.info(f"📁 节点总数: {self.stats.nodes_created}")
        logger.info(f"  - 法规节点: {self.stats.norms_imported}")
        logger.info(f"  - 条款节点: {self.stats.articles_imported}")
        logger.info(f"  - 实体节点: {self.stats.entities_extracted}")
        logger.info(f"🔗 关系总数: {self.stats.relationships_created}")
        logger.info("=" * 60 + "\n")

    def import_citation_relations(self, pg_conn, limit: int | None = None) -> int:
        """
        导入引用关系到知识图谱

        Args:
            pg_conn: PostgreSQL连接
            limit: 限制处理数量

        Returns:
            导入的引用关系数量
        """
        try:
            # 主游标:用于迭代条款
            cursor = pg_conn.cursor()

            # 查询游标:用于查找法规(避免中断主游标迭代)
            lookup_cursor = pg_conn.cursor()

            # 获取所有条款
            # 使用参数化查询防止SQL注入
            base_query = """
                SELECT c.id, c.original_text, c.norm_id
                FROM legal_clauses c
            """
            if limit:
                base_query += " LIMIT %s"
                cursor.execute(base_query, (limit,))
            else:
                cursor.execute(base_query)

            extractor = CitationExtractor()
            citation_count = 0

            logger.info("🔄 开始抽取引用关系...")

            for clause_id, clause_text, norm_id in cursor:
                # 抽取引用
                citations = extractor.extract_from_clause(clause_text, clause_id)

                # 导入引用关系
                for citation in citations:
                    # 跳过自引用
                    if citation.target_norm_name == "[同一法规]":
                        continue

                    # 查找被引用法规的ID(使用单独的游标)
                    target_norm_id = self._find_norm_id_by_name(
                        lookup_cursor, citation.target_norm_name
                    )
                    if target_norm_id:
                        self._insert_citation_relationship(norm_id, target_norm_id, citation)
                        citation_count += 1

                # 每处理1000个条款输出一次进度
                if extractor.stats["total_clauses"] % 1000 == 0:
                    logger.info(f"  已处理 {extractor.stats['total_clauses']} 个条款...")

            logger.info(f"✅ 导入{citation_count}条引用关系")
            extractor.print_stats()

            # 关闭游标
            lookup_cursor.close()
            cursor.close()

            return citation_count

        except Exception as e:
            logger.error(f"❌ 引用关系导入失败: {e}")
            import traceback

            traceback.print_exc()
            return 0

    def _find_norm_id_by_name(
        self, cursor, norm_name: str, fuzzy_threshold: float = 0.6
    ) -> str | None:
        """
        根据法规名称查找ID(支持模糊匹配)

        Args:
            cursor: PostgreSQL游标
            norm_name: 法规名称
            fuzzy_threshold: 模糊匹配阈值

        Returns:
            法规ID,如果未找到则返回None
        """
        try:
            # 1. 精确匹配
            cursor.execute(
                """
                SELECT id FROM legal_norms
                WHERE name = %s
                LIMIT 1
            """,
                (norm_name,),
            )

            result = cursor.fetchone()
            if result:
                return result[0]

            # 2. 包含匹配
            cursor.execute(
                """
                SELECT id, name FROM legal_norms
                WHERE name LIKE %s
                LIMIT 5
            """,
                (f"%{norm_name}%",),
            )

            results = cursor.fetchall()
            if results:
                # 返回第一个匹配项
                return results[0][0]

            # 3. 简化匹配(去除"法"、"条例"等后缀)
            simplified_name = norm_name.replace("法", "").replace("条例", "").replace("规定", "")
            if simplified_name != norm_name:
                cursor.execute(
                    """
                    SELECT id FROM legal_norms
                    WHERE name LIKE %s
                    LIMIT 1
                """,
                    (f"%{simplified_name}%",),
                )

                result = cursor.fetchone()
                if result:
                    return result[0]

            return None

        except Exception as e:
            logger.warning(f"⚠️  法规名称查找失败 {norm_name}: {e}")
            return None

    def _insert_citation_relationship(self, source_id: str, target_id: str, citation: ExtractedCitation):
        """
        插入CITES关系 (TD-001: 替换_insert_citation_edge)

        Args:
            source_id: 源法规ID
            target_id: 目标法规ID
            citation: 引用信息
        """
        # Cypher MERGE语句
        cypher = """
            MATCH (src:Norm {id: $src_id})
            MATCH (dst:Norm {id: $dst_id})
            MERGE (src)-[r:CITES]->(dst)
            SET r.citation_type = $citation_type,
                r.context = $context
            RETURN type(r) as rel_type
        """

        # 转义特殊字符
        context = (citation.context or "")[:100]

        props = {
            "src_id": str(source_id),
            "dst_id": str(target_id),
            "citation_type": citation.citation_type,
            "context": context,
        }

        try:
            self._execute_cypher(cypher, props)
            self.stats.relationships_created += 1
        except Exception:
            # 可能是重复插入,忽略
            pass

    def _insert_entity_relationship(self, relation: ExtractedEntityRelation):
        """
        插入实体关系 (TD-001: 替换_insert_entity_relation)

        Args:
            relation: 实体关系
        """
        # 生成节点ID
        src_id = Neo4jQueryBuilder.create_node_id(relation.from_type, relation.from_entity)
        dst_id = Neo4jQueryBuilder.create_node_id(relation.to_type, relation.to_entity)

        # 选择关系类型
        rel_type = relation.relation_type

        # 插入关系(带置信度过滤 - 优化阈值)
        if relation.confidence < 0.75:  # 提高阈值,过滤低质量关系
            return

        # 额外质量过滤
        # 1. 过滤过短的目标实体
        if len(relation.to_entity) < 4:
            return

        # 2. 过滤包含常见噪声词的关系
        noise_words = ["其他", "等", "有关", "相关", "按照", "根据", "依照", "依据"]
        if any(word in relation.to_entity for word in noise_words):
            # 如果整个to_entity就是噪声词,则过滤
            if relation.to_entity.strip() in noise_words:
                return

        # 根据关系类型设置属性
        if rel_type == "IMPOSES_ON":
            prop_key = "obligation_type"
            prop_value = "statutory"
        elif rel_type == "GRANTS_TO":
            prop_key = "right_type"
            prop_value = "legal"
        elif rel_type == "REGULATES":
            prop_key = "regulation_type"
            prop_value = "behavioral"
        else:
            prop_key = None
            prop_value = None

        # Cypher MERGE语句
        if prop_key:
            cypher = f"""
                MATCH (src {{id: $src_id}})
                MATCH (dst {{id: $dst_id}})
                MERGE (src)-[r:{rel_type}]->(dst)
                SET r.{prop_key} = ${prop_key}
                RETURN type(r) as rel_type
            """
            props = {
                "src_id": src_id,
                "dst_id": dst_id,
                prop_key: prop_value,
            }
        else:
            cypher = f"""
                MATCH (src {{id: $src_id}})
                MATCH (dst {{id: $dst_id}})
                MERGE (src)-[r:{rel_type}]->(dst)
                RETURN type(r) as rel_type
            """
            props = {
                "src_id": src_id,
                "dst_id": dst_id,
            }

        try:
            self._execute_cypher(cypher, props)
            self.stats.relationships_created += 1
        except Exception:
            # 可能是重复插入或关系不存在,忽略
            pass


# ========== 便捷函数 ==========


def build_legal_knowledge_graph(
    pg_conn,
    neo4j_config: dict[str, Any] | None = None,
    use_rule_extraction: bool = True,
    use_cloud_llm: bool = False,
    limit: int | None = None,
) -> bool:
    """
    构建法律知识图谱

    Args:
        pg_conn: PostgreSQL连接
        neo4j_config: Neo4j配置
        use_rule_extraction: 是否使用规则抽取实体
        use_cloud_llm: 是否使用云端LLM抽取实体
        limit: 限制导入数量

    Returns:
        是否成功
    """
    builder = Neo4jLegalKnowledgeGraphBuilder(neo4j_config)

    try:
        # 连接
        if not builder.connect():
            return False

        # 初始化Schema
        if not builder.initialize_graph():
            return False

        # 从PostgreSQL导入基础结构
        if not builder.build_from_postgresql(pg_conn, limit):
            return False

        # 抽取并导入实体
        if use_rule_extraction or use_cloud_llm:
            builder.extract_and_import_entities(
                pg_conn,
                use_rule_extraction=use_rule_extraction,
                use_cloud_llm=use_cloud_llm,
                limit=limit,
            )

        # 打印统计
        builder.print_stats()

        return True

    finally:
        builder.close()


# ========== 兼容层: 保持与旧API的兼容性 ==========

# 导入旧名称以保持向后兼容
LegalKnowledgeGraphBuilder = Neo4jLegalKnowledgeGraphBuilder


# 使用示例
if __name__ == "__main__":
    print("=" * 80)
    print("🧪 Neo4j法律知识图谱构建器测试 v3.0.0")
    print("=" * 80)
    print()

    print("TD-001迁移说明:")
    print("- 替换NebulaGraph为Neo4j")
    print("- 使用Cypher查询语言替代nGQL")
    print("- 更新配置参数为Neo4j标准")
    print("- initialize_space() → initialize_graph()")
    print("- _insert_*_vertex() → _insert_*_node()")
    print("- _insert_*_edge() → _insert_*_relationship()")
    print()
