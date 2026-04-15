#!/usr/bin/env python3
"""
NebulaGraph知识图谱构建器
Legal Knowledge Graph Builder for NebulaGraph

从PostgreSQL读取法规数据,抽取实体和关系,构建NebulaGraph知识图谱
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool

# 安全查询工具导入
from core.legal_database.citation_extractor import CitationExtractor, ExtractedCitation
from core.legal_database.extractor import ExtractedEntity, HybridLegalExtractor
from core.legal_database.nebula_schema import (
    NebulaQueryBuilder,
    NebulaSchema,
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

    vertices_created: int = 0
    edges_created: int = 0
    norms_imported: int = 0
    articles_imported: int = 0
    entities_extracted: int = 0
    relations_imported: int = 0  # 实体关系导入数量


class LegalKnowledgeGraphBuilder:
    """法律知识图谱构建器"""

    def __init__(self, nebula_config: dict[str, Any] | None = None):
        """
        初始化图谱构建器

        Args:
            nebula_config: NebulaGraph配置
        """
        self.config = nebula_config or {
            "addresses": ["127.0.0.1:9669"],
            "user": "root",
            "password": "nebula",
            "space": "legal_knowledge",
        }

        # 连接池
        self.connection_pool = None
        self.session = None

        # 实体抽取器(可选,用于高级实体抽取)
        self.entity_extractor = None

        # 统计信息
        self.stats = GraphBuildStats()

    def connect(self) -> bool:
        """连接NebulaGraph"""
        try:
            # 初始化连接池
            config = Config()
            config.max_connection_pool_size = 10

            # 解析地址
            addresses = []
            for addr in self.config["addresses"]:
                # 支持两种格式: "host:port" 或 ("host", port)
                if isinstance(addr, str):
                    parts = addr.split(":")
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else 9669
                    addresses.append((host, port))
                else:
                    addresses.append(addr)

            logger.info(f"🔗 连接NebulaGraph: {addresses}")

            self.connection_pool = ConnectionPool()
            self.connection_pool.init(addresses, config)

            # 获取session
            self.session = self.connection_pool.get_session(
                self.config["user"], self.config["password"]
            )

            logger.info("✅ NebulaGraph连接成功")
            return True

        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.session:
            self.session.release()
        if self.connection_pool:
            self.connection_pool.close()
        logger.info("📊 NebulaGraph连接已关闭")

    def initialize_space(self) -> bool:
        """初始化图空间和Schema"""
        try:
            import time

            # 首先添加存储主机(如果尚未添加)
            logger.info("📋 检查并添加存储主机...")
            try:
                # 尝试添加storaged主机
                self._execute_statement('ADD HOSTS "athena_nebula_storaged":9779;')
                logger.info("✅ 存储主机已添加")
            except Exception:
                logger.info("ℹ️  存储主机可能已存在")

            # 等待主机上线
            time.sleep(3)

            # 尝试使用图空间
            use_stmt = f"USE {NebulaSchema.SPACE_NAME};"
            self._execute_statement(use_stmt)
            logger.info(f"ℹ️  图空间 {NebulaSchema.SPACE_NAME} 已存在")

            # 创建Schema(Tag和Edge)
            tags = NebulaSchema.get_all_tags()
            edges = NebulaSchema.get_all_edges()

            # 执行Tag创建
            for tag_stmt in tags.split(";"):
                tag_stmt = tag_stmt.strip()
                if tag_stmt and "CREATE TAG" in tag_stmt:
                    try:
                        self._execute_statement(tag_stmt)
                    except Exception as e:
                        if "existed" not in str(e):
                            logger.warning(f"⚠️  Tag创建警告: {e}")

            # 执行Edge创建
            for edge_stmt in edges.split(";"):
                edge_stmt = edge_stmt.strip()
                if edge_stmt and "CREATE EDGE" in edge_stmt:
                    try:
                        self._execute_statement(edge_stmt)
                    except Exception as e:
                        if "existed" not in str(e):
                            logger.warning(f"⚠️  Edge创建警告: {e}")

            logger.info("✅ NebulaGraph Schema初始化完成")
            return True

        except Exception as e:
            # 如果使用失败,尝试创建图空间
            error_str = str(e)
            if "SpaceNotFound" in error_str or "Space not found" in error_str:
                logger.info("ℹ️  图空间不存在,正在创建...")
                try:
                    create_space_stmt = NebulaSchema.get_create_space_statement()
                    self._execute_statement(create_space_stmt)

                    # 等待图空间创建完成
                    import time

                    logger.info("⏳ 等待图空间创建完成...")
                    time.sleep(15)  # 等待15秒让图空间完全初始化

                    # 重新使用图空间
                    use_stmt = f"USE {NebulaSchema.SPACE_NAME};"
                    self._execute_statement(use_stmt)

                    # 创建Schema
                    tags = NebulaSchema.get_all_tags()
                    edges = NebulaSchema.get_all_edges()

                    for tag_stmt in tags.split(";"):
                        tag_stmt = tag_stmt.strip()
                        if tag_stmt and "CREATE TAG" in tag_stmt:
                            self._execute_statement(tag_stmt)

                    for edge_stmt in edges.split(";"):
                        edge_stmt = edge_stmt.strip()
                        if edge_stmt and "CREATE EDGE" in edge_stmt:
                            self._execute_statement(edge_stmt)

                    logger.info("✅ NebulaGraph Schema初始化完成")
                    return True

                except Exception as create_error:
                    logger.error(f"❌ 图空间创建失败: {create_error}")
                    return False
            else:
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
                self._insert_norm_vertex(norm)
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
                self._insert_article_vertex(clause)
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
                self._insert_contains_edge(norm_id, clause_id)
                self.stats.edges_created += 1

            logger.info(f"✅ 创建{self.stats.edges_created}条结构关系")

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
                        self._insert_entity_vertex(entity, clause_id)
                        self.stats.entities_extracted += 1

                    # 抽取关系
                    relations = self.relation_extractor.extract_relations(
                        entities, clause_text, clause_id
                    )

                    # 导入关系
                    for relation in relations:
                        self._insert_entity_relation(relation)
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

    def _execute_statement(self, stmt: str) -> Any:
        """执行NebulaGraph语句"""
        if not self.session:
            raise RuntimeError("未连接到NebulaGraph")

        # 将USE语句和实际语句合并执行
        combined_stmt = f"USE {NebulaSchema.SPACE_NAME}; {stmt}"
        result = self.session.execute(combined_stmt)

        if not result.is_succeeded():
            error_msg = result.error_msg()
            logger.error(f"❌ 语句执行失败: {error_msg}")
            raise RuntimeError(error_msg)

        return result

    def _insert_norm_vertex(self, norm_data: tuple):
        """插入法规顶点"""
        norm_id, name, status, hierarchy, issuing_authority, effective_date, category = norm_data

        # 生成顶点ID
        vertex_id = NebulaQueryBuilder.create_vertex_id("Norm", norm_id)

        # 构建属性
        props = {
            "id": norm_id,
            "name": name,
            "status": status or "现行有效",
            "hierarchy": hierarchy or "",
            "issuing_authority": issuing_authority or "",
            "effective_date": str(effective_date) if effective_date else "",
            "category": category or "",
        }

        # 插入
        stmt = f"""
            INSERT VERTEX Norm(
                id, name, status, hierarchy,
                issuing_authority, effective_date, category
            ) VALUES "{vertex_id}": (
                "{props["id"]}", "{props["name"]}", "{props["status"]}",
                "{props["hierarchy"]}", "{props["issuing_authority"]}",
                "{props["effective_date"]}", "{props["category"]}"
            );
        """

        self._execute_statement(stmt)
        self.stats.vertices_created += 1

    def _insert_article_vertex(self, clause_data: tuple):
        """插入条款顶点"""
        clause_id, _norm_id, article_number, original_text, hierarchy_path = clause_data

        # 生成顶点ID
        vertex_id = NebulaQueryBuilder.create_vertex_id("Article", clause_id)

        # 截断过长的文本
        text = original_text[:500] if original_text else ""

        # 插入
        escaped_text = text.replace('"', '\\"')
        stmt = f'''
            INSERT VERTEX Article(id, article_number, original_text, hierarchy_path)
            VALUES "{vertex_id}": (
                "{clause_id}", "{article_number or ""}", "{escaped_text}",
                "{hierarchy_path or ""}"
            );
        '''

        self._execute_statement(stmt)
        self.stats.vertices_created += 1

    def _insert_entity_vertex(self, entity: ExtractedEntity, clause_id: str):
        """插入实体顶点"""
        # 根据实体类型选择Tag
        tag_map = {
            "Subject": "Subject",
            "Action": "Action",
            "Right": "Right",
            "Obligation": "Obligation",
            "Liability": "Liability",
        }

        tag = tag_map.get(entity.entity_type, "Subject")

        # 生成顶点ID
        vertex_id = NebulaQueryBuilder.create_vertex_id(tag, entity.entity_name)

        # 插入(忽略重复)
        try:
            escaped_entity_text = entity.entity_text[:100].replace('"', '\\"')
            stmt = f'''
                INSERT VERTEX {tag}(id, name, type, description)
                VALUES "{vertex_id}": (
                    "{vertex_id}", "{entity.entity_name}", "{entity.entity_type}",
                    "{escaped_entity_text}"
                );
            '''
            self._execute_statement(stmt)
            self.stats.vertices_created += 1
        except (TypeError, ZeroDivisionError) as e:
            logger.warning(f"计算时发生错误: {e}")
        except Exception as e:
            logger.error(f"未预期的错误: {e}")
            # 可能是重复插入,忽略
            pass

    def _insert_contains_edge(self, norm_id: str, clause_id: str):
        """插入CONTAINS关系"""
        src_id = NebulaQueryBuilder.create_vertex_id("Norm", norm_id)
        dst_id = NebulaQueryBuilder.create_vertex_id("Article", clause_id)

        stmt = f"""
            INSERT EDGE CONTAINS(hierarchy_type)
            VALUES "{src_id}"->"{dst_id}": ("article");
        """

        try:
            self._execute_statement(stmt)
        except Exception as e:
            logger.warning(f"⚠️  边插入失败 {norm_id}->{clause_id}: {e}")

    def print_stats(self):
        """打印统计信息"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 知识图谱构建统计")
        logger.info("=" * 60)
        logger.info(f"📁 顶点总数: {self.stats.vertices_created}")
        logger.info(f"  - 法规节点: {self.stats.norms_imported}")
        logger.info(f"  - 条款节点: {self.stats.articles_imported}")
        logger.info(f"  - 实体节点: {self.stats.entities_extracted}")
        logger.info(f"🔗 边总数: {self.stats.edges_created}")
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
                        self._insert_citation_edge(norm_id, target_norm_id, citation)
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

    def _insert_citation_edge(self, source_id: str, target_id: str, citation: ExtractedCitation):
        """插入CITES边"""
        src_vid = NebulaQueryBuilder.create_vertex_id("Norm", source_id)
        dst_vid = NebulaQueryBuilder.create_vertex_id("Norm", target_id)

        # 转义特殊字符
        context = citation.context[:100].replace('"', '\\"').replace("'", "\\'")

        stmt = f"""
            INSERT EDGE CITES(citation_type, context)
            VALUES "{src_vid}"->"{dst_vid}": (
                "{citation.citation_type}",
                "{context}"
            );
        """
        try:
            self._execute_statement(stmt)
            self.stats.edges_created += 1
        except Exception:
            # 可能是重复插入,忽略
            pass

    def _insert_entity_relation(self, relation: ExtractedEntityRelation):
        """插入实体关系(优化版)"""
        # 生成顶点ID
        src_id = NebulaQueryBuilder.create_vertex_id(relation.from_type, relation.from_entity)
        dst_id = NebulaQueryBuilder.create_vertex_id(relation.to_type, relation.to_entity)

        # 选择边类型
        edge_type = relation.relation_type

        # 插入边(带置信度过滤 - 优化阈值)
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

        # 根据边类型设置属性
        if edge_type == "IMPOSES_ON":
            props = "obligation_type"
            prop_value = '"statutory"'
        elif edge_type == "GRANTS_TO":
            props = "right_type"
            prop_value = '"legal"'
        elif edge_type == "REGULATES":
            props = "regulation_type"
            prop_value = '"behavioral"'
        else:
            props = ""
            prop_value = ""

        if props:
            stmt = f"""
                INSERT EDGE {edge_type}({props})
                VALUES "{src_id}"->"{dst_id}": ({prop_value});
            """
        else:
            stmt = f"""
                INSERT EDGE {edge_type}()
                VALUES "{src_id}"->"{dst_id}": ();
            """

        try:
            self._execute_statement(stmt)
            self.stats.edges_created += 1
        except Exception:
            # 可能是重复插入或关系不存在,忽略
            pass


# ========== 便捷函数 ==========


def build_legal_knowledge_graph(
    pg_conn,
    nebula_config: dict[str, Any] | None = None,
    use_rule_extraction: bool = True,
    use_cloud_llm: bool = False,
    limit: int | None = None,
) -> bool:
    """
    构建法律知识图谱

    Args:
        pg_conn: PostgreSQL连接
        nebula_config: NebulaGraph配置
        use_rule_extraction: 是否使用规则抽取实体
        use_cloud_llm: 是否使用云端LLM抽取实体
        limit: 限制导入数量

    Returns:
        是否成功
    """
    builder = LegalKnowledgeGraphBuilder(nebula_config)

    try:
        # 连接
        if not builder.connect():
            return False

        # 初始化Schema
        if not builder.initialize_space():
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
